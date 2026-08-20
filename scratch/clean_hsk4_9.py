# scratch/clean_hsk4_9.py
import os
import shutil
import json

print("Cleaning HSK 4-9 files to prepare for full-member re-crawl...")

# 1. Delete HSK 4-9 folders
for level in range(4, 10):
    folder_path = f"db/stories/hsk-{level}"
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            print(f"Deleted folder: {folder_path}")
        except Exception as e:
            print(f"Error deleting folder {folder_path}: {e}")

# 2. Filter db/library.json to keep only HSK 1-3
library_index_path = "db/library.json"
if os.path.exists(library_index_path):
    try:
        with open(library_index_path, "r", encoding="utf-8") as f:
            library_data = json.load(f)
            
        clean_library = [s for s in library_data if s.get("hsk_level", 1) in [1, 2, 3]]
        
        with open(library_index_path, "w", encoding="utf-8") as f:
            json.dump(clean_library, f, ensure_ascii=False, indent=2)
            
        print(f"Cleaned db/library.json. Kept {len(clean_library)} stories (HSK 1-3).")
    except Exception as e:
        print(f"Error cleaning library index: {e}")

print("Clean up completed successfully!")
