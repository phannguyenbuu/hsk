// library.js - HSKStory Vietnamese Library Portal

// State
let stories = [];
let filteredStories = [];
let currentLevelFilter = "all";
let currentTheme = localStorage.getItem("hsk-reader-theme") || "light";

// DOM elements
const storiesGrid = document.getElementById("stories-grid");
const searchInput = document.getElementById("search-input");
const tabButtons = document.querySelectorAll(".tab-btn");
const settingsBtn = document.getElementById("settings-btn");
const settingsMenu = document.getElementById("settings-menu");

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    loadLibrary();
    setupEvents();
});

// Theme Management
function initTheme() {
    applyTheme(currentTheme);
    
    // Setup setting toggle options
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
}

function applyTheme(theme) {
    // Keep HSKStory NextJS variables
    document.documentElement.className = "__variable_3ca20b __variable_2b6cd5 " + theme;
}

// Load stories from local library JSON database
async function loadLibrary() {
    try {
        const response = await fetch("db/library.json");
        if (!response.ok) {
            throw new Error("Failed to load library catalog");
        }
        stories = await response.json();
        
        // Wait, if library is empty because crawler is still running, let's add a placeholder or fallback
        if (stories.length === 0) {
            storiesGrid.innerHTML = `
                <div class="empty-state">
                    <p>Đang tải thư viện truyện và dịch sang tiếng Việt...</p>
                    <div class="loading-spinner"></div>
                </div>`;
            // Check again in 3 seconds
            setTimeout(loadLibrary, 3000);
            return;
        }
        
        filteredStories = [...stories];
        renderStories();
    } catch (err) {
        console.error("Error loading library:", err);
        // Fallback placeholder card showing "Morning at Home" (if offline or not fully crawled yet)
        stories = [
            {
                "id": 159,
                "slug": "morning-at-home",
                "hsk_level": 1,
                "title": "Morning at Home (早上的家)",
                "chapter_count": 4,
                "chapters": [
                    { "chapter_number": 1, "chapter_slug": "chapter-1-dad-cooks", "title_en": "Dad Cooks (厨房里的爸爸)" },
                    { "chapter_number": 2, "chapter_slug": "chapter-2-daughters-backpack", "title_en": "Daughter's Backpack (女儿的书包)" },
                    { "chapter_number": 3, "chapter_slug": "chapter-3-xiao-dongs-shoes", "title_en": "Xiao Dong's Shoes (小东的鞋子)" },
                    { "chapter_number": 4, "chapter_slug": "chapter-4-running-late", "title_en": "Running Late (快迟到了)" }
                ]
            }
        ];
        filteredStories = [...stories];
        renderStories();
    }
}

// Render stories to the DOM
function renderStories() {
    if (filteredStories.length === 0) {
        storiesGrid.innerHTML = `
            <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
                <p>Không tìm thấy truyện nào khớp với bộ lọc.</p>
            </div>`;
        return;
    }
    
    storiesGrid.innerHTML = filteredStories.map(story => {
        const levelBadgeClass = `level-badge level-${story.hsk_level}`;
        
        // Render list of chapters inside card
        const chaptersHtml = story.chapters.map(ch => `
            <a href="reader.html?level=${story.hsk_level}&story=${story.slug}&chapter=${ch.chapter_slug}" class="chapter-link">
                <span class="ch-num">C.${ch.chapter_number}</span>
                <span class="ch-name">${ch.title_en}</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
            </a>
        `).join("");
        
        // Translating genres or summary dynamically
        let vnSynopsis = "Câu chuyện học tiếng Trung HSK sinh động kèm audio và phiên âm.";
        if (story.slug === "morning-at-home") {
            vnSynopsis = "Chào buổi sáng tại gia đình nhà Liang. Những rắc rối nho nhỏ chuẩn bị đi học, đi làm tạo nên tình huống vui nhộn.";
        } else if (story.slug === "first-plane-trip") {
            vnSynopsis = "Chuyến đi máy bay đầu tiên của gia đình nhà Gao đến Bắc Kinh thăm bà nội, sự cố trễ taxi và quên điện thoại.";
        }
        
        return `
            <div class="story-card warm-border">
                <div class="story-card-header">
                    <span class="${levelBadgeClass}">HSK ${story.hsk_level}</span>
                    <h2 class="story-title">${story.title}</h2>
                    <p class="story-synopsis">${vnSynopsis}</p>
                </div>
                <div class="story-chapters-list">
                    <span class="chapters-title">Danh sách chương (${story.chapter_count}):</span>
                    <div class="chapters-wrapper">
                        ${chaptersHtml}
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

// Setup listeners
function setupEvents() {
    // Search input
    searchInput.addEventListener("input", (e) => {
        filterStories();
    });
    
    // Level tabs
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentLevelFilter = btn.getAttribute("data-level");
            filterStories();
        });
    });
    
    // Settings dropdown toggle
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
}

// Filtering core logic
function filterStories() {
    const query = searchInput.value.toLowerCase().trim();
    
    filteredStories = stories.filter(story => {
        // Filter by HSK Level
        const levelMatch = currentLevelFilter === "all" || story.hsk_level.toString() === currentLevelFilter;
        
        // Filter by Search Query
        const titleMatch = story.title.toLowerCase().includes(query) || story.slug.toLowerCase().includes(query);
        
        return levelMatch && titleMatch;
    });
    
    renderStories();
}
