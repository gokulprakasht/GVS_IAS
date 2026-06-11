import os

app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
print(f"Patching: {app_path}")

with open(app_path, encoding='utf-8', errors='replace') as f:
    content = f.read()

before = content.count('infographic')
content = content.replace('from infographic import show_infographic\n', '')
content = content.replace('from infographic import show_infographic\r\n', '')
content = content.replace('    show_infographic()\n', '')
content = content.replace('    show_infographic()\r\n', '')
after = content.count('infographic')

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed. Removed {before - after} reference(s).")
print("Now run: python -m streamlit run app.py")
