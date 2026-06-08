"""
IAS Auto-Session Loader
Checks data/auto_session.json written by gmail_monitor.py
and pre-fills the workflow session state automatically.
Call _check_auto_session() at the top of the workflow page.
"""
import json
from pathlib import Path
from datetime import datetime


def check_auto_session(root: Path, session_state) -> bool:
    """
    Check for a session file written by gmail_monitor.py.
    If found and newer than current session, load it.
    Returns True if a new session was loaded.
    """
    session_file = root / "data" / "auto_session.json"
    flag_file    = root / "data" / "auto_session.loaded"

    if not session_file.exists():
        return False

    # Don't reload if already loaded this file
    if flag_file.exists():
        s_mtime = session_file.stat().st_mtime
        f_mtime = flag_file.stat().st_mtime
        if f_mtime >= s_mtime:
            return False

    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
    except Exception:
        return False

    # Load into session state
    if data.get("candidate_name"):
        session_state["candidate_name"]  = data["candidate_name"]
        session_state["candidate_email"] = data.get("candidate_email", "")
        session_state["candidate_phone"] = data.get("candidate_phone", "")
    if data.get("cv_text"):
        session_state["cv_text"]  = data["cv_text"]
    if data.get("jd_text"):
        session_state["jd_text"]  = data["jd_text"]
        session_state["_jd_words"] = data["jd_text"]
    if data.get("zoom_link"):
        session_state["_zoom_link"] = data["zoom_link"]
    if data.get("interview_time"):
        session_state["_interview_time"] = data["interview_time"]
    if data.get("skills"):
        session_state["_email_skills"] = data["skills"]
    if data.get("dl_path") and Path(data["dl_path"]).exists():
        session_state["photo_id_ok"]  = True
        session_state["photo_id_src"] = "Auto-loaded (DL from email)"
    if data.get("candidate_folder"):
        session_state["_candidate_folder"] = data["candidate_folder"]

    # Mark as loaded
    flag_file.write_text(datetime.now().isoformat(), encoding="utf-8")
    return True
