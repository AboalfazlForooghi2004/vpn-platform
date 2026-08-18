import hmac

def token_matches(provided: str | None, expected: str | None) -> bool:
    """Constant-time admin token check that fails closed.

    Returns False when either side is missing or empty, so a deployment without
    ADMIN_API_TOKEN configured denies all admin API access by default.
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
