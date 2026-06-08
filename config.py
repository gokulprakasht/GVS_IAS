"""
IAS Core Configuration Manager
Handles all data read/write operations with cloud-safe directory creation.
"""
import json, os, re
from pathlib import Path
from datetime import datetime

BASE  = Path(__file__).parent.parent
DATA  = BASE / "data"
OUT   = BASE / "output"

def _ensure_dirs():
    """Create data and output directories if they don't exist (needed on Render)."""
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        OUT.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

def _load(name):
    _ensure_dirs()
    f = DATA / f"{name}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

def _save(name, data):
    _ensure_dirs()
    f = DATA / f"{name}.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def get_setting(key, default=""):
    s = _load("settings").get(key, default)
    cloud_map = {
        "sender_email":       "SENDER_EMAIL",
        "gmail_app_password": "GMAIL_APP_PASSWORD",
        "interviewer_name":   "INTERVIEWER_NAME",
        "api_model":          "ANTHROPIC_MODEL",
    }
    if key in cloud_map:
        try:
            import streamlit as st
            v = st.secrets.get(cloud_map[key], "")
            if v: return v
        except Exception:
            pass
        v = os.environ.get(cloud_map[key], "")
        if v: return v
    return s

def get_settings():
    return _load("settings")

def save_settings(patch: dict):
    _ensure_dirs()
    s = _load("settings")
    s.update(patch)
    _save("settings", s)

def get_active_client():
    raw     = _load("clients")
    clients = raw.get("clients", raw) if isinstance(raw.get("clients"), dict) else raw
    clients = {k:v for k,v in clients.items() if isinstance(v, dict)}
    if not clients:
        return {"company_name":"Your Organisation","primary_color":"1F3864",
                "accent_color":"00C9A7","interviewer_name":"",
                "website":"","report_footer":"Confidential"}
    active  = raw.get("active_client","") or get_setting("active_client","")
    return clients.get(active, list(clients.values())[0])

def get_active_client_name():
    return get_active_client().get("company_name", "Your Organisation")

def get_report_template(key):
    return _load("report_templates").get(key, {})

def get_report_template_names():
    return list(_load("report_templates").keys())

def get_workflow(key):
    return _load("workflows").get(key, {})

def get_all_workflows():
    return _load("workflows")

def get_all_domains():
    return _load("jd_templates")

def get_stats(results):
    total    = len(results)
    selected = sum(1 for r in results if "SELECT" in r.get("verdict","").upper())
    avg      = sum(float(r.get("overall_score",0)) for r in results) / total if total else 0
    return {"total": total, "selected": selected, "rejected": total-selected, "avg_score": round(avg,1)}

def load_results(email="", is_admin=False):
    _ensure_dirs()
    f = DATA / "results.json"
    if not f.exists():
        return []
    all_r = json.loads(f.read_text(encoding="utf-8"))
    if is_admin:
        return all_r
    return [r for r in all_r if r.get("recruiter_email","") == email]

def save_result(data, **kwargs):
    _ensure_dirs()
    f     = DATA / "results.json"
    all_r = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    entry = {
        "id":            datetime.now().strftime("%Y%m%d%H%M%S"),
        "date":          data.get("date", datetime.now().strftime("%d-%b-%Y")),
        "time":          datetime.now().strftime("%H:%M"),
        "candidate":     data.get("candidate",""),
        "role":          data.get("role","")[:60],
        "verdict":       data.get("verdict",""),
        "overall_score": data.get("overall_score",0),
        **kwargs
    }
    all_r.append(entry)
    f.write_text(json.dumps(all_r, indent=2, ensure_ascii=False), encoding="utf-8")

def get_user(email):
    return _load("users").get(email, {})

def save_user(email, data):
    users = _load("users")
    users[email] = data
    _save("users", users)

def get_all_users():
    return _load("users")
