"""
IAS Keep-Alive Service
Pings the app every 10 minutes to prevent Render free tier sleep.
Runs as a background thread automatically when app starts.
"""
import threading
import time
import urllib.request
import os

PING_URL = "https://gvs-ias.onrender.com"
PING_INTERVAL = 600  # 10 minutes

def ping():
    while True:
        try:
            urllib.request.urlopen(PING_URL, timeout=10)
        except Exception:
            pass
        time.sleep(PING_INTERVAL)

def start():
    # Only run on cloud (Render sets PORT env var)
    if os.environ.get("PORT"):
        t = threading.Thread(target=ping, daemon=True)
        t.start()
