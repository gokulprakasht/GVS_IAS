"""
IAS Gmail Monitor — Continuous Background Thread
Polls Gmail IMAP every 60 seconds for new interview emails.
Writes data/auto_session.json when a new email is detected.
Triggered automatically at startup if Gmail credentials are configured.
"""
import imaplib, email, json, re, os, tempfile, threading, time, logging
from email import policy as _policy
from pathlib import Path
from datetime import datetime

log = logging.getLogger("ias.gmail_monitor")
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
_STOP = threading.Event()
_THREAD = None

# ── SUBJECT PATTERNS that indicate an interview email ────────────────────────
SUBJECT_PATTERNS = [
    r"video interview",
    r"interview.*empower",
    r"empower.*interview",
    r"interview.*eteki",
    r"eteki.*interview",
    r"interview.*scheduled",
    r"candidate.*interview",
    r"interview.*invitation",
    r"zoom.*interview",
]

def _is_interview_email(subject: str) -> bool:
    subj = subject.lower()
    return any(re.search(p, subj) for p in SUBJECT_PATTERNS)

def _extract_from_body(body: str) -> dict:
    """Extract candidate details from email body."""
    result = {
        "candidate_name": "", "candidate_email": "", "candidate_phone": "",
        "interview_time": "", "zoom_link": "", "skills": [],
        "jd_text": "", "special_instructions": [],
    }
    # Candidate name
    m = re.search(r'Candidate(?:\s+Full)?\s+Name\s*[\n:]\s*([A-Za-z][^\n]{2,50})', body)
    if m: result["candidate_name"] = m.group(1).strip()

    # Email
    m = re.search(r'Email\s*[\n:]\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', body)
    if m: result["candidate_email"] = m.group(1).strip()

    # Phone
    m = re.search(r'Phone(?:\s+Number)?\s*[\n:]\s*([\+\d\s\-\(\)]{7,20})', body)
    if m: result["candidate_phone"] = m.group(1).strip()

    # Interview time
    m = re.search(r'(?:Timing|Time|Scheduled)\s*[\n:]\s*([^\n]{6,60}(?:AM|PM|EST|PST|CST|IST|UTC)[^\n]*)', body, re.I)
    if m: result["interview_time"] = m.group(1).strip()

    # Zoom link
    m = re.search(r'(https://[^\s<>]+zoom\.us[^\s<>]+)', body)
    if m: result["zoom_link"] = m.group(1).strip()

    # Skills
    skills_sec = re.search(r'(?:Mandatory|Required|Skills|Checkpoints)[^\n]*\n(.*?)(?:\n\n\n|\Z)', body, re.DOTALL | re.I)
    if skills_sec:
        skills = re.findall(r'[•\*\-]\s*([A-Za-z][^\n\*•\-]{1,60})', skills_sec.group(1))
        result["skills"] = [s.strip() for s in skills if len(s.strip()) < 60][:12]

    # JD text
    subj_role = ""
    result["jd_text"] = (
        f"Role: {subj_role}\nRequired Skills: {', '.join(result['skills'])}\n\n"
        + "\n".join(f"- {s}" for s in result["skills"])
    )
    return result

def _save_auto_session(data: dict, cv_text: str = "", folder: str = ""):
    """Write auto_session.json for the workflow page to pick up."""
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {**data, "cv_text": cv_text, "candidate_folder": folder,
               "loaded_at": datetime.now().isoformat()}
    session_file = DATA / "auto_session.json"
    session_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    # Remove loaded flag so workflow picks it up fresh
    flag = DATA / "auto_session.loaded"
    if flag.exists():
        flag.unlink()
    log.info(f"Auto-session written for: {data.get('candidate_name','?')}")

def _process_message(msg, subject: str):
    """Parse a single email message and save auto_session."""
    body = ""
    cv_text = ""
    dl_bytes = None
    dl_filename = ""

    for part in msg.walk():
        ct = part.get_content_type()
        fn = part.get_filename() or ""
        payload = part.get_payload(decode=True)

        if ct == "text/plain" and not body:
            try: body = part.get_content()
            except:
                try: body = (payload or b"").decode("utf-8", "replace")
                except: pass

        if payload:
            # CV attachment
            if (("docx" in ct.lower() or fn.lower().endswith(".docx")) and not cv_text):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                        tmp.write(payload); tp = tmp.name
                    from docx import Document as _Doc
                    cv_text = "\n".join(p.text for p in _Doc(tp).paragraphs if p.text.strip())
                    os.unlink(tp)
                except Exception as e:
                    log.warning(f"CV DOCX read error: {e}")
            elif (("pdf" in ct.lower() or fn.lower().endswith(".pdf")) and not cv_text):
                if not any(k in fn.lower() for k in ["dl","license","licence","driving"]):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(payload); tp = tmp.name
                        try:
                            from pypdf import PdfReader
                            cv_text = " ".join(p.extract_text() or "" for p in PdfReader(tp).pages)
                        except ImportError:
                            import subprocess
                            r = subprocess.run(["pdftotext", tp, "-"], capture_output=True)
                            cv_text = r.stdout.decode("utf-8", "replace")
                        os.unlink(tp)
                    except Exception as e:
                        log.warning(f"CV PDF read error: {e}")

    data = _extract_from_body(body)
    if not data["candidate_name"] and subject:
        # Try to get name from subject
        m = re.search(r'[-–]\s*([A-Z][a-z]+ [A-Z][a-z]+)', subject)
        if m: data["candidate_name"] = m.group(1)

    # Create candidate folder
    folder = ""
    if data["candidate_name"]:
        safe = re.sub(r'[^\w\s-]', '', data["candidate_name"]).strip().replace(' ', '_')
        today = datetime.now().strftime("%Y-%m-%d")
        cdir = ROOT / "output" / "candidates" / f"{today}_{safe}"
        cdir.mkdir(parents=True, exist_ok=True)
        folder = str(cdir)
        if cv_text:
            (cdir / "cv_snapshot.txt").write_text(cv_text[:5000], encoding="utf-8")
        if data["jd_text"]:
            (cdir / "jd_snapshot.txt").write_text(data["jd_text"][:3000], encoding="utf-8")
        # Save email metadata
        meta = {**data, "subject": subject, "folder": folder,
                "received_at": datetime.now().isoformat()}
        (cdir / "email_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    _save_auto_session(data, cv_text=cv_text, folder=folder)
    return data.get("candidate_name", "Unknown")

def _monitor_loop(gmail: str, app_password: str, interval: int = 60):
    """Main monitoring loop — runs in background thread."""
    log.info(f"Gmail monitor started — polling every {interval}s for {gmail}")
    last_uid = None

    while not _STOP.is_set():
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com", 993) as imap:
                imap.login(gmail, app_password)
                imap.select("INBOX")

                # Search for UNSEEN emails
                _, msgs = imap.search(None, "UNSEEN")
                uids = msgs[0].split() if msgs[0] else []

                for uid in uids:
                    if _STOP.is_set(): break
                    try:
                        _, data = imap.fetch(uid, "(RFC822)")
                        raw = data[0][1]
                        msg = email.message_from_bytes(raw, policy=_policy.default)
                        subject = msg.get("Subject", "")

                        if _is_interview_email(subject):
                            log.info(f"Interview email found: {subject[:60]}")
                            name = _process_message(msg, subject)
                            log.info(f"Processed: {name}")
                            # Mark as read
                            imap.store(uid, "+FLAGS", "\\Seen")
                        else:
                            log.debug(f"Skipped (not interview): {subject[:60]}")
                    except Exception as e:
                        log.warning(f"Error processing email uid {uid}: {e}")

        except imaplib.IMAP4.error as e:
            log.error(f"IMAP auth error: {e}")
            _STOP.wait(300)  # Wait 5 min on auth error
        except Exception as e:
            log.error(f"Monitor error: {e}")

        _STOP.wait(interval)

    log.info("Gmail monitor stopped.")

def start(gmail: str, app_password: str, interval: int = 60):
    """Start the background Gmail monitor thread."""
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        log.info("Monitor already running.")
        return
    _STOP.clear()
    _THREAD = threading.Thread(
        target=_monitor_loop,
        args=(gmail, app_password, interval),
        daemon=True,
        name="IAS-GmailMonitor"
    )
    _THREAD.start()
    log.info("Gmail monitor thread started.")

def stop():
    """Stop the background monitor."""
    _STOP.set()
    if _THREAD:
        _THREAD.join(timeout=5)
    log.info("Gmail monitor stopped.")

def is_running() -> bool:
    return _THREAD is not None and _THREAD.is_alive()
