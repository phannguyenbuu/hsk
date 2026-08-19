# scratch/test_story_details.py
import urllib.request
import re

url = "https://hskstory.com/stories/hsk-1/morning-at-home"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        print("[SUCCESS] Loaded story landing page.")
        # Find chapter links like: href="/stories/hsk-1/morning-at-home/chapter-X-slug"
        pattern = r'href="/stories/hsk-1/morning-at-home/([a-z0-9\-]+)"'
        matches = re.findall(pattern, content)
        print("Chapters found:", list(set(matches)))
except Exception as e:
    print("Error:", e)
