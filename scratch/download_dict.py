# scratch/download_dict.py
import urllib.request
import json
import os

url = "https://hskstory.com/zh-dict-simplified.json?v=4"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)

try:
    print("Downloading master dictionary...")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        # Save locally in root directory
        with open("zh-dict-simplified.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("Successfully downloaded dictionary!")
        print("Number of dictionary entries:", len(data))
        # Print first 3 entries for inspection
        first_keys = list(data.keys())[:3]
        for k in first_keys:
            print(f"  {k} -> {data[k]}")
except Exception as e:
    print("Error:", e)
