from pathlib import Path

p = Path(r"C:\IAS\IAS_CLOUD_FULL\app.py")
c = p.read_text(encoding="utf-8")
orig = len(c)
n = 0

# FIX 1: _extract_text BytesIO
if "NamedTemporaryFile" in c[c.find("def _extract_text"):c.find("def _extract_text")+600]:
    old1 = "    with tf.NamedTemporaryFile(delete=False, suffix=_os.path.splitext(nm)[1]) as t:\n        t.write(raw); tp = t.name\n    try:\n        if nm.endswith(\".pdf\"):\n            from pypdf import PdfReader\n            return \" \".join(p.extract_text() or \"\" for p in PdfReader(tp).pages).strip()\n        elif nm.endswith(\".docx\"):\n            from docx import Document\n            return \"\\n\".join(p.text for p in Document(tp).paragraphs if p.text.strip())\n        elif nm.endswith(\".txt\"):\n            return raw.decode(\"utf-8\", \"replace\").strip()\n    except Exception as e: return f\"Error: {e}\"\n    finally:\n        try: _os.unlink(tp)\n        except: pass\n    return \"\""
    new1 = "    from io import BytesIO\n    bio = BytesIO(raw)\n    try:\n        if nm.endswith(\".pdf\"):\n            try:\n                from pypdf import PdfReader\n            except ImportError:\n                from PyPDF2 import PdfReader\n            return \" \".join(pg.extract_text() or \"\" for pg in PdfReader(bio).pages).strip()\n        elif nm.endswith(\".docx\"):\n            from docx import Document\n            return \"\\n\".join(pg.text for pg in Document(bio).paragraphs if pg.text.strip())\n        elif nm.endswith(\".txt\"):\n            return raw.decode(\"utf-8\", \"replace\").strip()\n        else:\n            return \"Error: unsupported type\"\n    except Exception as e:\n        return f\"Error: {e}\""
    if old1 in c:
        c = c.replace(old1, new1, 1); n += 1; print("FIX1 OK: _extract_text BytesIO")
    else:
        print("FIX1 SKIP")
else:
    print("FIX1 already applied")

# FIX 2: API key direct inject
if "apikey._KEY = _ak" not in c:
    old2 = "            _kf = ROOT / \"api_key.txt\"\n            if not _kf.exists() or _kf.read_text().strip() != _ak:\n                _kf.write_text(_ak)"
    new2 = "            apikey._KEY = _ak\n            try:\n                (ROOT / \"api_key.txt\").write_text(_ak)\n            except Exception:\n                pass"
    if old2 in c:
        c = c.replace(old2, new2, 1); n += 1; print("FIX2 OK: API key inject")
    else:
        print("FIX2 SKIP")
else:
    print("FIX2 already applied")

# FIX 3: settings_e before report preview
if c.count("settings_e = cfg.get_settings()") < 2:
    marker = "                st.markdown(\"#### \U0001f4c4 Generate DOCX Report\")\n                # \u2500\u2500 REPORT PREVIEW"
    if marker in c:
        c = c.replace(marker, "                st.markdown(\"#### \U0001f4c4 Generate DOCX Report\")\n                settings_e = cfg.get_settings()\n                # \u2500\u2500 REPORT PREVIEW", 1)
        n += 1; print("FIX3 OK: settings_e")
    else:
        print("FIX3 SKIP")
else:
    print("FIX3 already applied")

# FIX 4: _curr_ind in home block
if "_curr_ind = (st.session_state.get" not in c:
    marker4 = "    _interviewer = settings_h.get(\"interviewer_name\", \"Gokul Prakash T\").split()[0]\n\n    # \u2500\u2500 Derived metrics"
    if marker4 in c:
        c = c.replace(marker4, "    _interviewer = settings_h.get(\"interviewer_name\", \"Gokul Prakash T\").split()[0]\n    _curr_ind = (st.session_state.get(\"selected_industry\") or \"IT & Software\")\n    st.session_state[\"selected_industry\"] = _curr_ind\n\n    # \u2500\u2500 Derived metrics", 1)
        n += 1; print("FIX4 OK: _curr_ind home block")
    else:
        print("FIX4 SKIP")
else:
    print("FIX4 already applied")

# FIX 5: CV uploader - stop session_state text_inputs from triggering rerun
# The text_input widgets write directly to session_state causing page refresh
# which collapses the file uploader before it can be interacted with
old5 = "        d1,d2,d3=st.columns(3)\n        with d1:\n            st.session_state.candidate_name=st.text_input(\"Candidate Name *\",\n                value=st.session_state.candidate_name,placeholder=\"Auto-filled from CV\")\n        with d2:\n            st.session_state.candidate_email=st.text_input(\"Email\",\n                value=st.session_state.candidate_email,placeholder=\"Auto-filled from CV\")\n        with d3:\n            st.session_state.candidate_phone=st.text_input(\"Phone\",\n                value=st.session_state.candidate_phone,placeholder=\"Auto-filled from CV\")"
new5 = "        d1,d2,d3=st.columns(3)\n        with d1:\n            _cname_val=st.text_input(\"Candidate Name *\",\n                value=st.session_state.candidate_name,placeholder=\"Auto-filled from CV\",key=\"_inp_cname\")\n            if _cname_val != st.session_state.candidate_name: st.session_state.candidate_name=_cname_val\n        with d2:\n            _cemail_val=st.text_input(\"Email\",\n                value=st.session_state.candidate_email,placeholder=\"Auto-filled from CV\",key=\"_inp_cemail\")\n            if _cemail_val != st.session_state.candidate_email: st.session_state.candidate_email=_cemail_val\n        with d3:\n            _cphone_val=st.text_input(\"Phone\",\n                value=st.session_state.candidate_phone,placeholder=\"Auto-filled from CV\",key=\"_inp_cphone\")\n            if _cphone_val != st.session_state.candidate_phone: st.session_state.candidate_phone=_cphone_val"
if old5 in c:
    c = c.replace(old5, new5, 1); n += 1; print("FIX5 OK: text_input session state stabilised")
else:
    if "_inp_cname" in c:
        print("FIX5 already applied")
    else:
        print("FIX5 SKIP: pattern not found")

p.write_text(c, encoding="utf-8")
print(f"\nTotal: {n} fixes. {orig} -> {len(c)} bytes. Done.")

# FIX 6: Add .doc support to CV uploader
from pathlib import Path
p = Path(r"C:\IAS\IAS_CLOUD_FULL\app.py")
c = p.read_text(encoding="utf-8")
n = 0

# Add .doc to file uploader accepted types
old6a = 'cv_file=st.file_uploader("📎 Upload CV (PDF or DOCX)",type=["pdf","docx"],'
new6a = 'cv_file=st.file_uploader("📎 Upload CV (PDF, DOCX or DOC)",type=["pdf","docx","doc"],'
if old6a in c:
    c = c.replace(old6a, new6a, 1); n += 1; print("FIX6a OK: .doc added to CV uploader")

# Add .doc handling in _extract_text
old6b = '        else:\n            return "Error: unsupported type"\n    except Exception as e:\n        return f"Error: {e}"'
new6b = '        elif nm.endswith(".doc"):\n            # Convert .doc via python-docx (works for most .doc files)\n            try:\n                from docx import Document\n                return "\\n".join(pg.text for pg in Document(bio).paragraphs if pg.text.strip())\n            except Exception:\n                return "Error: .doc format not fully supported. Please save as .docx and re-upload."\n        else:\n            return "Error: unsupported type"\n    except Exception as e:\n        return f"Error: {e}"'
if old6b in c:
    c = c.replace(old6b, new6b, 1); n += 1; print("FIX6b OK: .doc handling added")

# Also add .doc to JD uploader
old6c = '"📎 Upload JD (PDF or DOCX)",\n            type=["pdf","docx","txt"],'
new6c = '"📎 Upload JD (PDF, DOCX, DOC or TXT)",\n            type=["pdf","docx","doc","txt"],'
if old6c in c:
    c = c.replace(old6c, new6c, 1); n += 1; print("FIX6c OK: .doc added to JD uploader")

p.write_text(c, encoding="utf-8")
print(f"FIX6 total: {n} changes applied")
