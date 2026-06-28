const DATA_URLS = {
  "v1.7a": "data/istqb-v1.7a.v1.0-beta2.json",
  "v1.7b": "data/istqb-v1.7b.v1.0-beta2.json",
  "v1.6": "data/istqb-v1.6.v1.0-beta2.json",
  "v1.5": "data/istqb-v1.5.v1.0-beta2.json",
  "all": "data/all.v1.0-beta2.json",
  "random": "data/all.v1.0-beta2.json"
};

const DATASET_STATS = {
  "v1.7a": { label: "V1.7A", exam: 40, additional: 26, total: 66 },
  "v1.7b": { label: "V1.7B", exam: 40, additional: 0, total: 40 },
  "v1.6": { label: "V1.6", exam: 40, additional: 0, total: 40 },
  "v1.5": { label: "V1.5", exam: 40, additional: 0, total: 40 },
  "all": { label: "전체", exam: 160, additional: 26, total: 186 },
  "random": { label: "랜덤", exam: 160, additional: 26, total: 186 }
};

const WRONG_KEY = "istqb_wrong_ids_v5";
const BOOKMARK_KEY = "istqb_bookmarks_v5";

const state = {
  allQuestions: [],
  quiz: [],
  index: 0,
  answers: [],
  currentSelection: [],
  locked: false,
};

const $ = (id) => document.getElementById(id);
const screens = ["titleScreen", "selectScreen", "quizScreen", "resultScreen"];
function showScreen(id) {
  screens.forEach(s => $(s).classList.toggle("active", s === id));
}
function shuffle(arr) {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}
function getList(key) {
  try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch { return []; }
}
function setList(key, value) { localStorage.setItem(key, JSON.stringify([...new Set(value)])); }
function normalizeAnswer(list) { return [...list].map(x => x.toLowerCase()).sort().join(","); }
function formatAnswer(list) { return list.map(x => x.toUpperCase()).join(", "); }

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


function renderQuestionBlocks(blocks) {
  return blocks.map(block => {
    if (block.type === "paragraph") {
      const cls = block.variant === "note" ? "questionParagraph note" : "questionParagraph";
      return `<p class="${cls}">${escapeHtml(block.text)}</p>`;
    }
    if (block.type === "list") {
      const variantClass = block.variant ? String(block.variant).replace(/[^a-zA-Z0-9_-]/g, "") : "";
      const cls = ["questionList", variantClass].filter(Boolean).join(" ");
      const items = (block.items || []).map(item => `<li>${escapeHtml(item)}</li>`).join("");
      return `<ul class="${cls}">${items}</ul>`;
    }
    if (block.type === "keyValue") {
      const rows = (block.rows || []).map(row => `
        <div class="keyValueRow">
          <div class="keyValueKey">${escapeHtml(row[0])}</div>
          <div class="keyValueValue">${escapeHtml(row[1])}</div>
        </div>`).join("");
      return `
        <div class="questionKeyValue">
          ${block.title ? `<div class="questionTableCaption">${escapeHtml(block.title)}</div>` : ""}
          ${rows}
        </div>`;
    }
    if (block.type === "table") {
      const headers = (block.headers || []).map(header => `<th>${escapeHtml(header)}</th>`).join("");
      const rows = (block.rows || []).map(row => `<tr>${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("");
      return `
        <div class="questionTableWrap">
          ${block.caption ? `<div class="questionTableCaption">${escapeHtml(block.caption)}</div>` : ""}
          <div class="tableScroll" role="region" aria-label="${escapeHtml(block.caption || "문제 표")}" tabindex="0">
            <table class="questionTable">
              <thead><tr>${headers}</tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>`;
    }
    if (block.type === "report") {
      const paragraphs = (block.paragraphs || []).map(text => `<p>${escapeHtml(text)}</p>`).join("");
      const fields = (block.fields || []).map(row => `
        <div class="reportField">
          <div class="reportFieldKey">${escapeHtml(row[0])}</div>
          <div class="reportFieldValue">${escapeHtml(row[1])}</div>
        </div>`).join("");
      return `
        <div class="questionReport">
          <div class="questionReportTitle">${escapeHtml(block.title || "보고서")}</div>
          ${block.meta ? `<div class="questionReportMeta">${escapeHtml(block.meta)}</div>` : ""}
          <div class="questionReportBody">${paragraphs}${fields}</div>
        </div>`;
    }
    return "";
  }).join("");
}

function renderQuestionContent(q) {
  const el = $("questionText");
  if (q.questionBlocks && q.questionBlocks.length) {
    el.classList.add("structuredQuestion");
    el.innerHTML = renderQuestionBlocks(q.questionBlocks);
  } else {
    el.classList.remove("structuredQuestion");
    el.textContent = q.question;
  }
}

function renderLearningExplanation(q) {
  const le = q.learningExplanation;
  if (!le) {
    return `<div class="emptyLearning">이 문항은 아직 학습 해설 Beta가 없습니다. 아래 원문 해설을 확인하세요.</div>`;
  }
  const isTutor = le.mode === "tutor_explanation";
  const wrongSource = le.wrongReasonDetailed || le.wrongReasons || {};
  const wrongItems = Object.entries(wrongSource).map(([key, text]) => `
    <li><strong>${escapeHtml(key.toUpperCase())}</strong> ${escapeHtml(text)}</li>
  `).join("");
  const steps = (le.stepByStep || []).map((text, idx) => `
    <li><strong>${idx + 1}.</strong> ${escapeHtml(text)}</li>
  `).join("");
  const terms = (le.terms || []).map(term => `<span class="termChip">${escapeHtml(term)}</span>`).join("");
  if (isTutor) {
    return `
      <div class="learningBlock tutorBlock">
        <div class="betaBadge">초보자 튜터형 해설 Beta 2 · ${escapeHtml(le.status || "beta")}</div>
        <h3>이 문제가 묻는 것</h3>
        <p>${escapeHtml(le.questionIntent)}</p>
        <h3>먼저 알아야 할 개념</h3>
        <p>${escapeHtml(le.backgroundConcept)}</p>
        <h3>풀이 흐름</h3>
        <ol class="stepList">${steps}</ol>
        <h3>왜 정답인가</h3>
        <p>${escapeHtml(le.correctReasonDetailed || le.correctReason)}</p>
        <h3>왜 오답인가</h3>
        <ul class="wrongReasonList">${wrongItems}</ul>
        <h3>초보자가 빠지기 쉬운 함정</h3>
        <p>${escapeHtml(le.beginnerTrap || le.beginnerTip)}</p>
        <h3>다음에 비슷한 문제를 만났을 때</h3>
        <p>${escapeHtml(le.howToSolveNextTime || "")}</p>
        <h3>한 줄 암기 포인트</h3>
        <p class="memoryPoint">${escapeHtml(le.memoryPoint || le.keyPoint)}</p>
        <div class="termWrap">${terms}</div>
      </div>`;
  }
  return `
    <div class="learningBlock">
      <div class="betaBadge">학습 해설 Beta · ${escapeHtml(le.status || "beta")}</div>
      <h3>핵심 요약</h3>
      <p>${escapeHtml(le.summary)}</p>
      <h3>정답 이유</h3>
      <p>${escapeHtml(le.correctReason)}</p>
      <h3>오답 포인트</h3>
      <ul class="wrongReasonList">${wrongItems}</ul>
      <h3>초보자 팁</h3>
      <p>${escapeHtml(le.beginnerTip)}</p>
      <h3>한 줄 암기 포인트</h3>
      <p>${escapeHtml(le.keyPoint)}</p>
      <div class="termWrap">${terms}</div>
    </div>`;
}

function renderFeedback(q, isCorrect) {
  return `
    <div class="answerSummary">
      <strong>${isCorrect ? "정답입니다." : "오답입니다."}</strong>
      <div>내 선택: ${escapeHtml(formatAnswer(state.currentSelection))}</div>
      <div>정답: ${escapeHtml(formatAnswer(q.answer))}</div>
    </div>
    <div class="explainTabs" role="tablist" aria-label="해설 보기 방식">
      <button type="button" class="tabBtn active" data-tab="learning">학습 해설 Beta</button>
      <button type="button" class="tabBtn" data-tab="original">원문 해설</button>
    </div>
    <div class="explainPanel active" data-panel="learning">${renderLearningExplanation(q)}</div>
    <div class="explainPanel" data-panel="original">
      <h3>원문 해설</h3>
      <p>${escapeHtml(q.explanation || "해설이 없습니다.")}</p>
    </div>`;
}

function bindExplanationTabs(container) {
  const tabs = [...container.querySelectorAll(".tabBtn")];
  const panels = [...container.querySelectorAll(".explainPanel")];
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const name = tab.dataset.tab;
      tabs.forEach(t => t.classList.toggle("active", t === tab));
      panels.forEach(panel => panel.classList.toggle("active", panel.dataset.panel === name));
    });
  });
}

function scopeOptionsFor(version) {
  const stats = DATASET_STATS[version] || DATASET_STATS.all;
  const options = [];
  if (version === "all" || version === "random") {
    options.push(["all", `전체 문항 ${stats.total}문항`]);
    options.push(["exam", `본시험 전체 ${stats.exam}문항`]);
    if (stats.additional > 0) options.push(["additional", `추가문제 ${stats.additional}문항 (V1.7A 부록)`]);
    options.push(["wrong", "오답노트"]);
    return options;
  }
  options.push(["exam", `본시험 문항 ${stats.exam}문항`]);
  if (stats.additional > 0) {
    options.push(["additional", `추가문제 ${stats.additional}문항`]);
    options.push(["all", `전체 문항 ${stats.total}문항`]);
  }
  options.push(["wrong", "오답노트"]);
  return options;
}

function updateScopeOptions() {
  const version = $("versionSelect").value;
  const select = $("questionScope");
  const previous = select.value;
  const options = scopeOptionsFor(version);
  select.innerHTML = options.map(([value, label]) => `<option value="${value}">${label}</option>`).join("");
  select.value = options.some(([value]) => value === previous) ? previous : options[0][0];
  const stats = DATASET_STATS[version] || DATASET_STATS.all;
  $("scopeHint").textContent = stats.additional > 0
    ? "이 세트에는 원본 PDF 부록의 추가문제가 포함되어 있습니다."
    : "이 세트의 원본 PDF에는 추가문제 부록이 없어 본시험 문항만 표시합니다.";
}

async function loadData(versionValue) {
  const url = DATA_URLS[versionValue] || DATA_URLS["all"];
  const res = await fetch(url);
  if (!res.ok) throw new Error("데이터를 불러오지 못했습니다.");
  const data = await res.json();
  state.allQuestions = data.questions;
}

function buildQuizFromSelection() {
  const version = $("versionSelect").value;
  const scope = $("questionScope").value;
  const limit = $("limitSelect").value;
  const wrongIds = getList(WRONG_KEY);
  let questions = [...state.allQuestions];
  if (scope === "exam") questions = questions.filter(q => q.type === "exam");
  if (scope === "additional") questions = questions.filter(q => q.type === "additional");
  if (scope === "wrong") questions = questions.filter(q => wrongIds.includes(q.id));
  if (version === "random" || limit !== "all") questions = shuffle(questions);
  if (limit !== "all") questions = questions.slice(0, Number(limit));
  return questions;
}

function renderQuestion() {
  const q = state.quiz[state.index];
  state.currentSelection = [];
  state.locked = false;
  $("nextBtn").disabled = true;
  $("feedbackBox").className = "feedback hidden";
  $("feedbackBox").innerHTML = "";

  $("progressText").textContent = `${state.index + 1} / ${state.quiz.length}`;
  $("progressBar").style.width = `${((state.index + 1) / state.quiz.length) * 100}%`;
  $("metaChips").innerHTML = `
    <span class="chip">${q.version}</span>
    <span class="chip">${q.type === "exam" ? "본시험" : "추가문제"}</span>
    <span class="chip">${q.learningObjective || "LO 없음"}</span>
    <span class="chip">${q.kLevel || "K 없음"}</span>
    ${q.answer.length > 1 ? '<span class="chip">복수정답</span>' : ''}
  `;
  $("questionNumber").textContent = `문제 ${q.number}`;
  renderQuestionContent(q);

  const visualBox = $("visualBox");
  if (q.visualAsset) {
    visualBox.classList.add("active");
    visualBox.innerHTML = `<a href="${q.visualAsset}" target="_blank" rel="noopener"><img src="${q.visualAsset}" alt="문제 ${q.number} 원본 PDF 페이지 이미지"></a><p>${q.visualNote || "원본 페이지 이미지"}</p>`;
  } else {
    visualBox.classList.remove("active");
    visualBox.innerHTML = "";
  }

  $("choicesBox").innerHTML = "";
  q.choices.forEach(choice => {
    const btn = document.createElement("button");
    btn.className = "choice";
    btn.dataset.key = choice.key;
    btn.innerHTML = `<span class="key">${choice.key.toUpperCase()}</span><span>${choice.text}</span>`;
    btn.addEventListener("click", () => selectChoice(choice.key));
    $("choicesBox").appendChild(btn);
  });
  const bookmarks = getList(BOOKMARK_KEY);
  $("bookmarkBtn").textContent = bookmarks.includes(q.id) ? "북마크 해제" : "북마크";
}

function selectChoice(key) {
  if (state.locked) return;
  const q = state.quiz[state.index];
  if (q.answer.length > 1) {
    if (state.currentSelection.includes(key)) {
      state.currentSelection = state.currentSelection.filter(x => x !== key);
    } else {
      state.currentSelection.push(key);
    }
    [...document.querySelectorAll(".choice")].forEach(btn => {
      btn.classList.toggle("selected", state.currentSelection.includes(btn.dataset.key));
    });
    if (state.currentSelection.length < q.answer.length) return;
  } else {
    state.currentSelection = [key];
  }
  revealAnswer();
}

function revealAnswer() {
  const q = state.quiz[state.index];
  const selected = normalizeAnswer(state.currentSelection);
  const correct = normalizeAnswer(q.answer);
  const isCorrect = selected === correct;
  state.locked = true;
  $("nextBtn").disabled = false;

  document.querySelectorAll(".choice").forEach(btn => {
    const k = btn.dataset.key;
    btn.classList.remove("selected");
    if (q.answer.includes(k)) btn.classList.add("correct");
    if (state.currentSelection.includes(k) && !q.answer.includes(k)) btn.classList.add("wrong");
    btn.disabled = true;
  });

  state.answers[state.index] = { id: q.id, selected: [...state.currentSelection], correct: isCorrect };
  const wrongs = getList(WRONG_KEY).filter(id => id !== q.id);
  if (!isCorrect) wrongs.push(q.id);
  setList(WRONG_KEY, wrongs);

  const box = $("feedbackBox");
  box.className = `feedback ${isCorrect ? "good" : "bad"}`;
  box.innerHTML = renderFeedback(q, isCorrect);
  bindExplanationTabs(box);
}

function showResult() {
  const total = state.quiz.length;
  const correct = state.answers.filter(x => x?.correct).length;
  const wrong = total - correct;
  const rate = total ? Math.round((correct / total) * 100) : 0;
  $("scoreText").textContent = `${rate}%`;
  $("scoreDetail").textContent = `총 ${total}문항 중 ${correct}개 정답, ${wrong}개 오답`;
  $("retryWrongBtn").disabled = wrong === 0;
  showScreen("resultScreen");
}

function startQuiz(questions) {
  if (!questions.length) {
    alert("선택한 조건에 해당하는 문제가 없습니다.");
    return;
  }
  state.quiz = questions;
  state.index = 0;
  state.answers = [];
  renderQuestion();
  showScreen("quizScreen");
}

$("startBtn").addEventListener("click", () => showScreen("selectScreen"));
$("backToTitle").addEventListener("click", () => showScreen("titleScreen"));
$("exitQuizBtn").addEventListener("click", () => showScreen("selectScreen"));
$("backToSelectFromResult").addEventListener("click", () => showScreen("selectScreen"));
$("versionSelect").addEventListener("change", updateScopeOptions);
$("beginQuizBtn").addEventListener("click", async () => {
  try {
    await loadData($("versionSelect").value);
    startQuiz(buildQuizFromSelection());
  } catch (e) {
    alert(e.message + " 로컬 파일로 직접 열었다면 간단한 웹 서버에서 실행하세요.");
  }
});
$("nextBtn").addEventListener("click", () => {
  if (state.index + 1 >= state.quiz.length) showResult();
  else { state.index += 1; renderQuestion(); window.scrollTo({top:0, behavior:"smooth"}); }
});
$("restartBtn").addEventListener("click", () => startQuiz(shuffle(state.quiz)));
$("retryWrongBtn").addEventListener("click", () => {
  const wrongIds = state.answers.filter(x => !x.correct).map(x => x.id);
  const questions = state.allQuestions.filter(q => wrongIds.includes(q.id));
  startQuiz(questions);
});
$("clearWrongBtn").addEventListener("click", () => {
  setList(WRONG_KEY, []);
  alert("오답노트를 비웠습니다.");
});
$("bookmarkBtn").addEventListener("click", () => {
  const q = state.quiz[state.index];
  let bookmarks = getList(BOOKMARK_KEY);
  if (bookmarks.includes(q.id)) bookmarks = bookmarks.filter(id => id !== q.id);
  else bookmarks.push(q.id);
  setList(BOOKMARK_KEY, bookmarks);
  $("bookmarkBtn").textContent = bookmarks.includes(q.id) ? "북마크 해제" : "북마크";
});

updateScopeOptions();
