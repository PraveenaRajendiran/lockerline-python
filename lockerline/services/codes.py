
"""Pickup codes: six random digits from a cryptographic source, stored only as a keyed SHA-256 hash.

Why keyed SHA-256 rather than bcrypt: a code has only a million values, so an unkeyed hash could be brute-forced
from a leaked table in seconds; the key (CODE_HASH_KEY, from the environment) makes the stored hash useless without
it, and HMAC is fast enough to look up by equality. The comparison itself is constant-time.
"""

import hashlib
import hmac
import secrets


def issue_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_code(key: str, code: str) -> str:
    return hmac.new(key.encode(), code.encode(), hashlib.sha256).hexdigest()


def matches(key: str, code: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_code(key, code), stored_hash)
