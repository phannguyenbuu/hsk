// vocab.js - Vocabulary Book & HSK Dictionary Controller

// State
let isVocabDbLoaded = false;
let isVocabDbLoading = false;
let vocabHskWords = {};
let vocabVietDict = {};

// Flashcards State
let fcState = {
    isActive: false,
    words: [],
    currentIdx: 0
};

// DOM Cache
let vocabElements = {};

document.addEventListener("DOMContentLoaded", () => {
    cacheVocabDOM();
    setupVocabTabs();
    setupVocabListeners();
    setupFlashcardEvents();
    setupSearchEvents();
});

function cacheVocabDOM() {
    vocabElements = {
        // Tab Switchers
        tabSaved: document.getElementById("vocab-tab-saved"),
        tabSearch: document.getElementById("vocab-tab-search"),
        panelSaved: document.getElementById("panel-vocab-saved"),
        panelSearch: document.getElementById("panel-vocab-search"),
        
        // Saved list
        savedGrid: document.getElementById("vocab-saved-grid"),
        savedEmpty: document.getElementById("vocab-saved-empty"),
        startFlashcardBtn: document.getElementById("start-flashcard-btn"),
        
        // Flashcard DOM
        flashcardContainer: document.getElementById("flashcard-container"),
        flashcardCard: document.getElementById("flashcard-card"),
        fcZh: document.getElementById("fc-zh"),
        fcPinyin: document.getElementById("fc-pinyin"),
        fcLevel: document.getElementById("fc-level"),
        fcVi: document.getElementById("fc-vi"),
        fcFailBtn: document.getElementById("fc-fail-btn"),
        fcPassBtn: document.getElementById("fc-pass-btn"),
        fcProgressText: document.getElementById("fc-progress-text"),
        fcExitBtn: document.getElementById("fc-exit-btn"),
        
        // Search DOM
        dictSearchInput: document.getElementById("dict-search-input"),
        dictLevelSelect: document.getElementById("dict-level-select"),
        dictSpinner: document.getElementById("dict-spinner"),
        dictResultsGrid: document.getElementById("dict-results-grid"),
        dictResultsEmpty: document.getElementById("dict-results-empty")
    };
}

function setupVocabTabs() {
    if (!vocabElements.tabSaved || !vocabElements.tabSearch) return;
    
    vocabElements.tabSaved.addEventListener("click", () => {
        vocabElements.tabSaved.classList.add("active");
        vocabElements.tabSearch.classList.remove("active");
        vocabElements.panelSaved.classList.add("active");
        vocabElements.panelSearch.classList.remove("active");
        
        renderSavedVocabList();
    });
    
    vocabElements.tabSearch.addEventListener("click", () => {
        vocabElements.tabSearch.classList.add("active");
        vocabElements.tabSaved.classList.remove("active");
        vocabElements.panelSearch.classList.add("active");
        vocabElements.panelSaved.classList.remove("active");
        
        ensureVocabDbLoaded();
    });
}

function setupVocabListeners() {
    window.addEventListener("hsk-vocab-active", () => {
        renderSavedVocabList();
        ensureVocabDbLoaded();
    });
}

// Lazy load databases
async function ensureVocabDbLoaded() {
    if (isVocabDbLoaded || isVocabDbLoading) return;
    isVocabDbLoading = true;
    
    if (vocabElements.dictSpinner) {
        vocabElements.dictSpinner.style.display = "flex";
    }
    
    try {
        const [wordsRes, dictRes] = await Promise.all([
            fetch("db/hsk_words.json").then(res => res.json()),
            fetch("db/vietnamese_dict.json").then(res => res.json())
        ]);
        
        vocabHskWords = wordsRes;
        vocabVietDict = dictRes;
        isVocabDbLoaded = true;
        console.log("[Vocab] Databases loaded.");
    } catch (err) {
        console.error("[Vocab] Error loading dicts:", err);
    } finally {
        isVocabDbLoading = false;
        if (vocabElements.dictSpinner) {
            vocabElements.dictSpinner.style.display = "none";
        }
    }
}

// Parse dictionary entry helper
function parseVocabDictEntry(str) {
    if (!str) return null;
    try {
        const normalized = str.replace(/'/g, '"');
        return JSON.parse(normalized);
    } catch (e) {
        const pinyinMatch = str.match(/'p':\s*'([^']*)'/);
        const pinyin = pinyinMatch ? pinyinMatch[1] : '';
        const eMatch = str.match(/'e':\s*\[(.*?)\]/);
        let meanings = [];
        if (eMatch) {
            meanings = eMatch[1].split(',').map(m => m.trim().replace(/^'|'$/g, ''));
        }
        const hskMatch = str.match(/'h':\s*(\d+)/);
        const hsk = hskMatch ? parseInt(hskMatch[1]) : null;
        return { p: pinyin, e: meanings, h: hsk };
    }
}

// ==========================================
// SAVED VOCABULARY TAB LOGIC
// ==========================================

function renderSavedVocabList() {
    const saved = JSON.parse(localStorage.getItem("saved-vocab") || "[]");
    
    if (saved.length === 0) {
        vocabElements.savedEmpty.style.display = "block";
        vocabElements.savedGrid.style.display = "none";
        vocabElements.startFlashcardBtn.style.display = "none";
        return;
    }
    
    vocabElements.savedEmpty.style.display = "none";
    vocabElements.savedGrid.style.display = "grid";
    vocabElements.startFlashcardBtn.style.display = "block";
    
    vocabElements.savedGrid.innerHTML = "";
    saved.forEach((item, idx) => {
        const card = document.createElement("div");
        card.className = "vocab-card";
        card.innerHTML = `
            <button class="dict-close remove-vocab-btn" style="top: 8px; right: 8px; padding: 2px;" title="Xóa khỏi sổ">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"></path></svg>
            </button>
            <div class="card-zh font-zh">${item.word}</div>
            <div class="card-pinyin">${item.pinyin}</div>
            <div class="card-vi" title="${item.definition}">${item.definition}</div>
            <span class="card-level">HSK ${item.level}</span>
        `;
        
        // Remove button click
        card.querySelector(".remove-vocab-btn").addEventListener("click", (e) => {
            e.stopPropagation();
            removeSavedWord(item.word);
        });
        
        vocabElements.savedGrid.appendChild(card);
    });
}

function removeSavedWord(word) {
    let saved = JSON.parse(localStorage.getItem("saved-vocab") || "[]");
    saved = saved.filter(item => item.word !== word);
    localStorage.setItem("saved-vocab", JSON.stringify(saved));
    renderSavedVocabList();
}

// ==========================================
// FLASHCARDS STUDY ENGINE
// ==========================================

function setupFlashcardEvents() {
    vocabElements.startFlashcardBtn.addEventListener("click", startFlashcards);
    vocabElements.flashcardCard.addEventListener("click", toggleFlashcardFlip);
    vocabElements.fcFailBtn.addEventListener("click", nextFlashcard);
    vocabElements.fcPassBtn.addEventListener("click", nextFlashcard);
    vocabElements.fcExitBtn.addEventListener("click", exitFlashcards);
}

function startFlashcards() {
    const saved = JSON.parse(localStorage.getItem("saved-vocab") || "[]");
    if (saved.length === 0) return;
    
    // Shuffle cards
    fcState.words = [...saved].sort(() => Math.random() - 0.5);
    fcState.currentIdx = 0;
    fcState.isActive = true;
    
    // Toggle DOM views
    vocabElements.savedGrid.style.display = "none";
    vocabElements.savedEmpty.style.display = "none";
    vocabElements.startFlashcardBtn.style.display = "none";
    vocabElements.flashcardContainer.style.display = "flex";
    
    showFlashcard();
}

function showFlashcard() {
    const idx = fcState.currentIdx;
    if (idx >= fcState.words.length) {
        alert("Chúc mừng! Bạn đã hoàn thành đợt ôn tập từ vựng lần này.");
        exitFlashcards();
        return;
    }
    
    // Reset flip
    vocabElements.flashcardCard.classList.remove("flipped");
    
    const item = fcState.words[idx];
    
    vocabElements.fcZh.innerText = item.word;
    vocabElements.fcPinyin.innerText = item.pinyin;
    vocabElements.fcLevel.innerText = `HSK ${item.level}`;
    vocabElements.fcVi.innerText = item.definition;
    vocabElements.fcProgressText.innerText = `Tiến độ: ${idx + 1} / ${fcState.words.length}`;
}

function toggleFlashcardFlip() {
    vocabElements.flashcardCard.classList.toggle("flipped");
}

function nextFlashcard() {
    fcState.currentIdx++;
    // Add brief timeout for flip animation reset
    vocabElements.flashcardCard.classList.remove("flipped");
    setTimeout(showFlashcard, 250);
}

function exitFlashcards() {
    fcState.isActive = false;
    vocabElements.flashcardContainer.style.display = "none";
    renderSavedVocabList();
}

// ==========================================
// OFFLINE HSK DICTIONARY SEARCH
// ==========================================

function setupSearchEvents() {
    let searchTimeout = null;
    
    vocabElements.dictSearchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performDictionarySearch, 300);
    });
    
    vocabElements.dictLevelSelect.addEventListener("change", performDictionarySearch);
}

function performDictionarySearch() {
    const query = vocabElements.dictSearchInput.value.trim().toLowerCase();
    const lvlFilter = vocabElements.dictLevelSelect.value;
    
    if (!isVocabDbLoaded) {
        ensureVocabDbLoaded().then(performDictionarySearch);
        return;
    }
    
    if (!query && lvlFilter === "all") {
        vocabElements.dictResultsGrid.innerHTML = "";
        vocabElements.dictResultsEmpty.style.display = "block";
        vocabElements.dictResultsEmpty.innerText = "Nhập từ khóa tìm kiếm để bắt đầu tra từ điển.";
        return;
    }
    
    vocabElements.dictResultsEmpty.style.display = "none";
    vocabElements.dictResultsGrid.innerHTML = "";
    
    // Search logic
    let matches = [];
    
    Object.entries(vocabHskWords).forEach(([word, lvl]) => {
        // Level filter check
        if (lvlFilter !== "all" && parseInt(lvlFilter) !== lvl) return;
        
        const dictStr = vocabVietDict[word] || "";
        const parsed = parseVocabDictEntry(dictStr);
        
        const pinyin = parsed ? parsed.p.toLowerCase() : "";
        const meanings = parsed && parsed.e ? parsed.e.join(", ").toLowerCase() : "";
        
        // Match conditions: Chinese, Pinyin, or Vietnamese definition
        const isZhMatch = word.includes(query);
        const isPyMatch = pinyin.replace(/\s+/g, "").includes(query.replace(/\s+/g, ""));
        const isViMatch = meanings.includes(query);
        
        if (isZhMatch || isPyMatch || isViMatch || !query) {
            matches.push({
                word: word,
                pinyin: parsed ? parsed.p : "",
                level: lvl,
                definition: parsed && parsed.e ? parsed.e.join(", ") : "Chưa dịch"
            });
        }
    });
    
    // Cap results at 50 to avoid DOM bloating
    const limitedMatches = matches.slice(0, 50);
    
    if (limitedMatches.length === 0) {
        vocabElements.dictResultsEmpty.style.display = "block";
        vocabElements.dictResultsEmpty.innerText = "Không tìm thấy từ vựng nào khớp với từ khóa.";
        return;
    }
    
    const saved = JSON.parse(localStorage.getItem("saved-vocab") || "[]");
    
    limitedMatches.forEach(item => {
        const isStarred = saved.some(s => s.word === item.word);
        
        const card = document.createElement("div");
        card.className = "vocab-card";
        card.innerHTML = `
            <button class="dict-star-btn ${isStarred ? 'active' : ''}" style="position: absolute; top: 8px; right: 8px; margin: 0;" title="Lưu từ">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            </button>
            <div class="card-zh font-zh">${item.word}</div>
            <div class="card-pinyin">${item.pinyin}</div>
            <div class="card-vi" title="${item.definition}">${item.definition}</div>
            <span class="card-level">HSK ${item.level}</span>
        `;
        
        // Star toggle logic
        const starBtn = card.querySelector(".dict-star-btn");
        starBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            toggleSearchResultStar(starBtn, item);
        });
        
        vocabElements.dictResultsGrid.appendChild(card);
    });
}

function toggleSearchResultStar(starBtn, item) {
    let saved = JSON.parse(localStorage.getItem("saved-vocab") || "[]");
    const isSaved = saved.some(s => s.word === item.word);
    
    if (isSaved) {
        saved = saved.filter(s => s.word !== item.word);
        starBtn.classList.remove("active");
    } else {
        saved.push(item);
        starBtn.classList.add("active");
    }
    localStorage.setItem("saved-vocab", JSON.stringify(saved));
}
