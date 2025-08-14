import json
import hashlib

def canonicalize(obj) -> bytes:
    """Return canonical JSON bytes: sorted keys, no spaces, UTF-8."""
    return json.dumps(obj, separators=(',', ':'), sort_keys=True, ensure_ascii=False).encode('utf-8')

def sha256_hexdigest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
