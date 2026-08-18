from vpn_platform.infrastructure.security.tokens import token_matches

def test_token_matches_only_for_exact_secret() -> None:
    assert token_matches("s3cr3t-token", "s3cr3t-token") is True
    assert token_matches("s3cr3t-token", "other-token") is False
    assert token_matches("S3CR3T", "s3cr3t") is False

def test_token_check_fails_closed_when_unconfigured_or_missing() -> None:
    assert token_matches(None, "s3cr3t") is False
    assert token_matches("s3cr3t", None) is False
    assert token_matches("", "s3cr3t") is False
    assert token_matches("s3cr3t", "") is False
    assert token_matches(None, None) is False
