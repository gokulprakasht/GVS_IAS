"""
gcal_integration.py — Google Calendar Service Account Integration for IAS v9.0
GVS Technologies · Gokul Prakash T · Innovate before you automate

Provides:
  - GCalClient      : Service account auth + event CRUD
  - create_interview_event() : One-call interview scheduler
  - list_upcoming()          : Fetch upcoming interviews from Google Calendar
  - delete_event()           : Cancel / remove an event
  - check_availability()     : Check if a time slot is free

Dependencies (install once):
    pip install google-api-python-client google-auth google-auth-httplib2

Usage in IAS app.py:
    from gcal_integration import GCalClient, create_interview_event
    client = GCalClient.from_json_file("google_credentials.json", calendar_id="primary")
    result = create_interview_event(client, candidate=..., ...)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo


# ── Dependency guard ────────────────────────────────────────────────────────
def _require_google_libs():
    """Raise ImportError with install instruction if google libs are missing."""
    try:
        from googleapiclient.discovery import build          # noqa: F401
        from google.oauth2 import service_account            # noqa: F401
    except ImportError:
        raise ImportError(
            "Google API libraries not installed.\n"
            "Run: pip install google-api-python-client google-auth google-auth-httplib2"
        )


# ── Data classes ────────────────────────────────────────────────────────────
@dataclass
class InterviewEvent:
    """All fields needed to create a Google Calendar interview event."""
    candidate_name:  str
    candidate_email: str
    role:            str
    round_name:      str                        # e.g. "Technical F2F"
    start_dt:        datetime                   # timezone-aware recommended
    duration_mins:   int         = 45
    mode:            str         = "Zoom"       # Zoom | Google Meet | MS Teams | In-person
    meeting_link:    str         = ""
    panel_emails:    list[str]   = field(default_factory=list)
    notes:           str         = ""
    timezone:        str         = "Asia/Kolkata"
    organizer_name:  str         = "Gokul Prakash T"
    organizer_email: str         = "gokul1978@gmail.com"
    send_notifications: bool     = True


@dataclass
class EventResult:
    """Result from a Google Calendar API call."""
    success:  bool
    event_id: str         = ""
    html_link: str        = ""
    error:    str         = ""
    raw:      dict        = field(default_factory=dict)


# ── Client ──────────────────────────────────────────────────────────────────
class GCalClient:
    """
    Thin wrapper around the Google Calendar API v3 service.

    Instantiate via:
        GCalClient.from_json_file("google_credentials.json", calendar_id="primary")
        GCalClient.from_json_string(json_str, calendar_id="primary")
        GCalClient.from_settings_dict(settings, calendar_id=None)  # reads from IAS cfg
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, service, calendar_id: str = "primary"):
        self._service     = service
        self.calendar_id  = calendar_id

    # ── Constructors ────────────────────────────────────────────────────────
    @classmethod
    def from_json_file(cls, path: str | Path, calendar_id: str = "primary") -> "GCalClient":
        _require_google_libs()
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            str(path), scopes=cls.SCOPES
        )
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return cls(service, calendar_id)

    @classmethod
    def from_json_string(cls, json_str: str, calendar_id: str = "primary") -> "GCalClient":
        _require_google_libs()
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        info  = json.loads(json_str)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=cls.SCOPES
        )
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return cls(service, calendar_id)

    @classmethod
    def from_settings_dict(cls, settings: dict, calendar_id: str | None = None) -> "GCalClient":
        """
        Build client from IAS cfg.get_settings() dict.
        Expects keys: gcal_creds_json (full JSON string) and gcal_id.
        Falls back to google_credentials.json file in current dir.
        """
        cal_id     = calendar_id or settings.get("gcal_id", "primary")
        creds_json = settings.get("gcal_creds_json", "")

        if creds_json:
            return cls.from_json_string(creds_json, cal_id)

        # Fallback: look for file next to app.py / cwd
        for candidate_path in [
            Path("google_credentials.json"),
            Path(__file__).parent / "google_credentials.json",
        ]:
            if candidate_path.exists():
                return cls.from_json_file(candidate_path, cal_id)

        raise FileNotFoundError(
            "google_credentials.json not found and no JSON stored in settings.\n"
            "Go to IAS → Settings → Calendar Config and paste your Service Account JSON."
        )

    # ── Core API methods ────────────────────────────────────────────────────
    def create_event(self, event_body: dict) -> EventResult:
        """Raw event creation — pass a Google Calendar event resource dict."""
        try:
            result = (
                self._service.events()
                .insert(
                    calendarId=self.calendar_id,
                    body=event_body,
                    sendUpdates="all",   # sends email invites to all attendees
                )
                .execute()
            )
            return EventResult(
                success=True,
                event_id=result.get("id", ""),
                html_link=result.get("htmlLink", ""),
                raw=result,
            )
        except Exception as exc:
            return EventResult(success=False, error=str(exc))

    def get_event(self, event_id: str) -> EventResult:
        try:
            result = (
                self._service.events()
                .get(calendarId=self.calendar_id, eventId=event_id)
                .execute()
            )
            return EventResult(success=True, event_id=event_id, raw=result)
        except Exception as exc:
            return EventResult(success=False, error=str(exc))

    def delete_event(self, event_id: str) -> EventResult:
        try:
            self._service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates="all",
            ).execute()
            return EventResult(success=True, event_id=event_id)
        except Exception as exc:
            return EventResult(success=False, error=str(exc))

    def list_upcoming(self, max_results: int = 20, days_ahead: int = 30) -> list[dict]:
        """Return upcoming interview events (created by IAS) sorted by start time."""
        try:
            now       = datetime.utcnow().isoformat() + "Z"
            until     = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
            result    = (
                self._service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=now,
                    timeMax=until,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                    q="IAS",            # IAS prefix in all event titles
                )
                .execute()
            )
            return result.get("items", [])
        except Exception:
            return []

    def check_availability(
        self, start_dt: datetime, end_dt: datetime, emails: list[str]
    ) -> dict[str, bool]:
        """
        Check if each email is free during the given time window.
        Returns {email: is_free} dict.
        """
        try:
            body = {
                "timeMin": start_dt.isoformat(),
                "timeMax": end_dt.isoformat(),
                "timeZone": "UTC",
                "items": [{"id": e} for e in emails],
            }
            result = self._service.freebusy().query(body=body).execute()
            calendars = result.get("calendars", {})
            availability = {}
            for email in emails:
                busy_slots = calendars.get(email, {}).get("busy", [])
                availability[email] = len(busy_slots) == 0
            return availability
        except Exception:
            return {email: True for email in emails}  # assume free on error


# ── High-level helper ───────────────────────────────────────────────────────
def create_interview_event(client: GCalClient, ev: InterviewEvent) -> EventResult:
    """
    Build and create a fully-formatted Google Calendar interview event.

    The event includes:
      - Structured title: [IAS] Technical F2F — Candidate Name — Role
      - HTML description with all interview details
      - Candidate + panel as attendees (with email invites)
      - Google Meet / Zoom link as conferenceData location
      - IST timezone handling
      - IAS branding in description footer
    """
    tz        = ZoneInfo(ev.timezone)
    start     = ev.start_dt if ev.start_dt.tzinfo else ev.start_dt.replace(tzinfo=tz)
    end       = start + timedelta(minutes=ev.duration_mins)

    title     = f"[IAS] {ev.round_name} — {ev.candidate_name} — {ev.role}"

    description = f"""
<b>Interview Details</b><br>
<br>
<b>Candidate:</b> {ev.candidate_name}<br>
<b>Role:</b> {ev.role}<br>
<b>Round:</b> {ev.round_name}<br>
<b>Mode:</b> {ev.mode}<br>
{f'<b>Meeting Link:</b> <a href="{ev.meeting_link}">{ev.meeting_link}</a><br>' if ev.meeting_link else ''}
<b>Duration:</b> {ev.duration_mins} minutes<br>
<b>Organiser:</b> {ev.organizer_name}<br>
<br>
{f'<b>Notes for Panel:</b><br>{ev.notes}<br><br>' if ev.notes else ''}
<hr>
<i>Scheduled by IAS v9.0 · GVS Technologies · Innovate before you automate</i>
""".strip()

    attendees = [{"email": ev.candidate_email, "displayName": ev.candidate_name}]
    for panel_email in ev.panel_emails:
        if panel_email.strip():
            attendees.append({"email": panel_email.strip()})

    event_body = {
        "summary": title,
        "description": description,
        "location": ev.meeting_link or ev.mode,
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": ev.timezone,
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": ev.timezone,
        },
        "attendees": attendees,
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email",  "minutes": 24 * 60},   # 24h before
                {"method": "popup",  "minutes": 30},         # 30 min before
            ],
        },
        "guestsCanSeeOtherGuests": True,
        "guestsCanModify": False,
    }

    # Add video conferencing metadata if a link is provided
    if ev.meeting_link:
        if "zoom.us" in ev.meeting_link:
            event_body["conferenceData"] = {
                "conferenceSolution": {"name": "Zoom"},
                "entryPoints": [{"entryPointType": "video", "uri": ev.meeting_link}],
            }
        elif "meet.google.com" in ev.meeting_link:
            event_body["conferenceData"] = {
                "conferenceSolution": {"key": {"type": "hangoutsMeet"}},
                "entryPoints": [{"entryPointType": "video", "uri": ev.meeting_link}],
            }

    return client.create_event(event_body)


# ── IAS Streamlit UI block ──────────────────────────────────────────────────
def render_gcal_schedule_button(
    settings: dict,
    candidate_name: str,
    candidate_email: str,
    role: str,
    round_name: str,
    start_dt: datetime,
    duration_mins: int,
    mode: str,
    meeting_link: str,
    panel_emails: list[str],
    notes: str,
) -> None:
    """
    Drop this into any Streamlit page to render a
    'Push to Google Calendar' button with full status feedback.

    Example usage in app.py calendar page:

        from gcal_integration import render_gcal_schedule_button
        render_gcal_schedule_button(
            settings=cfg.get_settings(),
            candidate_name=cal_cand,
            candidate_email=cal_email,
            ...
        )
    """
    import streamlit as st

    gcal_ready = bool(
        settings.get("gcal_creds_json") or
        Path("google_credentials.json").exists() or
        (Path(__file__).parent / "google_credentials.json").exists()
    )

    if not gcal_ready:
        st.info(
            "🔑 Google Calendar not configured. "
            "Go to **Settings → Calendar Config** and paste your Service Account JSON."
        )
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(
            "📅 Push to Google Calendar",
            type="primary",
            use_container_width=True,
            disabled=not (candidate_name and candidate_email),
            help="Creates a Google Calendar event and sends email invites to all attendees",
        ):
            with st.spinner("Creating Google Calendar event..."):
                try:
                    client = GCalClient.from_settings_dict(settings)
                    ev = InterviewEvent(
                        candidate_name=candidate_name,
                        candidate_email=candidate_email,
                        role=role,
                        round_name=round_name,
                        start_dt=start_dt,
                        duration_mins=duration_mins,
                        mode=mode,
                        meeting_link=meeting_link,
                        panel_emails=panel_emails,
                        notes=notes,
                        organizer_name=settings.get("interviewer_name", "Gokul Prakash T"),
                        organizer_email=settings.get("sender_email", "gokul1978@gmail.com"),
                        send_notifications=True,
                    )
                    result = create_interview_event(client, ev)
                    if result.success:
                        st.success(
                            f"✅ Google Calendar event created!\n\n"
                            f"📅 **{round_name}** — {candidate_name}\n\n"
                            f"[Open in Google Calendar]({result.html_link})"
                        )
                        # Store event ID in session for later cancellation
                        if "_gcal_events" not in st.session_state:
                            st.session_state["_gcal_events"] = []
                        st.session_state["_gcal_events"].append({
                            "event_id":  result.event_id,
                            "html_link": result.html_link,
                            "candidate": candidate_name,
                            "round":     round_name,
                            "datetime":  start_dt.strftime("%d-%b-%Y %H:%M"),
                        })
                    else:
                        st.error(f"❌ Failed to create event: {result.error}")
                except FileNotFoundError as e:
                    st.error(str(e))
                except ImportError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
    with col2:
        st.caption("Sends email invites to candidate + panel automatically")


# ── Settings UI block ───────────────────────────────────────────────────────
def render_gcal_config_form(settings: dict, save_fn) -> None:
    """
    Renders the Google Calendar configuration form.
    Drop into IAS Settings → Calendar Config tab.

    Args:
        settings: cfg.get_settings()
        save_fn:  cfg.save_settings  (called with dict of changed keys)
    """
    import streamlit as st

    with st.form("gcal_sa_form"):
        st.markdown("##### 🔑 Service Account Credentials")
        st.caption(
            "Paste the full contents of your `google_credentials.json` file downloaded "
            "from Google Cloud Console → IAM & Admin → Service Accounts → Keys."
        )
        creds_json = st.text_area(
            "Service Account JSON",
            value=settings.get("gcal_creds_json", ""),
            height=120,
            placeholder='{"type":"service_account","project_id":"ias-calendar",...}',
            help="Full JSON — never share this externally",
        )

        gc1, gc2 = st.columns(2)
        cal_id = gc1.text_input(
            "Calendar ID",
            value=settings.get("gcal_id", "primary"),
            help="'primary' or your full email, or a shared calendar ID",
            placeholder="gokul1978@gmail.com",
        )
        tz = gc2.selectbox(
            "Timezone",
            ["Asia/Kolkata", "Asia/Dubai", "Europe/London",
             "America/New_York", "America/Los_Angeles", "UTC"],
            index=["Asia/Kolkata", "Asia/Dubai", "Europe/London",
                   "America/New_York", "America/Los_Angeles", "UTC"].index(
                settings.get("gcal_timezone", "Asia/Kolkata")
            ),
        )

        st.markdown("##### 📋 Reminder Defaults")
        r1, r2 = st.columns(2)
        remind_email = r1.number_input(
            "Email reminder (hours before)",
            min_value=1, max_value=72,
            value=settings.get("gcal_remind_email_hrs", 24),
        )
        remind_popup = r2.number_input(
            "Popup reminder (minutes before)",
            min_value=5, max_value=120,
            value=settings.get("gcal_remind_popup_mins", 30),
        )

        submitted = st.form_submit_button(
            "💾 Save & Verify Connection", type="primary", use_container_width=True
        )
        if submitted:
            if creds_json.strip():
                # Validate JSON structure
                try:
                    parsed = json.loads(creds_json)
                    if parsed.get("type") != "service_account":
                        st.error("❌ This doesn't look like a service account JSON. "
                                 "Check the 'type' field.")
                    else:
                        save_fn({
                            "gcal_creds_json":        creds_json.strip(),
                            "gcal_id":                cal_id,
                            "gcal_timezone":          tz,
                            "gcal_remind_email_hrs":  remind_email,
                            "gcal_remind_popup_mins": remind_popup,
                        })
                        # Quick connection test
                        try:
                            client = GCalClient.from_json_string(creds_json.strip(), cal_id)
                            upcoming = client.list_upcoming(max_results=1)
                            st.success(
                                f"✅ Connected to Google Calendar · Calendar ID: `{cal_id}` · "
                                f"Timezone: {tz}"
                            )
                        except Exception as conn_err:
                            st.warning(
                                f"⚠️ Settings saved but connection test failed: {conn_err}\n\n"
                                "Make sure you shared the calendar with the service account email."
                            )
                except json.JSONDecodeError as je:
                    st.error(f"❌ Invalid JSON: {je}")
            else:
                st.warning("Paste your service account JSON to save.")

    # Show service account email hint
    creds_preview = settings.get("gcal_creds_json", "")
    if creds_preview:
        try:
            sa_email = json.loads(creds_preview).get("client_email", "")
            if sa_email:
                st.info(
                    f"📧 **Share your Google Calendar with this service account email:**\n\n"
                    f"`{sa_email}`\n\n"
                    f"Go to calendar.google.com → Your Calendar → Settings → "
                    f"Share with specific people → Add `{sa_email}` → Make changes to events"
                )
        except Exception:
            pass


# ── Upcoming interviews renderer ────────────────────────────────────────────
def render_upcoming_interviews(settings: dict) -> None:
    """Renders the Upcoming Interviews tab — fetches live from Google Calendar."""
    import streamlit as st

    gcal_ready = bool(settings.get("gcal_creds_json"))
    if not gcal_ready:
        st.info("Configure Google Calendar in the ⚙️ Calendar Config tab to see upcoming interviews here.")
        return

    with st.spinner("Fetching upcoming interviews from Google Calendar..."):
        try:
            client   = GCalClient.from_settings_dict(settings)
            upcoming = client.list_upcoming(max_results=20, days_ahead=30)
        except Exception as e:
            st.error(f"Could not fetch calendar: {e}")
            return

    if not upcoming:
        st.info("📭 No upcoming interviews in the next 30 days.")
        return

    st.markdown(f"**{len(upcoming)} upcoming interview(s)** — next 30 days")
    for ev in upcoming:
        start_raw  = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
        summary    = ev.get("summary", "Untitled")
        html_link  = ev.get("htmlLink", "#")
        attendees  = ev.get("attendees", [])
        event_id   = ev.get("id", "")

        try:
            from datetime import datetime as _dt
            start_fmt = _dt.fromisoformat(start_raw).strftime("%a %d %b %Y · %I:%M %p")
        except Exception:
            start_fmt = start_raw

        with st.expander(f"📅 {summary}  ·  {start_fmt}", expanded=False):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**🔗 [Open in Google Calendar]({html_link})**")
                if attendees:
                    att_list = [a.get("email", "") for a in attendees if a.get("email")]
                    st.caption("Attendees: " + " · ".join(att_list))
                desc = ev.get("description", "")
                if desc:
                    import re
                    clean_desc = re.sub(r"<[^>]+>", "", desc).strip()
                    st.text(clean_desc[:300])
            with col_b:
                if st.button(
                    "🗑 Cancel",
                    key=f"del_{event_id}",
                    help="Delete this event from Google Calendar",
                ):
                    result = client.delete_event(event_id)
                    if result.success:
                        st.success("Event cancelled.")
                        st.rerun()
                    else:
                        st.error(f"Could not cancel: {result.error}")


# ── CLI test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    """Quick smoke test — run: python gcal_integration.py"""
    import sys
    creds_file = Path("google_credentials.json")
    if not creds_file.exists():
        print("❌ google_credentials.json not found in current directory.")
        sys.exit(1)

    print("🔌 Connecting to Google Calendar...")
    client = GCalClient.from_json_file(creds_file, calendar_id="primary")

    from datetime import datetime, timedelta
    test_event = InterviewEvent(
        candidate_name  = "Test Candidate",
        candidate_email = "test@example.com",
        role            = "Senior Software Engineer",
        round_name      = "Technical F2F",
        start_dt        = datetime.now() + timedelta(hours=2),
        duration_mins   = 45,
        mode            = "Zoom",
        meeting_link    = "https://zoom.us/j/123456789",
        notes           = "IAS smoke test event — safe to delete",
        timezone        = "Asia/Kolkata",
    )

    print("📅 Creating test event...")
    result = create_interview_event(client, test_event)
    if result.success:
        print(f"✅ Event created: {result.html_link}")
        print(f"   Event ID: {result.event_id}")
        print("\n🗑 Deleting test event...")
        del_result = client.delete_event(result.event_id)
        print("✅ Deleted." if del_result.success else f"❌ Delete failed: {del_result.error}")
    else:
        print(f"❌ Failed: {result.error}")
