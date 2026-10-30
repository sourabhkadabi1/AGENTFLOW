"""Ed25519 request/response signing. Every agent-to-agent call is signed; a registered name proves nothing."""
import base64, hashlib, os, time, uuid, threading
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

KEY_DIR = Path(os.getenv("AGENTFLOW_KEYS", ".keys"))
MAX_SKEW_S = 30

def _b64(b: bytes) -> str: return base64.b64encode(b).decode()
def _unb64(s: str) -> bytes: return base64.b64decode(s.encode())

def load_or_create_key(agent_id: str) -> Ed25519PrivateKey:
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    p = KEY_DIR / f"{agent_id}.key"
    if p.exists():
        return Ed25519PrivateKey.from_private_bytes(_unb64(p.read_text().strip()))
    k = Ed25519PrivateKey.generate()
    raw = k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    p.write_text(_b64(raw)); os.chmod(p, 0o600)
    return k

def pub_b64(k: Ed25519PrivateKey) -> str:
    return _b64(k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))

def body_hash(body: bytes) -> str: return hashlib.sha256(body or b"").hexdigest()

def canonical(method: str, path: str, ts: str, nonce: str, bh: str) -> bytes:
    return f"{method.upper()}\n{path}\n{ts}\n{nonce}\n{bh}".encode()

def sign_headers(key: Ed25519PrivateKey, agent_id: str, method: str, path: str, body: bytes) -> dict:
    ts, nonce = str(int(time.time())), uuid.uuid4().hex
    sig = key.sign(canonical(method, path, ts, nonce, body_hash(body)))
    return {"X-Agent-Id": agent_id, "X-Timestamp": ts, "X-Nonce": nonce, "X-Signature": _b64(sig)}

def sign_blob(key: Ed25519PrivateKey, data: bytes) -> str: return _b64(key.sign(data))

def verify_blob(pub: str, sig: str, data: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(_unb64(pub)).verify(_unb64(sig), data); return True
    except (InvalidSignature, ValueError): return False

class NonceCache:
    """Replay protection: an (agent, nonce) pair is accepted once inside the skew window."""
    def __init__(self): self._d, self._l = {}, threading.Lock()
    def check_and_store(self, agent_id: str, nonce: str) -> bool:
        now = time.time()
        with self._l:
            for k in [k for k, v in self._d.items() if v < now]: del self._d[k]
            if (agent_id, nonce) in self._d: return False
            self._d[(agent_id, nonce)] = now + 2 * MAX_SKEW_S
            return True

def verify_headers(pub: str, headers, method: str, path: str, body: bytes, nonces: NonceCache) -> tuple[bool, str]:
    try:
        aid, ts, nonce, sig = headers["x-agent-id"], headers["x-timestamp"], headers["x-nonce"], headers["x-signature"]
    except KeyError: return False, "missing_signature_headers"
    try:
        if abs(time.time() - int(ts)) > MAX_SKEW_S: return False, "timestamp_outside_window"
    except ValueError: return False, "bad_timestamp"
    if not verify_blob(pub, sig, canonical(method, path, ts, nonce, body_hash(body))): return False, "bad_signature"
    if not nonces.check_and_store(aid, nonce): return False, "replayed_nonce"
    return True, "ok"
