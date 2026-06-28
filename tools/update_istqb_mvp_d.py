import sys
import json
import shutil
import csv
from pathlib import Path
from datetime import datetime
from collections import Counter

TOOLS = Path('/mnt/data/istqb_foundation_mvp/tools')
sys.path.insert(0, str(TOOLS))
import update_istqb_mvp_c as base

OUT = Path('/mnt/data/istqb_foundation_mvp')
QPDF_D = Path('/mnt/data/ISTQB_FL_v4.0_샘플문제_D_v1.5_한글_v1.0.1.pdf')
APDF_D = Path('/mnt/data/ISTQB_FL_v4.0_샘플문제_D_v1.5_정답과_해설_한글_v1.0.pdf')
JSON_FILES = [
    OUT / 'data' / 'istqb-v1.7a.json',
    OUT / 'data' / 'istqb-v1.7b.json',
    OUT / 'data' / 'istqb-v1.6.json',
]


def write_app_files():
    html = '''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ISTQB FOUNDATION 문제은행</title>
  <link rel="stylesheet" href="css/style.css" />
</head>
<body>
  <main class="app" id="app">
    <section class="screen active" id="titleScreen">
      <div class="hero">
        <p class="eyebrow">CTFL 4.0 Sample Exam Trainer</p>
        <h1>ISTQB FOUNDATION<br/>문제은행</h1>
        <p class="desc">PDF 문제은행을 JSON으로 변환해 모바일에서도 반복 풀이할 수 있는 MVP입니다.</p>
        <button class="primary" id="startBtn">시작하기</button>
      </div>
    </section>

    <section class="screen" id="selectScreen">
      <header class="topbar"><button class="ghost" id="backToTitle">←</button><h2>버전 선택</h2></header>
      <div class="card">
        <label for="versionSelect">문제 세트</label>
        <select id="versionSelect">
          <option value="v1.7a">V1.7A</option>
          <option value="v1.7b">V1.7B</option>
          <option value="v1.6">V1.6</option>
          <option value="v1.5">V1.5</option>
          <option value="all">전체 - 현재 등록된 전체 문제</option>
          <option value="random">랜덤 - 전체 문제 셔플</option>
        </select>
        <label for="questionScope">범위</label>
        <select id="questionScope"></select>
        <p class="tiny inlineHint" id="scopeHint"></p>
        <label for="limitSelect">문항 수</label>
        <select id="limitSelect">
          <option value="all">전체</option>
          <option value="10">랜덤 10문항</option>
          <option value="20">랜덤 20문항</option>
          <option value="40">랜덤 40문항</option>
        </select>
        <button class="primary wide" id="beginQuizBtn">문제 풀기</button>
        <p class="tiny" id="datasetHint">현재 MVP 데이터: V1.7A 66문항 + V1.7B 40문항 + V1.6 40문항 + V1.5 40문항, 총 186문항. 추가문제는 원본 PDF에 부록이 있는 V1.7A에만 포함됩니다.</p>
      </div>
    </section>

    <section class="screen" id="quizScreen">
      <header class="topbar quizbar">
        <button class="ghost" id="exitQuizBtn">←</button>
        <div class="progressWrap"><div class="progressText" id="progressText"></div><div class="progress"><span id="progressBar"></span></div></div>
      </header>
      <article class="questionCard">
        <div class="chips" id="metaChips"></div>
        <h2 id="questionNumber"></h2>
        <p class="question" id="questionText"></p>
        <div id="visualBox" class="visualBox"></div>
        <div class="choices" id="choicesBox"></div>
        <section class="feedback hidden" id="feedbackBox"></section>
        <div class="navRow">
          <button class="secondary" id="bookmarkBtn">북마크</button>
          <button class="primary" id="nextBtn" disabled>다음</button>
        </div>
      </article>
    </section>

    <section class="screen" id="resultScreen">
      <header class="topbar"><button class="ghost" id="backToSelectFromResult">←</button><h2>결과</h2></header>
      <div class="card resultCard">
        <h1 id="scoreText"></h1>
        <p id="scoreDetail"></p>
        <div class="resultActions">
          <button class="primary" id="retryWrongBtn">틀린 문제 다시 풀기</button>
          <button class="secondary" id="restartBtn">다시 풀기</button>
          <button class="ghost danger" id="clearWrongBtn">오답노트 비우기</button>
        </div>
      </div>
    </section>
  </main>
  <footer class="footer">Source: ISTQB® / KSTQB Sample Exam A, B, C, D. 학습용 MVP.</footer>
  <script src="js/app.js"></script>
</body>
</html>
'''
    (OUT / 'index.html').write_text(html, encoding='utf-8')

    js = r'''const DATA_URLS = {
  "v1.7a": "data/istqb-v1.7a.json",
  "v1.7b": "data/istqb-v1.7b.json",
  "v1.6": "data/istqb-v1.6.json",
  "v1.5": "data/istqb-v1.5.json",
  "all": "data/all.json",
  "random": "data/all.json"
};

const DATASET_STATS = {
  "v1.7a": { label: "V1.7A", exam: 40, additional: 26, total: 66 },
  "v1.7b": { label: "V1.7B", exam: 40, additional: 0, total: 40 },
  "v1.6": { label: "V1.6", exam: 40, additional: 0, total: 40 },
  "v1.5": { label: "V1.5", exam: 40, additional: 0, total: 40 },
  "all": { label: "전체", exam: 160, additional: 26, total: 186 },
  "random": { label: "랜덤", exam: 160, additional: 26, total: 186 }
};

const WRONG_KEY = "istqb_wrong_ids_v4";
const BOOKMARK_KEY = "istqb_bookmarks_v4";

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
  $("questionText").textContent = q.question;

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
  box.innerHTML = `${isCorrect ? "정답입니다." : "오답입니다."}\n\n내 선택: ${formatAnswer(state.currentSelection)}\n정답: ${formatAnswer(q.answer)}\n\n해설:\n${q.explanation || "해설이 없습니다."}`;
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
'''
    (OUT / 'js' / 'app.js').write_text(js, encoding='utf-8')


def write_reports(d_diag, all_questions):
    rows = []
    for item in all_questions:
        rows.append({
            'id': item['id'],
            'version': item['version'],
            'number': item['number'],
            'type': item['type'],
            'page': item['source']['questionPage'],
            'choices': len(item['choices']),
            'answer': ','.join(item['answer']),
            'lo': item['learningObjective'],
            'kLevel': item['kLevel'],
            'hasExplanation': bool(item['explanation']),
            'hasVisualAsset': bool(item.get('visualAsset')),
            'warnings': '',
        })
    with open(OUT / 'parse_report.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    warnings = []
    if d_diag['questionCount'] != 40:
        warnings.append(f'V1.5 문항 수가 40이 아닙니다: {d_diag["questionCount"]}')
    if d_diag['answerCount'] != 40:
        warnings.append(f'V1.5 정답표 매칭 수 확인 필요: {d_diag["answerCount"]}')
    if d_diag['explanationCount'] != 40:
        warnings.append(f'V1.5 해설 매칭 수 확인 필요: {d_diag["explanationCount"]}')
    for qid in d_diag['badChoiceCounts']:
        warnings.append(f'V1.5 {qid}: 보기 수 확인 필요')
    for qid in d_diag['missingAnswers']:
        warnings.append(f'V1.5 {qid}: 정답 누락')
    for qid in d_diag['missingExplanations']:
        warnings.append(f'V1.5 {qid}: 해설 누락')

    cnt_by_version = Counter(x['version'] for x in all_questions)
    cnt_by_type = Counter(x['type'] for x in all_questions)
    choice_count = Counter(len(x['choices']) for x in all_questions)
    visual_ids = [x['id'] for x in all_questions if x.get('visualAsset')]
    md = []
    md.append('# ISTQB Foundation PDF 파싱 검증 리포트')
    md.append('')
    md.append(f'- 총 문항 수: {len(all_questions)}')
    for version in ['V1.7A', 'V1.7B', 'V1.6', 'V1.5']:
        md.append(f'- {version}: {cnt_by_version.get(version, 0)}문항')
    md.append(f'- 본시험 문항: {cnt_by_type.get("exam", 0)}')
    md.append(f'- 추가 문항: {cnt_by_type.get("additional", 0)}')
    md.append(f'- 정답 매칭: {sum(1 for x in all_questions if x["answer"])} / {len(all_questions)}')
    md.append(f'- 해설 매칭: {sum(1 for x in all_questions if x["explanation"])} / {len(all_questions)}')
    md.append(f'- 원본 표/그림 보조 이미지 포함 문항: {", ".join(visual_ids)}')
    md.append('')
    md.append('## V1.5 신규 파싱 결과')
    md.append(f'- 문항 수: {d_diag["questionCount"]}')
    md.append(f'- 정답표 매칭: {d_diag["answerCount"]} / 40')
    md.append(f'- 해설 매칭: {d_diag["explanationCount"]} / 40')
    md.append(f'- 원본 표/그림 보조 이미지 포함 문항: {", ".join(d_diag["visualQuestionIds"])}')
    md.append(f'- 복수 정답 문항: {", ".join(d_diag["multiAnswer"]) if d_diag["multiAnswer"] else "없음"}')
    md.append('')
    md.append('## 추가문제 구성')
    md.append('- 현재 추가문제는 원본 PDF에 부록 추가문제가 있는 V1.7A에만 포함되어 있습니다.')
    md.append('- V1.7B, V1.6, V1.5는 업로드된 원본 기준으로 본시험 40문항만 포함합니다.')
    md.append('')
    md.append('## 주의 / 수동 확인 권장')
    if warnings:
        for w in warnings:
            md.append(f'- {w}')
    else:
        md.append('- V1.5 자동 검증에서 큰 이상 없음')
    md.append('- 표/다이어그램/그래프 문항은 원본 페이지 이미지를 함께 제공했습니다. 모바일 화면에서는 이미지를 눌러 크게 확인하는 것을 권장합니다.')
    md.append('')
    md.append('## 보기 수 분포')
    for k in sorted(choice_count):
        md.append(f'- 보기 {k}개: {choice_count[k]}문항')
    md.append('')
    md.append('## 전체 복수 정답 문항')
    for x in all_questions:
        if len(x['answer']) > 1:
            md.append(f'- {x["version"]} {x["number"]}: {", ".join(x["answer"])}')
    (OUT / 'parse_report.md').write_text('\n'.join(md), encoding='utf-8')

    d_md = []
    d_md.append('# ISTQB Foundation V1.5 PDF 파싱 검증 리포트')
    d_md.append('')
    d_md.append(f'- 총 문항 수: {d_diag["questionCount"]}')
    d_md.append(f'- 정답표 매칭: {d_diag["answerCount"]} / 40')
    d_md.append(f'- 해설 매칭: {d_diag["explanationCount"]} / 40')
    d_md.append(f'- 보기 수 분포: {d_diag["choiceCounts"]}')
    d_md.append(f'- 원본 표/그림 보조 이미지 포함 문항: {", ".join(d_diag["visualQuestionIds"])}')
    d_md.append(f'- 복수 정답 문항: {", ".join(d_diag["multiAnswer"]) if d_diag["multiAnswer"] else "없음"}')
    d_md.append('')
    d_md.append('## 수동 확인 권장')
    if warnings:
        for w in warnings:
            d_md.append(f'- {w}')
    else:
        d_md.append('- 자동 검증에서 큰 이상 없음')
    (OUT / 'parse_report_v1.5.md').write_text('\n'.join(d_md), encoding='utf-8')


def write_readme():
    readme = '''# ISTQB FOUNDATION 문제은행 MVP

## 실행 방법

정적 파일이므로 GitHub Pages에 그대로 올려도 동작합니다.
로컬에서 확인하려면 브라우저로 `index.html`을 직접 열기보다 간단한 웹 서버를 사용하세요.

```bash
python -m http.server 8000
```

그 다음 브라우저에서 `http://localhost:8000` 접속.

## 현재 포함 데이터

- V1.7A 본시험 40문항
- V1.7A 추가문제 26문항
- V1.7B 본시험 40문항
- V1.6 본시험 40문항
- V1.5 본시험 40문항
- 총 186문항
- 정답, 해설, LO, K-Level 포함
- 표/그림 확인이 필요한 문항은 원본 페이지 이미지를 함께 표시

## 주요 기능

- 타이틀 화면
- 버전 선택 화면
- V1.7A / V1.7B / V1.6 / V1.5 / 전체 / 랜덤 선택
- 버전별 범위 자동 조정: 추가문제는 V1.7A 또는 전체/랜덤에서만 표시
- 본시험 / 추가문제 / 전체 / 오답노트 선택
- 랜덤 10/20/40문항
- 정답 즉시 확인
- 해설 표시
- 오답노트 저장(localStorage)
- 틀린 문제 다시 풀기
- 모바일 대응 UI

## 확장 방향

새 PDF 버전을 추가할 때는 PDF를 JSON으로 변환한 뒤 `data/all.json`에 병합하면 됩니다.
앱 로직은 문제 데이터의 `version`, `type`, `answer`, `explanation` 필드만 맞으면 그대로 사용할 수 있습니다.
'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8')


def main():
    (OUT / 'data').mkdir(parents=True, exist_ok=True)
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    (OUT / 'css').mkdir(parents=True, exist_ok=True)
    (OUT / 'js').mkdir(parents=True, exist_ok=True)
    (OUT / 'tools').mkdir(parents=True, exist_ok=True)

    expected_d = [str(i) for i in range(1, 41)]
    bundle_d, diag_d = base.build_bundle(
        question_pdf=QPDF_D,
        answer_pdf=APDF_D,
        version='V1.5',
        version_slug='v1.5',
        set_name='D',
        expected_qids=expected_d,
        answer_summary_pages=[2],
        explanation_page_indices=range(3, 36),
        visual_page_map={'21': 12, '22': 12, '23': 13, '32': 18},
    )
    (OUT / 'data' / 'istqb-v1.5.json').write_text(json.dumps(bundle_d, ensure_ascii=False, indent=2), encoding='utf-8')

    all_questions = []
    for p in JSON_FILES:
        all_questions.extend(json.loads(p.read_text(encoding='utf-8'))['questions'])
    all_questions.extend(bundle_d['questions'])
    all_bundle = {
        'meta': {
            'title': 'ISTQB FOUNDATION 문제은행',
            'version': 'ALL',
            'set': 'ALL',
            'syllabus': 'Foundation Level v4.0.1 compatible',
            'sourceNotice': 'ISTQB 및 KSTQB 샘플문제 문서 기반. 원문 저작권 고지에 따라 출처를 표시해야 합니다.',
            'generatedAt': datetime.now().isoformat(timespec='seconds'),
            'questionCount': len(all_questions),
            'examQuestionCount': sum(1 for x in all_questions if x['type'] == 'exam'),
            'additionalQuestionCount': sum(1 for x in all_questions if x['type'] == 'additional'),
            'includedVersions': ['V1.7A', 'V1.7B', 'V1.6', 'V1.5'],
        },
        'questions': all_questions,
    }
    (OUT / 'data' / 'all.json').write_text(json.dumps(all_bundle, ensure_ascii=False, indent=2), encoding='utf-8')

    write_app_files()
    write_reports(diag_d, all_questions)
    write_readme()
    shutil.copy('/mnt/data/update_istqb_mvp_d.py', OUT / 'tools' / 'update_istqb_mvp_d.py')
    zip_path = shutil.make_archive('/mnt/data/istqb_foundation_mvp', 'zip', OUT)
    print('Wrote', zip_path)
    print('D diagnostics:', diag_d)
    print('All questions:', len(all_questions), Counter(x['version'] for x in all_questions))


if __name__ == '__main__':
    main()
