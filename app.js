// app.js - HSKStory Vietnamese Interactive Reader

// Parse URL Parameters
const urlParams = new URLSearchParams(window.location.search);
const levelParam = urlParams.get("level") || "1";
const storyParam = urlParams.get("story") || "morning-at-home";
const chapterParam = urlParams.get("chapter") || "chapter-1-dad-cooks";

// Application State
let currentPage = 1;
let totalPages = 1;
const paragraphsPerPage = 7;
let paragraphTimeRanges = [];

let currentPinyinMode = localStorage.getItem("hsk-reader-pinyin") || "on"; 
let currentTheme = localStorage.getItem("hsk-reader-theme") || "light";
let toneColorsEnabled = localStorage.getItem("hsk-reader-tones") === "true";
let readerTextSize = parseFloat(localStorage.getItem("hsk-reader-size")) || 1.50; 
let showTranslations = localStorage.getItem("hsk-reader-show-trans") !== "false";

let isPlaying = false;
let updateInterval = null;
let lastHighlightedIdx = -1;

// Global Data caches
let libraryData = [];
let vietnameseDict = {};
let chapterData = null;

// Audio Object
const audio = new Audio();

// DOM Cache
const contentArea = document.getElementById("content-area");
const prevPageBtn = document.getElementById("prev-page-btn");
const nextPageBtn = document.getElementById("next-page-btn");
const pageStatus = document.getElementById("page-status");

const playToggleBtn = document.getElementById("play-toggle-btn");
const skipBackBtn = document.getElementById("skip-back-btn");
const skipForwardBtn = document.getElementById("skip-forward-btn");
const speedBadge = document.getElementById("speed-badge");

const timeDisplay = document.getElementById("time-display");
const durationDisplay = document.getElementById("duration-display");
const progressSlider = document.getElementById("progress-slider");
const progressFill = document.getElementById("progress-fill");
const progressHandle = document.getElementById("progress-handle");

const dictCard = document.getElementById("dict-card");
const dictCloseBtn = document.getElementById("dict-close-btn");
const dictWordZh = document.getElementById("dict-word-zh");
const dictWordPinyin = document.getElementById("dict-word-pinyin");
const dictLevelBadge = document.getElementById("dict-level-badge");
const dictDefinition = document.getElementById("dict-definition");
const dictExample = document.getElementById("dict-example");

const translationToggleBtn = document.getElementById("translation-toggle-btn");
const settingsBtn = document.getElementById("settings-btn");
const settingsMenu = document.getElementById("settings-menu");

// Initialize Reader
document.addEventListener("DOMContentLoaded", () => {
    loadReaderData();
});

// Load catalog, dict and chapter JSON files
async function loadReaderData() {
    try {
        // Fetch library master and Vietnamese custom dict
        const [lib, dict] = await Promise.all([
            fetch("db/library.json").then(res => res.json()),
            fetch("db/vietnamese_dict.json").then(res => res.json())
        ]);
        
        libraryData = lib;
        vietnameseDict = dict;
        
        // Find story info
        const storyMeta = libraryData.find(s => s.slug === storyParam);
        if (storyMeta) {
            document.getElementById("reader-story-title").innerText = storyMeta.title;
            document.getElementById("reader-level-badge").innerText = `HSK ${storyMeta.hsk_level}`;
            
            // Build Chapter Dropdown Selection
            renderChapterDropdown(storyMeta);
        }
        
        // Fetch specific chapter details
        const chapterRes = await fetch(`db/stories/hsk-${levelParam}/${storyParam}/${chapterParam}.json`);
        if (!chapterRes.ok) throw new Error("Chapter data not found");
        
        chapterData = await chapterRes.json();
        
        // Set Audio source
        audio.src = chapterData.audio_url;
        audio.load();
        
        // Setup Reader DOM
        initializeReader();
        
    } catch (err) {
        console.error("Error loading reader assets:", err);
        contentArea.innerHTML = `
            <div class="empty-state">
                <p style="color:red; font-weight:bold;">Không thể tải dữ liệu bài học này.</p>
                <p style="margin-top:0.5rem; font-size:0.9rem;">Hãy đảm bảo bạn đã chạy crawler thành công.</p>
                <a href="index.html" class="nav-link" style="margin-top:1rem; display:inline-block; border:1px solid var(--primary); padding:0.5rem 1rem; border-radius:6px;">Quay lại Thư viện</a>
            </div>`;
    }
}

// Generate chapter selection dropdown list
function renderChapterDropdown(storyMeta) {
    const dropdownMenu = document.getElementById("chapter-dropdown-menu");
    const dropdownBtn = document.getElementById("chapter-dropdown-btn");
    
    // Click button to toggle chapter dropdown menu
    dropdownBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle("active");
    });
    
    document.addEventListener("click", () => {
        dropdownMenu.classList.remove("active");
    });
    
    dropdownMenu.innerHTML = storyMeta.chapters.map(ch => {
        const isActive = ch.chapter_slug === chapterParam;
        return `
            <a href="reader.html?level=${storyMeta.hsk_level}&story=${storyMeta.slug}&chapter=${ch.chapter_slug}" class="dropdown-item ${isActive ? 'active' : ''}">
                Chương ${ch.chapter_number}: ${ch.title_en}
            </a>
        `;
    }).join("");
    
    // Set current active chapter label
    const currentCh = storyMeta.chapters.find(ch => ch.chapter_slug === chapterParam);
    if (currentCh) {
        document.getElementById("reader-chapter-title").innerText = `Chương ${currentCh.chapter_number}: ${currentCh.title_en}`;
    }
}

// Extract pure Chinese text from paragraph element (strips rt annotations)
function getChineseText(pElement) {
    const clone = pElement.cloneNode(true);
    clone.querySelectorAll("rt").forEach(rt => rt.remove());
    return clone.textContent.replace(/\s+/g, "").trim();
}

// Populate and set up interactive reader
function initializeReader() {
    // 1. Render content and translations
    renderBilingualContent();
    
    // 2. Map word timestamps
    mapWordTimestamps();
    
    // 3. Auto-calculate paragraph ranges
    calculateParagraphTimeRanges();
    
    // 4. Initialize dynamic pagination
    const totalParagraphs = contentArea.querySelectorAll(".paragraph-block").length;
    totalPages = Math.ceil(totalParagraphs / paragraphsPerPage);
    currentPage = 1;
    renderPage(currentPage);
    
    // 5. Setup event listeners
    setupEvents();
    
    // 6. Apply settings
    applyTheme(currentTheme);
    applyPinyinMode(currentPinyinMode);
    applyToneColors(toneColorsEnabled);
    applyTextSize(readerTextSize);
    applyShowTranslations(showTranslations);
}

// Renders the HSKStory HTML and appends corresponding sentence translations
function renderBilingualContent() {
    contentArea.innerHTML = chapterData.content_html;
    const paragraphs = contentArea.querySelectorAll("p");
    
    paragraphs.forEach((p, pIdx) => {
        // Create block container
        const block = document.createElement("div");
        block.className = "paragraph-block";
        p.parentNode.insertBefore(block, p);
        block.appendChild(p);
        
        // Match sentence translations
        const cnText = getChineseText(p);
        let viTranslation = "";
        
        if (chapterData.translation_data_vi) {
            Object.keys(chapterData.translation_data_vi).forEach(cnSent => {
                const cleanSent = cnSent.replace(/[，。？！、“”’‘,.\/\\?!]/g, "");
                const cleanParagraph = cnText.replace(/[，。？！、“”’‘,.\/\\?!]/g, "");
                
                if (cleanSent && cleanParagraph.includes(cleanSent)) {
                    viTranslation += chapterData.translation_data_vi[cnSent] + " ";
                }
            });
        }
        
        viTranslation = viTranslation.trim();
        if (viTranslation) {
            const transDiv = document.createElement("div");
            transDiv.className = "paragraph-translation-vi";
            transDiv.innerText = viTranslation;
            block.appendChild(transDiv);
        }
    });
}

// Map timestamps to each word span
function mapWordTimestamps() {
    if (chapterData.timestamps && chapterData.timestamps.length > 0) {
        const paragraphs = contentArea.querySelectorAll("p");
        paragraphs.forEach((p, pIdx) => {
            const pTimestamps = chapterData.timestamps[pIdx];
            if (!pTimestamps) return;
            
            // Filter out punctuation mapping
            const wordTimestampsOnly = pTimestamps.filter(tok => tok.p !== null);
            const wordsInDOM = p.querySelectorAll(".pw");
            
            wordsInDOM.forEach((pwElement, wIdx) => {
                const ts = wordTimestampsOnly[wIdx];
                if (ts && ts.s !== undefined) {
                    pwElement.setAttribute("data-start", ts.s);
                    pwElement.setAttribute("data-end", ts.e);
                }
            });
        });
    }
}

// Dynamically compute paragraph starts/ends based on word times
function calculateParagraphTimeRanges() {
    paragraphTimeRanges = [];
    if (!chapterData.timestamps) return;
    
    chapterData.timestamps.forEach((pTimestamps) => {
        const timedWords = pTimestamps.filter(tok => tok.s !== undefined && tok.e !== undefined);
        if (timedWords.length > 0) {
            const start = timedWords[0].s;
            const end = timedWords[timedWords.length - 1].e;
            paragraphTimeRanges.push({ start, end });
        } else {
            paragraphTimeRanges.push({ start: 0, end: 0 });
        }
    });
    
    // Fill gaps
    if (paragraphTimeRanges.length > 0) {
        paragraphTimeRanges[0].start = 0;
        for (let i = 0; i < paragraphTimeRanges.length - 1; i++) {
            paragraphTimeRanges[i].end = paragraphTimeRanges[i+1].start;
        }
        paragraphTimeRanges[paragraphTimeRanges.length - 1].end = 10000;
    }
}

// Display page logic
function renderPage(pageNumber) {
    // Clear dict popup on page change
    hideDictionaryCard();
    
    // Set page status text
    pageStatus.innerText = `Trang ${pageNumber} / ${totalPages}`;
    
    // Enable/disable page buttons
    prevPageBtn.disabled = pageNumber === 1;
    nextPageBtn.disabled = pageNumber === totalPages;
    
    // Hide/show paragraph blocks
    const blocks = contentArea.querySelectorAll(".paragraph-block");
    blocks.forEach((block, idx) => {
        const start = (pageNumber - 1) * paragraphsPerPage;
        const end = pageNumber * paragraphsPerPage;
        if (idx >= start && idx < end) {
            block.style.display = "block";
        } else {
            block.style.display = "none";
        }
    });
}

// Dictionary Card Helper
function showWordTranslation(wordElement) {
    const rawWord = getChineseText(wordElement);
    const hskLevel = wordElement.getAttribute("data-hsk") || "Chưa rõ";
    
    // Translate lookups
    const translation = vietnameseDict[rawWord] || "Chưa cập nhật bản dịch tiếng Việt cho từ này.";
    
    // Get Pinyin annotation
    let pinyin = "";
    const rubies = wordElement.querySelectorAll("ruby");
    rubies.forEach(r => {
        const rt = r.querySelector("rt");
        if (rt) {
            pinyin += rt.innerText + " ";
        }
    });
    pinyin = pinyin.trim();
    
    // Render definitions on popup card
    dictWordZh.innerText = rawWord;
    dictWordPinyin.innerText = pinyin;
    dictLevelBadge.innerText = `HSK ${hskLevel}`;
    dictDefinition.innerText = translation;
    
    // Star/save word bookmarking logic
    const starBtn = document.getElementById("dict-star-btn");
    if (starBtn) {
        let savedVocab = JSON.parse(localStorage.getItem("saved-vocab") || "[]");
        let isSaved = savedVocab.some(item => item.word === rawWord);
        starBtn.classList.toggle("active", isSaved);
        
        // Clone button to strip any previous event listeners cleanly
        const newStarBtn = starBtn.cloneNode(true);
        starBtn.parentNode.replaceChild(newStarBtn, starBtn);
        
        newStarBtn.addEventListener("click", () => {
            savedVocab = JSON.parse(localStorage.getItem("saved-vocab") || "[]");
            isSaved = savedVocab.some(item => item.word === rawWord);
            
            if (isSaved) {
                savedVocab = savedVocab.filter(item => item.word !== rawWord);
                newStarBtn.classList.remove("active");
            } else {
                savedVocab.push({
                    word: rawWord,
                    pinyin: pinyin,
                    level: hskLevel,
                    definition: translation
                });
                newStarBtn.classList.add("active");
            }
            localStorage.setItem("saved-vocab", JSON.stringify(savedVocab));
        });
    }
    
    // Fetch example
    dictExample.innerText = `Ví dụ: Dữ liệu đang được biên soạn.`;
    
    // Show dictionary popup
    const rect = wordElement.getBoundingClientRect();
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Set placement coords centered above word
    dictCard.style.display = "block";
    const popupWidth = dictCard.offsetWidth;
    const popupHeight = dictCard.offsetHeight;
    
    dictCard.style.left = `${Math.max(10, rect.left + scrollLeft + (rect.width / 2) - (popupWidth / 2))}px`;
    dictCard.style.top = `${rect.top + scrollTop - popupHeight - 12}px`;
}

function hideDictionaryCard() {
    dictCard.style.display = "none";
}

// Sync Karaoke Highlighting & Pages during playback
function syncHighlights(time) {
    let activeParagraphIdx = -1;
    
    for (let pIdx = 0; pIdx < paragraphTimeRanges.length; pIdx++) {
        const range = paragraphTimeRanges[pIdx];
        if (time >= range.start && time < range.end) {
            activeParagraphIdx = pIdx;
            break;
        }
    }
    
    if (activeParagraphIdx !== -1) {
        // Page flip detection
        const activePage = Math.floor(activeParagraphIdx / paragraphsPerPage) + 1;
        if (activePage !== currentPage) {
            currentPage = activePage;
            renderPage(currentPage);
        }
        
        const blocks = contentArea.querySelectorAll(".paragraph-block");
        const activeBlock = blocks[activeParagraphIdx];
        if (!activeBlock) return;
        
        // Highlight active paragraph block
        blocks.forEach(b => {
            const pTag = b.querySelector("p");
            const viTag = b.querySelector(".paragraph-translation-vi");
            if (pTag) pTag.classList.remove("audio-highlight");
            if (viTag) viTag.classList.remove("audio-highlight");
        });
        const pElement = activeBlock.querySelector("p");
        pElement.classList.add("audio-highlight");
        const viElement = activeBlock.querySelector(".paragraph-translation-vi");
        if (viElement) {
            viElement.classList.add("audio-highlight");
        }
        
        // Highlight active word
        const words = contentArea.querySelectorAll(".pw");
        words.forEach(w => w.classList.remove("word-highlight"));
        
        const wordsInP = pElement.querySelectorAll(".pw");
        wordsInP.forEach(wordEl => {
            const start = parseFloat(wordEl.getAttribute("data-start"));
            const end = parseFloat(wordEl.getAttribute("data-end"));
            if (!isNaN(start) && !isNaN(end) && time >= start && time <= end) {
                wordEl.classList.add("word-highlight");
            }
        });
        
        // Smooth follow-along scroll
        if (activeParagraphIdx !== lastHighlightedIdx) {
            lastHighlightedIdx = activeParagraphIdx;
            pElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } else {
        lastHighlightedIdx = -1;
    }
}

// Media Player Setup & Events
function updateProgressBar() {
    if (audio.duration) {
        const percent = (audio.currentTime / audio.duration) * 100;
        progressFill.style.width = `${percent}%`;
        progressHandle.style.left = `${percent}%`;
        timeDisplay.innerText = formatTime(audio.currentTime);
    }
}

function startPlaybackTracking() {
    updateInterval = setInterval(() => {
        updateProgressBar();
        syncHighlights(audio.currentTime);
    }, 100);
}

function stopPlaybackTracking() {
    clearInterval(updateInterval);
}

// Handle play states
function setPlayingState(playing) {
    isPlaying = playing;
    if (playing) {
        audio.play().then(() => {
            playToggleBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>`;
            startPlaybackTracking();
        }).catch(err => {
            console.error("Audio play blocked/failed:", err);
            setPlayingState(false);
        });
    } else {
        audio.pause();
        playToggleBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
        stopPlaybackTracking();
    }
}

// Settings Apply Hooks
function applyTheme(theme) {
    document.documentElement.className = "__variable_3ca20b __variable_2b6cd5 " + theme;
}

function applyPinyinMode(mode) {
    contentArea.className = contentArea.className.replace(/\bpinyin-\w+\b/g, "").trim();
    contentArea.classList.add(`pinyin-${mode}`);
}

function applyToneColors(enabled) {
    contentArea.classList.toggle("tone-colors-enabled", enabled);
}

function applyTextSize(size) {
    document.documentElement.style.setProperty("--reader-text-size", `${size}rem`);
    document.getElementById("size-slider-val").innerText = `${Math.round((size / 1.5) * 100)}%`;
}

function applyShowTranslations(show) {
    contentArea.classList.toggle("show-translations", show);
    translationToggleBtn.classList.toggle("active", show);
}

// Formatting helpers
function formatTime(secs) {
    if (isNaN(secs)) return "0:00";
    const minutes = Math.floor(secs / 60);
    const seconds = Math.floor(secs % 60);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

// Listeners Setup
function setupEvents() {
    // 1. Interactive Word Translation Popup click
    const words = contentArea.querySelectorAll(".pw");
    words.forEach(word => {
        word.addEventListener("click", (e) => {
            e.stopPropagation();
            showWordTranslation(word);
        });
    });
    
    document.addEventListener("click", () => {
        hideDictionaryCard();
    });
    
    dictCard.addEventListener("click", (e) => {
        e.stopPropagation();
    });
    
    dictCloseBtn.addEventListener("click", () => {
        hideDictionaryCard();
    });
    
    // 2. Playback Control actions
    playToggleBtn.addEventListener("click", () => {
        setPlayingState(!isPlaying);
    });
    
    skipBackBtn.addEventListener("click", () => {
        audio.currentTime = Math.max(0, audio.currentTime - 10);
        updateProgressBar();
    });
    
    skipForwardBtn.addEventListener("click", () => {
        audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 10);
        updateProgressBar();
    });
    
    // 3. Playback speed cyling
    speedBadge.addEventListener("click", () => {
        const speeds = [1.0, 1.25, 1.5, 0.75];
        let nextIdx = speeds.indexOf(audio.playbackRate) + 1;
        if (nextIdx >= speeds.length || nextIdx === -1) nextIdx = 0;
        
        const nextSpeed = speeds[nextIdx];
        audio.playbackRate = nextSpeed;
        speedBadge.innerText = `${nextSpeed}x`;
    });
    
    // 4. Progress bar seek drag
    progressSlider.addEventListener("click", (e) => {
        if (!audio.duration) return;
        const rect = progressSlider.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        const percent = offsetX / rect.width;
        
        audio.currentTime = percent * audio.duration;
        updateProgressBar();
        syncHighlights(audio.currentTime);
    });
    
    // 5. Audio events
    audio.addEventListener("loadedmetadata", () => {
        durationDisplay.innerText = formatTime(audio.duration);
    });
    
    audio.addEventListener("ended", () => {
        setPlayingState(false);
        audio.currentTime = 0;
        updateProgressBar();
    });
    
    // 6. Navigation Pagination buttons
    prevPageBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage(currentPage);
        }
    });
    
    nextPageBtn.addEventListener("click", () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderPage(currentPage);
        }
    });
    
    // 7. Settings menu buttons
    settingsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        settingsMenu.classList.toggle("active");
    });
    
    document.addEventListener("click", () => {
        settingsMenu.classList.remove("active");
    });
    
    settingsMenu.addEventListener("click", (e) => {
        e.stopPropagation();
    });
    
    // Themes options
    const themeButtons = document.querySelectorAll("[data-opt-theme]");
    themeButtons.forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-opt-theme") === currentTheme);
        btn.addEventListener("click", () => {
            currentTheme = btn.getAttribute("data-opt-theme");
            localStorage.setItem("hsk-reader-theme", currentTheme);
            applyTheme(currentTheme);
            themeButtons.forEach(b => b.classList.toggle("active", b === btn));
        });
    });
    
    // Pinyin options
    const pinyinButtons = document.querySelectorAll("[data-opt-pinyin]");
    pinyinButtons.forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-opt-pinyin") === currentPinyinMode);
        btn.addEventListener("click", () => {
            currentPinyinMode = btn.getAttribute("data-opt-pinyin");
            localStorage.setItem("hsk-reader-pinyin", currentPinyinMode);
            applyPinyinMode(currentPinyinMode);
            pinyinButtons.forEach(b => b.classList.toggle("active", b === btn));
        });
    });
    
    // Tone colors options
    const toneButtons = document.querySelectorAll("[data-opt-tones]");
    toneButtons.forEach(btn => {
        const state = btn.getAttribute("data-opt-tones") === "on";
        btn.classList.toggle("active", state === toneColorsEnabled);
        btn.addEventListener("click", () => {
            toneColorsEnabled = state;
            localStorage.setItem("hsk-reader-tones", toneColorsEnabled);
            applyToneColors(toneColorsEnabled);
            toneButtons.forEach(b => b.classList.toggle("active", b === btn));
        });
    });
    
    // Text size slider
    const sizeSlider = document.getElementById("setting-size-slider");
    sizeSlider.value = readerTextSize;
    sizeSlider.addEventListener("input", () => {
        readerTextSize = parseFloat(sizeSlider.value);
        localStorage.setItem("hsk-reader-size", readerTextSize);
        applyTextSize(readerTextSize);
    });
    
    // Translation toggle button
    translationToggleBtn.addEventListener("click", () => {
        showTranslations = !showTranslations;
        localStorage.setItem("hsk-reader-show-trans", showTranslations);
        applyShowTranslations(showTranslations);
    });
}
