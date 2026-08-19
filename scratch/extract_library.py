# scratch/extract_library.py
import re
import json

file_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\8c374b56-5464-4432-9397-e10c63492b40\.system_generated\steps\634\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's search for story objects. They usually look like:
# {"slug":"...", "hsk_level":..., "title":"...", "id":...} or similar
# Let's match all instances of story-like JSON fragments.
# A typical pattern: "slug":"some-slug","hsk_level":1
stories = []
matches = re.finditer(r'\{"slug":"([a-z0-9\-]+?)","hsk_level":(\d+),', content)
for m in matches:
    # Let's try to extract the whole dictionary by finding the matching braces
    start_idx = m.start()
    # Read forward to find the ending brace
    brace_count = 0
    end_idx = start_idx
    for i in range(start_idx, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    dict_str = content[start_idx:end_idx]
    # Clean escaped characters in next.js format if necessary
    try:
        # Unescape quotes \"
        dict_str_clean = dict_str.replace('\\"', '"').replace('\\\\', '\\')
        obj = json.loads(dict_str_clean)
        if "slug" in obj and "title" in obj and obj not in stories:
            stories.append(obj)
    except Exception as e:
        # If it failed to parse, let's try a regex for the individual fields
        title_match = re.search(r'"title":"(.*?)"', dict_str)
        id_match = re.search(r'"id":(\d+)', dict_str)
        if title_match and id_match:
            stories.append({
                "slug": m.group(1),
                "hsk_level": int(m.group(2)),
                "title": title_match.group(1),
                "id": int(id_match.group(1))
            })

# Let's print how many we found and write to JSON
print(f"Found {len(stories)} stories in library!")
with open("scratch/library_stories.json", "w", encoding="utf-8") as out:
    json.dump(stories, out, ensure_ascii=False, indent=2)
