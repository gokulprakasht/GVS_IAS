"""
IAS API Key Manager - Multi-Mode
Supports 3 modes:
  Option 1: User's own key (saved permanently, asked only once)
  Option 2: Host key (set via ANTHROPIC_API_KEY env var - cloud/SaaS mode)
  Option 3: Freemium (5 free interviews using host key, then user's own)
"""
import os, json
from pathlib import Path

_KEY = ""
BASE = Path(__file__).parent.parent
KEY_FILE  = BASE / "api_key.txt"
DATA_FILE = BASE / "data" / "usage.json"
FREE_LIMIT = 5  # freemium interview limit

# ── Freemium usage tracking ──────────────────────────────────────────────────

def _load_usage() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"count": 0, "own_key": ""}

def _save_usage(u: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(u, indent=2), encoding="utf-8")

def get_freemium_count() -> int:
    return _load_usage().get("count", 0)

def increment_usage():
    u = _load_usage()
    u["count"] = u.get("count", 0) + 1
    _save_usage(u)

def freemium_exhausted() -> bool:
    return get_freemium_count() >= FREE_LIMIT

def remaining_free() -> int:
    return max(0, FREE_LIMIT - get_freemium_count())

# ── Key resolution (priority chain) ─────────────────────────────────────────

def get_key() -> str:
    global _KEY
    if _KEY:
        return _KEY

    # 1. Streamlit secrets (cloud deployment - Option 2)
    try:
        import streamlit as st
        k = st.secrets.get("ANTHROPIC_API_KEY", "").strip()
        if k.startswith("sk-ant") and len(k) > 40:
            _KEY = k
            return _KEY
    except Exception:
        pass

    # 2. Environment variable (Render / Railway / Docker - Option 2)
    env = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env.startswith("sk-ant") and len(env) > 40:
        _KEY = env
        return _KEY

    # 3. User's saved key from api_key.txt (Option 1 - saved permanently)
    if KEY_FILE.exists():
        try:
            k = KEY_FILE.read_text(encoding="utf-8-sig").strip()
            if k.startswith("sk-ant") and len(k) > 40:
                _KEY = k
                return _KEY
        except Exception:
            pass

    # 4. Check .env file
    env_file = BASE / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    k = line.split("=", 1)[1].strip()
                    if k.startswith("sk-ant") and len(k) > 40:
                        _KEY = k
                        return _KEY
        except Exception:
            pass

    return ""

def set_key(key: str):
    """Save user's own key permanently (Option 1)."""
    global _KEY
    key = key.strip()
    if not key.startswith("sk-ant"):
        raise ValueError("Invalid key — must start with sk-ant")
    _KEY = key
    KEY_FILE.write_text(key, encoding="utf-8")
    # Also update usage record
    u = _load_usage()
    u["own_key"] = key
    _save_usage(u)

def is_valid() -> bool:
    return get_key().startswith("sk-ant")

def has_own_key() -> bool:
    """Check if user has saved their own key."""
    if KEY_FILE.exists():
        try:
            k = KEY_FILE.read_text(encoding="utf-8-sig").strip()
            return k.startswith("sk-ant") and len(k) > 40
        except Exception:
            pass
    return False

def is_host_key() -> bool:
    """True when running in cloud/SaaS mode with host's key."""
    try:
        import streamlit as st
        k = st.secrets.get("ANTHROPIC_API_KEY", "").strip()
        if k.startswith("sk-ant"):
            return True
    except Exception:
        pass
    env = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    return env.startswith("sk-ant") and len(env) > 40

def get_mode() -> str:
    """Returns: 'host', 'user', 'freemium', or 'none'"""
    if is_host_key():
        if not has_own_key() and not freemium_exhausted():
            return "freemium"
        return "host"
    if has_own_key():
        return "user"
    return "none"

def get_client():
    import anthropic
    key = get_key()
    if not key:
        raise ValueError("API key not set.")
    return anthropic.Anthropic(api_key=key)

def get_model() -> str:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import config
    return os.environ.get("ANTHROPIC_MODEL",
                          config.get_setting("api_model", "claude-opus-4-6"))
