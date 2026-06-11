# IAS v9 — Setup Guide
### GVS Technologies / Digitaliotai | "Innovate before you automate"

---

## ⚡ Deploy in 3 Steps

### Option A — Streamlit Cloud (Recommended — Free, public URL)

1. Fork this repo: https://github.com/gokulprakasht/GVS_IAS
2. Go to https://share.streamlit.io → New app → select your fork → `app.py`
3. Add secret in App Settings → Secrets:
```toml
[anthropic]
api_key = "sk-ant-YOUR-KEY-HERE"
```
4. Click Deploy → your URL: **https://YOUR-APP.streamlit.app**

---

### Option B — Local (Windows)

```bash
# 1. Clone
git clone https://github.com/gokulprakasht/GVS_IAS.git
cd GVS_IAS

# 2. Install
pip install -r requirements.txt

# 3. Set API key
echo sk-ant-YOUR-KEY > api_key.txt

# 4. Run
streamlit run app.py
```
Or double-click **IAS_Start.bat**

---

### Option C — Docker (Any OS)

```bash
git clone https://github.com/gokulprakasht/GVS_IAS.git
cd GVS_IAS
echo "ANTHROPIC_API_KEY=sk-ant-YOUR-KEY" > .env
docker build -t ias-v9 .
docker run -p 8501:8501 --env-file .env ias-v9
```
Open: **http://localhost:8501**

---

## 🔑 Required

| Item | Where to get |
|---|---|
| Anthropic API key | https://console.anthropic.com |
| Gmail App Password | Google Account → Security → App Passwords |
| Google Calendar API | console.cloud.google.com (optional) |

---

## 🌐 Live Deployment

| Environment | URL |
|---|---|
| Production | https://gvs-ias.streamlit.app |
| Backup | https://gvs-ias.onrender.com |
| GitHub | https://github.com/gokulprakasht/GVS_IAS |

---

## 📞 Support
**Gokul Prakash T** | gokul1978@gmail.com | GVS Technologies
