"""
IAS Gmail Monitor — Continuous Background Thread
Polls Gmail IMAP every 60 seconds for new interview emails.
Writes data/auto_session.json when a new email is detected.

FIXES:
  1. JD extracted fully from email body (not just skills)
  2. Folder format: <CandidateName_InterviewDate_Duration>
  3. CV + Photo ID + Generated Questions copied into folder
"""
import imaplib, email, json, re, os, tempfile, threading, time, logging, shutil
from email import policy as _policy
from pathlib import Path
from datetime import datetime

log = logging.getLogger("ias.gmail_monitor")
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
_STOP = threading.Event()
_THREAD = None

# ── SUBJECT PATTERNS ─────────────────────────────────────────────
SUBJECT_PATTERNS = [
    r"video interview", r"interview.*empower", r"empower.*interview",
    r"interview.*eteki", r"eteki.*interview", r"interview.*scheduled",
    r"candidate.*interview", r"interview.*invitation", r"zoom.*interview",
    r"interview.*request", r"technical.*interview", r"scheduled.*interview",
]

def _is_interview_email(subject: str) -> bool:
    subj = subject.lower()
    return any(re.search(p, subj) for p in SUBJECT_PATTERNS)


def _extract_from_body(body: str, subject: str = "") -> dict:
    """
    FIX 1: Extract full JD + all candidate details from email body.
    Handles eTeki / Empower Professionals email formats.
    """
    result = {
        "candidate_name": "", "candidate_email": "", "candidate_phone": "",
        "interview_time": "", "interview_date": "", "interview_duration": "30 Minutes",
        "zoom_link": "", "skills": [], "jd_text": "", "role": "",
        "special_instructions": [],
    }

    # ── Candidate name ────────────────────────────────────────────
    for pat in [
        r'Candidate(?:\s+Full)?\s+Name\s*[:\n]\s*([A-Za-z][^\n]{2,50})',
        r'Candidate\s*[:\n]\s*([A-Za-z][^\n]{2,50})',
        r'Name\s*[:\n]\s*([A-Za-z][A-Za-z\s]{4,40})',
    ]:
        m = re.search(pat, body, re.I)
        if m: result["candidate_name"] = m.group(1).strip(); break

    # Try from subject if not found
    if not result["candidate_name"] and subject:
        m = re.search(r'[-–:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', subject)
        if m: result["candidate_name"] = m.group(1).strip()

    # ── Email ─────────────────────────────────────────────────────
    m = re.search(r'(?:Email|Mail)\s*[:\n]\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', body, re.I)
    if m: result["candidate_email"] = m.group(1).strip()

    # ── Phone ─────────────────────────────────────────────────────
    m = re.search(r'(?:Phone|Mobile|Contact)\s*(?:Number)?\s*[:\n]\s*([\+\d\s\-\(\)]{7,20})', body, re.I)
    if m: result["candidate_phone"] = m.group(1).strip()

    # ── Role / Position ───────────────────────────────────────────
    for pat in [
        r'(?:Role|Position|Job Title|Opening)\s*[:\n]\s*([^\n]{5,80})',
        r'(?:for the role of|for the position of)\s+([^\n]{5,80})',
        r'(?:Interview for)\s*[:\n]?\s*([^\n]{5,80})',
    ]:
        m = re.search(pat, body, re.I)
        if m: result["role"] = m.group(1).strip(); break

    # Try from subject
    if not result["role"] and subject:
        m = re.search(r'(?:for|interview[:\s]+)\s*([A-Za-z][^\n\|]{5,60})', subject, re.I)
        if m: result["role"] = m.group(1).strip()

    # ── Interview date ────────────────────────────────────────────
    for pat in [
        r'(?:Date|Interview Date|Scheduled Date)\s*[:\n]\s*([^\n]{6,40})',
        r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
    ]:
        m = re.search(pat, body, re.I)
        if m: result["interview_date"] = m.group(1).strip(); break

    # ── Interview time ────────────────────────────────────────────
    m = re.search(r'(?:Time|Timing|Scheduled Time|Interview Time)\s*[:\n]\s*([^\n]{5,60})', body, re.I)
    if m: result["interview_time"] = m.group(1).strip()

    # ── Duration ─────────────────────────────────────────────────
    m = re.search(r'(?:Duration|Length)\s*[:\n]\s*(\d+\s*(?:Minutes?|Mins?|Hours?))', body, re.I)
    if m: result["interview_duration"] = m.group(1).strip()

    # ── Zoom / Meet link ─────────────────────────────────────────
    m = re.search(r'(https://[^\s<>"]+(?:zoom\.us|meet\.google)[^\s<>"]+)', body)
    if m: result["zoom_link"] = m.group(1).strip()

    # ── Skills ───────────────────────────────────────────────────
    skills_sec = re.search(
        r'(?:Mandatory Skills?|Required Skills?|Key Skills?|Checkpoints?|Technical Skills?)[^\n]*\n(.*?)(?:\n{2,}|\Z)',
        body, re.DOTALL | re.I
    )
    if skills_sec:
        skills = re.findall(r'[•\*\-\d\.]\s*([A-Za-z][^\n\*•\-]{1,80})', skills_sec.group(1))
        result["skills"] = [s.strip() for s in skills if 2 < len(s.strip()) < 80][:15]

    # ── FIX 1: Full JD extraction ─────────────────────────────────
    # Try to extract complete JD section from email
    jd_section = ""

    # Pattern: look for JD block between known headers
    jd_match = re.search(
        r'(?:Job Description|JD|Position Summary|About the Role)[:\s]*\n(.*?)(?:\n{3,}|(?:Regards|Thanks|Best|Note:|Please|Warm))',
        body, re.DOTALL | re.I
    )
    if jd_match:
        jd_section = jd_match.group(1).strip()

    # If no explicit JD section, build from extracted fields
    if not jd_section:
        parts = []
        if result["role"]:        parts.append(f"Position: {result['role']}")
        if result["skills"]:      parts.append(f"Required Skills:\n" + "\n".join(f"  - {s}" for s in result["skills"]))

        # Extract responsibilities/requirements section
        resp_match = re.search(
            r'(?:Responsibilities|Requirements|Key Responsibilities|Job Duties)[:\s]*\n(.*?)(?:\n{2,}|\Z)',
            body, re.DOTALL | re.I
        )
        if resp_match:
            parts.append(f"Responsibilities:\n{resp_match.group(1).strip()[:1000]}")

        # Extract experience requirement
        exp_match = re.search(r'(?:Experience|Exp\.?)\s*[:\n]\s*([^\n]{3,60})', body, re.I)
        if exp_match:
            parts.append(f"Experience: {exp_match.group(1).strip()}")

        # Extract education
        edu_match = re.search(r'(?:Education|Qualification)\s*[:\n]\s*([^\n]{3,60})', body, re.I)
        if edu_match:
            parts.append(f"Education: {edu_match.group(1).strip()}")

        jd_section = "\n\n".join(parts)

    # Fallback: use substantial body portion as JD
    if not jd_section and len(body) > 200:
        # Remove greeting/signature, keep the meat
        lines = [l for l in body.split("\n")
                 if len(l.strip()) > 10
                 and not re.match(r'^(?:Hi|Hello|Dear|Regards|Thanks|Best|Warm)', l.strip(), re.I)]
        jd_section = "\n".join(lines[:40])

    result["jd_text"] = jd_section.strip()

    # ── Special instructions ──────────────────────────────────────
    note_match = re.search(r'(?:Note|Important|Please Note)[:\s]*\n(.*?)(?:\n{2,}|\Z)', body, re.DOTALL | re.I)
    if note_match:
        notes = [l.strip() for l in note_match.group(1).split("\n") if l.strip()]
        result["special_instructions"] = notes[:5]

    return result


def _make_folder_name(candidate_name: str, interview_date: str, duration: str) -> str:
    """
    FIX 2: Folder format — <CandidateName_InterviewDate_Duration>
    Example: Loka_Kalyan_Palla_12-Jun-2026_45 Minutes
    """
    # Clean candidate name
    safe_name = re.sub(r'[^\w\s-]', '', candidate_name).strip()
    safe_name = re.sub(r'\s+', '_', safe_name)

    # Format date
    if interview_date:
        # Try to parse and reformat
        for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%d",
                    "%d %B %Y", "%d %b %Y", "%B %d, %Y"]:
            try:
                dt = datetime.strptime(interview_date.strip(), fmt)
                safe_date = dt.strftime("%d-%b-%Y")
                break
            except ValueError:
                continue
        else:
            # Use as-is, just make filesystem safe
            safe_date = re.sub(r'[^\w\-]', '-', interview_date.strip())[:20]
    else:
        safe_date = datetime.now().strftime("%d-%b-%Y")

    # Clean duration
    dur = re.sub(r'[^\w\s]', '', duration).strip() or "30 Minutes"

    return f"{safe_name}_{safe_date}_{dur}"


def _save_auto_session(data: dict, cv_text: str = "", folder: str = ""):
    """Write auto_session.json for the workflow page to pick up."""
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {**data, "cv_text": cv_text, "candidate_folder": folder,
               "loaded_at": datetime.now().isoformat()}
    session_file = DATA / "auto_session.json"
    session_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    flag = DATA / "auto_session.loaded"
    if flag.exists():
        flag.unlink()
    log.info(f"Auto-session written for: {data.get('candidate_name','?')}")


def _process_message(msg, subject: str):
    """Parse email, create folder, save all files."""
    body = ""
    cv_text = ""
    cv_bytes = None
    cv_filename = ""
    photo_bytes = None
    photo_filename = ""

    for part in msg.walk():
        ct   = part.get_content_type()
        fn   = part.get_filename() or ""
        fn_l = fn.lower()
        payload = part.get_payload(decode=True)

        # ── Body text ─────────────────────────────────────────────
        if ct == "text/plain" and not body:
            try: body = part.get_content()
            except:
                try: body = (payload or b"").decode("utf-8", "replace")
                except: pass

        if not payload:
            continue

        # ── CV — DOCX ─────────────────────────────────────────────
        if (("docx" in ct.lower() or fn_l.endswith(".docx"))
                and not any(k in fn_l for k in ["photo","id","license","passport"])
                and not cv_text):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp.write(payload); tp = tmp.name
                from docx import Document as _Doc
                cv_text = "\n".join(p.text for p in _Doc(tp).paragraphs if p.text.strip())
                os.unlink(tp)
                cv_bytes    = payload
                cv_filename = fn or "CV.docx"
            except Exception as e:
                log.warning(f"CV DOCX read error: {e}")

        # ── CV — PDF ─────────────────────────────────────────────
        elif (("pdf" in ct.lower() or fn_l.endswith(".pdf"))
              and not any(k in fn_l for k in ["dl","license","licence","driving","photo","id","passport"])
              and not cv_text):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(payload); tp = tmp.name
                try:
                    from pypdf import PdfReader
                    cv_text = " ".join(p.extract_text() or "" for p in PdfReader(tp).pages)
                except ImportError:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(tp)
                    cv_text = " ".join(p.extract_text() or "" for p in reader.pages)
                os.unlink(tp)
                cv_bytes    = payload
                cv_filename = fn or "CV.pdf"
            except Exception as e:
                log.warning(f"CV PDF read error: {e}")

        # ── Photo ID ──────────────────────────────────────────────
        elif any(k in fn_l for k in ["photo","id","license","licence","driving","passport","dl"]) \
             or ct.startswith("image/"):
            if not photo_bytes:
                photo_bytes    = payload
                photo_filename = fn or f"PhotoID{Path(fn).suffix or '.jpg'}"

    # ── Extract all data from body ────────────────────────────────
    data = _extract_from_body(body, subject)

    # ── FIX 2: Create folder with correct format ──────────────────
    folder = ""
    cdir   = None

    if data["candidate_name"]:
        folder_name = _make_folder_name(
            data["candidate_name"],
            data.get("interview_date", ""),
            data.get("interview_duration", "30 Minutes"),
        )
        cdir = ROOT / "output" / "candidates" / folder_name
        cdir.mkdir(parents=True, exist_ok=True)
        folder = str(cdir)
        log.info(f"Candidate folder created: {folder_name}")

        # ── FIX 3: Copy CV into folder ───────────────────────────
        if cv_bytes and cv_filename:
            cv_path = cdir / cv_filename
            cv_path.write_bytes(cv_bytes)
            log.info(f"CV saved: {cv_filename}")

        # ── FIX 3: Copy Photo ID into folder ─────────────────────
        if photo_bytes and photo_filename:
            photo_path = cdir / photo_filename
            photo_path.write_bytes(photo_bytes)
            log.info(f"Photo ID saved: {photo_filename}")

        # ── Save CV text snapshot ─────────────────────────────────
        if cv_text:
            (cdir / "cv_text.txt").write_text(cv_text[:8000], encoding="utf-8")

        # ── Save full JD ──────────────────────────────────────────
        if data["jd_text"]:
            (cdir / "job_description.txt").write_text(data["jd_text"], encoding="utf-8")

        # ── FIX 3: Questions placeholder — filled after generation ─
        # Create a marker file; app.py will write actual questions here
        (cdir / "QUESTIONS_PENDING.txt").write_text(
            f"Questions will be auto-generated for: {data['candidate_name']}\n"
            f"Role: {data.get('role','')}\n"
            f"Skills: {', '.join(data.get('skills',[]))}\n"
            f"Trigger: Open IAS → Interview Workflow → questions auto-load\n",
            encoding="utf-8"
        )

        # ── Save email metadata ───────────────────────────────────
        meta = {**data, "subject": subject, "folder": folder,
                "folder_name": folder_name,
                "received_at": datetime.now().isoformat()}
        (cdir / "email_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        log.info(f"Folder contents: CV={'yes' if cv_bytes else 'no'}, "
                 f"PhotoID={'yes' if photo_bytes else 'no'}, JD={'yes' if data['jd_text'] else 'no'}")

    _save_auto_session(data, cv_text=cv_text, folder=folder)
    return data.get("candidate_name", "Unknown")


def _monitor_loop(gmail: str, app_password: str, interval: int = 60):
    """Main monitoring loop — runs in background thread."""
    log.info(f"Gmail monitor started — polling every {interval}s for {gmail}")

    while not _STOP.is_set():
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com", 993) as imap:
                imap.login(gmail, app_password)
                imap.select("INBOX")
                _, msgs = imap.search(None, "UNSEEN")
                uids = msgs[0].split() if msgs[0] else []

                for uid in uids:
                    if _STOP.is_set(): break
                    try:
                        _, data = imap.fetch(uid, "(RFC822)")
                        raw  = data[0][1]
                        msg  = email.message_from_bytes(raw, policy=_policy.default)
                        subj = msg.get("Subject", "")

                        if _is_interview_email(subj):
                            log.info(f"Interview email found: {subj[:80]}")
                            name = _process_message(msg, subj)
                            log.info(f"Processed: {name}")
                            imap.store(uid, "+FLAGS", "\\Seen")
                        else:
                            log.debug(f"Skipped: {subj[:60]}")
                    except Exception as e:
                        log.warning(f"Error processing email uid {uid}: {e}")

        except imaplib.IMAP4.error as e:
            log.error(f"IMAP auth error: {e}")
            _STOP.wait(300)
        except Exception as e:
            log.error(f"Monitor error: {e}")

        _STOP.wait(interval)

    log.info("Gmail monitor stopped.")


def start(gmail: str, app_password: str, interval: int = 60):
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        log.info("Monitor already running.")
        return
    _STOP.clear()
    _THREAD = threading.Thread(
        target=_monitor_loop,
        args=(gmail, app_password, interval),
        daemon=True, name="IAS-GmailMonitor"
    )
    _THREAD.start()
    log.info("Gmail monitor thread started.")


def stop():
    _STOP.set()
    if _THREAD: _THREAD.join(timeout=5)
    log.info("Gmail monitor stopped.")


def is_running() -> bool:
    return _THREAD is not None and _THREAD.is_alive()
