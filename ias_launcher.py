import subprocess, os, sys, time, webbrowser, threading

APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

def open_browser():
    time.sleep(12)
    webbrowser.open("http://localhost:8502")

def run(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)

def main():
    os.chdir(APP_DIR)
    print("===============================================")
    print("  IAS v8 - Interview Assessment System")
    print("  GVS Technologies / Digitaliotai")
    print("===============================================\n")

    # Check Docker
    r = run(["docker", "info"], capture_output=True)
    if r.returncode != 0:
        print("ERROR: Docker is not running. Please start Docker Desktop and try again.")
        input("Press Enter to exit...")
        return

    # Check api key
    if not os.path.exists(os.path.join(APP_DIR, "api_key.txt")):
        key = input("Enter your ANTHROPIC_API_KEY: ").strip()
        with open(os.path.join(APP_DIR, "api_key.txt"), "w") as f:
            f.write(key)
        with open(os.path.join(APP_DIR, ".env"), "w") as f:
            f.write(f"ANTHROPIC_API_KEY={key}\n")
        print("API key saved.\n")

    # Write Dockerfile
    dockerfile = "\n".join([
        "FROM python:3.12-slim",
        "RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential ffmpeg && rm -rf /var/lib/apt/lists/*",
        "RUN groupadd -r ias && useradd -r -g ias -d /app -s /sbin/nologin ias",
        "WORKDIR /app",
        "COPY requirements.txt .",
        "RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt",
        "COPY --chown=ias:ias . .",
        "RUN mkdir -p /app/data /app/output /app/logs && chown -R ias:ias /app/data /app/output /app/logs",
        "USER ias",
        "EXPOSE 8501",
        'CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]',
    ])
    with open(os.path.join(APP_DIR, "Dockerfile"), "w") as f:
        f.write(dockerfile)

    print("[1/3] Stopping any old IAS container...")
    run(["docker", "rm", "-f", "ias-v8"], capture_output=True)

    print("[2/3] Building IAS v8 image (3-5 mins on first run)...")
    r = run(["docker", "build", "-t", "gvstechnologies/ias-v8:latest", APP_DIR])
    if r.returncode != 0:
        print("\nERROR: Docker build failed.")
        input("Press Enter to exit...")
        return

    print("[3/3] Starting IAS v8...")
    r = run(["docker", "run", "-d", "--name", "ias-v8",
             "-p", "8502:8501",
             "--env-file", os.path.join(APP_DIR, ".env"),
             "gvstechnologies/ias-v8:latest"])
    if r.returncode != 0:
        print("\nERROR: Failed to start container.")
        input("Press Enter to exit...")
        return

    threading.Thread(target=open_browser, daemon=True).start()
    print("\n===============================================")
    print("  IAS v8 is LIVE at http://localhost:8502")
    print("  Browser opening automatically...")
    print("===============================================\n")
    input("  Press Enter to STOP IAS v8...\n")
    run(["docker", "rm", "-f", "ias-v8"])
    print("IAS v8 stopped. Goodbye!")

if __name__ == "__main__":
    main()
