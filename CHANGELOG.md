# IAS v9.0 — Release Notes
**GVS Technologies / Digitaliotai**
**Release Date: 11 Jun 2026**

---

## What's New in v9.0

### Core Workflow
- Zero-touch email-to-interview pipeline — Gmail monitor auto-starts on launch
- Questions pre-generated on email receipt — ready before Zoom starts
- Candidate folder: `CandidateName_InterviewDate_Duration` format
- CV + Photo ID + JD + Questions saved to folder automatically
- Question caching — no regeneration unless explicitly requested
- Question Records table — tracks all generated Q-Banks with metadata

### Executive Dashboard
- Role-based views: CxO/Board · Business Leadership · Operational · Manager/Director
- RAG drill-down: Big Picture → Contributing Factors → Root Causes → Authority Actions
- Pipeline funnel, Risk Register, Recruiter Productivity per role

### Assessment Intelligence
- 6 Telecom Assessment Packs (Nokia NetAct, TM Forum, 5G, OSS/BSS, Autonomous, AI for Telecom)
- 6 Competency Frameworks (Leadership, Architecture, DevOps, AI/ML, Telecom, Programme Mgmt)
- AI Interview Copilot with real-time guidance and competency alerts
- GenAI Hiring Insights — strengths/risks, gap analysis, HM briefing

### Integrations
- ATS Integration Layer — 8 platforms (Workday, SAP, Oracle, Greenhouse, Lever, Bullhorn, iCIMS, SmartRecruiters)
- Google Calendar live scheduling with Meet auto-generation
- Gmail monitor — 24h search window, HTML email parsing, forwarded email support

### Quality & DevOps
- QA Test Report — 70 test cases (40 functional + 30 non-functional)
- Zero Data Loss certification across 12 data elements
- Zero Performance Degradation certification (k6: 0 errors at 100 VUs)
- Docker Compose 6-container stack with Grafana performance dashboard
- GitHub Actions CI/CD pipeline with auto-rollback
- Terraform AWS ECS + Azure ACI deployment

### UI/UX
- Theme 01 Dark Command — navy/teal/orange throughout all 47 pages
- All emoji removed from expander labels (Windows encoding fix)
- Questions DOCX export via python-docx (no Node.js required)
- Self-healing IAS_Start.bat with 7 Q-gates

### Bug Fixes
- infographic import removed
- _today_str NameError fixed
- Select All button stays on Step 2
- NEXT/PREV navigation unique keys
- Gmail monitor auto-starts without restart
- .doc file support (4-method conversion chain)
- Duplicate widget key conflicts resolved

---

## Deployment

| Option | How |
|---|---|
| Streamlit Cloud | Fork repo → share.streamlit.io → add API key secret |
| Local Windows | Double-click IAS_Start.bat |
| Docker | docker-compose up -d |
| AWS ECS | terraform apply (terraform/aws/) |

## Live URLs
- **Production:** https://gvs-ias.streamlit.app
- **Backup:** https://gvs-ias.onrender.com
- **GitHub:** https://github.com/gokulprakasht/GVS_IAS
