# scratch/generate_mock_tests.py
import json
import os
import random
import glob

print("Generating HSK mock test questions from stories (optimized)...")

hsk_words_path = "db/hsk_words.json"
mock_tests_path = "db/mock_tests.json"

if not os.path.exists(hsk_words_path):
    print(f"Error: {hsk_words_path} does not exist.")
    exit(1)

with open(hsk_words_path, "r", encoding="utf-8") as f:
    hsk_words = json.load(f)

# Group HSK words by level
words_by_level = {i: [] for i in range(1, 10)}
for word, level in hsk_words.items():
    if 1 <= level <= 9:
        words_by_level[level].append(word)

questions_by_level = {i: [] for i in range(1, 10)}

# Find all chapter files recursively
story_files = glob.glob("db/stories/hsk-*/**/*.json", recursive=True)
print(f"Found {len(story_files)} chapter files to process.")

for file_path in story_files:
    # Get level from path (e.g., db/stories/hsk-1/... -> level 1)
    parts = os.path.normpath(file_path).split(os.sep)
    level_dir = next((p for p in parts if p.startswith("hsk-")), None)
    if not level_dir:
        continue
    try:
        story_level = int(level_dir.split("-")[1])
    except:
        continue
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            chapter = json.load(f)
            
        trans_vi = chapter.get("translation_data_vi", {})
        if not trans_vi:
            continue
            
        for cn_sent, vi_trans in trans_vi.items():
            cn_sent = cn_sent.strip()
            vi_trans = vi_trans.strip()
            if not cn_sent or not vi_trans:
                continue
            if len(cn_sent) < 12 or len(cn_sent) > 45:
                continue # Skip very short or very long sentences
                
            # Find candidate HSK words in the sentence by looking up substrings
            candidates = []
            
            # Check substrings of length 2 to 4
            for length in range(2, 5):
                for start in range(len(cn_sent) - length + 1):
                    sub = cn_sent[start:start+length]
                    if sub in hsk_words:
                        word_level = hsk_words[sub]
                        candidates.append((sub, word_level))
                        
            # Fallback to single characters if no multi-character words found
            if not candidates:
                for start in range(len(cn_sent)):
                    sub = cn_sent[start]
                    if sub in hsk_words:
                        word_level = hsk_words[sub]
                        candidates.append((sub, word_level))
                        
            if not candidates:
                continue
                
            # Choose a candidate word
            # Prioritize words matching the story level, otherwise any level
            story_level_candidates = [c for c in candidates if c[1] == story_level]
            target_word, target_level = random.choice(story_level_candidates) if story_level_candidates else random.choice(candidates)
            
            # Make sure we have enough distractors of the same HSK level
            distractors_pool = words_by_level[target_level]
            if len(distractors_pool) < 5:
                # fallback to adjacent levels if pool is too small
                distractors_pool = words_by_level.get(target_level - 1, []) + words_by_level.get(target_level + 1, [])
                
            if len(distractors_pool) < 4:
                continue
                
            # Get 3 distractors
            distractors = []
            attempts = 0
            while len(distractors) < 3 and attempts < 100:
                d = random.choice(distractors_pool)
                if d != target_word and d not in distractors and d not in cn_sent:
                    distractors.append(d)
                attempts += 1
                
            if len(distractors) < 3:
                continue
                
            # Create the blanked sentence
            blank_sentence = cn_sent.replace(target_word, " ___ ", 1)
            
            # Put options together and shuffle
            options = [target_word] + distractors
            random.shuffle(options)
            
            question = {
                "sentence_cn": cn_sent,
                "sentence_blank": blank_sentence,
                "translation_vi": vi_trans,
                "word": target_word,
                "level": target_level,
                "options": options,
                "story_title": chapter.get("title_en", "Reading Practice")
            }
            
            questions_by_level[target_level].append(question)
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Output counts and save
total_q = 0
for lvl, qs in questions_by_level.items():
    # Shuffle and limit to 50 questions per level
    random.shuffle(qs)
    questions_by_level[lvl] = qs[:50]
    print(f"Level {lvl}: generated {len(questions_by_level[lvl])} questions.")
    total_q += len(questions_by_level[lvl])

with open(mock_tests_path, "w", encoding="utf-8") as f:
    json.dump(questions_by_level, f, ensure_ascii=False, indent=2)

print(f"Successfully generated {total_q} questions and saved to {mock_tests_path} (size: {os.path.getsize(mock_tests_path)} bytes)")
