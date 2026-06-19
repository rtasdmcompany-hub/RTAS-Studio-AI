"""User-facing API error messages and classification helpers."""

FAL_AUTH_USER_MESSAGE = (
    "Fal.ai rejected this request. Check FAL_KEY in apps/backend/.env, "
    "or add billing credit at https://fal.ai/dashboard/billing "
    "(zero balance can also block generation)."
)
FAL_CREDIT_USER_MESSAGE = (
    "Insufficient Fal.ai balance. Add billing credit at "
    "https://fal.ai/dashboard/billing then try again."
)

REPLICATE_AUTH_USER_MESSAGE = "Invalid Replicate API Token. Please check your config."
REPLICATE_CREDIT_USER_MESSAGE = (
    "Insufficient Replicate credit. Add billing credit at "
    "https://replicate.com/account/billing then try again."
)


def is_fal_auth_failure(
    message: str | None,
    status_code: int | None = None,
) -> bool:
    if message and is_fal_credit_failure(message, status_code):
        return False
    if not message:
        return status_code == 401
    lower = message.lower()
    markers = (
        "invalid fal.ai api key",
        "invalid api key",
        "authentication",
    )
    if any(marker in lower for marker in markers):
        return True
    if status_code in (401, 403) and "unauthorized" in lower:
        return True
    return False


def is_fal_credit_failure(
    message: str | None,
    status_code: int | None = None,
) -> bool:
    if status_code == 402:
        return True
    if not message:
        return False
    lower = message.lower()
    credit_markers = (
        "exhausted balance",
        "user is locked",
        "top up your balance",
        "insufficient fal.ai balance",
        "insufficient balance",
        "out of credits",
        "billing",
    )
    if any(marker in lower for marker in credit_markers):
        return True
    return (
        "insufficient" in lower
        and ("balance" in lower or "credit" in lower or "billing" in lower)
    ) or "402" in lower


def is_replicate_credit_failure(
    message: str | None,
    status_code: int | None = None,
) -> bool:
    if status_code == 402:
        return True
    if not message:
        return False
    lower = message.lower()
    return "insufficient credit" in lower or "402" in lower


def is_replicate_auth_failure(
    message: str | None,
    status_code: int | None = None,
) -> bool:
    if status_code == 401:
        return True
    if not message:
        return False
    lower = message.lower()
    markers = (
        "unauthorized",
        "invalid token",
        "auth error",
        "401",
        "authentication",
    )
    return any(marker in lower for marker in markers)
