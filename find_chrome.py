import os

paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
]

found = False
for p in paths:
    if os.path.exists(p):
        print(f"Found Chrome at: {p}")
        found = True
        break

if not found:
    print("Chrome not found in default paths.")
