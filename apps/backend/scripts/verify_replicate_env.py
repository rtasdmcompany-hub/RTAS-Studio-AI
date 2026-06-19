#!/usr/bin/env python3
"""
Verify REPLICATE_API_TOKEN in apps/backend/.env (presence + Replicate API validity).

Usage (from apps/backend):
  python scripts/verify_replicate_env.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.services.replicate_verify import (  # noqa: E402
    log_replicate_startup_status,
    verify_replicate_token_sync,
)


def main() -> int:
    env_path = BACKEND_ROOT / ".env"
    print("RTAS backend Replicate env check")
    print(f"  .env path: {env_path}")
    print(f"  AI_PROVIDER_MODE: {settings.ai_provider_mode}")
    print("")

    result = verify_replicate_token_sync()
    log_replicate_startup_status(result)

    if not result.configured:
        print("")
        print("[info] REPLICATE_API_TOKEN is empty — simulation mode.")
        print("[info] Paste your token in apps/backend/.env line 11:")
        print("       REPLICATE_API_TOKEN=r8_YourTokenHere")
        return 0

    if result.valid:
        print("")
        print(f"[ok] Token valid — live generation enabled (user={result.username or 'unknown'})")
        return 0

    print("")
    print(f"[fail] Token invalid: {result.error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
