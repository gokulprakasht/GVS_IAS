import os
os.chdir(r"C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL")

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

clean = []
skip = False
for line in lines:
    if line.startswith('<<<<<<<'):
        skip = False
        continue
    elif line.startswith('======='):
        skip = True
        continue
    elif line.startswith('>>>>>>>'):
        skip = False
        continue
    if not skip:
        clean.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(clean)

removed = len(lines) - len(clean)
print(f"Done! Removed {removed} conflict lines from app.py")
input("Press Enter to continue...")
