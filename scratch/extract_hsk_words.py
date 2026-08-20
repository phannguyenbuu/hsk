# scratch/extract_hsk_words.py
import json
import os

print("Extracting HSK words mapping from zh-dict-simplified.json...")

master_path = "zh-dict-simplified.json"
output_path = "db/hsk_words.json"

if not os.path.exists(master_path):
    print(f"Error: {master_path} does not exist.")
    exit(1)

try:
    with open(master_path, "r", encoding="utf-8") as f:
        master_dict = json.load(f)
        
    hsk_mapping = {}
    for word, info in master_dict.items():
        if isinstance(info, dict) and "h" in info:
            hsk_mapping[word] = int(info["h"])
            
    print(f"Found {len(hsk_mapping)} words with HSK levels.")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(hsk_mapping, f, ensure_ascii=False)
        
    print(f"Saved lightweight mapping to {output_path} (size: {os.path.getsize(output_path)} bytes)")
    
except Exception as e:
    print(f"Error extracting HSK words: {e}")
