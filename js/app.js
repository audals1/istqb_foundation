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
const EXAM_DURATION_SECONDS = 60 * 60;
const EXAM_PASS_SCORE = 26;

const state = {
  mode: "study", // study | exam | review
  resultMode: "study",
  selectedMode: "study",
  allQuestions: [],
  quiz: [],
  index: 0,
  answers: [],
  currentSelection: [],
  locked: false,
  flagged: new Set(),
  examRemainingSeconds: EXAM_DURATION_SECONDS,
  examTimerId: null,
  examStartedAt: null,
  lastExam: null,
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
function normalizeAnswer(list) { return [...(list || [])].map(x => String(x).toLowerCase()).sort().join(","); }
function formatAnswer(list) { return (list || []).map(x => String(x).toUpperCase()).join(", "); }
function formatTime(seconds) {
  const safe = Math.max(0, Number(seconds || 0));
  const m = Math.floor(safe / 60);
  const s = safe % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
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
        <div class="betaBadge">초보자 튜터형 해설 · ${escapeHtml(le.status || "reviewed")}</div>
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
      <div class="betaBadge">학습 해설 · ${escapeHtml(le.status || "reviewed")}</div>
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

function renderFeedback(q, isCorrect, selectedOverride = null) {
  const selected = selectedOverride || state.currentSelection;
  return `
    <div class="answerSummary">
      <strong>${isCorrect ? "정답입니다." : "오답입니다."}</strong>
      <div>내 선택: ${selected && selected.length ? escapeHtml(formatAnswer(selected)) : "미응답"}</div>
      <div>정답: ${escapeHtml(formatAnswer(q.answer))}</div>
    </div>
    <div class="explainTabs" role="tablist" aria-label="해설 보기 방식">
      <button type="button" class="tabBtn active" data-tab="learning">학습 해설</button>
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

function getSelectedMode() {
  return document.querySelector('input[name="quizMode"]:checked')?.value || "study";
}

function scopeOptionsFor(version) {
  const stats = DATASET_STATS[version] || DATASET_STATS.all;
  const options = [];
  if (state.selectedMode === "exam") {
    if (version === "all" || version === "random") return [["exam", "본시험 전체 160문항 중 랜덤 40문항"]];
    return [["exam", `${stats.label} 본시험 40문항`]];
  }
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

function renderLimitOptions() {
  if (state.selectedMode === "exam") {
    $("limitSelect").innerHTML = `<option value="40">실전 40문항</option>`;
    $("limitSelect").disabled = true;
  } else {
    $("limitSelect").innerHTML = `
      <option value="all">전체</option>
      <option value="10">랜덤 10문항</option>
      <option value="20">랜덤 20문항</option>
      <option value="40">랜덤 40문항</option>`;
    $("limitSelect").disabled = false;
  }
}

function updateScopeOptions() {
  const version = $("versionSelect").value;
  const select = $("questionScope");
  const previous = select.value;
  const options = scopeOptionsFor(version);
  select.innerHTML = options.map(([value, label]) => `<option value="${value}">${label}</option>`).join("");
  select.value = options.some(([value]) => value === previous) ? previous : options[0][0];
  select.disabled = state.selectedMode === "exam";
  const stats = DATASET_STATS[version] || DATASET_STATS.all;
  if (state.selectedMode === "exam") {
    $("scopeHint").textContent = version === "all" || version === "random"
      ? "전체 본시험 160문항 중 40문항을 무작위로 뽑아 60분 모의고사를 시작합니다. 추가문제는 제외됩니다."
      : `${stats.label} 본시험 40문항으로 60분 모의고사를 시작합니다. 추가문제는 제외됩니다.`;
  } else {
    $("scopeHint").textContent = stats.additional > 0
      ? "이 세트에는 원본 PDF 부록의 추가문제가 포함되어 있습니다."
      : "이 세트의 원본 PDF에는 추가문제 부록이 없어 본시험 문항만 표시합니다.";
  }
}

function updateModeUI() {
  state.selectedMode = getSelectedMode();
  const isExamMode = state.selectedMode === "exam";
  document.querySelectorAll("[data-mode-card]").forEach(card => {
    card.classList.toggle("active", card.dataset.modeCard === state.selectedMode);
  });
  $("mockPreview").classList.toggle("hidden", !isExamMode);
  $("modeHint").textContent = isExamMode
    ? "모의고사 모드는 본시험 40문항, 제한시간 60분, 제출 후 채점 방식으로 진행됩니다. 풀이 중 정답과 해설은 보이지 않습니다."
    : "학습 모드는 문제를 풀자마자 정답과 튜터형 해설, 원문 해설을 함께 확인할 수 있습니다.";
  $("beginQuizBtn").disabled = false;
  $("beginQuizBtn").textContent = isExamMode ? "모의고사 시작" : "문제 풀기";
  $("datasetHint").textContent = isExamMode
    ? "모의고사 모드는 실제 CTFL 시험 흐름에 가깝게 40문항/60분/26점 이상 합격 기준으로 동작합니다."
    : "현재 V1.0 1차 완성본 기준: 총 186문항을 수록했으며, 4종 전체 문항에 초보자 튜터형 해설과 주요 문항 가독성 보정을 적용했습니다.";
  renderLimitOptions();
  updateScopeOptions();
}

async function loadData(versionValue) {
  const url = DATA_URLS[versionValue] || DATA_URLS["all"];
  const res = await fetch(url);
  if (!res.ok) throw new Error("데이터를 불러오지 못했습니다.");
  const data = await res.json();
  state.allQuestions = data.questions;
}

function buildStudyQuizFromSelection() {
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

function buildExamFromSelection() {
  const version = $("versionSelect").value;
  let questions = state.allQuestions.filter(q => q.type === "exam");
  if (version === "all" || version === "random") questions = shuffle(questions).slice(0, 40);
  return questions.slice(0, 40);
}

function stopExamTimer() {
  if (state.examTimerId) clearInterval(state.examTimerId);
  state.examTimerId = null;
}

function updateTimerText() {
  if (state.mode === "exam" && $("progressText")) {
    $("progressText").textContent = `모의고사 · ${state.index + 1} / ${state.quiz.length} · 남은 시간 ${formatTime(state.examRemainingSeconds)}`;
  }
}

function startExamTimer() {
  stopExamTimer();
  state.examTimerId = setInterval(() => {
    state.examRemainingSeconds -= 1;
    updateTimerText();
    if (state.examRemainingSeconds <= 0) submitExam(true);
  }, 1000);
}

function answerForCurrentQuestion() {
  return state.answers[state.index] || { id: state.quiz[state.index]?.id, selected: [] };
}

function saveCurrentExamSelection() {
  const q = state.quiz[state.index];
  if (!q) return;
  state.answers[state.index] = {
    ...(state.answers[state.index] || {}),
    id: q.id,
    selected: [...state.currentSelection],
  };
}

function isCurrentModeExamLike() {
  return state.mode === "exam" || state.mode === "review";
}

function renderExamNavigator() {
  const box = $("examNavigator");
  if (!isCurrentModeExamLike()) {
    box.classList.add("hidden");
    box.innerHTML = "";
    return;
  }
  box.classList.remove("hidden");
  const label = state.mode === "exam" ? "문제 이동" : "해설 이동";
  const buttons = state.quiz.map((q, idx) => {
    const ans = state.answers[idx] || { selected: [] };
    const classes = ["navDot"];
    if (idx === state.index) classes.push("current");
    if (ans.selected && ans.selected.length) classes.push("answered");
    if (state.flagged.has(q.id)) classes.push("flagged");
    return `<button type="button" class="${classes.join(" ")}" data-jump-index="${idx}" aria-label="${idx + 1}번 문제로 이동">${idx + 1}</button>`;
  }).join("");
  box.innerHTML = `
    <div class="examNavigatorHead">
      <strong>${label}</strong>
      <span>답변 완료 ${state.answers.filter(a => a?.selected?.length).length} / ${state.quiz.length}</span>
    </div>
    <div class="examNavGrid">${buttons}</div>`;
  box.querySelectorAll("[data-jump-index]").forEach(btn => {
    btn.addEventListener("click", () => {
      if (state.mode === "exam") saveCurrentExamSelection();
      state.index = Number(btn.dataset.jumpIndex);
      renderQuestion();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
}

function updateChoiceStates() {
  document.querySelectorAll(".choice").forEach(btn => {
    btn.classList.toggle("selected", state.currentSelection.includes(btn.dataset.key));
  });
}

function renderQuestion() {
  const q = state.quiz[state.index];
  const isExam = state.mode === "exam";
  const isReview = state.mode === "review";
  const saved = answerForCurrentQuestion();
  state.currentSelection = (isExam || isReview) ? [...(saved.selected || [])] : [];
  state.locked = isReview;

  $("nextBtn").disabled = false;
  $("feedbackBox").className = "feedback hidden";
  $("feedbackBox").innerHTML = "";

  if (isExam) updateTimerText();
  else $("progressText").textContent = isReview ? `해설 보기 · ${state.index + 1} / ${state.quiz.length}` : `${state.index + 1} / ${state.quiz.length}`;
  $("progressBar").style.width = `${((state.index + 1) / state.quiz.length) * 100}%`;
  $("metaChips").innerHTML = `
    <span class="chip">${q.version}</span>
    <span class="chip">${isExam ? "모의고사" : isReview ? "해설 보기" : (q.type === "exam" ? "본시험" : "추가문제")}</span>
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
    if (state.currentSelection.includes(choice.key)) btn.classList.add("selected");
    if (isReview) {
      btn.disabled = true;
      if (q.answer.includes(choice.key)) btn.classList.add("correct");
      if (state.currentSelection.includes(choice.key) && !q.answer.includes(choice.key)) btn.classList.add("wrong");
    } else {
      btn.addEventListener("click", () => selectChoice(choice.key));
    }
    $("choicesBox").appendChild(btn);
  });

  if (isReview) {
    const isCorrect = normalizeAnswer(state.currentSelection) === normalizeAnswer(q.answer);
    const box = $("feedbackBox");
    box.className = `feedback ${isCorrect ? "good" : "bad"}`;
    box.innerHTML = renderFeedback(q, isCorrect, state.currentSelection);
    bindExplanationTabs(box);
  }

  $("prevBtn").classList.toggle("hidden", !isCurrentModeExamLike());
  $("prevBtn").disabled = state.index === 0;
  $("nextBtn").textContent = isExam && state.index + 1 >= state.quiz.length
    ? "제출하기"
    : isReview && state.index + 1 >= state.quiz.length
      ? "결과로"
      : "다음";

  if (isExam) {
    $("bookmarkBtn").textContent = state.flagged.has(q.id) ? "검토 해제" : "검토 표시";
  } else {
    const bookmarks = getList(BOOKMARK_KEY);
    $("bookmarkBtn").textContent = bookmarks.includes(q.id) ? "북마크 해제" : "북마크";
  }
  renderExamNavigator();
}

function selectChoice(key) {
  if (state.mode === "review" || state.locked) return;
  const q = state.quiz[state.index];
  if (state.mode === "exam") {
    if (q.answer.length > 1) {
      if (state.currentSelection.includes(key)) {
        state.currentSelection = state.currentSelection.filter(x => x !== key);
      } else if (state.currentSelection.length < q.answer.length) {
        state.currentSelection.push(key);
      } else {
        alert(`이 문항은 ${q.answer.length}개를 선택하는 복수정답 문항입니다.`);
        return;
      }
    } else {
      state.currentSelection = [key];
    }
    saveCurrentExamSelection();
    updateChoiceStates();
    renderExamNavigator();
    return;
  }

  if (q.answer.length > 1) {
    if (state.currentSelection.includes(key)) {
      state.currentSelection = state.currentSelection.filter(x => x !== key);
    } else {
      state.currentSelection.push(key);
    }
    updateChoiceStates();
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

function finalizeExamAnswers() {
  state.answers = state.quiz.map((q, idx) => {
    const selected = state.answers[idx]?.selected || [];
    return {
      id: q.id,
      selected,
      correct: normalizeAnswer(selected) === normalizeAnswer(q.answer),
    };
  });
}

function submitExam(auto = false) {
  if (state.mode !== "exam") return;
  saveCurrentExamSelection();
  const unanswered = state.answers.filter(a => !a?.selected?.length).length;
  if (!auto && unanswered > 0) {
    const ok = confirm(`미응답 문항이 ${unanswered}개 있습니다. 그래도 제출할까요?`);
    if (!ok) return;
  } else if (!auto) {
    const ok = confirm("모의고사를 제출하고 채점할까요? 제출 후에는 풀이 중 답안을 변경할 수 없습니다.");
    if (!ok) return;
  }
  stopExamTimer();
  finalizeExamAnswers();
  showExamResult(auto);
}

function showStudyResult() {
  const total = state.quiz.length;
  const correct = state.answers.filter(x => x?.correct).length;
  const wrong = total - correct;
  const rate = total ? Math.round((correct / total) * 100) : 0;
  state.resultMode = "study";
  state.mode = "result";
  $("scoreText").textContent = `${rate}%`;
  $("scoreDetail").textContent = `총 ${total}문항 중 ${correct}개 정답, ${wrong}개 오답`;
  $("retryWrongBtn").textContent = "틀린 문제 다시 풀기";
  $("retryWrongBtn").disabled = wrong === 0;
  $("reviewAllBtn").classList.add("hidden");
  $("restartBtn").textContent = "다시 풀기";
  $("clearWrongBtn").classList.remove("hidden");
  showScreen("resultScreen");
}

function showExamResult(auto = false) {
  const total = state.quiz.length;
  const correct = state.answers.filter(x => x?.correct).length;
  const wrong = total - correct;
  const rate = total ? Math.round((correct / total) * 100) : 0;
  const passed = correct >= EXAM_PASS_SCORE;
  const usedSeconds = EXAM_DURATION_SECONDS - state.examRemainingSeconds;
  state.resultMode = "exam";
  state.mode = "result";
  state.lastExam = {
    questions: [...state.quiz],
    answers: state.answers.map(a => ({ ...a, selected: [...(a.selected || [])] })),
    flagged: [...state.flagged],
  };
  const wrongIds = state.answers.filter(a => !a.correct).map(a => a.id);
  const wrongs = getList(WRONG_KEY).filter(id => !state.quiz.some(q => q.id === id));
  setList(WRONG_KEY, [...wrongs, ...wrongIds]);

  $("scoreText").textContent = passed ? `${correct} / ${total} 합격` : `${correct} / ${total} 불합격`;
  $("scoreDetail").innerHTML = `
    <strong>${passed ? "합격 기준을 넘었습니다." : "합격 기준인 26점에 도달하지 못했습니다."}</strong><br>
    정답률 ${rate}% · 기준 ${EXAM_PASS_SCORE}/40 · 소요 시간 ${formatTime(usedSeconds)}${auto ? " · 시간 종료 자동 제출" : ""}`;
  $("retryWrongBtn").textContent = "오답 해설 보기";
  $("retryWrongBtn").disabled = wrong === 0;
  $("reviewAllBtn").classList.remove("hidden");
  $("restartBtn").textContent = "같은 문제로 다시 풀기";
  $("clearWrongBtn").classList.remove("hidden");
  showScreen("resultScreen");
}

function showResult() {
  if (state.mode === "exam") submitExam(false);
  else showStudyResult();
}

function startStudyQuiz(questions) {
  stopExamTimer();
  if (!questions.length) {
    alert("선택한 조건에 해당하는 문제가 없습니다.");
    return;
  }
  state.mode = "study";
  state.quiz = questions;
  state.index = 0;
  state.answers = [];
  state.flagged = new Set();
  renderQuestion();
  showScreen("quizScreen");
}

function startExam(questions) {
  if (!questions.length) {
    alert("모의고사에 사용할 문제가 없습니다.");
    return;
  }
  if (questions.length !== 40) {
    alert(`모의고사 모드는 40문항 기준입니다. 현재 ${questions.length}문항이 선택되었습니다.`);
    return;
  }
  state.mode = "exam";
  state.quiz = questions;
  state.index = 0;
  state.answers = questions.map(q => ({ id: q.id, selected: [] }));
  state.currentSelection = [];
  state.flagged = new Set();
  state.examRemainingSeconds = EXAM_DURATION_SECONDS;
  state.examStartedAt = Date.now();
  renderQuestion();
  showScreen("quizScreen");
  startExamTimer();
}

function startReview(questions, answers) {
  stopExamTimer();
  if (!questions.length) {
    alert("해설을 볼 문제가 없습니다.");
    return;
  }
  state.mode = "review";
  state.quiz = questions;
  state.answers = answers;
  state.index = 0;
  state.currentSelection = [];
  state.flagged = new Set(state.lastExam?.flagged || []);
  renderQuestion();
  showScreen("quizScreen");
}

function leaveQuizToSelect() {
  if (state.mode === "exam") {
    const ok = confirm("진행 중인 모의고사를 종료하고 선택 화면으로 돌아갈까요? 현재 답안은 저장되지 않습니다.");
    if (!ok) return;
  }
  stopExamTimer();
  showScreen("selectScreen");
}

$("startBtn").addEventListener("click", () => showScreen("selectScreen"));
$("backToTitle").addEventListener("click", () => showScreen("titleScreen"));
$("exitQuizBtn").addEventListener("click", leaveQuizToSelect);
$("backToSelectFromResult").addEventListener("click", () => showScreen("selectScreen"));
$("versionSelect").addEventListener("change", updateScopeOptions);

$("beginQuizBtn").addEventListener("click", async () => {
  try {
    await loadData($("versionSelect").value);
    if (state.selectedMode === "exam") startExam(buildExamFromSelection());
    else startStudyQuiz(buildStudyQuizFromSelection());
  } catch (e) {
    alert(e.message + " 로컬 파일로 직접 열었다면 간단한 웹 서버에서 실행하세요.");
  }
});

$("prevBtn").addEventListener("click", () => {
  if (!isCurrentModeExamLike() || state.index === 0) return;
  if (state.mode === "exam") saveCurrentExamSelection();
  state.index -= 1;
  renderQuestion();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

$("nextBtn").addEventListener("click", () => {
  if (state.mode === "exam") {
    saveCurrentExamSelection();
    if (state.index + 1 >= state.quiz.length) submitExam(false);
    else { state.index += 1; renderQuestion(); window.scrollTo({ top: 0, behavior: "smooth" }); }
    return;
  }
  if (state.mode === "review") {
    if (state.index + 1 >= state.quiz.length) {
      if (state.lastExam) {
        state.quiz = [...state.lastExam.questions];
        state.answers = state.lastExam.answers.map(a => ({ ...a, selected: [...(a.selected || [])] }));
      }
      showExamResult(false);
    }
    else { state.index += 1; renderQuestion(); window.scrollTo({ top: 0, behavior: "smooth" }); }
    return;
  }
  if (state.index + 1 >= state.quiz.length) showStudyResult();
  else { state.index += 1; renderQuestion(); window.scrollTo({ top: 0, behavior: "smooth" }); }
});

$("restartBtn").addEventListener("click", () => {
  if (state.resultMode === "exam" && state.lastExam) startExam([...state.lastExam.questions]);
  else startStudyQuiz(shuffle(state.quiz));
});

$("retryWrongBtn").addEventListener("click", () => {
  if (state.resultMode === "exam" && state.lastExam) {
    const pairs = state.lastExam.questions.map((q, idx) => ({ q, a: state.lastExam.answers[idx] })).filter(pair => !pair.a.correct);
    startReview(pairs.map(pair => pair.q), pairs.map(pair => pair.a));
    return;
  }
  const wrongIds = state.answers.filter(x => !x.correct).map(x => x.id);
  const questions = state.allQuestions.filter(q => wrongIds.includes(q.id));
  startStudyQuiz(questions);
});

$("reviewAllBtn").addEventListener("click", () => {
  if (!state.lastExam) return;
  startReview([...state.lastExam.questions], state.lastExam.answers.map(a => ({ ...a, selected: [...(a.selected || [])] })));
});

$("clearWrongBtn").addEventListener("click", () => {
  setList(WRONG_KEY, []);
  alert("오답노트를 비웠습니다.");
});

$("bookmarkBtn").addEventListener("click", () => {
  const q = state.quiz[state.index];
  if (state.mode === "exam") {
    if (state.flagged.has(q.id)) state.flagged.delete(q.id);
    else state.flagged.add(q.id);
    renderQuestion();
    return;
  }
  let bookmarks = getList(BOOKMARK_KEY);
  if (bookmarks.includes(q.id)) bookmarks = bookmarks.filter(id => id !== q.id);
  else bookmarks.push(q.id);
  setList(BOOKMARK_KEY, bookmarks);
  $("bookmarkBtn").textContent = bookmarks.includes(q.id) ? "북마크 해제" : "북마크";
});

document.querySelectorAll('input[name="quizMode"]').forEach(input => {
  input.addEventListener("change", updateModeUI);
});

window.addEventListener("beforeunload", (event) => {
  if (state.mode === "exam") {
    event.preventDefault();
    event.returnValue = "";
  }
});

updateModeUI();
