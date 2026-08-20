# scratch/crawl_explore.py
import os
import sys
import json
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

# Authentication Token
SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMTciLCJleHAiOjE3ODczOTcyMTUsInZlciI6MX0.UWlX7SDoK2QxmE-WHif5g9W8J1JNO5xquYCtjmSwYYY"

# Output Paths
SLANG_OUTPUT_PATH = "db/slang.json"
CHAR_OUTPUT_PATH = "db/characters.json"
GLYPHS_DIR = "db/etymology/glyphs"
os.makedirs(GLYPHS_DIR, exist_ok=True)

# Static backup lists
SLANG_LIST = [
    "qiyueshou", "haiwang", "lvcha", "tiangou", "bailianghua", "pua", "xiaorou", "baifumei", "qingxu-jiazhi", 
    "bailan", "tangping", "neijuan", "jiwa", "fanersai", "yyds", "chigua", "jiujiuliu", "foxi", "dagong", 
    "jiucai", "zhenxiang", "dazi", "pofang", "saibo-duizhang", "fafeng-wenxue", "neihao"
]

CHAR_LIST = ["安", "婚", "忍", "教", "囚", "笑", "想", "好", "爱"]

# Google Translate free endpoint helper
def translate(text, sl="en", tl="vi"):
    if not text or not text.strip(): 
        return ""
    # Avoid translating single Chinese characters or pinyin if they are passed
    if len(text.strip()) <= 4 and all(ord(c) < 128 for c in text):
        # Check if it looks like a single pinyin word (e.g. ān)
        # We can just return it
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=" + sl + "&tl=" + tl + "&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        translated = "".join([sentence[0] for sentence in data[0] if sentence[0]])
        return translated
    except Exception as e:
        print(f"  [Translate Warning] Failed to translate: {e}")
        return text

# Fetch helper with Cookie auth
def fetch_page(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    req.add_header("Cookie", f"hskstory.auth.token={SESSION_TOKEN}")
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"  [Fetch Error] URL: {url} -> {e}")
        return None

# Download SVG helper
def download_svg(url_path, filename):
    local_path = os.path.join(GLYPHS_DIR, filename)
    if os.path.exists(local_path):
        return  # Skip if already exists
        
    full_url = f"https://hskstory.com{url_path}"
    req = urllib.request.Request(full_url)
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req) as response:
            svg_data = response.read()
            with open(local_path, "wb") as f:
                f.write(svg_data)
            print(f"    [SVG Saved] {filename}")
    except Exception as e:
        print(f"    [SVG Download Error] {full_url} -> {e}")

# ==========================================
# CRAWL SLANG LIST & DETAILS
# ==========================================
def crawl_slang():
    print("\n--- Starting Slang Scraper ---")
    slang_data = []
    
    for slug in SLANG_LIST:
        print(f"Scraping Slang: {slug}...")
        url = f"https://hskstory.com/slang/{slug}"
        html = fetch_page(url)
        if not html:
            continue
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Parse LD+JSON schema for metadata
        schema_data = {}
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                js = json.loads(script.string)
                if js.get("@type") == "DefinedTerm":
                    schema_data = js
                    break
            except:
                pass
                
        # DOM Header elements
        header = soup.find("header", class_="text-center")
        if not header:
            # Fallback
            header = soup
            
        hanzi_elem = header.find(class_="font-zh")
        hanzi = hanzi_elem.text.strip() if hanzi_elem else schema_data.get("name", slug)
        
        pinyin_elem = header.find(class_="text-amber-800")
        pinyin = pinyin_elem.text.strip() if pinyin_elem else ""
        
        literal_elem = header.find(class_="text-muted-foreground")
        literal = literal_elem.text.strip().replace('“', '').replace('”', '') if literal_elem else ""
        vi_literal = translate(literal)
        
        # Badges/Metadata
        badges = []
        badge_spans = header.find_all(class_=lambda x: x and "border" in x and "text-xs" in x)
        for b in badge_spans:
            badges.append(b.text.strip().lower())
            
        # Textbook & Internet definition (from DOM p-5 classes)
        textbook_en = ""
        internet_en = ""
        for div in soup.find_all(class_="p-5"):
            text_xs = div.find(class_="text-xs")
            if text_xs:
                label = text_xs.text.strip().lower()
                desc_p = div.find("p")
                desc = desc_p.text.strip() if desc_p else ""
                if "textbook" in label:
                    textbook_en = desc
                elif "internet" in label:
                    internet_en = desc
                    
        vi_textbook = translate(textbook_en)
        vi_internet = translate(internet_en)
        
        # Character breakdown
        breakdown = []
        cards = soup.find_all(class_=lambda x: x and "px-5" in x and "py-4" in x)
        for card in cards:
            zh = card.find(class_="font-zh")
            py = card.find(class_="text-amber-800")
            m_div = card.find(class_="text-muted-foreground")
            if zh and py and m_div:
                en_m = m_div.text.strip()
                breakdown.append({
                    "char": zh.text.strip(),
                    "pinyin": py.text.strip(),
                    "en_meaning": en_m,
                    "vi_meaning": translate(en_m)
                })
                
        # Cultural Context
        context_en = ""
        for sec in soup.find_all("section"):
            h2 = sec.find("h2")
            if h2 and "cultural context" in h2.text.strip().lower():
                paragraphs = sec.find_all("p")
                context_en = "\n\n".join([p.text.strip() for p in paragraphs])
        vi_context = translate(context_en)
        
        # Examples
        examples = []
        example_divs = soup.find_all(class_=lambda x: x and "p-5" in x and "mb-3" in x)
        for div in example_divs:
            badge_span = div.find(class_="bg-primary")
            badge = badge_span.text.strip() if badge_span else "Ví dụ"
            vi_badge = "Tự giễu" if "self-deprecating" in badge.lower() else ("Chọc ghẹo" if "teasing" in badge.lower() else "Phê phán")
            
            desc_elem = div.find(class_="text-xs")
            desc_en = desc_elem.text.strip() if desc_elem else ""
            vi_desc = translate(desc_en)
            
            zh_p = div.find(class_="font-zh")
            zh_text = zh_p.text.strip() if zh_p else ""
            
            p_tags = div.find_all("p")
            en_meaning = p_tags[-1].text.strip() if p_tags else ""
            vi_meaning = translate(en_meaning.replace('"', '').replace('“', '').replace('”', ''))
            
            examples.append({
                "badge": vi_badge,
                "desc_en": desc_en,
                "desc_vi": vi_desc,
                "zh": zh_text,
                "en": en_meaning,
                "vi": vi_meaning
            })
            
        # Append entry
        slang_data.append({
            "slug": slug,
            "hanzi": hanzi,
            "pinyin": pinyin,
            "literal_en": literal,
            "literal_vi": vi_literal,
            "badges": badges,
            "textbook_en": textbook_en,
            "textbook_vi": vi_textbook,
            "internet_en": internet_en,
            "internet_vi": vi_internet,
            "breakdown": breakdown,
            "context_en": context_en,
            "context_vi": vi_context,
            "examples": examples
        })
        print(f"  [Done] {hanzi} ({pinyin})")
        time.sleep(0.5)
        
    with open(SLANG_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(slang_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(slang_data)} slang items to {SLANG_OUTPUT_PATH}")

# ==========================================
# CRAWL CHARACTER DETAILS & SVGs
# ==========================================
def crawl_characters():
    print("\n--- Starting Character Etymology Scraper ---")
    char_data = []
    
    for char in CHAR_LIST:
        print(f"Scraping Character: {char}...")
        quoted_char = urllib.parse.quote(char)
        url = f"https://hskstory.com/characters/{quoted_char}"
        html = fetch_page(url)
        if not html:
            continue
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Parse LD+JSON schema for metadata
        schema_data = {}
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                js = json.loads(script.string)
                if js.get("@type") == "LearningResource":
                    schema_data = js
                    break
            except:
                pass
                
        # Parse schema name: "安 (ān) — peace · safe · calm"
        name_str = schema_data.get("name", "")
        pinyin = ""
        meaning_en = ""
        
        if " — " in name_str:
            parts = name_str.split(" — ")
            meaning_en = parts[1]
            # Get pinyin from brackets
            bracket_part = parts[0]
            if "(" in bracket_part and ")" in bracket_part:
                pinyin = bracket_part[bracket_part.find("(")+1 : bracket_part.find(")")]
                
        vi_meaning = translate(meaning_en)
        hsk_level = schema_data.get("educationalLevel", "HSK 1")
        
        # Etymology story & type
        etymology_type = "etymology"
        story_en = schema_data.get("description", "")
        
        # Find etymology type badge in DOM (folk etymology, dark history etc)
        # Typically the sibling or inside the section snippet
        for sec in soup.find_all("section"):
            h2 = sec.find("h2")
            if not h2:  # Titleless sections
                text_content = sec.text.strip().lower()
                if "etymology" in text_content or "history" in text_content or "pictograph" in text_content:
                    # Look for badge spans
                    badges = sec.find_all(class_=lambda x: x and "badge" in x or "bg-primary" in x)
                    # Get etymology category
                    p_text = sec.find("p")
                    if p_text:
                        story_en = p_text.text.strip()
                    # The first child is usually the badge text
                    badge_elem = sec.find(class_=lambda x: x and ("badge" in x or "uppercase" in x))
                    if badge_elem:
                        etymology_type = badge_elem.text.strip().lower()
                        
        vi_story = translate(story_en)
        
        # SVG Glyphs downloads
        glyphs = {}
        for img in soup.find_all("img"):
            src = img.get("src")
            alt = img.get("alt", "")
            if src and "etymology/glyphs" in src:
                # Clean URL param (?dpl=...)
                clean_src = src.split("?")[0]
                # SVG filename on disk
                filename = urllib.parse.unquote(clean_src.split("/")[-1])
                script_type = "modern"
                if "oracle" in filename.lower():
                    script_type = "oracle"
                elif "bronze" in filename.lower():
                    script_type = "bronze"
                elif "seal" in filename.lower():
                    script_type = "seal"
                elif "liushutong" in filename.lower():
                    script_type = "liushutong"
                    
                glyphs[script_type] = filename
                # Download the SVG locally!
                download_svg(clean_src, filename)
                
        # Components
        components = []
        for sec in soup.find_all("section"):
            h2 = sec.find("h2")
            if h2 and "components" in h2.text.strip().lower():
                # Loop through components blocks (usually flex items with character + details)
                # Structure: px-5 py-4 or div with text center
                comp_blocks = sec.find_all(class_=lambda x: x and "px-5" in x or "text-center" in x)
                # Clean nested cards
                for comp in comp_blocks:
                    comp_zh = comp.find(class_="font-zh")
                    # meaning is under text-muted-foreground
                    comp_m = comp.find(class_="text-muted-foreground")
                    if comp_zh and comp_m:
                        en_c = comp_m.text.strip()
                        components.append({
                            "char": comp_zh.text.strip(),
                            "en": en_c,
                            "vi": translate(en_c)
                        })
                break
                
        # Related characters
        related = []
        for sec in soup.find_all("section"):
            h2 = sec.find("h2")
            if h2 and "related characters" in h2.text.strip().lower():
                # Just characters text
                # Find all single Chinese characters in text
                related_chars = sec.text.replace("Related Characters", "").strip()
                related = [c for c in related_chars if 0x4e00 <= ord(c) <= 0x9fff]
                break
                
        char_data.append({
            "char": char,
            "pinyin": pinyin,
            "meaning_en": meaning_en,
            "meaning_vi": vi_meaning,
            "hsk_level": hsk_level,
            "etymology_type": etymology_type,
            "story_en": story_en,
            "story_vi": vi_story,
            "glyphs": glyphs,
            "components": components,
            "related": related
        })
        print(f"  [Done] {char} ({pinyin})")
        time.sleep(0.5)
        
    with open(CHAR_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(char_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(char_data)} characters to {CHAR_OUTPUT_PATH}")

if __name__ == "__main__":
    crawl_slang()
    crawl_characters()
    print("\n--- Explore Scraper Completed successfully ---")
