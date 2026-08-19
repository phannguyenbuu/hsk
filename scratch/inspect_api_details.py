# scratch/inspect_api_details.py
import urllib.request
import json

url = "https://hskstory.com/api/stories/1/morning-at-home/chapters/chapter-2-daughters-backpack?script=simplified&reader_media_contract=1"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        with open("scratch/api_inspect.txt", "w", encoding="utf-8") as out:
            out.write("Keys: " + str(list(data.keys())) + "\n\n")
            
            for key in ["translation_data", "pinyin_data"]:
                val = data.get(key)
                out.write(f"--- {key} (type: {type(val)}) ---\n")
                if isinstance(val, str):
                    out.write("Snippet: " + val[:500] + "\n")
                    if val.strip().startswith('{') or val.strip().startswith('['):
                        try:
                            parsed = json.loads(val)
                            out.write(f"Parsed JSON! Keys: {list(parsed.keys())[:10] if isinstance(parsed, dict) else len(parsed)}\n")
                            # Write a sample item
                            if isinstance(parsed, dict):
                                sample_k = list(parsed.keys())[0]
                                out.write(f"Sample item: {sample_k} -> {parsed[sample_k]}\n")
                        except Exception as pe:
                            out.write(f"Failed to parse JSON: {pe}\n")
                else:
                    out.write(str(val)[:500] + "\n")
                out.write("\n" + "="*50 + "\n\n")
        print("Wrote results to scratch/api_inspect.txt")
except Exception as e:
    print("Error:", e)
