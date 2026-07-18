"""Phase 6 Sprint 8 — AI Enterprise Security, Compliance & Audit Engine tests."""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ES = ROOT / "app" / "services" / "enterprise_security"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("RTAS_JWT_SECRET", "unit-test-jwt-secret-key-32b")
os.environ.setdefault("AI_BACKEND_SECRET", "unit-test-backend-secret-32b")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_parents(pkg_name: str):
    parts = pkg_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            mod = type(sys)(parent)
            mod.__path__ = []
            sys.modules[parent] = mod
    if "app" in sys.modules:
        sys.modules["app"].__path__ = [str(ROOT / "app")]
    if "app.services" in sys.modules:
        sys.modules["app.services"].__path__ = [str(ROOT / "app" / "services")]


def _load_pkg():
    _ensure_parents("app.services.enterprise_security")
    pkg = type(sys)("app.services.enterprise_security")
    pkg.__path__ = [str(ES)]
    sys.modules["app.services.enterprise_security"] = pkg
    for name in (
        "version",
        "models",
        "store",
        "secrets",
        "auth",
        "rbac",
        "api_security",
        "policies",
        "audit",
        "compliance",
        "observability",
        "engine",
    ):
        _load(f"app.services.enterprise_security.{name}", ES / f"{name}.py")
    eng = sys.modules["app.services.enterprise_security.engine"]
    ver = sys.modules["app.services.enterprise_security.version"]
    pkg.ENGINE_NAME = ver.ENGINE_NAME
    pkg.ENGINE_VERSION = ver.ENGINE_VERSION
    pkg.ENGINE_LABEL = ver.ENGINE_LABEL
    pkg.get_security_engine = eng.get_security_engine
    pkg.reset_engine = eng.reset_engine


_load_pkg()

version = sys.modules["app.services.enterprise_security.version"]
secrets = sys.modules["app.services.enterprise_security.secrets"]
auth = sys.modules["app.services.enterprise_security.auth"]
rbac = sys.modules["app.services.enterprise_security.rbac"]
api_security = sys.modules["app.services.enterprise_security.api_security"]
compliance = sys.modules["app.services.enterprise_security.compliance"]
engine_mod = sys.modules["app.services.enterprise_security.engine"]


def setup_function():
    engine_mod.reset_engine()


def test_version_unit():
    assert version.ENGINE_VERSION == "1.0.0"
    assert version.PHASE == 6
    assert version.SPRINT == 8


def test_secrets_from_environment_only():
    report = secrets.secret_validation_report()
    assert report["source"] == "environment_variables_only"
    assert report["hardcoded_secrets_allowed"] is False
    assert secrets.get_secret("RTAS_JWT_SECRET")
    assert "sk-live-" in secrets.scan_text_for_hardcoded_secrets("token sk-live-abc")


def test_jwt_authentication():
    issued = auth.issue_jwt(subject="alice", role="user", scopes=["read:own"])
    principal = auth.validate_jwt(issued["token"])
    assert principal.subject == "alice"
    assert principal.role == "user"
    try:
        auth.validate_jwt(issued["token"] + "x")
        assert False
    except auth.AuthError:
        pass


def test_session_api_key_service_account():
    sess = auth.create_session(subject="bob", role="team")
    p = auth.validate_session(sess["session_token"])
    assert p.role == "team"
    auth.logout_session(sess["session_token"])
    try:
        auth.validate_session(sess["session_token"])
        assert False
    except auth.AuthError:
        pass

    key = "rtas-test-api-key-123456"
    auth.register_api_key(api_key=key, subject="svc-user", role="user")
    assert auth.validate_api_key(key).subject == "svc-user"

    auth.register_service_account(account_id="svc_render")
    sa = auth.validate_service_account("svc_render", os.environ["AI_BACKEND_SECRET"])
    assert sa.auth_method == "service_account"


def test_rbac_authorization():
    user = auth.issue_jwt(subject="u", role="user")["principal"]
    from app.services.enterprise_security.models import Principal

    up = Principal(**user)
    rbac.require_permission(up, "job:create")
    try:
        rbac.require_permission(up, "admin:action")
        assert False
    except rbac.AccessDenied:
        pass
    admin = Principal(**auth.issue_jwt(subject="a", role="admin")["principal"])
    rbac.require_permission(admin, "admin:action")
    rbac.require_role(admin, "team")


def test_api_security_layer():
    api_security.sanitize_input("safe prompt about desert sunrise")
    try:
        api_security.sanitize_input("<script>alert(1)</script>")
        assert False
    except api_security.ApiSecurityError:
        pass

    body = '{"hello":"world"}'
    ts = str(int(time.time()))
    sig = engine_mod.sign_body(body, ts)
    assert api_security.validate_api_signature(body=body, signature=sig, timestamp=ts)

    sess = "sess_abc123"
    csrf = api_security.csrf_token_for_session(sess)
    assert api_security.validate_csrf(csrf, sess)
    api_security.validate_cors_origin("http://localhost:3000")
    api_security.check_replay_protection("nonce-one-1234", timestamp=ts)
    try:
        api_security.check_replay_protection("nonce-one-1234", timestamp=ts)
        assert False
    except api_security.ApiSecurityError:
        pass
    headers = api_security.secure_headers()
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_security_validate_endpoint_logic():
    eng = engine_mod.get_security_engine()
    token = eng.issue_token(subject="carol", role="admin")["token"]
    result = eng.validate(
        {
            "auth_method": "jwt",
            "credential": token,
            "permission": "security:manage",
            "prompt": "generate cinematic shot",
            "nonce": "validate-nonce-001",
            "timestamp": str(int(time.time())),
            "origin": "http://localhost:3000",
            "track_action": "job_creation",
            "resource": "jobs",
        }
    )
    assert result["valid"] is True
    assert result["checks"]["authentication"] is True
    assert result["checks"]["authorization"] is True


def test_unauthorized_and_failed_login_tracking():
    eng = engine_mod.get_security_engine()
    bad = eng.validate({"auth_method": "jwt", "credential": "not.a.jwt", "actor_id": "eve"})
    assert bad["valid"] is False
    events = eng.events()
    assert events["count"] >= 1
    obs = eng.status()["observability"]
    assert "failed_logins" in obs or obs["unauthorized_requests"] >= 0


def test_compliance_and_consent():
    eng = engine_mod.get_security_engine()
    compliance.record_consent("user_1", marketing=False, analytics=True, terms_accepted=True)
    report = eng.compliance()
    assert report["compliance"]["consent_count"] >= 1
    assert report["privacy_controls"]["user_consent_framework"] is True
    activity = compliance.account_activity_report("user_1")
    assert activity["user_id"] == "user_1"


def test_audit_actions_coverage():
    eng = engine_mod.get_security_engine()
    token = eng.issue_token(subject="auditor", role="admin")["token"]
    for action in (
        "job_creation",
        "job_cancellation",
        "ai_provider_usage",
        "export_request",
        "download",
        "admin_action",
    ):
        eng.validate(
            {
                "auth_method": "jwt",
                "credential": token,
                "track_action": action,
                "resource": action,
                "nonce": f"aud-{action}-{time.time_ns()}",
            }
        )
    audits = eng.audit_logs(limit=100)
    actions = {a["action"] for a in audits["audits"]}
    assert "job_creation" in actions
    assert "admin_action" in actions


def test_stress_validate_and_rate_limit():
    eng = engine_mod.get_security_engine()
    token = eng.issue_token(subject="stress", role="user")["token"]
    t0 = time.perf_counter()
    ok = 0
    for i in range(80):
        r = eng.validate(
            {
                "auth_method": "jwt",
                "credential": token,
                "actor_id": "stress",
                "prompt": f"safe prompt {i}",
                "nonce": f"stress-nonce-{i}-{time.time_ns()}",
            }
        )
        if r["valid"]:
            ok += 1
    elapsed = time.perf_counter() - t0
    assert ok >= 70
    assert elapsed < 5.0
    status = eng.status()
    assert status["secrets"]["hardcoded_secrets_allowed"] is False
