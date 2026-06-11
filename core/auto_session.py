"""
IAS Auto-Session Loader v2
Loads email-triggered session AND pre-generated questions.
When interviewer opens Workflow page, everything is ready —
no manual generation needed before starting Zoom interview.
"""
import json
from pathlib import Path
from datetime import datetime


def check_auto_session(root: Path, session_state) -> bool:
    """
    Check for auto_session.json written by gmail_monitor.
    Loads: candidate details + CV + JD + pre-generated questions.
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

    # ── Load candidate details ────────────────────────────────────
    if data.get("candidate_name"):
        session_state["candidate_name"]    = data["candidate_name"]
        session_state["candidate_email"]   = data.get("candidate_email", "")
        session_state["candidate_phone"]   = data.get("candidate_phone", "")
    if data.get("cv_text"):
        session_state["cv_text"]           = data["cv_text"]
    if data.get("jd_text"):
        session_state["jd_text"]           = data["jd_text"]
        session_state["_jd_words"]         = data["jd_text"]
    if data.get("zoom_link"):
        session_state["_zoom_link"]        = data["zoom_link"]
    if data.get("meet_link"):
        session_state["_meet_link"]        = data["meet_link"]
    if data.get("interview_time"):
        session_state["_interview_time"]   = data["interview_time"]
    if data.get("interview_date"):
        session_state["interview_date"]    = data["interview_date"]
    if data.get("interview_duration"):
        session_state["interview_duration"]= data["interview_duration"]
    if data.get("role"):
        session_state["_email_role"]       = data["role"]
    if data.get("skills"):
        session_state["_email_skills"]     = data["skills"]
    if data.get("candidate_folder"):
        session_state["_candidate_folder"] = data["candidate_folder"]
    if data.get("special_instructions"):
        session_state["_special_instructions"] = data["special_instructions"]

    # ── FIX: Load pre-generated questions directly into session ───
    questions = data.get("questions", [])

    # If not in session file, try loading from candidate folder
    if not questions and data.get("candidate_folder"):
        q_file = Path(data["candidate_folder"]) / "questions.json"
        if q_file.exists():
            try:
                qdata = json.loads(q_file.read_text(encoding="utf-8"))
                questions = qdata.get("questions", [])
            except Exception:
                pass

    if questions:
        session_state["questions"] = questions
        session_state["notes"]     = {}
        session_state["curr_q"]    = 0
        session_state["scores"]    = {}
        # Set cache keys so generate button knows questions exist
        session_state["_qcache_name"]  = data.get("candidate_name", "")
        session_state["_qcache_count"] = len(questions)
        loaded_qs = len(questions)
    else:
        loaded_qs = 0

    # ── Mark as loaded ────────────────────────────────────────────
    flag_file.write_text(datetime.now().isoformat(), encoding="utf-8")

    n = data.get("candidate_name", "candidate")
    msg = f"Email session loaded: {n}"
    if loaded_qs:
        msg += f" · {loaded_qs} questions ready"
    else:
        msg += " · Questions pending (will auto-generate)"

    import logging
    logging.getLogger("ias.auto_session").info(msg)
    return True
