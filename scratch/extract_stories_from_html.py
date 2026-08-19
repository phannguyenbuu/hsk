# scratch/extract_stories_from_html.py
import re
import json

file_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\8c374b56-5464-4432-9397-e10c63492b40\.system_generated\steps\634\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's search for story links:
# href="/stories/hsk-X/story-slug/chapter-slug"
pattern = r'href="/stories/hsk-(\d+)/([a-z0-9\-]+)/([a-z0-9\-]+)"'
matches = re.finditer(pattern, content)

stories_map = {}

for m in matches:
    hsk_level = int(m.group(1))
    story_slug = m.group(2)
    first_chapter_slug = m.group(3)
    
    # Let's extract the title by looking at the card that contains this link.
    # In Next.js, the card contains data-testid="story-library-card-story-slug"
    # Let's find the card markup around this match.
    card_pattern = r'data-testid="story-library-card-' + re.escape(story_slug) + r'".*?card-title".*?>(.*?)</span>'
    card_match = re.search(card_pattern, content, re.DOTALL)
    
    if card_match:
        # Clean title (unescape HTML characters or remove spans)
        title = card_match.group(1)
        # Strip any internal tags
        title = re.sub(r'<[^>]*?>', '', title).strip()
    else:
        title = story_slug.replace("-", " ").title()
        
    stories_map[story_slug] = {
        "slug": story_slug,
        "hsk_level": hsk_level,
        "title": title,
        "first_chapter_slug": first_chapter_slug
    }

stories_list = list(stories_map.values())
print(f"Extracted {len(stories_list)} stories from HTML!")

# Let's print the first 10 for validation
for s in stories_list[:10]:
    print(f"  Level {s['hsk_level']}: {s['title']} ({s['slug']})")

with open("scratch/library_stories.json", "w", encoding="utf-8") as out:
    json.dump(stories_list, out, ensure_ascii=False, indent=2)
