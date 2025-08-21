from analysis.static_analysis.secret_scanner import scan


def test_detects_common_tokens():
    text = (
        "This string has an AWS key AKIA1234567890ABCDEF and a Google key "
        "AIzaSyA-12345678901234567890123456789012 plus a Slack token "
        "xoxb-123456789012-abcdefGhijkl and a GitHub token "
        "ghp_1234567890abcdef1234567890abcdef1234."
    )
    results = scan(text)
    assert results["aws_access_key"] == ["AKIA1234567890ABCDEF"]
    assert results["google_api_key"], "Should detect Google API key"
    assert any(token.startswith("xoxb-") for token in results["slack_token"])
    assert results["github_token"][0].startswith("ghp_")


def test_detects_jwt_private_and_secret_key():
    text = (
        "aws_secret_access_key=ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234 "
        "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c ----"
        "-----BEGIN PRIVATE KEY-----"
    )
    results = scan(text)
    assert results["aws_secret_key"], "Should detect AWS secret access key"
    assert results["jwt_token"], "Should detect JWT token"
    assert results["private_key"], "Should detect private key block"
