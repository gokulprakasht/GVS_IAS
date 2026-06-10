import os, subprocess, sys

IAS_DIR = r"C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL"
os.chdir(IAS_DIR)

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.returncode

print()
print("=" * 55)
print("  IAS v9.0 - Auto Push to GitHub + Streamlit Cloud")
print("  GVS Technologies . Gokul Prakash T")
print("=" * 55)
print()

# Step 1: Fix any conflicts
print("[1/5] Checking for merge conflicts...")
files_to_check = [
    "app.py", ".gitignore", "requirements.txt",
    ".streamlit\\config.toml"
]
for filepath in files_to_check:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    has_conflict = any(l.startswith('<<<<<<<') or l.startswith('>>>>>>>') for l in lines)
    if has_conflict:
        clean = []
        skip = False
        for line in lines:
            if line.startswith('<<<<<<< '): skip=False; continue
            elif line.startswith('======='): skip=True; continue
            elif line.startswith('>>>>>>> '): skip=False; continue
            if not skip: clean.append(line)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(clean)
        print(f"  Fixed conflicts in: {filepath}")
print("  Done.")

# Step 2: Stage all files
print()
print("[2/5] Staging files...")
files_to_stage = [
    "app.py",
    "requirements.txt",
    "gcal_integration.py",
    ".gitignore",
    ".streamlit\\config.toml",
    "core\\apikey.py",
    "core\\config.py",
    "core\\reporter.py",
    "core\\auto_session.py",
    "core\\gmail_monitor.py",
]
for f in files_to_stage:
    if os.path.exists(f):
        run(f'git add "{f}" -f')
        print(f"  Staged: {f}")

# Step 3: Commit
print()
print("[3/5] Committing...")
import datetime
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
commit_msg = f"IAS v9.0 auto-deploy - {timestamp}"
rc = run(f'git commit -m "{commit_msg}"')
if rc != 0:
    print("  Nothing new to commit or already committed.")

# Step 4: Push to GVS_IAS (Streamlit Cloud source)
print()
print("[4/5] Pushing to GitHub (GVS_IAS)...")
rc = run("git push gvsias main")
if rc != 0:
    print("  Trying force push...")
    run("git push gvsias main --force")

# Step 5: Also push to IAS_CLOUD backup
print()
print("[5/5] Pushing to backup repo (IAS_CLOUD)...")
run("git push origin main")

print()
print("=" * 55)
print("  DONE! Streamlit Cloud will redeploy in ~60 seconds")
print("  Live URL: https://gvs-ias.streamlit.app")
print("=" * 55)
print()
input("Press Enter to close...")
