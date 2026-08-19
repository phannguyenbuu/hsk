# scratch/test_api.py
import urllib.request
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

urls = [
    # Story details API
    "https://hskstory.com/api/stories/1/morning-at-home/chapters/chapter-2-daughters-backpack?script=simplified&reader_media_contract=1",
]

for url in urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            print(f"[SUCCESS] {url}")
            print("  Status code:", response.getcode())
            data = json.loads(response.read().decode('utf-8'))
            print("  Keys:", list(data.keys()))
            # Print a snippet of content_html
            if "content_html" in data:
                print("  content_html snippet:", data["content_html"][:150] + "...")
    except Exception as e:
        print(f"[FAILED] {url}: {e}")
