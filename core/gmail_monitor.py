"""
IAS Gmail Monitor — Fixed v2
- Searches ALL mail (not just UNSEEN) from last 24h to catch missed emails
- Broader subject patterns for eTeki / Empower Professionals
- Questions auto-generated and saved to candidate folder
- Session file includes pre-generated questions for instant Zoom start
"""
import imaplib, email, json, re, os, tempfile, threading, time, logging, shutil
from email import policy as _policy
from pathlib import Path
from datetime import datetime, timedelta

log = logging.getLogger("ias.gmail_monitor")
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
_STOP    = threading.Event()
_THREAD  = None

# ── BROADER subject patterns — catches more eTeki / Empower emails ──
SUBJECT_PATTERNS = [
    r"interview",           # catches all interview emails
    r"empower",
    r"eteki",
    r"zoom.*meet",
    r"candidate",
    r"scheduled.*call",
    r"tcon",
    r"telephonic",
    r"assessment",
]

def _is_interview_email(subject: str, body: str = "") -> bool:
    subj = subject.lower()
    # Match on subject
    if any(re.search(p, subj) for p in SUBJECT_PATTERNS):
        return True
    # Also match on body keywords (for forwarded emails)
    body_l = body.lower()
    return any(k in body_l for k in ["zoom.us", "meet.google", "candidate name", "interview scheduled"])


def _extract_from_body(body: str, subject: str = "") -> dict:
    """Extract all candidate details + full JD from email body."""
    result = {
        "candidate_name": "", "candidate_email": "", "candidate_phone": "",
        "interview_time": "", "interview_date": "", "interview_duration": "30 Minutes",
        "zoom_link": "", "meet_link": "", "skills": [], "jd_text": "", "role": "",
        "special_instructions": [],
    }

    # ── Candidate name ────────────────────────────────────────────
    for pat in [
        r'Candidate(?:\s+Full)?\s+Name\s*[:\n]\s*([A-Za-z][^\n]{2,50})',
        r'Candidate\s*[:\n]\s*([A-Za-z][^\n]{2,50})',
        r'Name\s*[:\n]\s*([A-Za-z][A-Za-z\s]{4,40})',
        r'(?:Hi|Hello|Dear)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]:
        m = re.search(pat, body, re.I)
        if m:
            val = m.group(1).strip()
            if len(val.split()) <= 4 and len(val) > 3:
                result["candidate_name"] = val; break
    if not result["candidate_name"] and subject:
        m = re.search(r'[-–:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', subject)
        if m: result["candidate_name"] = m.group(1).strip()

    # ── Email ─────────────────────────────────────────────────────
    m = re.search(r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', body)
    if m: result["candidate_email"] = m.group(1).strip()

    # ── Phone ─────────────────────────────────────────────────────
    m = re.search(r'(?:Phone|Mobile|Contact)?\s*[:\n]?\s*((?:\+91|0)?[\s\-]?\d{10})', body, re.I)
    if m: result["candidate_phone"] = m.group(1).strip()

    # ── Role ─────────────────────────────────────────────────────
    for pat in [
        r'(?:Role|Position|Opening|Profile|Job Title)\s*[:\n]\s*([^\n]{5,80})',
        r'(?:for the role of|for the position of|interview for)\s+([^\n]{5,80})',
    ]:
        m = re.search(pat, body, re.I)
        if m: result["role"] = m.group(1).strip(); break
    if not result["role"] and subject:
        # Clean subject to get role
        role_sub = re.sub(r'(?:Re:|Fwd:|Interview|Scheduled|Meeting|Invite)[:\s]*', '', subject, flags=re.I).strip()
        if len(role_sub) > 5: result["role"] = role_sub[:80]

    # ── Interview date ────────────────────────────────────────────
    for pat in [
        r'(?:Date|Interview Date|On)\s*[:\n]\s*([^\n]{6,40})',
        r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
    ]:
        m = re.search(pat, body, re.I)
        if m: result["interview_date"] = m.group(1).strip(); break

    # ── Interview time ────────────────────────────────────────────
    m = re.search(r'(?:Time|Timing|At)\s*[:\n]\s*([^\n]{5,60}(?:AM|PM|IST|UTC|EST)[^\n]*)', body, re.I)
    if m: result["interview_time"] = m.group(1).strip()

    # ── Duration ─────────────────────────────────────────────────
    m = re.search(r'(?:Duration|Length)\s*[:\n]\s*(\d+\s*(?:Minutes?|Mins?|Hours?))', body, re.I)
    if m: result["interview_duration"] = m.group(1).strip()

    # ── Zoom / Meet link ─────────────────────────────────────────
    m = re.search(r'(https://[^\s<>"]+zoom\.us[^\s<>"]+)', body)
    if m: result["zoom_link"] = m.group(1).strip()
    m = re.search(r'(https://[^\s<>"]+meet\.google[^\s<>"]+)', body)
    if m: result["meet_link"] = m.group(1).strip()

    # ── Skills ───────────────────────────────────────────────────
    skills_sec = re.search(
        r'(?:Mandatory|Required|Key|Technical|Primary)\s*Skills?\s*[:\n](.*?)(?:\n{2,}|\Z)',
        body, re.DOTALL | re.I)
    if skills_sec:
        skills = re.findall(r'[•\*\-\d\.]\s*([A-Za-z][^\n\*•\-]{1,80})', skills_sec.group(1))
        result["skills"] = [s.strip() for s in skills if 2 < len(s.strip()) < 80][:15]

    # ── Full JD extraction ───────────────────────────────────────
    jd_section = ""
    jd_match = re.search(
        r'(?:Job Description|JD|Position Summary|About the Role|Job Summary)[:\s]*\n(.*?)(?:\n{3,}|(?:Regards|Thanks|Best|Note:|Warm))',
        body, re.DOTALL | re.I)
    if jd_match: jd_section = jd_match.group(1).strip()

    if not jd_section:
        parts = []
        if result["role"]:   parts.append(f"Position: {result['role']}")
        if result["skills"]: parts.append("Required Skills:\n" + "\n".join(f"  - {s}" for s in result["skills"]))
        resp = re.search(r'(?:Responsibilities|Requirements)[:\s]*\n(.*?)(?:\n{2,}|\Z)', body, re.DOTALL | re.I)
        if resp: parts.append(f"Responsibilities:\n{resp.group(1).strip()[:800]}")
        exp = re.search(r'(?:Experience|Exp\.?)\s*[:\n]\s*([^\n]{3,60})', body, re.I)
        if exp: parts.append(f"Experience: {exp.group(1).strip()}")
        jd_section = "\n\n".join(parts)

    if not jd_section:
        lines = [l for l in body.split("\n")
                 if len(l.strip()) > 15
                 and not re.match(r'^(?:Hi|Hello|Dear|Regards|Thanks|Best|From:|To:|Subject:)', l.strip(), re.I)]
        jd_section = "\n".join(lines[:50])

    result["jd_text"] = jd_section.strip()
    return result


def _make_folder_name(candidate_name: str, interview_date: str, duration: str) -> str:
    """Format: CandidateName_InterviewDate_Duration"""
    safe_name = re.sub(r'[^\w\s-]', '', candidate_name).strip().replace(' ', '_')
    if interview_date:
        for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y"]:
            try:
                safe_date = datetime.strptime(interview_date.strip(), fmt).strftime("%d-%b-%Y")
                break
            except ValueError:
                continue
        else:
            safe_date = re.sub(r'[^\w\-]', '-', interview_date.strip())[:20]
    else:
        safe_date = datetime.now().strftime("%d-%b-%Y")
    dur = re.sub(r'[^\w\s]', '', duration).strip() or "30 Minutes"
    return f"{safe_name}_{safe_date}_{dur}"


def _save_auto_session(data: dict, cv_text: str = "", folder: str = "", questions: list = None):
    """Write auto_session.json — includes pre-generated questions."""
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        **data,
        "cv_text":          cv_text,
        "candidate_folder": folder,
        "questions":        questions or [],   # PRE-LOADED QUESTIONS
        "loaded_at":        datetime.now().isoformat(),
    }
    session_file = DATA / "auto_session.json"
    session_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    flag = DATA / "auto_session.loaded"
    if flag.exists(): flag.unlink()
    log.info(f"Auto-session written for: {data.get('candidate_name','?')} "
             f"(questions: {len(questions or [])})")


def _generate_questions_background(cv_text: str, jd_text: str, candidate_name: str,
                                   skills: list, role: str, api_key_path: Path) -> list:
    """
    Generate questions in background thread using Claude API.
    Called right after email is received — questions ready before interview starts.
    """
    try:
        # Read API key
        key_file = api_key_path
        if not key_file.exists():
            key_file = api_key_path.parent / "api_key.txt"
        if not key_file.exists():
            log.warning("API key not found — skipping background question generation")
            return []

        api_key = key_file.read_text(encoding="utf-8").strip()
        if not api_key.startswith("sk-ant-"):
            return []

        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        skills_str = ", ".join(skills[:8]) if skills else "general technical skills"
        jd_preview = (jd_text or "")[:800]
        cv_preview = (cv_text or "")[:600]

        prompt = f"""Generate 10 interview questions for this candidate.

Candidate: {candidate_name}
Role: {role or 'Technical Professional'}
Key Skills: {skills_str}
JD: {jd_preview}
CV Summary: {cv_preview}

Return ONLY valid JSON array, no markdown:
[
  {{
    "num": 1,
    "type": "scenario",
    "skill": "skill name",
    "question": "specific scenario question",
    "expected_answer": "what a good answer looks like in 50 words",
    "follow_up": "follow-up probe question",
    "red_flag": "what poor answer looks like"
  }}
]

Mix 7 scenario + 3 coding/technical. Be specific to the role. No generic questions."""

        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        questions = json.loads(raw)
        log.info(f"Background questions generated: {len(questions)} for {candidate_name}")
        return questions

    except Exception as e:
        log.warning(f"Background question generation failed: {e}")
        return []


def _process_message(msg, subject: str):
    """Parse email, create folder, generate questions in background."""
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

        if ct == "text/plain" and not body:
            try: body = part.get_content()
            except:
                try: body = (payload or b"").decode("utf-8", "replace")
                except: pass
        if ct == "text/html" and not body:
            try:
                html_body = (payload or b"").decode("utf-8", "replace")
                body = re.sub(r'<[^>]+>', ' ', html_body)
                body = re.sub(r'\s+', ' ', body).strip()
            except: pass

        if not payload: continue

        # CV — DOCX
        if ("docx" in ct.lower() or fn_l.endswith(".docx")) and \
           not any(k in fn_l for k in ["photo","id","license","passport"]) and not cv_text:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp.write(payload); tp = tmp.name
                from docx import Document as _Doc
                cv_text    = "\n".join(p.text for p in _Doc(tp).paragraphs if p.text.strip())
                os.unlink(tp)
                cv_bytes   = payload; cv_filename = fn or "CV.docx"
            except Exception as e: log.warning(f"CV DOCX: {e}")

        # CV — PDF
        elif ("pdf" in ct.lower() or fn_l.endswith(".pdf")) and \
             not any(k in fn_l for k in ["dl","license","licence","driving","photo","id","passport"]) and not cv_text:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(payload); tp = tmp.name
                try:
                    from pypdf import PdfReader
                    cv_text = " ".join(p.extract_text() or "" for p in PdfReader(tp).pages)
                except:
                    import PyPDF2
                    cv_text = " ".join(p.extract_text() or "" for p in PyPDF2.PdfReader(tp).pages)
                os.unlink(tp)
                cv_bytes = payload; cv_filename = fn or "CV.pdf"
            except Exception as e: log.warning(f"CV PDF: {e}")

        # Photo ID
        elif any(k in fn_l for k in ["photo","id","license","licence","driving","passport","dl"]) \
             or ct.startswith("image/"):
            if not photo_bytes:
                photo_bytes = payload; photo_filename = fn or "PhotoID.jpg"

    data = _extract_from_body(body, subject)

    # ── Create candidate folder ───────────────────────────────────
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
        log.info(f"Folder created: {folder_name}")

        # Save CV file
        if cv_bytes and cv_filename:
            (cdir / cv_filename).write_bytes(cv_bytes)
            log.info(f"CV saved: {cv_filename}")

        # Save Photo ID
        if photo_bytes and photo_filename:
            (cdir / photo_filename).write_bytes(photo_bytes)
            log.info(f"Photo ID saved: {photo_filename}")

        # Save CV text + JD
        if cv_text:
            (cdir / "cv_text.txt").write_text(cv_text[:8000], encoding="utf-8")
        if data["jd_text"]:
            (cdir / "job_description.txt").write_text(data["jd_text"], encoding="utf-8")

        # Save email metadata
        meta = {**data, "subject": subject, "folder": folder,
                "received_at": datetime.now().isoformat()}
        (cdir / "email_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Generate questions immediately in background ──────────────
    log.info(f"Generating questions for {data['candidate_name']} in background...")
    questions = _generate_questions_background(
        cv_text   = cv_text,
        jd_text   = data["jd_text"],
        candidate_name = data["candidate_name"],
        skills    = data["skills"],
        role      = data["role"],
        api_key_path = ROOT / "api_key.txt",
    )

    # Save questions to candidate folder
    if questions and cdir:
        q_file = cdir / "questions.json"
        q_file.write_text(json.dumps({
            "candidate": data["candidate_name"],
            "role": data["role"],
            "generated_at": datetime.now().isoformat(),
            "questions": questions,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

        # Human-readable version
        lines = [
            f"IAS — Interview Questions",
            f"Candidate: {data['candidate_name']}",
            f"Role: {data['role']}",
            f"Generated: {datetime.now().strftime('%d %b %Y %I:%M %p')}",
            "=" * 60, ""
        ]
        for q in questions:
            lines += [
                f"Q{q.get('num','')}. [{q.get('type','').upper()}] {q.get('skill','')}",
                f"   {q.get('question','')}",
                f"   Expected: {q.get('expected_answer','')[:100]}",
                f"   Red flag: {q.get('red_flag','')[:80]}",
                ""
            ]
        (cdir / "questions.txt").write_text("\n".join(lines), encoding="utf-8")
        log.info(f"Questions saved to folder: {len(questions)} questions")

        # Remove pending marker
        pending = cdir / "QUESTIONS_PENDING.txt"
        if pending.exists(): pending.unlink()

    # ── Write auto_session with pre-loaded questions ──────────────
    _save_auto_session(data, cv_text=cv_text, folder=folder, questions=questions)
    return data.get("candidate_name", "Unknown")


def _monitor_loop(gmail: str, app_password: str, interval: int = 60):
    """
    Main monitoring loop.
    FIX: Searches last 24h of ALL mail (not just UNSEEN)
    to catch emails that may have been auto-read or filtered.
    """
    log.info(f"Gmail monitor started — polling every {interval}s")
    _processed_uids = set()

    while not _STOP.is_set():
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com", 993) as imap:
                imap.login(gmail, app_password)
                imap.select("INBOX")

                # FIX: Search last 24h — not just UNSEEN
                since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
                _, msgs = imap.search(None, f'(SINCE "{since}")')
                uids = msgs[0].split() if msgs[0] else []
                log.info(f"Found {len(uids)} emails in last 24h")

                for uid in uids:
                    if _STOP.is_set(): break
                    if uid in _processed_uids:
                        continue  # Skip already processed

                    try:
                        # Fetch headers only first (faster)
                        _, hdr_data = imap.fetch(uid, "(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])")
                        hdr_msg = email.message_from_bytes(hdr_data[0][1])
                        subj    = hdr_msg.get("Subject", "")

                        # Fetch full message for candidate emails
                        _, data = imap.fetch(uid, "(RFC822)")
                        raw  = data[0][1]
                        msg  = email.message_from_bytes(raw, policy=_policy.default)

                        # Get body for content-based matching
                        body_check = ""
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try: body_check = part.get_content()[:500]
                                except: body_check = (part.get_payload(decode=True) or b"").decode("utf-8","replace")[:500]
                                break

                        if _is_interview_email(subj, body_check):
                            log.info(f"Interview email: {subj[:80]}")
                            name = _process_message(msg, subj)
                            log.info(f"Processed: {name}")
                            _processed_uids.add(uid)
                        else:
                            _processed_uids.add(uid)  # Mark as checked
                            log.debug(f"Skipped: {subj[:60]}")

                    except Exception as e:
                        log.warning(f"Error uid {uid}: {e}")

        except imaplib.IMAP4.error as e:
            log.error(f"IMAP error: {e}")
            _STOP.wait(300)
        except Exception as e:
            log.error(f"Monitor error: {e}")

        _STOP.wait(interval)

    log.info("Gmail monitor stopped.")


def start(gmail: str, app_password: str, interval: int = 60):
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        log.info("Monitor already running."); return
    _STOP.clear()
    _THREAD = threading.Thread(
        target=_monitor_loop, args=(gmail, app_password, interval),
        daemon=True, name="IAS-GmailMonitor")
    _THREAD.start()
    log.info("Gmail monitor thread started.")

def stop():
    _STOP.set()
    if _THREAD: _THREAD.join(timeout=5)

def is_running() -> bool:
    return _THREAD is not None and _THREAD.is_alive()
