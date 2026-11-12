# Excerpt from web/app.py; uses its existing imports, helpers and JWT_SECRET.

def verify_jwt(token: str):
    """Accept only HS256 tokens signed with the configured server secret."""
    if not isinstance(token, str):
        return None
    try:
        h_b64, p_b64, sig_b64 = token.split(".")
        header = json.loads(_b64url_decode(h_b64))
        payload = json.loads(_b64url_decode(p_b64))
    except (ValueError, TypeError, UnicodeError):
        return None
    if not isinstance(header, dict) or not isinstance(payload, dict):
        return None
    # The server pins the algorithm, regardless of what the token requests.
    if header.get("alg") != "HS256" or not sig_b64.isascii():
        return None
    signing_input = f"{h_b64}.{p_b64}".encode()
    expected = _b64url(hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig_b64):
        return None
    return payload
