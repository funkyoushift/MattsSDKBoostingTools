"""Verify generated JSON resources across checkout line-ending conversions."""
import hashlib


def equivalent_digests(data, expected, error):
    # The published catalog hashes were generated from specific newline bytes.
    # Git may check out the identical JSON with the other platform's newlines.
    normalized = data.replace(b'\r\n', b'\n')
    digests = {hashlib.sha256(candidate).hexdigest()
               for candidate in (data, normalized, normalized.replace(b'\n', b'\r\n'))}
    if expected not in digests:
        raise RuntimeError(error)
    return digests


def verified_digest(data, expected, error):
    equivalent_digests(data, expected, error)
    return expected
