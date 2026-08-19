# scratch/test_url_timeout.py
import urllib.request
import urllib.error

url = "https://hskstory.com/stories/hsk-1/movie-night"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
req = urllib.request.Request(url, headers=headers)

try:
    print("Fetching story page with 5s timeout...")
    with urllib.request.urlopen(req, timeout=5) as response:
        print("Success! Status code:", response.getcode())
        print("Content length:", len(response.read()))
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
except Exception as e:
    print(f"Error / Timeout: {e}")
