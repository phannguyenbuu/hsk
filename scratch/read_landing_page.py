# scratch/read_landing_page.py
import urllib.request
import re

url = "https://hskstory.com/stories/hsk-1/morning-at-home"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        
        # Save to file
        with open("scratch/landing_page.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Landing page saved to scratch/landing_page.html")
        
        # Search for any strings containing "chapter-" or "chapters"
        matches = re.finditer(r'chapter-[a-z0-9\-]+', content)
        found = list(set([m.group(0) for m in matches]))
        print("Found chapter-like slugs in HTML:")
        for f_slug in found[:10]:
            print("  -", f_slug)
            
except Exception as e:
    print("Error:", e)
