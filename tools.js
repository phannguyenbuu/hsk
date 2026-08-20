// tools.js - Interactive HSK Learning Tools

// State Variables
let isDbLoaded = false;
let isDbLoading = false;
let hskWords = {};
let vietnameseDict = {};
let mockTests = {};
let wordsByLevel = { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [] };

// Active Tool Tab
let activeTool = "quiz";

// Quiz State
let quizState = {
    currentLevel: 1,
    currentQuestionIndex: 0,
    questionsAnswered: 0,
    correctAnswers: 0,
    currentWord: "",
    correctMeaning: "",
    options: [],
    history: []
};

// Practice Test State
let practiceState = {
    level: 1,
    questions: [],
    currentIdx: 0,
    correctCount: 0,
    selectedOption: null,
    answered: false
};

// DOM Elements Cache
let elements = {};

// Wait for DOM to load
document.addEventListener("DOMContentLoaded", () => {
    cacheDOM();
    setupToolTabs();
    setupViewListeners();
    setupQuizEvents();
    setupAnalyzerEvents();
    setupDiffEvents();
    setupPracticeEvents();
});

// Cache elements
function cacheDOM() {
    elements = {
        // Tab buttons
        toolTabButtons: document.querySelectorAll(".tool-tab-btn"),
        viewPanels: document.querySelectorAll(".tool-view-panel"),
        
        // Quiz DOM
        startQuizBtn: document.getElementById("start-quiz-btn"),
        quizGame: document.getElementById("quiz-game"),
        quizWord: document.getElementById("quiz-word"),
        quizOptions: document.getElementById("quiz-options"),
        quizProgress: document.getElementById("quiz-progress"),
        quizCurrentLevel: document.getElementById("quiz-current-level"),
        quizScore: document.getElementById("quiz-score"),
        quizResultView: document.getElementById("quiz-result-view"),
        quizResultLevel: document.getElementById("quiz-result-level"),
        quizResultDesc: document.getElementById("quiz-result-desc"),
        restartQuizBtn: document.getElementById("restart-quiz-btn"),
        panelQuizIntro: document.querySelector("#panel-quiz .tool-intro"),

        // Analyzer DOM
        analyzerInput: document.getElementById("analyzer-input"),
        analyzeBtn: document.getElementById("analyze-btn"),
        clearAnalyzerBtn: document.getElementById("clear-analyzer-btn"),
        analyzerSpinner: document.getElementById("analyzer-spinner"),
        analyzerResults: document.getElementById("analyzer-results"),
        analyzerChart: document.getElementById("analyzer-chart"),
        analyzerOutput: document.getElementById("analyzer-output"),
        analyzerTooltip: document.getElementById("analyzer-tooltip"),
        tooltipZh: document.getElementById("tooltip-zh"),
        tooltipPinyin: document.getElementById("tooltip-pinyin"),
        tooltipLevel: document.getElementById("tooltip-level"),
        tooltipDefinition: document.getElementById("tooltip-definition"),

        // Diff DOM
        diffLevelSelect: document.getElementById("diff-level-select"),
        diffContent: document.getElementById("diff-content"),

        // Practice DOM
        practiceIntro: document.getElementById("practice-intro"),
        startPracticeBtn: document.getElementById("start-practice-btn"),
        practiceLevelSelect: document.getElementById("practice-level-select"),
        practiceGame: document.getElementById("practice-game"),
        practiceNumber: document.getElementById("practice-number"),
        practiceScore: document.getElementById("practice-score"),
        practicePassage: document.getElementById("practice-passage"),
        practiceHintBtn: document.getElementById("practice-hint-btn"),
        practiceTranslation: document.getElementById("practice-translation"),
        practiceOptions: document.getElementById("practice-options"),
        practiceNextBtn: document.getElementById("practice-next-btn"),
        practiceResultView: document.getElementById("practice-result-view"),
        practiceResultScore: document.getElementById("practice-result-score"),
        practiceResultDesc: document.getElementById("practice-result-desc"),
        restartPracticeBtn: document.getElementById("restart-practice-btn")
    };
}

// Setup View Tab Switcher inside Tools Sidebar
function setupToolTabs() {
    elements.toolTabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const toolName = btn.getAttribute("data-tool");
            switchToolPanel(toolName);
        });
    });
}

function switchToolPanel(toolName) {
    activeTool = toolName;
    
    // Toggle active sidebar button
    elements.toolTabButtons.forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-tool") === toolName);
    });

    // Toggle active panel view
    elements.viewPanels.forEach(panel => {
        panel.classList.toggle("active", panel.getAttribute("id") === `panel-${toolName}`);
    });

    // Load data if switching to a tool and databases aren't loaded yet
    ensureDatabasesLoaded();

    // Trigger tool-specific load/view updates
    if (toolName === "diff") {
        renderDiffContent();
    }
}

// Listen to navigation from main library page (library.js switcher)
function setupViewListeners() {
    window.addEventListener("hsk-tools-active", () => {
        ensureDatabasesLoaded();
    });
}

// Safe parser for Python stringified dictionaries in vietnamese_dict.json
function parseDictEntry(str) {
    if (!str) return null;
    try {
        // Replace single quotes with double quotes
        const normalized = str.replace(/'/g, '"');
        return JSON.parse(normalized);
    } catch (e) {
        // Regex fallback parser
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

// Lazy load databases on demand
async function ensureDatabasesLoaded() {
    if (isDbLoaded || isDbLoading) return;
    isDbLoading = true;
    
    // Show spinner in analyzer if it's the current view
    if (elements.analyzerSpinner) {
        elements.analyzerSpinner.style.display = "flex";
    }

    try {
        console.log("[Tools] Loading database files...");
        
        const [wordsRes, dictRes, mockRes] = await Promise.all([
            fetch("db/hsk_words.json").then(res => res.json()),
            fetch("db/vietnamese_dict.json").then(res => res.json()),
            fetch("db/mock_tests.json").then(res => res.json()).catch(() => ({}))
        ]);

        hskWords = wordsRes;
        vietnameseDict = dictRes;
        mockTests = mockRes;

        // Populate words by level, filtering only words that actually have a Vietnamese definition in our dict
        Object.entries(hskWords).forEach(([word, lvl]) => {
            if (lvl >= 1 && lvl <= 9 && vietnameseDict[word]) {
                wordsByLevel[lvl].push(word);
            }
        });

        isDbLoaded = true;
        console.log("[Tools] All databases loaded successfully.");
    } catch (err) {
        console.error("[Tools] Error loading dictionaries:", err);
    } finally {
        isDbLoading = false;
        if (elements.analyzerSpinner) {
            elements.analyzerSpinner.style.display = "none";
        }
    }
}

// ==========================================
// 1. ADAPTIVE HSK LEVEL QUIZ LOGIC
// ==========================================

function setupQuizEvents() {
    elements.startQuizBtn.addEventListener("click", startQuiz);
    elements.restartQuizBtn.addEventListener("click", startQuiz);
}

function startQuiz() {
    quizState.currentLevel = 1;
    quizState.currentQuestionIndex = 0;
    quizState.questionsAnswered = 0;
    quizState.correctAnswers = 0;
    quizState.history = [];
    
    elements.panelQuizIntro.style.display = "none";
    elements.quizResultView.style.display = "none";
    elements.quizGame.style.display = "block";
    
    generateQuizQuestion();
}

function generateQuizQuestion() {
    const lvl = quizState.currentLevel;
    const levelWords = wordsByLevel[lvl];

    if (!levelWords || levelWords.length < 5) {
        // Fallback if level words are not fully populated
        endQuiz(lvl);
        return;
    }

    // Pick a random word from the current level
    let attempts = 0;
    let word = "";
    do {
        word = levelWords[Math.floor(Math.random() * levelWords.length)];
        attempts++;
    } while (quizState.history.includes(word) && attempts < 50);

    quizState.history.push(word);
    quizState.currentWord = word;

    // Parse dictionary entry
    const parsed = parseDictEntry(vietnameseDict[word]);
    const correctMeaning = parsed && parsed.e && parsed.e.length > 0 ? parsed.e.join(", ") : "Nghĩa tiếng Việt";
    quizState.correctMeaning = correctMeaning;

    // Generate 3 distractors from adjacent levels or same level
    let distractorPool = [];
    // Combine same level and adjacent level words
    distractorPool = distractorPool.concat(wordsByLevel[lvl]);
    if (lvl > 1) distractorPool = distractorPool.concat(wordsByLevel[lvl - 1]);
    if (lvl < 9 && wordsByLevel[lvl + 1]) distractorPool = distractorPool.concat(wordsByLevel[lvl + 1]);

    // Clean distractors pool
    distractorPool = distractorPool.filter(w => w !== word && vietnameseDict[w]);

    let distractors = [];
    while (distractors.length < 3 && distractorPool.length > 0) {
        const idx = Math.floor(Math.random() * distractorPool.length);
        const dWord = distractorPool[idx];
        const parsedD = parseDictEntry(vietnameseDict[dWord]);
        const dMeaning = parsedD && parsedD.e ? parsedD.e.join(", ") : "";
        
        if (dMeaning && dMeaning !== correctMeaning && !distractors.includes(dMeaning)) {
            distractors.push(dMeaning);
        }
        // Remove to avoid infinite loops
        distractorPool.splice(idx, 1);
    }

    // Fallback distractors if pool empty
    while (distractors.length < 3) {
        distractors.push("Nghĩa giả định " + (distractors.length + 1));
    }

    // Put options together and shuffle
    quizState.options = [correctMeaning, ...distractors].sort(() => Math.random() - 0.5);

    // Update DOM
    elements.quizWord.innerText = word;
    elements.quizCurrentLevel.innerText = `Cấp độ: HSK ${lvl}`;
    elements.quizScore.innerText = `Câu hỏi: ${quizState.currentQuestionIndex + 1}/3 (Đúng: ${quizState.correctAnswers})`;
    
    // Update progress bar
    const progressPercent = ((quizState.currentQuestionIndex) / 3) * 100;
    elements.quizProgress.style.width = `${progressPercent}%`;

    // Render option buttons
    elements.quizOptions.innerHTML = "";
    quizState.options.forEach(opt => {
        const btn = document.createElement("button");
        btn.className = "quiz-opt-btn";
        btn.innerText = opt;
        btn.addEventListener("click", () => handleQuizAnswer(btn, opt === correctMeaning));
        elements.quizOptions.appendChild(btn);
    });
}

function handleQuizAnswer(selectedBtn, isCorrect) {
    // Disable all buttons
    const buttons = elements.quizOptions.querySelectorAll("button");
    buttons.forEach(btn => btn.disabled = true);

    // Color correct/incorrect
    if (isCorrect) {
        selectedBtn.classList.add("correct");
        quizState.correctAnswers++;
    } else {
        selectedBtn.classList.add("incorrect");
        // Highlight correct one
        buttons.forEach(btn => {
            if (btn.innerText === quizState.correctMeaning) {
                btn.classList.add("correct");
            }
        });
    }

    quizState.currentQuestionIndex++;
    quizState.questionsAnswered++;

    // Wait 1.5 seconds and load next step
    setTimeout(() => {
        if (quizState.currentQuestionIndex === 3) {
            // Evaluated current level
            if (quizState.correctAnswers >= 2) {
                // Promoted to next level!
                if (quizState.currentLevel < 9) {
                    quizState.currentLevel++;
                    quizState.currentQuestionIndex = 0;
                    quizState.correctAnswers = 0;
                    alert(`Chúc mừng! Bạn đã đỗ HSK ${quizState.currentLevel - 1} và tiến lên HSK ${quizState.currentLevel}!`);
                    generateQuizQuestion();
                } else {
                    // Passed HSK 9! Master of Chinese!
                    endQuiz(9);
                }
            } else {
                // Failed to pass. Quiz ends!
                endQuiz(quizState.currentLevel - 1);
            }
        } else {
            generateQuizQuestion();
        }
    }, 1500);
}

function endQuiz(passedLevel) {
    elements.quizGame.style.display = "none";
    elements.quizResultView.style.display = "block";

    if (passedLevel === 0) {
        elements.quizResultLevel.innerText = "Dưới HSK 1";
        elements.quizResultDesc.innerText = "Có vẻ bạn mới bắt đầu học tiếng Trung. Hãy thử đọc các mẩu truyện HSK 1 cực kỳ đơn giản trên website của chúng tôi nhé!";
    } else {
        elements.quizResultLevel.innerText = `HSK ${passedLevel}`;
        let description = "";
        if (passedLevel <= 2) {
            description = `Bạn đang ở trình độ Sơ cấp (HSK ${passedLevel}). Bạn có vốn từ căn bản về các chủ đề đời sống hàng ngày. Hãy luyện đọc thêm các mẩu truyện HSK 1 & 2 nhé!`;
        } else if (passedLevel <= 5) {
            description = `Tuyệt vời! Bạn đang ở trình độ Trung cấp (HSK ${passedLevel}). Bạn có thể hiểu hầu hết các đoạn hội thoại phức tạp và đọc hiểu bài viết trung bình. Hãy đọc thêm các truyện HSK 3, 4, 5.`;
        } else {
            description = `Kinh ngạc! Bạn đang ở trình độ Cao cấp (HSK ${passedLevel}). Bạn sở hữu vốn từ vựng cực kỳ phong phú và tự tin giao tiếp chuẩn học thuật. Hãy khám phá kho truyện HSK 6+!`;
        }
        elements.quizResultDesc.innerText = description;
    }
}

// ==========================================
// 2. HIGH-PERFORMANCE HSK ANALYZER LOGIC
// ==========================================

function setupAnalyzerEvents() {
    elements.analyzeBtn.addEventListener("click", runTextAnalysis);
    elements.clearAnalyzerBtn.addEventListener("click", () => {
        elements.analyzerInput.value = "";
        elements.analyzerResults.style.display = "none";
        hideTooltip();
    });
}

async function runTextAnalysis() {
    const text = elements.analyzerInput.value.trim();
    if (!text) {
        alert("Vui lòng nhập văn bản tiếng Trung cần phân tích.");
        return;
    }

    if (!isDbLoaded) {
        elements.analyzerSpinner.style.display = "flex";
        await ensureDatabasesLoaded();
        elements.analyzerSpinner.style.display = "none";
    }

    // Segment text and match HSK levels
    const words = segmentChineseText(text);
    
    // Statistics counters
    const levelCounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, un: 0 };
    let totalCount = 0;

    // Build interactive output HTML
    elements.analyzerOutput.innerHTML = "";
    
    words.forEach(word => {
        // Skip whitespace/newlines in counters but keep in output
        if (/^\s+$/.test(word)) {
            const span = document.createElement("span");
            span.innerHTML = word.replace(/\n/g, "<br>");
            elements.analyzerOutput.appendChild(span);
            return;
        }

        // Punctuation check
        const isChinese = /[\u4e00-\u9fa5]/.test(word);
        if (!isChinese) {
            const span = document.createElement("span");
            span.innerText = word;
            elements.analyzerOutput.appendChild(span);
            return;
        }

        // It is a word! Get HSK level
        const level = hskWords[word] || "un";
        levelCounts[level]++;
        totalCount++;

        const span = document.createElement("span");
        span.className = "az-word";
        span.setAttribute("data-level", level);
        span.setAttribute("data-word", word);
        span.innerText = word;
        
        // Tooltip listeners
        span.addEventListener("mouseenter", (e) => showTooltip(e, word, level));
        span.addEventListener("mousemove", (e) => positionTooltip(e));
        span.addEventListener("mouseleave", hideTooltip);

        elements.analyzerOutput.appendChild(span);
    });

    // Render Stats Chart
    elements.analyzerChart.innerHTML = "";
    const levelsList = [1, 2, 3, 4, 5, 6, 7, 8, 9, "un"];
    
    levelsList.forEach(lvl => {
        const count = levelCounts[lvl];
        const percent = totalCount > 0 ? ((count / totalCount) * 100).toFixed(1) : 0;
        
        const row = document.createElement("div");
        row.className = "chart-row";
        
        const labelText = lvl === "un" ? "Chưa rõ" : `HSK ${lvl}`;
        const barClass = lvl === "un" ? "bar-hsk-un" : `bar-hsk-${lvl}`;

        row.innerHTML = `
            <div class="chart-label">${labelText}</div>
            <div class="chart-bar-wrapper">
                <div class="chart-bar-fill ${barClass}" style="width: ${percent}%;"></div>
            </div>
            <div class="chart-value">${percent}%</div>
        `;
        elements.analyzerChart.appendChild(row);
    });

    elements.analyzerResults.style.display = "block";
}

// Maximum Matching (Greedy) segmentation algorithm
function segmentChineseText(text) {
    const result = [];
    let i = 0;
    const len = text.length;

    while (i < len) {
        // Handle newlines and spaces directly
        const char = text[i];
        if (/\s/.test(char)) {
            result.push(char);
            i++;
            continue;
        }

        // Handle punctuation directly
        const isChinese = /[\u4e00-\u9fa5]/.test(char);
        if (!isChinese) {
            result.push(char);
            i++;
            continue;
        }

        // Maximum matching substring lookup (length 4 down to 1)
        let matched = false;
        for (let size = 4; size >= 1; size--) {
            if (i + size <= len) {
                const sub = text.substring(i, i + size);
                if (hskWords[sub]) {
                    result.push(sub);
                    i += size;
                    matched = true;
                    break;
                }
            }
        }

        // If no match found in dictionary, fallback to single character
        if (!matched) {
            result.push(char);
            i++;
        }
    }
    return result;
}

// Tooltip display handlers
function showTooltip(e, word, level) {
    const parsed = parseDictEntry(vietnameseDict[word]);
    const pinyin = parsed ? parsed.p : "Chưa cập nhật";
    const meanings = parsed && parsed.e ? parsed.e.join(", ") : "Chưa cập nhật nghĩa Việt";

    elements.tooltipZh.innerText = word;
    elements.tooltipPinyin.innerText = pinyin;
    elements.tooltipLevel.innerText = level === "un" ? "Ngoài HSK" : `HSK ${level}`;
    elements.tooltipDefinition.innerText = meanings;
    
    // Set level badge background color
    elements.tooltipLevel.style.backgroundColor = level === "un" ? "#6b7280" : getHskColor(level);

    elements.analyzerTooltip.style.display = "flex";
    positionTooltip(e);
}

function positionTooltip(e) {
    const tooltip = elements.analyzerTooltip;
    const scrollX = window.scrollX || window.pageXOffset;
    const scrollY = window.scrollY || window.pageYOffset;
    
    // Position tooltip right above mouse cursor
    tooltip.style.left = `${e.clientX + scrollX - tooltip.offsetWidth / 2}px`;
    tooltip.style.top = `${e.clientY + scrollY - tooltip.offsetHeight - 15}px`;
}

function hideTooltip() {
    elements.analyzerTooltip.style.display = "none";
}

function getHskColor(lvl) {
    const colors = {
        1: "#22c55e",
        2: "#3b82f6",
        3: "#14b8a6",
        4: "#f97316",
        5: "#a855f7",
        6: "#db2777",
        7: "#eab308",
        8: "#4f46e5",
        9: "#ef4444"
    };
    return colors[lvl] || "#6b7280";
}

// ==========================================
// 3. HSK 3.0 WORD DIFF CATALOG LOGIC
// ==========================================

function setupDiffEvents() {
    elements.diffLevelSelect.addEventListener("change", renderDiffContent);
}

function renderDiffContent() {
    const lvl = elements.diffLevelSelect.value;
    
    // Structural level data mapping
    const diffData = {
        "1": {
            oldNum: 150,
            newNum: 500,
            chars: 300,
            desc: "HSK 1 mới tăng gấp 3 lần từ vựng, chuyển hóa trọng tâm từ từ đơn lẻ sang cụm từ ghép thông dụng thường ngày.",
            additions: [
                { w: "微信", n: "Mạng xã hội WeChat" },
                { w: "地铁", n: "Tàu điện ngầm" },
                { w: "发短信", n: "Gửi tin nhắn" },
                { w: "电子邮件", n: "Thư điện tử (Email)" },
                { w: "点赞", n: "Ấn thích (Like)" },
                { w: "共享单车", n: "Xe đạp chia sẻ" }
            ],
            shifts: [
                { w: "出租车", n: "Chuyển lên HSK 2" },
                { w: "医生", n: "Chuyển lên HSK 2" }
            ]
        },
        "2": {
            oldNum: 300,
            newNum: 1272,
            chars: 600,
            desc: "HSK 2 tích hợp một lượng lớn từ ghép chỉ công nghệ số và đời sống tiện ích hiện đại.",
            additions: [
                { w: "支付宝", n: "Ví điện tử Alipay" },
                { w: "二维码", n: "Mã QR" },
                { w: "刷脸", n: "Quét khuôn mặt (Face ID)" },
                { w: "快递", n: "Chuyển phát nhanh" },
                { w: "网购", n: "Mua sắm trực tuyến" }
            ],
            shifts: [
                { w: "经理", n: "Chuyển lên HSK 3" },
                { w: "护照", n: "Chuyển lên HSK 3" }
            ]
        },
        "3": {
            oldNum: 600,
            newNum: 2245,
            chars: 900,
            desc: "HSK 3 hoàn thiện vốn từ sơ cấp để người học sẵn sàng bước vào giai đoạn giao tiếp trung cấp trôi chảy.",
            additions: [
                { w: "互联网", n: "Mạng Internet" },
                { w: "人工智能", n: "Trí tuệ nhân tạo (AI)" },
                { w: "自 d 媒体", n: "Tự truyền thông (Vlogger/Creator)" },
                { w: "数码相机", n: "Máy ảnh kỹ thuật số" }
            ],
            shifts: [
                { w: "翻译", n: "Chuyển lên HSK 4" }
            ]
        },
        "4": {
            oldNum: 1200,
            newNum: 3245,
            chars: 1200,
            desc: "HSK 4 mới mở rộng sâu sắc các thành ngữ (thành ngữ bốn chữ) và các từ mô tả trạng thái trừu tượng.",
            additions: [
                { w: "不可思议", n: "Không thể tin nổi" },
                { w: "顺其自然", n: "Thuận theo tự nhiên" },
                { w: "低碳生活", n: "Lối sống ít carbon" }
            ],
            shifts: [
                { w: "辩论", n: "Chuyển từ cấp độ cũ" }
            ]
        },
        "5": {
            oldNum: 2500,
            newNum: 4305,
            chars: 1500,
            desc: "Mức độ trung - cao cấp yêu cầu kỹ năng viết bình luận văn học và phân tích ngữ pháp chuyên sâu.",
            additions: [
                { w: "朝气蓬勃", n: "Tràn đầy sức sống" },
                { w: "地道", n: "Chuẩn bản xứ; chính gốc" }
            ],
            shifts: []
        },
        "6": {
            oldNum: "5000+",
            newNum: 5456,
            chars: 1800,
            desc: "HSK 6 chuyển dịch sang các bài luận xã hội phức tạp, triết học và các tác phẩm văn học cổ điển.",
            additions: [
                { w: "精益求精", n: "Đã tốt muốn tốt hơn" }
            ],
            shifts: []
        },
        "7-9": {
            oldNum: "Không có",
            newNum: 11092,
            chars: 3000,
            desc: "Cấp độ Cao cấp hoàn toàn mới dành cho nghiên cứu sinh, phiên dịch chuyên nghiệp và chuyên gia học thuật.",
            additions: [
                { w: "学术讨论", n: "Thảo luận học thuật" },
                { w: "博大精深", n: "Rộng lớn tinh sâu" }
            ],
            shifts: []
        }
    };

    const data = diffData[lvl];
    if (!data) return;

    let additionsHtml = "";
    if (data.additions.length > 0) {
        additionsHtml = `
            <div style="margin-top: 1rem;">
                <span class="diff-change-badge badge-added">Mới bổ sung nổi bật:</span>
                <div class="diff-words-list">
                    ${data.additions.map(a => `
                        <div class="diff-word-tag" title="${a.n}">
                            <span class="word-cn">${a.w}</span>
                            <span class="word-note">(${a.n})</span>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;
    }

    let shiftsHtml = "";
    if (data.shifts && data.shifts.length > 0) {
        shiftsHtml = `
            <div style="margin-top: 1rem;">
                <span class="diff-change-badge badge-shifted">Chuyển cấp độ tiêu biểu:</span>
                <div class="diff-words-list">
                    ${data.shifts.map(s => `
                        <div class="diff-word-tag" title="${s.n}">
                            <span class="word-cn">${s.w}</span>
                            <span class="word-note">(${s.n})</span>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;
    }

    elements.diffContent.innerHTML = `
        <table class="diff-summary-table">
            <thead>
                <tr>
                    <th>Tiêu chí so sánh</th>
                    <th>HSK Cũ (2.0)</th>
                    <th>HSK Mới (3.0)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Số lượng từ vựng tích lũy</td>
                    <td><strong style="color: var(--muted-foreground);">${data.oldNum} từ</strong></td>
                    <td><strong style="color: var(--primary);">${data.newNum} từ</strong></td>
                </tr>
                <tr>
                    <td>Số lượng chữ Hán cần biết</td>
                    <td>-</td>
                    <td><strong>${data.chars} chữ</strong></td>
                </tr>
            </tbody>
        </table>
        
        <p style="font-size: 0.92rem; line-height: 1.5; color: var(--foreground); margin-bottom: 1rem;">
            <strong>Mô tả thay đổi:</strong> ${data.desc}
        </p>
        
        ${additionsHtml}
        ${shiftsHtml}
    `;
}

// ==========================================
// 4. HSK PRACTICE READING TEST LOGIC
// ==========================================

function setupPracticeEvents() {
    elements.startPracticeBtn.addEventListener("click", startPractice);
    elements.restartPracticeBtn.addEventListener("click", startPractice);
    
    elements.practiceHintBtn.addEventListener("click", () => {
        const trans = elements.practiceTranslation;
        if (trans.style.display === "none") {
            trans.style.display = "block";
            elements.practiceHintBtn.innerText = "Ẩn gợi ý dịch nghĩa";
        } else {
            trans.style.display = "none";
            elements.practiceHintBtn.innerText = "Xem gợi ý dịch nghĩa";
        }
    });

    elements.practiceNextBtn.addEventListener("click", () => {
        practiceState.currentIdx++;
        showPracticeQuestion();
    });
}

async function startPractice() {
    const lvl = parseInt(elements.practiceLevelSelect.value);
    
    if (!isDbLoaded) {
        await ensureDatabasesLoaded();
    }

    // Pull questions for selected level
    const levelQuestions = mockTests[lvl];
    if (!levelQuestions || levelQuestions.length === 0) {
        alert(`Hiện tại chưa có đủ truyện HSK ${lvl} được dịch để lập đề thi. Vui lòng thử các cấp độ khác (ví dụ HSK 1, 2, 3, 4).`);
        return;
    }

    // Shuffle and pick 10 questions
    practiceState.level = lvl;
    practiceState.questions = [...levelQuestions].sort(() => Math.random() - 0.5).slice(0, 10);
    practiceState.currentIdx = 0;
    practiceState.correctCount = 0;
    
    elements.practiceIntro.style.display = "none";
    elements.practiceResultView.style.display = "none";
    elements.practiceGame.style.display = "block";

    showPracticeQuestion();
}

function showPracticeQuestion() {
    const idx = practiceState.currentIdx;
    
    if (idx >= practiceState.questions.length) {
        endPractice();
        return;
    }

    practiceState.answered = false;
    practiceState.selectedOption = null;
    elements.practiceNextBtn.style.display = "none";
    
    // Reset hints
    elements.practiceTranslation.style.display = "none";
    elements.practiceHintBtn.innerText = "Xem gợi ý dịch nghĩa";

    const q = practiceState.questions[idx];

    // Update Meta
    elements.practiceNumber.innerText = `Câu hỏi: ${idx + 1}/10`;
    elements.practiceScore.innerText = `Đúng: ${practiceState.correctCount}`;
    
    // Set Question Content
    elements.practicePassage.innerText = q.sentence_blank;
    elements.practiceTranslation.innerText = q.translation_vi;

    // Render Options
    elements.practiceOptions.innerHTML = "";
    q.options.forEach(opt => {
        const btn = document.createElement("button");
        btn.className = "quiz-opt-btn";
        btn.innerText = opt;
        btn.addEventListener("click", () => handlePracticeAnswer(btn, opt === q.word));
        elements.practiceOptions.appendChild(btn);
    });
}

function handlePracticeAnswer(selectedBtn, isCorrect) {
    if (practiceState.answered) return;
    practiceState.answered = true;

    const q = practiceState.questions[practiceState.currentIdx];

    // Disable all options
    const buttons = elements.practiceOptions.querySelectorAll("button");
    buttons.forEach(btn => btn.disabled = true);

    // Apply colors
    if (isCorrect) {
        selectedBtn.classList.add("correct");
        practiceState.correctCount++;
    } else {
        selectedBtn.classList.add("incorrect");
        // Show correct
        buttons.forEach(btn => {
            if (btn.innerText === q.word) {
                btn.classList.add("correct");
            }
        });
    }

    // Show correct count
    elements.practiceScore.innerText = `Đúng: ${practiceState.correctCount}`;

    // Show Next Button
    elements.practiceNextBtn.style.display = "block";
}

function endPractice() {
    elements.practiceGame.style.display = "none";
    elements.practiceResultView.style.display = "block";

    const score = practiceState.correctCount;
    elements.practiceResultScore.innerText = `${score} / 10`;

    let desc = "";
    if (score === 10) {
        desc = "Hoàn hảo! Bạn trả lời chính xác tất cả các câu hỏi. Khả năng đọc hiểu ngữ cảnh của bạn thật phi thường!";
    } else if (score >= 8) {
        desc = "Rất tốt! Bạn hiểu rất kỹ từ vựng và vận dụng trôi chảy. Hãy thử nâng độ khó lên nhé!";
    } else if (score >= 5) {
        desc = "Tốt! Bạn đã vượt qua bài test. Đọc thêm nhiều truyện HSK để cải thiện trực giác ngữ cảnh nhé!";
    } else {
        desc = "Có vẻ cấp độ này hơi khó so với bạn. Bạn có thể chọn cấp độ thấp hơn hoặc đọc kỹ các câu truyện và học từ vựng trước khi làm lại đề thi nhé!";
    }
    elements.practiceResultDesc.innerText = desc;
}
