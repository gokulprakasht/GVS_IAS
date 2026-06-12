# IAS v9.0 — Interview Assessment System
**GVS Technologies · Zero Touch · Run Anywhere**

## Deploy to Streamlit Cloud (3 Steps)

### Step 1 — Push to GitHub
```bash
git add .
git commit -m "IAS v9.0 deploy"
git push origin main
```

### Step 2 — Add Secrets on Streamlit Cloud
Go to [share.streamlit.io](https://share.streamlit.io) → your app → **Settings → Secrets**

Paste the contents of `.streamlit/secrets.toml.template` and fill in your values.

### Step 3 — Deploy
Streamlit Cloud auto-deploys on every push. Your app will be live at:
`https://gvs-ias.streamlit.app`

## Local Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Fixes Applied (v9.0 Final)
- ✅ `_curr_ind` NameError on home page resolved
- ✅ Industry synced across all pages via session state
- ✅ NAV defaults to COMMAND CENTRE expanded
- ✅ `integrations` page redirects to `intHub`
- ✅ Cloud secrets loaded from Streamlit secrets
- ✅ Data directories auto-created on cloud
