"""One-shot migration: replace fail-open route auth helpers with require_backend_secret."""

from __future__ import annotations

import re
from pathlib import Path

ROUTES = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"

AUTH_BLOCK = re.compile(
    r"def _auth\(secret: str \| None\) -> None:\n"
    r"    expected = \(settings\.ai_backend_secret or \"\"\)\.strip\(\)\n"
    r"    if expected and \(secret or \"\"\)\.strip\(\) != expected:\n"
    r"        raise HTTPException\(status_code=\d+, detail=\"[^\"]+\"\)\n"
)

REQUIRE_BLOCK = re.compile(
    r"def _require_backend_auth\(x_rtas_backend_secret: str \| None\) -> None:\n"
    r"    expected = \(settings\.ai_backend_secret or \"\"\)\.strip\(\)\n"
    r"    if not expected:\n"
    r"        return\n"
    r"    if \(x_rtas_backend_secret or \"\"\)\.strip\(\) != expected:\n"
    r"        raise HTTPException\(status_code=\d+, detail=\"[^\"]+\"\)\n"
)

REQUIRE_BOOL = re.compile(
    r"def _require_backend_auth\(x_rtas_backend_secret: str \| None\) -> bool:\n"
    r"    expected = \(settings\.ai_backend_secret or \"\"\)\.strip\(\)\n"
    r"    if not expected:\n"
    r"        return True\n"
    r"    if \(x_rtas_backend_secret or \"\"\)\.strip\(\) != expected:\n"
    r"        raise HTTPException\(status_code=\d+, detail=\"[^\"]+\"\)\n"
    r"    return True\n"
)

AUTH_REPL = (
    "def _auth(secret: str | None) -> None:\n"
    "    require_backend_secret(x_rtas_backend_secret=secret)\n"
)
REQUIRE_REPL = (
    "def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:\n"
    "    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)\n"
)
REQUIRE_BOOL_REPL = (
    "def _require_backend_auth(x_rtas_backend_secret: str | None) -> bool:\n"
    "    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)\n"
    "    return True\n"
)


def ensure_import(text: str) -> str:
    if "require_backend_secret" in text and "from app.core.backend_auth import require_backend_secret" in text:
        return text
    if "from app.core.backend_auth import require_backend_secret" in text:
        return text
    if "from app.core.config import" in text:
        return text.replace(
            "from app.core.config import",
            "from app.core.backend_auth import require_backend_secret\nfrom app.core.config import",
            1,
        )
    m = re.search(r"from fastapi import[^\n]+\n", text)
    if m:
        return text[: m.end()] + "from app.core.backend_auth import require_backend_secret\n" + text[m.end() :]
    return "from app.core.backend_auth import require_backend_secret\n" + text


def main() -> None:
    changed: list[str] = []
    for path in sorted(ROUTES.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        orig = text
        if AUTH_BLOCK.search(text) or REQUIRE_BLOCK.search(text) or REQUIRE_BOOL.search(text):
            text = ensure_import(text)
            text = AUTH_BLOCK.sub(AUTH_REPL, text)
            text = REQUIRE_BLOCK.sub(REQUIRE_REPL, text)
            text = REQUIRE_BOOL.sub(REQUIRE_BOOL_REPL, text)
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            changed.append(path.name)

    print(f"changed={len(changed)}")
    for name in changed:
        print(name)

    print("---REMAINING fail-open---")
    for path in sorted(ROUTES.glob("*.py")):
        t = path.read_text(encoding="utf-8")
        if re.search(r"if not expected:\n\s+return", t) or re.search(
            r"if expected and \(secret", t
        ):
            # ignore if already delegated
            if "require_backend_secret(x_rtas_backend_secret=" in t and not re.search(
                r"if not expected:\n\s+return", t
            ):
                continue
            if re.search(r"if not expected:\n\s+return", t) or re.search(
                r"if expected and \(secret", t
            ):
                print(path.name)


if __name__ == "__main__":
    main()
