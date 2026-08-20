// explore.js - Explore Slang & Character Origins Controller

// State
let isExploreLoaded = false;
let isExploreLoading = false;
let slangDatabase = [];
let charactersDatabase = [];

// DOM Cache
let exploreElements = {};

document.addEventListener("DOMContentLoaded", () => {
    cacheExploreDOM();
    setupExploreTabs();
    setupExploreListeners();
});

function cacheExploreDOM() {
    exploreElements = {
        // Tab Switchers
        tabSlang: document.getElementById("explore-tab-slang"),
        tabOrigins: document.getElementById("explore-tab-origins"),
        panelSlang: document.getElementById("panel-explore-slang"),
        panelOrigins: document.getElementById("panel-explore-origins"),
        
        // Slang List & Detail Views
        slangListView: document.getElementById("slang-list-view"),
        slangDetailView: document.getElementById("slang-detail-view"),
        slangGrid: document.getElementById("slang-grid"),
        slangBackBtn: document.getElementById("slang-back-btn"),
        
        // Slang Details DOM
        slangDetZh: document.getElementById("slang-det-zh"),
        slangDetPy: document.getElementById("slang-det-py"),
        slangDetLiteral: document.getElementById("slang-det-literal"),
        slangDetBadges: document.getElementById("slang-det-badges"),
        slangDetTextbook: document.getElementById("slang-det-textbook"),
        slangDetInternet: document.getElementById("slang-det-internet"),
        slangDetBreakdown: document.getElementById("slang-det-breakdown"),
        slangDetContext: document.getElementById("slang-det-context"),
        slangDetExamples: document.getElementById("slang-det-examples"),
        
        // Origins List & Detail Views
        originsListView: document.getElementById("origins-list-view"),
        originsDetailView: document.getElementById("origins-detail-view"),
        originsGrid: document.getElementById("origins-grid"),
        originsBackBtn: document.getElementById("origins-back-btn"),
        
        // Origins Details DOM
        originsDetZh: document.getElementById("origins-det-zh"),
        originsDetPy: document.getElementById("origins-det-py"),
        originsDetMeaning: document.getElementById("origins-det-meaning"),
        originsDetBadge: document.getElementById("origins-det-badge"),
        originsDetEvolution: document.getElementById("origins-det-evolution"),
        originsDetStory: document.getElementById("origins-det-story"),
        originsDetComponents: document.getElementById("origins-det-components"),
        originsDetRelated: document.getElementById("origins-det-related")
    };
}

function setupExploreTabs() {
    if (!exploreElements.tabSlang || !exploreElements.tabOrigins) return;
    
    exploreElements.tabSlang.addEventListener("click", () => {
        exploreElements.tabSlang.classList.add("active");
        exploreElements.tabOrigins.classList.remove("active");
        exploreElements.panelSlang.classList.add("active");
        exploreElements.panelOrigins.classList.remove("active");
        
        // Reset detail views
        exploreElements.slangListView.style.display = "block";
        exploreElements.slangDetailView.style.display = "none";
        
        renderSlangList();
    });
    
    exploreElements.tabOrigins.addEventListener("click", () => {
        exploreElements.tabOrigins.classList.add("active");
        exploreElements.tabSlang.classList.remove("active");
        exploreElements.panelOrigins.classList.add("active");
        exploreElements.panelSlang.classList.remove("active");
        
        // Reset detail views
        exploreElements.originsListView.style.display = "block";
        exploreElements.originsDetailView.style.display = "none";
        
        renderOriginsList();
    });
    
    // Bind Back Buttons
    exploreElements.slangBackBtn.addEventListener("click", () => {
        exploreElements.slangListView.style.display = "block";
        exploreElements.slangDetailView.style.display = "none";
    });
    
    exploreElements.originsBackBtn.addEventListener("click", () => {
        exploreElements.originsListView.style.display = "block";
        exploreElements.originsDetailView.style.display = "none";
    });
}

function setupExploreListeners() {
    window.addEventListener("hsk-explore-active", () => {
        ensureExploreDataLoaded();
    });
}

// Lazy Load JSON Databases
async function ensureExploreDataLoaded() {
    if (isExploreLoaded || isExploreLoading) return;
    isExploreLoading = true;
    
    try {
        console.log("[Explore] Fetching slang & characters database...");
        const [slangRes, charRes] = await Promise.all([
            fetch("db/slang.json").then(res => res.json()).catch(() => []),
            fetch("db/characters.json").then(res => res.json()).catch(() => [])
        ]);
        
        slangDatabase = slangRes;
        charactersDatabase = charRes;
        isExploreLoaded = true;
        
        // Initial render
        if (exploreElements.tabSlang.classList.contains("active")) {
            renderSlangList();
        } else {
            renderOriginsList();
        }
        
    } catch (err) {
        console.error("[Explore] Error loading databases:", err);
    } finally {
        isExploreLoading = false;
    }
}

// Native Speech Synthesis Helper
function speakChinese(text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel(); // Stop any active speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.rate = 0.85; // Slightly slower for learner clarity
    window.speechSynthesis.speak(utterance);
}

// ==========================================
// 1. INTERNET SLANG PANEL
// ==========================================

function renderSlangList() {
    if (slangDatabase.length === 0) {
        exploreElements.slangGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: var(--muted-foreground); padding: 2rem;">
                Dữ liệu slang đang được tải hoặc chưa được crawl.
            </div>`;
        return;
    }
    
    exploreElements.slangGrid.innerHTML = "";
    slangDatabase.forEach(item => {
        const card = document.createElement("div");
        card.className = "vocab-card";
        
        // Build badges markup
        const badgeMarkup = item.badges && item.badges.length > 0 
            ? `<span class="card-level">${item.badges[0]}</span>`
            : "";
            
        card.innerHTML = `
            <div class="card-zh font-zh">${item.hanzi}</div>
            <div class="card-pinyin">${item.pinyin}</div>
            <div class="card-vi" title="${item.literal_vi}">${item.literal_vi}</div>
            ${badgeMarkup}
        `;
        
        card.addEventListener("click", () => showSlangDetail(item));
        exploreElements.slangGrid.appendChild(card);
    });
}

function showSlangDetail(item) {
    exploreElements.slangListView.style.display = "none";
    exploreElements.slangDetailView.style.display = "block";
    
    // Set text elements
    exploreElements.slangDetZh.innerText = item.hanzi;
    exploreElements.slangDetPy.innerText = item.pinyin;
    exploreElements.slangDetLiteral.innerText = `Nghĩa đen: "${item.literal_vi || item.literal_en}"`;
    
    // Set textbook vs internet
    exploreElements.slangDetTextbook.innerText = item.textbook_vi || item.textbook_en || "Chưa cập nhật";
    exploreElements.slangDetInternet.innerText = item.internet_vi || item.internet_en || "Chưa cập nhật";
    exploreElements.slangDetContext.innerHTML = (item.context_vi || item.context_en || "Chưa cập nhật bối cảnh").replace(/\n/g, "<br>");
    
    // Badges
    exploreElements.slangDetBadges.innerHTML = "";
    item.badges.forEach(b => {
        const span = document.createElement("span");
        span.className = "card-level";
        span.style.background = "rgba(244, 63, 94, 0.08)";
        span.innerText = b;
        exploreElements.slangDetBadges.appendChild(span);
    });
    
    // Character breakdown
    exploreElements.slangDetBreakdown.innerHTML = "";
    item.breakdown.forEach(c => {
        const card = document.createElement("div");
        card.className = "vocab-card";
        card.style.padding = "0.75rem";
        card.style.minWidth = "80px";
        card.style.margin = "0";
        card.innerHTML = `
            <div class="font-zh" style="font-size: 1.8rem; font-weight: bold; margin-bottom: 0.2rem;">${c.char}</div>
            <div style="font-size: 0.8rem; color: var(--primary); margin-bottom: 0.1rem;">${c.pinyin}</div>
            <div style="font-size: 0.75rem; color: var(--muted-foreground);">${c.vi_meaning || c.en_meaning}</div>
        `;
        exploreElements.slangDetBreakdown.appendChild(card);
    });
    
    // Examples & Text To Speech
    exploreElements.slangDetExamples.innerHTML = "";
    item.examples.forEach(ex => {
        const row = document.createElement("div");
        row.className = "bg-muted border border-border rounded-xl p-5 mb-4";
        
        row.innerHTML = `
            <div class="flex items-center gap-2 mb-3">
                <span class="inline-block bg-primary text-primary-foreground text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded">${ex.badge}</span>
                <p class="text-xs text-muted-foreground italic" style="margin: 0;">${ex.desc_vi || ex.desc_en}</p>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-bottom: 0.5rem;">
                <p class="font-zh text-lg" style="margin: 0; line-height: 1.5; color: var(--foreground);">${ex.zh}</p>
                <button class="dict-star-btn play-ex-btn" style="margin: 0; padding: 4px;" title="Phát âm thanh">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"></path></svg>
                </button>
            </div>
            <p class="text-sm text-muted-foreground" style="margin: 0; font-style: italic;">${ex.vi || ex.en}</p>
        `;
        
        row.querySelector(".play-ex-btn").addEventListener("click", () => speakChinese(ex.zh));
        exploreElements.slangDetExamples.appendChild(row);
    });
}

// ==========================================
// 2. CHARACTER ORIGINS PANEL
// ==========================================

function renderOriginsList() {
    if (charactersDatabase.length === 0) {
        exploreElements.originsGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: var(--muted-foreground); padding: 2rem;">
                Dữ liệu chiết tự đang được tải hoặc chưa được crawl.
            </div>`;
        return;
    }
    
    exploreElements.originsGrid.innerHTML = "";
    charactersDatabase.forEach(item => {
        const card = document.createElement("div");
        card.className = "vocab-card";
        
        card.innerHTML = `
            <div class="card-zh font-zh" style="font-size: 3rem;">${item.char}</div>
            <div class="card-pinyin">${item.pinyin}</div>
            <div class="card-vi" title="${item.meaning_vi}">${item.meaning_vi}</div>
            <span class="card-level">${item.hsk_level}</span>
        `;
        
        card.addEventListener("click", () => showOriginsDetail(item));
        exploreElements.originsGrid.appendChild(card);
    });
}

function showOriginsDetail(item) {
    exploreElements.originsListView.style.display = "none";
    exploreElements.originsDetailView.style.display = "block";
    
    // Set text elements
    exploreElements.originsDetZh.innerText = item.char;
    exploreElements.originsDetPy.innerText = item.pinyin;
    exploreElements.originsDetMeaning.innerText = `Ý nghĩa: ${item.meaning_vi || item.meaning_en}`;
    
    const badgeText = item.etymology_type === "etymology" ? "Chiết tự thực tế" : (item.etymology_type === "folk etymology" ? "Chiết tự dân gian" : "Lịch sử tối tăm");
    exploreElements.originsDetBadge.innerText = badgeText;
    
    exploreElements.originsDetStory.innerHTML = (item.story_vi || item.story_en || "Chưa cập nhật câu chuyện chiết tự").replace(/\n/g, "<br>");
    
    // Script history mapping
    const scriptsMap = {
        "oracle": { name: "Giáp cốt văn", period: "~1200 TCN" },
        "bronze": { name: "Kim văn", period: "~800 TCN" },
        "seal": { name: "Tiểu triện", period: "~200 TCN" },
        "liushutong": { name: "Lục thư thông", period: "~1600 CN" },
        "modern": { name: "Hiện đại", period: "Ngày nay" }
    };
    
    // Evolution SVGs
    exploreElements.originsDetEvolution.innerHTML = "";
    
    // Add historic glyph scripts
    ["oracle", "bronze", "seal", "liushutong"].forEach(script => {
        const svgFile = item.glyphs[script];
        if (svgFile) {
            const info = scriptsMap[script];
            const div = document.createElement("div");
            div.className = "evolution-item";
            div.innerHTML = `
                <img src="db/etymology/glyphs/${svgFile}" alt="${item.char} ${info.name}" style="background: rgba(var(--primary-rgb), 0.02); border-radius: 8px; padding: 4px;" onerror="this.style.display='none';">
                <span class="evolution-name">${info.name}</span>
                <span class="evolution-period">${info.period}</span>
            `;
            exploreElements.originsDetEvolution.appendChild(div);
        }
    });
    
    // Append Modern target character at the end of evolution
    const modernInfo = scriptsMap["modern"];
    const modDiv = document.createElement("div");
    modDiv.className = "evolution-item";
    modDiv.innerHTML = `
        <div class="font-zh" style="font-size: 3rem; font-weight: bold; width: 64px; height: 64px; line-height: 64px; display: flex; align-items: center; justify-content: center; color: var(--primary);">${item.char}</div>
        <span class="evolution-name">${modernInfo.name}</span>
        <span class="evolution-period">${modernInfo.period}</span>
    `;
    exploreElements.originsDetEvolution.appendChild(modDiv);
    
    // Components
    exploreElements.originsDetComponents.innerHTML = "";
    if (item.components && item.components.length > 0) {
        item.components.forEach(comp => {
            const card = document.createElement("div");
            card.className = "vocab-card";
            card.style.padding = "0.75rem";
            card.style.minWidth = "80px";
            card.style.margin = "0";
            card.innerHTML = `
                <div class="font-zh" style="font-size: 1.8rem; font-weight: bold; margin-bottom: 0.2rem;">${comp.char}</div>
                <div style="font-size: 0.8rem; color: var(--muted-foreground);">${comp.vi || comp.en}</div>
            `;
            exploreElements.originsDetComponents.appendChild(card);
        });
    } else {
        exploreElements.originsDetComponents.innerHTML = `<span style="color: var(--muted-foreground); font-size: 0.9rem;">Chưa cập nhật bộ thủ.</span>`;
    }
    
    // Related Characters
    exploreElements.originsDetRelated.innerHTML = "";
    if (item.related && item.related.length > 0) {
        item.related.forEach(c => {
            const span = document.createElement("span");
            span.style.cursor = "pointer";
            span.style.padding = "0.2rem 0.6rem";
            span.style.borderRadius = "6px";
            span.style.border = "1px solid var(--border)";
            span.style.background = "var(--bg-card) || var(--card)";
            span.style.fontSize = "2.2rem";
            span.className = "font-zh hover-primary-border";
            span.innerText = c;
            
            // Allow clicking related characters to navigate instantly!
            span.addEventListener("click", () => {
                const match = charactersDatabase.find(x => x.char === c);
                if (match) {
                    showOriginsDetail(match);
                } else {
                    alert(`Câu chuyện chiết tự của chữ "${c}" hiện tại chưa được crawl.`);
                }
            });
            exploreElements.originsDetRelated.appendChild(span);
        });
    } else {
        exploreElements.originsDetRelated.innerHTML = `<span style="color: var(--muted-foreground); font-size: 0.9rem;">Không có chữ liên quan.</span>`;
    }
}
