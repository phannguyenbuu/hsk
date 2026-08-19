# scratch/search_library_json.py
import re

file_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\8c374b56-5464-4432-9397-e10c63492b40\.system_generated\steps\634\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's search for "morning-at-home" and print the surrounding characters
matches = re.finditer(r'morning-at-home', content)
print("Matches for 'morning-at-home':")
for m in list(matches)[:5]:
    start = max(0, m.start() - 150)
    end = min(len(content), m.end() + 250)
    print(f"Match at {m.start()}:\n... {content[start:end]} ...\n")
