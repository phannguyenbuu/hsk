# scratch/crawl_and_translate.py
import os
import re
import json
import time
import urllib.request
import urllib.parse

# Ensure output directories exist
os.makedirs("db/stories", exist_ok=True)
os.makedirs("scratch", exist_ok=True)

# Google Translate free endpoint helper
def translate(text, sl="en", tl="vi"):
    if not text.strip():
        return ""
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=" + sl + "&tl=" + tl + "&dt=t&q=" + urllib.parse.quote(text)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))
            translation = "".join([item[0] for item in data[0] if item[0]])
            return translation
    except Exception as e:
        safe_text = text[:20].encode('ascii', 'ignore').decode('ascii')
        print(f"Translation error for '{safe_text}': {e}")
        time.sleep(1)
        return text

# Load global simplified dictionary for HSKStory
print("Loading master dictionary (zh-dict-simplified.json)...")
try:
    with open("zh-dict-simplified.json", "r", encoding="utf-8") as f:
        master_dict = json.load(f)
    print(f"Dictionary loaded with {len(master_dict)} entries.")
except Exception as e:
    print(f"Could not load master dictionary: {e}")
    master_dict = {}

# Load local Vietnamese dictionary
vi_dict_path = "db/vietnamese_dict.json"
if os.path.exists(vi_dict_path):
    with open(vi_dict_path, "r", encoding="utf-8") as f:
        vi_dict = json.load(f)
    print(f"Loaded existing local Vietnamese dictionary with {len(vi_dict)} entries.")
else:
    vi_dict = {}

def get_vietnamese_definition(word):
    if word in vi_dict:
        return vi_dict[word]
        
    if word not in master_dict:
        return None
        
    eng_definitions = master_dict[word]
    if isinstance(eng_definitions, list):
        eng_text = "; ".join(eng_definitions)
    else:
        eng_text = str(eng_definitions)
        
    vi_text = translate(eng_text, sl="en", tl="vi")
    vi_dict[word] = vi_text
    
    if len(vi_dict) % 20 == 0:
        save_vi_dict()
        
    return vi_text

def save_vi_dict():
    with open(vi_dict_path, "w", encoding="utf-8") as f:
        json.dump(vi_dict, f, ensure_ascii=False, indent=2)

def crawl_story(level, story_slug):
    print(f"  [Network] Fetching landing page for {story_slug}...")
    story_dir = f"db/stories/hsk-{level}/{story_slug}"
    
    # 1. Fetch story landing page to extract chapter slugs
    url = f"https://hskstory.com/stories/hsk-{level}/{story_slug}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            html = res.read().decode('utf-8')
    except Exception as e:
        print(f"  [ERROR] Failed to load story landing page: {e}")
        return None
        
    chapter_pattern = r'href="/stories/hsk-' + str(level) + r'/' + re.escape(story_slug) + r'/([a-z0-9\-]+)"'
    chapter_slugs = sorted(list(set(re.findall(chapter_pattern, html))))
    
    if not chapter_slugs:
        matches = re.findall(r'chapter-\d+-[a-z0-9\-]+', html)
        chapter_slugs = sorted(list(set(matches)))
        
    if not chapter_slugs:
        print(f"  [WARNING] No chapters found for {story_slug}")
        return None
        
    print(f"\n--- Crawling Story: Level {level} - {story_slug} ({len(chapter_slugs)} chapters) ---")
    os.makedirs(story_dir, exist_ok=True)
    
    chapters_metadata = []
    
    for c_slug in chapter_slugs:
        # Check if already crawled
        chapter_file_path = os.path.join(story_dir, f"{c_slug}.json")
        if os.path.exists(chapter_file_path):
            print(f"  Chapter {c_slug} already exists. Skipping crawl...")
            try:
                with open(chapter_file_path, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                chapters_metadata.append({
                    "chapter_number": c_data.get("chapter_number", 1),
                    "chapter_slug": c_slug,
                    "title_en": c_data.get("title_en", c_slug.replace("-", " ").title())
                })
            except:
                pass
            continue
            
        print(f"Processing Chapter: {c_slug}...")
        api_url = f"https://hskstory.com/api/stories/{level}/{story_slug}/chapters/{c_slug}?script=simplified&reader_media_contract=1"
        api_req = urllib.request.Request(api_url, headers=headers)
        
        try:
            with urllib.request.urlopen(api_req, timeout=15) as api_res:
                api_data = json.loads(api_res.read().decode('utf-8'))
        except Exception as e:
            print(f"  [ERROR] Failed to fetch API details for chapter {c_slug}: {e}")
            continue
            
        content_html = api_data.get("content_html")
        pinyin_data_str = api_data.get("pinyin_data")
        translation_data_str = api_data.get("translation_data")
        
        audio_version = api_data.get("audio_asset_version", 1)
        timestamp_version = api_data.get("timestamp_asset_version", 1)
        chapter_number = api_data.get("chapter_number", 1)
        
        try:
            pinyin_data = json.loads(pinyin_data_str) if isinstance(pinyin_data_str, str) else pinyin_data_str
        except:
            pinyin_data = []
            
        try:
            translation_data = json.loads(translation_data_str) if isinstance(translation_data_str, str) else translation_data_str
        except:
            translation_data = {}
            
        chapter_num_padded = f"{chapter_number:02d}"
        timestamps_url = f"https://audio.hskstory.com/hsk{level}-{story_slug}/timestamps/_versions/v{timestamp_version}/luna/chapter-{chapter_num_padded}.json"
        
        ts_req = urllib.request.Request(timestamps_url, headers=headers)
        timestamps = []
        try:
            with urllib.request.urlopen(ts_req, timeout=15) as ts_res:
                timestamps = json.loads(ts_res.read().decode('utf-8'))
            print(f"  [SUCCESS] Downloaded timestamps for chapter {chapter_number}")
        except Exception as e:
            print(f"  [WARNING] Could not download timestamps from {timestamps_url}: {e}")
            
        audio_url = f"https://audio.hskstory.com/hsk{level}-{story_slug}/audio/_versions/v{audio_version}/luna/chapter-{chapter_num_padded}.mp3"
        
        print("  Translating sentences to Vietnamese...")
        vi_sentences = {}
        for cn_sentence, eng_translation in translation_data.items():
            vi_trans = translate(eng_translation, sl="en", tl="vi")
            vi_sentences[cn_sentence] = vi_trans
            time.sleep(0.05)
            
        print("  Translating unique vocabularies...")
        vocab_count = 0
        if isinstance(pinyin_data, list):
            for paragraph in pinyin_data:
                if isinstance(paragraph, list):
                    for word_obj in paragraph:
                        word = word_obj.get("w")
                        pinyin = word_obj.get("p")
                        if word and pinyin:
                            vi_def = get_vietnamese_definition(word)
                            if vi_def:
                                vocab_count += 1
                                
        print(f"  Translated/Cached {vocab_count} words.")
        
        title_en = c_slug.replace(f"chapter-{chapter_number}-", "").replace("-", " ").title()
        chapter_db_obj = {
            "chapter_number": chapter_number,
            "chapter_slug": c_slug,
            "title_en": title_en,
            "content_html": content_html,
            "pinyin_data": pinyin_data,
            "translation_data_vi": vi_sentences,
            "timestamps": timestamps,
            "audio_url": audio_url
        }
        
        with open(chapter_file_path, "w", encoding="utf-8") as f:
            json.dump(chapter_db_obj, f, ensure_ascii=False, indent=2)
            
        chapters_metadata.append({
            "chapter_number": chapter_number,
            "chapter_slug": c_slug,
            "title_en": title_en
        })
        print(f"  Saved chapter file: {chapter_file_path}")
        time.sleep(0.5)
        
    save_vi_dict()
    return sorted(chapters_metadata, key=lambda x: x["chapter_number"])

def main():
    with open("scratch/all_library_stories.json", "r", encoding="utf-8") as f:
        stories = json.load(f)
        
    library_data = []
    library_index_path = "db/library.json"
    if os.path.exists(library_index_path):
        try:
            with open(library_index_path, "r", encoding="utf-8") as f:
                library_data = json.load(f)
        except:
            pass
            
    print(f"Total stories in library list: {len(stories)}")
    
    for story in stories:
        slug = story["slug"]
        level = story["hsk_level"]
        title = story["title"]
        
        print(f"\n[START] Story {slug}...")
        chapters = crawl_story(level, slug)
        
        if chapters:
            story_metadata = {
                "id": story.get("id"),
                "slug": slug,
                "hsk_level": level,
                "title": title,
                "chapters": chapters,
                "chapter_count": len(chapters)
            }
            
            library_data = [s for s in library_data if s["slug"] != slug]
            library_data.append(story_metadata)
            
            with open(library_index_path, "w", encoding="utf-8") as f:
                json.dump(library_data, f, ensure_ascii=False, indent=2)
                
            print(f"[LIBRARY UPDATE] Saved {slug} to db/library.json")
            
        time.sleep(1.0)
            
    print("\nAll HSK 1 stories processed successfully!")

if __name__ == "__main__":
    main()
