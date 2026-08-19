# scratch/check_html_link_format.py
import re

file_path = "scratch/landing_page.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's search for "chapter-2-daughters-backpack" and write context to a file
matches = re.finditer(r'chapter-2-daughters-backpack', content)
with open("scratch/link_context.txt", "w", encoding="utf-8") as out:
    for m in matches:
        start = max(0, m.start() - 100)
        end = min(len(content), m.end() + 150)
        out.write(f"Context at {m.start()}:\n{content[start:end]}\n\n")

print("Wrote results to scratch/link_context.txt")
