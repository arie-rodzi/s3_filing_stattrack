import re, hashlib, os
from pathlib import Path
from passlib.hash import bcrypt

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

def ensure_dirs(path: str | Path):
    p = Path(path); p.mkdir(parents=True, exist_ok=True); return p

def hash_password(pw: str) -> str:
    return bcrypt.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.verify(pw, hashed)
    except Exception:
        return False
