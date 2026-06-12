"""
IAS Gateway - Handles all 3 access modes transparently.
Call show_gateway() at the top of app.py before rendering main content.
Returns True if user can proceed, False if blocked.
"""
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import apikey

def show_gateway() -> bool:
    """
    Returns True = proceed to app.
    Returns False = show gateway screen (blocked).
    """
    mode = apikey.get_mode()

    # ── Mode: Host key available (Option 2 - Pure SaaS) ──────────────────
    if mode == "host":
        return True  # Just works — no prompt

    # ── Mode: Freemium (Option 3) ─────────────────────────────────────────
    if mode == "freemium":
        remaining = apikey.remaining_free()
        if remaining > 0:
            st.sidebar.info(
                f"🎁 **Free Plan** — {remaining} interview{'s' if remaining != 1 else ''} remaining\n\n"
                f"Add your own key in Settings to unlock unlimited access."
            )
            return True
        else:
            # Free limit exhausted — prompt for own key
            _show_key_prompt(
                title="🎁 Free interviews used up!",
                message=(
                    "You've used all **5 free interviews**.\n\n"
                    "Get your own FREE Anthropic API key to continue with **unlimited access**:"
                )
            )
            return False

    # ── Mode: User key saved (Option 1) ──────────────────────────────────
    if mode == "user":
        return True  # Already saved, just works

    # ── Mode: No key at all ───────────────────────────────────────────────
    _show_key_prompt(
        title="🚀 Welcome to IAS v8",
        message=(
            "To get started, enter your **free Anthropic API key**.\n\n"
            "Your key is saved permanently — you'll **never be asked again**."
        )
    )
    return False


def _show_key_prompt(title: str, message: str):
    st.markdown(f"## {title}")
    st.markdown(message)

    st.markdown("""
    **Get your free key in 2 minutes:**
    1. Go to [console.anthropic.com](https://console.anthropic.com) → Sign up free
    2. Click **API Keys** → **Create Key**
    3. Copy and paste below — you get **$5 free credits** (≈500 interviews)
    """)

    col1, col2 = st.columns([3, 1])
    with col1:
        key_input = st.text_input(
            "Your Anthropic API Key",
            type="password",
            placeholder="sk-ant-api03-...",
            key="gateway_key_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ Save & Launch", type="primary", use_container_width=True):
            if key_input and key_input.strip().startswith("sk-ant"):
                try:
                    apikey.set_key(key_input.strip())
                    st.success("Key saved! Launching IAS v8...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Invalid key — must start with sk-ant...")

    st.markdown("---")
    st.caption("🔒 Your key is stored locally on your machine only. Never shared.")


def track_interview():
    """Call this after each interview completes to track freemium usage."""
    if apikey.get_mode() == "freemium":
        apikey.increment_usage()
