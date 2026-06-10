import os

IAS_DIR = r"C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL"
os.chdir(IAS_DIR)

def fix_conflicts(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        clean = []
        skip = False
        removed = 0
        for line in lines:
            if line.startswith('<<<<<<<'):
                skip = False; removed += 1; continue
            elif line.startswith('======='):
                skip = True; removed += 1; continue
            elif line.startswith('>>>>>>>'):
                skip = False; removed += 1; continue
            if not skip:
                clean.append(line)
            else:
                removed += 1
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(clean)
        print(f"  Fixed: {filepath} ({removed} conflict lines removed)")
    except Exception as e:
        print(f"  Skip: {filepath} ({e})")

print()
print("IAS Merge Conflict Fixer")
print("=" * 40)
print()

for f in ["app.py", ".gitignore", "requirements.txt",
          ".streamlit\\config.toml", ".streamlit\\secrets.toml"]:
    if os.path.exists(f):
        fix_conflicts(f)

print()
print("Done! All conflicts fixed.")
print()
input("Press Enter to close...")
