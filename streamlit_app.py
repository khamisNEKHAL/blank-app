import os
import hashlib
import requests
import streamlit as st
from datetime import datetime, timezone

# ====== CONFIG ======
API_DEFAULT = os.getenv(
    "NEOMA_BEAUTY_API",
    "https://script.google.com/macros/s/REPLACE_WITH_YOUR_/exec"
)

# Local deadline shown to students (Paris) + hard UTC check to avoid tz issues
# Local deadline: 2025-11-30 23:59:59 Europe/Paris  ==  2025-11-30 22:59:59 UTC
COMMIT_DEADLINE_UTC = datetime(2025, 11, 30, 22, 59, 59, tzinfo=timezone.utc)

# ====== HELPERS ======
def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def commit_payload(uni_id: str, commit_hash: str) -> dict:
    return {"kind": "commit", "uni_id": uni_id, "commit": commit_hash}

def reveal_payload(uni_id: str, number: int, nonce: str) -> dict:
    # PRD: reveals contain the clear values; backend recomputes and verifies against commit. :contentReference[oaicite:1]{index=1}
    return {"kind": "reveal", "uni_id": uni_id, "number": number, "nonce": nonce}

def post_json(api_url: str, payload: dict):
    try:
        r = requests.post(api_url, json=payload, timeout=15)
        return r.status_code, r.text
    except Exception as e:
        return None, f"Network error: {e}"

# ====== UI ======
st.set_page_config(page_title="NEOMA Beauty Contest — Commit–Reveal", page_icon="🧩", layout="centered")

st.title("🧩 NEOMA Beauty Contest — Commit–Reveal")
st.caption("Trustless, transparent, verifiable classroom game (commit–reveal).")

with st.expander("How it works (30 seconds)"):
    st.markdown("""
- **Commit (before deadline):** Enter your **NEOMA ID**, **number (0–100)**, and a **secret nonce**.
  The app computes `sha256(uni_id|number|nonce)` and sends `{uni_id, commit}` to the ledger.  
- **Reveal (after deadline):** Re-enter **the same ID, number, and nonce**. The server recomputes the hash and verifies it against your commit.  
- Everything is **append-only** with public logs (commits & reveals) for verifiability.  """)  # :contentReference[oaicite:2]{index=2}

st.subheader("Configuration")
api_url = st.text_input("Apps Script API URL", value=API_DEFAULT, help="Provided by the instructor.")
cols = st.columns(2)
with cols[0]:
    st.write("**Commit deadline (Paris):** 30 Nov 2025 23:59:59")
with cols[1]:
    st.write("**Commit deadline (UTC):** 30 Nov 2025 22:59:59")

tab_commit, tab_reveal = st.tabs(["📝 Commit", "🔓 Reveal"])

# ===================== COMMIT TAB =====================
with tab_commit:
    st.markdown("Commit your choice **before the deadline**.")
    if now_utc() > COMMIT_DEADLINE_UTC:
        st.error("⛔ Commit window is CLOSED.")
    with st.form("commit_form", clear_on_submit=False):
        uni_id_c = st.text_input("NEOMA ID", key="commit_id")
        number_c = st.number_input("Your number (0–100)", min_value=0, max_value=100, step=1, key="commit_num")
        nonce_c = st.text_input("Secret nonce (keep it safe!)", type="password", key="commit_nonce",
                                help="Write this down — you'll need it to reveal.")
        submitted_c = st.form_submit_button("Commit")

        if submitted_c:
            if now_utc() > COMMIT_DEADLINE_UTC:
                st.error("⛔ Commit window is CLOSED.")
            elif not uni_id_c.strip():
                st.warning("Please enter your NEOMA ID.")
            elif not (0 <= int(number_c) <= 100):
                st.warning("Number must be between 0 and 100.")
            elif not nonce_c.strip():
                st.warning("Nonce cannot be empty.")
            elif not api_url.strip():
                st.warning("Please provide the API URL.")
            else:
                preimage = f"{uni_id_c.strip()}|{int(number_c)}|{nonce_c.strip()}"
                commit_hash = sha256(preimage)

                st.info("**Your PREIMAGE (save it!):**\n\n"
                        f"`{preimage}`\n\n"
                        "**Your COMMIT hash:**\n\n"
                        f"`{commit_hash}`")

                status, text = post_json(api_url, commit_payload(uni_id_c.strip(), commit_hash))
                if status is None:
                    st.error(text)
                elif 200 <= status < 300:
                    st.success(f"Server {status}: {text}")
                else:
                    st.error(f"Server {status}: {text}")

# ===================== REVEAL TAB =====================
with tab_reveal:
    st.markdown("Reveal your choice **after the commit phase** (in class).")
    with st.form("reveal_form", clear_on_submit=False):
        uni_id_r = st.text_input("NEOMA ID", key="reveal_id")
        number_r = st.number_input("Your number (0–100)", min_value=0, max_value=100, step=1, key="reveal_num")
        nonce_r = st.text_input("Secret nonce (the same one!)", type="password", key="reveal_nonce")
        submitted_r = st.form_submit_button("Reveal")

        if submitted_r:
            if not uni_id_r.strip():
                st.warning("Please enter your NEOMA ID.")
            elif not (0 <= int(number_r) <= 100):
                st.warning("Number must be between 0 and 100.")
            elif not nonce_r.strip():
                st.warning("Nonce cannot be empty.")
            elif not api_url.strip():
                st.warning("Please provide the API URL.")
            else:
                status, text = post_json(api_url, reveal_payload(uni_id_r.strip(), int(number_r), nonce_r.strip()))
                if status is None:
                    st.error(text)
                elif 200 <= status < 300:
                    st.success(f"Server {status}: {text}")
                else:
                    st.error(f"Server {status}: {text}")

st.divider()
st.caption("Implements PRD commit/reveal rules and append-only ledgers via Apps Script & Sheets. :contentReference[oaicite:3]{index=3}")

