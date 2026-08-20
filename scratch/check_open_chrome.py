# scratch/check_open_chrome.py
import urllib.request
import json

try:
    print("Checking if Chrome is running on debugging port 9222...")
    req = urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=3)
    tabs = json.loads(req.read().decode('utf-8'))
    print(f"Success! Chrome is debugging on port 9222. Found {len(tabs)} tabs open.")
    for t in tabs:
        print(f"- {t.get('title')} ({t.get('url')})")
except Exception as e:
    print(f"No active debugging Chrome found on port 9222: {e}")
