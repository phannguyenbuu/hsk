# scratch/extract_all_levels.py
import urllib.request
import re
import json
import os

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def extract_stories_from_url(url, level):
    print(f"Fetching story list for HSK {level} from {url}...")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            content = res.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch level {level}: {e}")
        return []
        
    pattern = r'href="/stories/hsk-' + str(level) + r'/([a-z0-9\-]+)/([a-z0-9\-]+)"'
    matches = re.finditer(pattern, content)
    
    stories_map = {}
    for m in matches:
        story_slug = m.group(1)
        first_chapter_slug = m.group(2)
        
        card_pattern = r'data-testid="story-library-card-' + re.escape(story_slug) + r'".*?card-title".*?>(.*?)</span>'
        card_match = re.search(card_pattern, content, re.DOTALL)
        
        if card_match:
            title = card_match.group(1)
            title = re.sub(r'<[^>]*?>', '', title).strip()
        else:
            title = story_slug.replace("-", " ").title()
            
        stories_map[story_slug] = {
            "slug": story_slug,
            "hsk_level": level,
            "title": title,
            "first_chapter_slug": first_chapter_slug
        }
        
    extracted = list(stories_map.values())
    print(f"Found {len(extracted)} stories for HSK {level}!")
    return extracted

def main():
    # Load HSK 1 stories from existing file or fetch it
    hsk1_stories = []
    if os.path.exists("scratch/library_stories.json"):
        with open("scratch/library_stories.json", "r", encoding="utf-8") as f:
            hsk1_stories = json.load(f)
            # Filter just HSK 1 to be safe
            hsk1_stories = [s for s in hsk1_stories if s["hsk_level"] == 1]
    
    if not hsk1_stories:
        hsk1_stories = extract_stories_from_url("https://hskstory.com/", 1)
        
    # Extract HSK 2 and HSK 3 stories
    hsk2_stories = extract_stories_from_url("https://hskstory.com/stories/hsk-2", 2)
    hsk3_stories = extract_stories_from_url("https://hskstory.com/stories/hsk-3", 3)
    
    all_stories = hsk1_stories + hsk2_stories + hsk3_stories
    print(f"\nTotal extracted stories across HSK 1, 2, 3: {len(all_stories)}")
    
    with open("scratch/all_library_stories.json", "w", encoding="utf-8") as out:
        json.dump(all_stories, out, ensure_ascii=False, indent=2)
        
    print("Saved unified library list to scratch/all_library_stories.json")

if __name__ == "__main__":
    main()
