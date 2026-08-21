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

# Name translation map (Pinyin -> Sino-Vietnamese names)
NAME_MAP = {
    "Zheng Yu": "Trịnh Vũ", "ZhengYu": "Trịnh Vũ",
    "Liang Dawei": "Lương Đại Vĩ", "Liang Da-wei": "Lương Đại Vĩ", "Liang Da Wei": "Lương Đại Vĩ",
    "Ye Mei": "Diệp Mỹ", "YeMei": "Diệp Mỹ",
    "Xiao Yun": "Tiểu Vân", "XiaoYun": "Tiểu Vân",
    "Xiao Dong": "Tiểu Đông", "XiaoDong": "Tiểu Đông",
    "Wang Jianguo": "Vương Kiến Quốc", "WangJianguo": "Vương Kiến Quốc", "Wang Jian Guo": "Vương Kiến Quốc",
    "Auntie Li": "Dì Lý", "Aunt Li": "Dì Lý", "Auntie Cheng": "Dì Trình", "Aunt Cheng": "Dì Trình",
    "Old Chen": "Lão Trần", "Old Guo": "Lão Quách", "Old Jiang": "Lão Khương", "Old Sun": "Lão Tôn", "Old Zhao": "Lão Triệu",
    "Master Chen": "Sư phụ Trần", "Master Cheng": "Sư phụ Trình", "Master Chu": "Sư phụ Chu", "Master Qin": "Sư phụ Tần", "Master Wen": "Sư phụ Ôn", "Master Zhao": "Sư phụ Triệu",
    "Coach Ma": "Huấn luyện viên Mã",
    "Afeng": "A Phong", "Ah Zhi": "A Chí", "Ahao": "A Hạo", "Aji": "A Cát", "Alimu": "A Lực Mộc", "Antongding": "An Đông Đinh", "Aqiao": "A Kiều", "Aren": "A Nhân",
    "Bailu": "Bạch Lộ", "Beichen": "Bắc Thần", "Beijing": "Bắc Kinh", "Bowen": "Bác Văn",
    "Cao Minh": "Tào Minh", "Cao Xung": "Tào Xung", "Cen Xue": "Sầm Tuyết",
    "Chen Mingyuan": "Trần Minh Viễn", "Chen Ming": "Trần Minh", "Chen Shimei": "Trần Thế Mỹ", "Chen Xiaman": "Trần Hạ Mạn", "Chen Xiaoman": "Trần Tiểu Mạn", "Chen Xing": "Trần Tinh", "Chen Xue": "Trần Tuyết", "Chen Yan": "Trần Yến", "Chen Yating": "Trần Nhã Đình", "Chen Yuqing": "Trần Vũ Thanh", "Chen Yutong": "Trần Vũ Đồng",
    "Cheng Feng": "Trình Phong", "Cheng Shan": "Trình Sơn", "Cheng Shiyuan": "Trình Sĩ Nguyên", "Cheng Siyuan": "Trình Tư Nguyên", "Cheng Xiaole": "Trình Tiểu Lạc", "Cheng Yang": "Trình Dương", "Cheng Yuan": "Trình Viên", "Cheng Zhiyuan": "Trình Chí Viễn",
    "Chu Bonian": "Chu Bá Niên", "Chu Houren": "Chu Hậu Nhân", "Chu Li": "Chu Lực", "Chu Mingyuan": "Chu Minh Viễn", "Chu Molin": "Chu Mặc Lâm", "Chu Mu": "Chu Mộc", "Chu Shian": "Chu Thế An", "Chu Siyuan": "Chu Tư Nguyên",
    "Ding Dongming": "Đinh Đông Minh", "Ding Xiaoman": "Đinh Tiểu Mạn", "Ding Xiaoyu": "Đinh Tiểu Vũ", "Du Yue": "Đỗ Nguyệt",
    "Fan Yuanhang": "Phạm Viễn Hàng", "Fang Dali": "Phương Đại Lực", "Fang Guoqiang": "Phương Quốc Cường", "Fang Min": "Phương Mẫn", "Fang Mingyuan": "Phương Minh Viễn", "Fang Qiang": "Phương Cường", "Fang Qingchuan": "Phương Thanh Xuyên", "Fang Tiantian": "Phương Điền Điền", "Fang Xiaoli": "Phương Tiểu Lệ", "Fang Xiaoyun": "Phương Tiểu Vân", "Fang Xuemei": "Phương Tuyết Mỹ", "Fang Zhiyuan": "Phương Chí Viễn", "Fang Ziming": "Phương Tử Minh", "Fang Zixuan": "Phương Tử Tuyên",
    "Feng Dawen": "Phùng Đại Văn", "Feng Yuanmei": "Phùng Viên Mỹ", "Feng Yuanqiao": "Phùng Viên Kiều", "Feng Yuanzhang": "Phùng Viên Chương",
    "Ga Nam": "Kha Nam", "Ga Qingshui": "Cát Thanh Thủy", "Ga Thanh Phong": "Cát Thanh Phong", "Gao Le": "Cao Lạc", "Gao Tian": "Cao Thiên", "Gao Yue": "Cao Nguyệt",
    "Gu Chenzhou": "Cố Thần Chu", "Gu Defa": "Cố Đắc Phát", "Gu Shouyi": "Cố Thủ Nghĩa", "Gu Siyuan": "Cố Tư Nguyên", "Gu Wanqing": "Cố Vãn Thanh", "Gu Xiaoyu": "Cố Tiểu Vũ", "Gu Yunqing": "Cố Vân Thanh", "Gu Zhiyuan": "Cố Chí Viễn",
    "Han Lei": "Hàn Lôi", "He Siqi": "Hà Tư Kỳ", "Jiang Mengxue": "Khương Mộng Tuyết", "Jiang Tianle": "Khương Thiên Lạc",
    "Ke Jin": "Kha Kim", "Ke Muning": "Kha Mộ Ninh", "Ke Zhenyang": "Kha Chấn Dương",
    "Li Baochen": "Lý Bảo Thần", "Li Daming": "Lý Đại Minh", "Li Gangwu": "Lý Cương Vũ", "Li Hong": "Lý Hồng", "Li Ming": "Lý Minh", "Li Wei": "Lý Vĩ", "Li Wen": "Lý Văn", "Li Wenbo": "Lý Văn Bác", "Li Xue": "Lý Tuyết",
    "Lin Ci": "Lâm Từ", "Lin Feiyue": "Lâm Phi Duyệt", "Lin Gangwu": "Lâm Cương Vũ", "Lin Haotian": "Lâm Hào Thiên", "Lin Hui": "Lâm Huy", "Lin Jianmin": "Lâm Kiến Dân", "Lin Jiashu": "Lâm Gia Thư", "Lin Jiayin": "Lâm Gia Ân", "Lin Meihua": "Lâm Mỹ Hoa", "Lin Meixin": "Lâm Mỹ Hân", "Lin Qiuning": "Lâm Thu Ninh", "Lin Ruobing": "Lâm Nhược Băng", "Lin Ruoyun": "Lâm Nhược Vân", "Lin Shuang": "Lâm Song", "Lin Shuqin": "Lâm Thư Cầm", "Lin Siyuan": "Lâm Tư Nguyên", "Lin Xiaman": "Lâm Hạ Mạn", "Lin Xiaobei": "Lâm Tiểu Bắc", "Lin Xiaochuan": "Lâm Tiểu Xuyên", "Lin Xiaoman": "Lâm Tiểu Mạn", "Lin Xiaomei": "Lâm Tiểu Mỹ", "Lin Xiaoqiang": "Lâm Tiểu Cường", "Lin Xiaoshu": "Lâm Tiểu Thư", "Lin Xiaoxue": "Lâm Tiểu Tuyết", "Lin Xiaoyu": "Lâm Tiểu Vũ", "Lin Xiaoyue": "Lâm Tiểu Nguyệt", "Lin Xiufang": "Lâm Tú Phương", "Lin Xubai": "Lâm Húc Bạch", "Lin Xue": "Lâm Tuyết", "Lin Yang": "Lâm Dương", "Lin Yao": "Lâm Diệu", "Lin Yating": "Lâm Nhã Đình", "Lin Yuan": "Lâm Viên", "Lin Yuanhang": "Lâm Viễn Hàng", "Lin Yue": "Lâm Nguyệt", "Lin Yuqing": "Lâm Vũ Thanh", "Lin Zhiyuan": "Lâm Chí Viễn",
    "Liu Meihua": "Lưu Mỹ Hoa", "Liu Xiulan": "Lưu Tú Lan", "Lu Wen": "Lục Văn", "Lu Wenjing": "Lục Văn Tĩnh", "Lu Yuwei": "Lục Vũ Vi",
    "Ma Deshui": "Mã Đắc Thủy", "Ma Li": "Mã Lệ", "Ma Wentao": "Mã Văn Đào", "Ma Xiangyang": "Mã Hướng Dương", "Ma Xiaodong": "Mã Tiểu Đông", "Ma Xiaotiao": "Mã Tiểu Tiếu", "Ma Xue": "Mã Tuyết",
    "Nie Haidong": "Nhiếp Hải Đông", "Pang Zhong": "Bàng Trọng",
    "Qin Bowen": "Tần Bác Văn", "Qin Guo": "Tần Quốc", "Qin Tieshan": "Tần Thiết Sơn", "Qin Xuewei": "Tần Tuyết Vĩ", "Qin Yunshen": "Tần Vân Thâm", "Qin Yutong": "Tần Vũ Đồng", "Qin Zhiyuan": "Tần Chí Viễn",
    "Shao Yuwei": "Thiệu Vũ Vi", "Shen Guifang": "Thẩm Quế Phương", "Shen Jiashu": "Thẩm Gia Thư", "Shen Qinghua": "Thẩm Thanh Hoa", "Shen Rusong": "Thẩm Như Tùng", "Shen Tao": "Thẩm Đào",
    "Shi Qing": "Thạch Thanh", "Shi Yaqin": "Thạch Nhã Cầm", "Shi Yawen": "Thạch Nhã Văn",
    "Su Dawen": "Tô Đại Văn", "Su Jinhua": "Tô Kim Hoa", "Su Li": "Tô Lệ", "Su Man": "Tô Mạn", "Su Mengyu": "Tô Mộng Vũ", "Su Min": "Tô Mẫn", "Su Nianqiu": "Tô Niệm Thu", "Su Qing": "Tô Thanh", "Su Shi": "Tô Thức", "Su Tianming": "Tô Thiên Minh", "Su Tiantian": "Tô Điền Điền", "Su Ting": "Tô Đình", "Su Wanqing": "Tô Vãn Thanh", "Su Xiaobei": "Tô Tiểu Bắc", "Su Xiaohe": "Tô Tiểu Hà", "Su Xiaomei": "Tô Tiểu Mỹ", "Su Xiaotang": "Tô Tiểu Đường", "Su Xiaoyu": "Tô Tiểu Vũ", "Su Xue": "Tô Tuyết", "Su Yuan": "Tô Viên", "Su Yue": "Tô Nguyệt", "Su Yuqing": "Tô Vũ Thanh",
    "Tang Ming": "Đường Minh", "Wen Hao": "Ôn Hạo", "Wen Heping": "Ôn Hòa Bình", "Wu Zixuan": "Ngô Tử Tuyên", "Xie Xiaowen": "Tạ Tiểu Văn",
    "Xu Jia": "Hứa Gia", "Xu Meili": "Hứa Mỹ Lệ", "Xu Wentao": "Hứa Văn Đào", "Yao Yawen": "Diệu Nhã Văn",
    "Zhang Daming": "Trương Đại Minh", "Zhang Ming": "Trương Minh", "Zhang Weiming": "Trương Vĩ Minh", "Zhang Xiaofang": "Trương Tiểu Phương", "Zhang Xing": "Trương Tinh",
    "Zhao Chen": "Triệu Thần", "Zhao Delin": "Triệu Đắc Lâm", "Zhao Lihua": "Triệu Lệ Hoa", "Zhao Meilin": "Triệu Mỹ Lâm", "Zhao Mengfu": "Triệu Mạnh Phủ", "Zhao Mingyuan": "Triệu Minh Viễn", "Zhao Siyu": "Triệu Tư Vũ", "Zhao Siyuan": "Triệu Tư Nguyên", "Zhao Tieliang": "Triệu Thiết Lương", "Zhao Wenyuan": "Triệu Văn Viễn", "Zhao Xiaoyue": "Triệu Tiểu Nguyệt", "Zhao Xue": "Triệu Tuyết", "Zhao Yuanfan": "Triệu Viễn Phàm", "Zhao Zhiqiang": "Triệu Chí Cường", "Zhao Zilong": "Triệu Tử Long",
    "Zhou Mingyuan": "Chu Minh Viễn", "Zhou Shi": "Chu Thị", "Zhou Wen": "Chu Văn"
}

# Sort keys by length descending to match longer combinations first
SORTED_NAME_KEYS = sorted(NAME_MAP.keys(), key=len, reverse=True)
NAME_REPLACEMENTS = [(re.compile(r'\b' + re.escape(key) + r'\b', re.IGNORECASE), NAME_MAP[key]) for key in SORTED_NAME_KEYS]

def fix_names_vi(text):
    if not text:
        return text
    for pattern, rep in NAME_REPLACEMENTS:
        text = pattern.sub(rep, text)
    return text

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

# Load session token if exists
session_token = ""
token_path = "scratch/session_token.txt"
if os.path.exists(token_path):
    try:
        with open(token_path, "r", encoding="utf-8") as f:
            session_token = f.read().strip()
        print(f"Loaded session token: {session_token[:20]}...")
    except Exception as e:
        print(f"Error loading session token: {e}")

def get_headers():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    if session_token:
        headers['Cookie'] = f"hskstory.auth.token={session_token}"
    return headers

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
    headers = get_headers()
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
            vi_trans = fix_names_vi(vi_trans)
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
