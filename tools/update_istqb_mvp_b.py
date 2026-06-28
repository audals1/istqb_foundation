import fitz
import json
import re
import os
import shutil
import csv
from pathlib import Path
from datetime import datetime
from collections import Counter

OUT = Path('/mnt/data/istqb_foundation_mvp')
QPDF_B = Path('/mnt/data/ISTQB_FL_v4.0_샘플문제_B_v1.7_한글_v1.0.pdf')
APDF_B = Path('/mnt/data/ISTQB_FL_v4.0_샘플문제_B_v1.7_정답과_해설_한글_v1.0.pdf')
A_JSON = OUT / 'data' / 'istqb-v1.7a.json'

header_patterns = [
    re.compile(r'^Korean Software Testing Qualifications Board$'),
    re.compile(r'^www\.kstqb\.org I info@kstqb\.org$'),
    re.compile(r'^\d+ of \d+$'),
    re.compile(r'^문제 Questions$'),
    re.compile(r'^정답$'),
]


def clean_line(s: str) -> str:
    s = s.replace('\u00a0', ' ')
    s = s.replace('', '•')
    s = s.replace('', '  -')
    s = s.replace('\uf0e0', '→')
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()


def is_header(line: str) -> bool:
    return any(p.match(line) for p in header_patterns)


def join_ko_lines(lines):
    out = []
    for line in lines:
        line = clean_line(line)
        if not line or is_header(line):
            continue
        if not out:
            out.append(line)
            continue
        prev = out[-1]
        starts_new = bool(re.match(
            r'^(?:•|[-]|[ivx]+\.|[A-Z]{1,4}\d{0,3}|TC\d+|P\d+|R\d+|\d+\.|\(\d+\)|규칙|조건|결과|위험 수준|프로젝트|테스트 우선순위|번호|테스트|환경 구성|시작|종료|총 테스트|Given:|When:|Then:|And:|A\.|B\.|C\.|D\.)',
            line
        ))
        # Keep choice explanations and bullets readable.
        if starts_new or prev.endswith((':', '?', '다:', '같다.', '같다:', '이다:', '했다:', '한다:')):
            out.append(line)
        else:
            if re.match(r'^(•|[ivx]+\.|a\)|b\)|c\)|d\)|e\))', prev):
                out[-1] = prev + ' ' + line
            else:
                out[-1] = prev + ' ' + line
    return out


def parse_answer_key(answer_pdf: Path, summary_pages):
    adoc = fitz.open(answer_pdf)
    lines = []
    for pi in summary_pages:
        for line in adoc.load_page(pi).get_text('text').splitlines():
            line = clean_line(line)
            if line:
                lines.append(line)
    key = {}
    i = 0
    while i < len(lines):
        q = lines[i]
        if re.fullmatch(r'(?:\d{1,2}|A\d+)', q):
            if i + 4 < len(lines):
                ans, lo, k, pt = lines[i+1], lines[i+2], lines[i+3], lines[i+4]
                if re.fullmatch(r'[a-e](?:,\s*[a-e])*', ans) and re.fullmatch(r'FL-\d+\.\d+\.\d+', lo) and re.fullmatch(r'K\d', k) and re.fullmatch(r'\d+', pt):
                    key[q] = {
                        'answer': [x.strip() for x in ans.split(',')],
                        'lo': lo,
                        'k_level': k,
                        'points': int(pt),
                    }
                    i += 5
                    continue
        i += 1
    return key


def parse_questions(question_pdf: Path, expected_qids, start_page_index=2):
    qdoc = fitz.open(question_pdf)
    raw_q_lines = []
    for pi in range(start_page_index, qdoc.page_count):
        for line in qdoc.load_page(pi).get_text('text').splitlines():
            raw_q_lines.append((pi+1, clean_line(line)))

    qid_re = re.compile(r'^(A\d+|\d{1,2})\.\s+(.*)$')
    choice_re = re.compile(r'^([a-e])\.\s*(.*)$')
    questions = []
    current = None
    expected_pos = 0
    for page, line in raw_q_lines:
        if not line or is_header(line):
            continue
        m = qid_re.match(line)
        is_expected_question_start = bool(m and expected_pos < len(expected_qids) and m.group(1) == expected_qids[expected_pos])
        if is_expected_question_start:
            if current:
                questions.append(current)
            qid, rest = m.group(1), m.group(2)
            current = {
                'raw_id': qid,
                'number': qid,
                'page': page,
                'stem_lines': [rest] if rest else [],
                'choices': [],
            }
            expected_pos += 1
            continue
        if not current:
            continue
        cm = choice_re.match(line)
        if cm:
            current['choices'].append({'key': cm.group(1), 'lines': [cm.group(2)] if cm.group(2) else []})
        else:
            if current['choices']:
                current['choices'][-1]['lines'].append(line)
            else:
                current['stem_lines'].append(line)
    if current:
        questions.append(current)
    return questions


def parse_explanations(answer_pdf: Path, answer_key, expected_qids, explanation_page_indices):
    adoc = fitz.open(answer_pdf)
    exp_lines = []
    skip = {'문제 번호', '(#)', '정답', '해설/근거', '학습목표', '(LO)', 'K-레벨', '배점', '부록: 추가 샘플 문제의 정답'}
    for pi in explanation_page_indices:
        for line in adoc.load_page(pi).get_text('text').splitlines():
            line = clean_line(line)
            if not line or line in skip or is_header(line):
                continue
            exp_lines.append(line)

    explanations = {}
    idx = 0
    for qid in expected_qids:
        if qid not in answer_key:
            continue
        while idx < len(exp_lines) and exp_lines[idx] != qid:
            idx += 1
        if idx >= len(exp_lines):
            continue
        idx += 1
        # answer line
        expected_ans = ', '.join(answer_key[qid]['answer'])
        expected_ans_nospace = ','.join(answer_key[qid]['answer'])
        if idx < len(exp_lines) and exp_lines[idx] in {expected_ans, expected_ans_nospace}:
            idx += 1
        elif idx < len(exp_lines) and re.fullmatch(r'[a-e](?:,\s*[a-e])*', exp_lines[idx]):
            idx += 1
        parts = []
        while idx < len(exp_lines):
            line = exp_lines[idx]
            if re.fullmatch(r'FL-\d+\.\d+\.\d+', line):
                idx += 1
                if idx < len(exp_lines) and re.fullmatch(r'K\d', exp_lines[idx]):
                    idx += 1
                if idx < len(exp_lines) and re.fullmatch(r'\d+', exp_lines[idx]):
                    idx += 1
                break
            parts.append(line)
            idx += 1
        explanations[qid] = '\n'.join(join_ko_lines(parts))
    return explanations


def render_visual_assets(question_pdf: Path, version_slug: str, visual_page_map):
    qdoc = fitz.open(question_pdf)
    asset_map = {}
    mat = fitz.Matrix(1.5, 1.5)
    asset_dir = OUT / 'assets'
    asset_dir.mkdir(exist_ok=True)
    prefix = version_slug.replace('.', '_')
    for qid, page_num in visual_page_map.items():
        page = qdoc.load_page(page_num - 1)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        fname = f'{prefix}_{qid.lower()}_page{page_num}.png'
        outpath = asset_dir / fname
        pix.save(outpath)
        asset_map[qid] = f'assets/{fname}'
    return asset_map


def build_bundle(question_pdf: Path, answer_pdf: Path, version: str, version_slug: str, set_name: str, expected_qids, answer_summary_pages, explanation_page_indices, visual_page_map):
    questions = parse_questions(question_pdf, expected_qids)
    answer_key = parse_answer_key(answer_pdf, answer_summary_pages)
    explanations = parse_explanations(answer_pdf, answer_key, expected_qids, explanation_page_indices)
    asset_map = render_visual_assets(question_pdf, version_slug, visual_page_map)
    final_questions = []
    for q in questions:
        qid = q['raw_id']
        qtype = 'additional' if qid.startswith('A') else 'exam'
        meta = answer_key.get(qid, {})
        item = {
            'id': f'{version_slug}-{qid.lower()}',
            'version': version,
            'set': set_name,
            'number': qid,
            'type': qtype,
            'question': '\n'.join(join_ko_lines(q['stem_lines'])),
            'choices': [{'key': c['key'], 'text': ' '.join(join_ko_lines(c['lines']))} for c in q['choices']],
            'answer': meta.get('answer', []),
            'explanation': explanations.get(qid, ''),
            'learningObjective': meta.get('lo', ''),
            'kLevel': meta.get('k_level', ''),
            'points': meta.get('points', 1),
            'source': {
                'questionPdf': question_pdf.name,
                'answerPdf': answer_pdf.name,
                'questionPage': q['page'],
            }
        }
        if qid in asset_map:
            item['visualAsset'] = asset_map[qid]
            item['visualNote'] = '이 문항은 원본 PDF의 표/그림을 함께 확인하는 것을 권장합니다.'
        final_questions.append(item)
    bundle = {
        'meta': {
            'title': 'ISTQB FOUNDATION 문제은행',
            'version': version,
            'set': set_name,
            'syllabus': 'Foundation Level v4.0.1 compatible',
            'sourceNotice': 'ISTQB 및 KSTQB 샘플문제 문서 기반. 원문 저작권 고지에 따라 출처를 표시해야 합니다.',
            'generatedAt': datetime.now().isoformat(timespec='seconds'),
            'questionCount': len(final_questions),
            'examQuestionCount': sum(1 for x in final_questions if x['type'] == 'exam'),
            'additionalQuestionCount': sum(1 for x in final_questions if x['type'] == 'additional'),
        },
        'questions': final_questions,
    }
    diagnostics = {
        'questionCount': len(final_questions),
        'answerCount': len(answer_key),
        'explanationCount': len(explanations),
        'choiceCounts': dict(Counter(len(x['choices']) for x in final_questions)),
        'visualQuestionIds': list(asset_map.keys()),
        'missingAnswers': [x['number'] for x in final_questions if not x['answer']],
        'missingExplanations': [x['number'] for x in final_questions if not x['explanation']],
        'badChoiceCounts': [x['number'] for x in final_questions if len(x['choices']) not in (4, 5)],
        'multiAnswer': [x['number'] for x in final_questions if len(x['answer']) > 1],
    }
    return bundle, diagnostics


def write_web_files():
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
          <option value="all">전체 - 현재 등록된 전체 문제</option>
          <option value="random">랜덤 - 전체 문제 셔플</option>
          <option disabled>V1.6 - 데이터 추가 예정</option>
          <option disabled>V1.5 - 데이터 추가 예정</option>
        </select>
        <label for="questionScope">범위</label>
        <select id="questionScope">
          <option value="exam">본시험 문항</option>
          <option value="additional">추가문제</option>
          <option value="all">전체 문항</option>
          <option value="wrong">오답노트</option>
        </select>
        <label for="limitSelect">문항 수</label>
        <select id="limitSelect">
          <option value="all">전체</option>
          <option value="10">랜덤 10문항</option>
          <option value="20">랜덤 20문항</option>
          <option value="40">랜덤 40문항</option>
        </select>
        <button class="primary wide" id="beginQuizBtn">문제 풀기</button>
        <p class="tiny" id="datasetHint">현재 MVP 데이터: V1.7A 66문항 + V1.7B 40문항. 표/그림이 필요한 일부 문항은 원본 페이지 이미지를 함께 표시합니다.</p>
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
  <footer class="footer">Source: ISTQB® / KSTQB Sample Exam A, B. 학습용 MVP.</footer>
  <script src="js/app.js"></script>
</body>
</html>
'''
    (OUT / 'index.html').write_text(html, encoding='utf-8')

    js = r'''const DATA_URLS = {
  "v1.7a": "data/istqb-v1.7a.json",
  "v1.7b": "data/istqb-v1.7b.json",
  "all": "data/all.json",
  "random": "data/all.json"
};
const WRONG_KEY = "istqb_wrong_ids_v2";
const BOOKMARK_KEY = "istqb_bookmarks_v2";

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
      btn.classList.toggle("correct", state.currentSelection.includes(btn.dataset.key));
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
    alert("선택한 조건에 해당하는 문제가 없습니다. V1.7B에는 현재 추가문제가 없습니다.");
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
'''
    (OUT / 'js' / 'app.js').write_text(js, encoding='utf-8')


def write_reports(b_diag, all_questions):
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
    if b_diag['questionCount'] != 40:
        warnings.append(f'V1.7B 문항 수가 40이 아닙니다: {b_diag["questionCount"]}')
    if b_diag['answerCount'] != 40:
        warnings.append(f'V1.7B 정답표 매칭 수 확인 필요: {b_diag["answerCount"]}')
    if b_diag['explanationCount'] != 40:
        warnings.append(f'V1.7B 해설 매칭 수 확인 필요: {b_diag["explanationCount"]}')
    for qid in b_diag['badChoiceCounts']:
        warnings.append(f'V1.7B {qid}: 보기 수 확인 필요')
    for qid in b_diag['missingAnswers']:
        warnings.append(f'V1.7B {qid}: 정답 누락')
    for qid in b_diag['missingExplanations']:
        warnings.append(f'V1.7B {qid}: 해설 누락')

    cnt_by_version = Counter(x['version'] for x in all_questions)
    cnt_by_type = Counter(x['type'] for x in all_questions)
    choice_count = Counter(len(x['choices']) for x in all_questions)
    md = []
    md.append('# ISTQB Foundation PDF 파싱 검증 리포트')
    md.append('')
    md.append(f'- 총 문항 수: {len(all_questions)}')
    for version in sorted(cnt_by_version):
        md.append(f'- {version}: {cnt_by_version[version]}문항')
    md.append(f'- 본시험 문항: {cnt_by_type.get("exam", 0)}')
    md.append(f'- 추가 문항: {cnt_by_type.get("additional", 0)}')
    md.append(f'- 정답 매칭: {sum(1 for x in all_questions if x["answer"])} / {len(all_questions)}')
    md.append(f'- 해설 매칭: {sum(1 for x in all_questions if x["explanation"])} / {len(all_questions)}')
    md.append(f'- 원본 표/그림 보조 이미지 포함 문항: {", ".join([x["id"] for x in all_questions if x.get("visualAsset")])}')
    md.append('')
    md.append('## V1.7B 신규 파싱 결과')
    md.append(f'- 문항 수: {b_diag["questionCount"]}')
    md.append(f'- 정답표 매칭: {b_diag["answerCount"]} / 40')
    md.append(f'- 해설 매칭: {b_diag["explanationCount"]} / 40')
    md.append(f'- 원본 표/그림 보조 이미지 포함 문항: {", ".join(b_diag["visualQuestionIds"])}')
    md.append(f'- 복수 정답 문항: {", ".join(b_diag["multiAnswer"]) if b_diag["multiAnswer"] else "없음"}')
    md.append('')
    md.append('## 주의 / 수동 확인 권장')
    if warnings:
        for w in warnings:
            md.append(f'- {w}')
    else:
        md.append('- V1.7B 자동 검증에서 큰 이상 없음')
    md.append('- 표/다이어그램 문항은 원본 페이지 이미지를 함께 제공했습니다. 모바일 화면에서는 이미지를 눌러 크게 확인하는 것을 권장합니다.')
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

    b_md = []
    b_md.append('# ISTQB Foundation V1.7B PDF 파싱 검증 리포트')
    b_md.append('')
    b_md.append(f'- 총 문항 수: {b_diag["questionCount"]}')
    b_md.append(f'- 정답표 매칭: {b_diag["answerCount"]} / 40')
    b_md.append(f'- 해설 매칭: {b_diag["explanationCount"]} / 40')
    b_md.append(f'- 보기 수 분포: {b_diag["choiceCounts"]}')
    b_md.append(f'- 원본 표/그림 보조 이미지 포함 문항: {", ".join(b_diag["visualQuestionIds"])}')
    b_md.append(f'- 복수 정답 문항: {", ".join(b_diag["multiAnswer"]) if b_diag["multiAnswer"] else "없음"}')
    b_md.append('')
    b_md.append('## 수동 확인 권장')
    if warnings:
        for w in warnings:
            b_md.append(f'- {w}')
    else:
        b_md.append('- 자동 검증에서 큰 이상 없음')
    (OUT / 'parse_report_v1.7b.md').write_text('\n'.join(b_md), encoding='utf-8')


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
- 총 106문항
- 정답, 해설, LO, K-Level 포함
- 표/그림 확인이 필요한 문항은 원본 페이지 이미지를 함께 표시

## 주요 기능

- 타이틀 화면
- 버전 선택 화면
- V1.7A / V1.7B / 전체 / 랜덤 선택
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


def write_parser_tool():
    parser = r'''"""ISTQB Sample Exam PDF parser note.

This MVP package stores parsed JSON under data/.
For future versions, reuse the parsing logic from update_istqb_mvp_b.py / build_istqb_mvp.py:
1. Extract questions by expected question number order.
2. Extract answer key from the summary table.
3. Extract explanations by question number and LO boundary.
4. Render figure/table-heavy pages as PNG assets.
5. Validate count, choices, answers, explanations, and visual assets.
"""
print("Use the parser/build script bundled in tools/ as the current reference implementation.")
'''
    (OUT / 'tools' / 'parse_istqb_pdf.py').write_text(parser, encoding='utf-8')


if __name__ == '__main__':
    (OUT / 'data').mkdir(parents=True, exist_ok=True)
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    (OUT / 'css').mkdir(parents=True, exist_ok=True)
    (OUT / 'js').mkdir(parents=True, exist_ok=True)
    (OUT / 'tools').mkdir(parents=True, exist_ok=True)

    expected_b = [str(i) for i in range(1, 41)]
    bundle_b, diag_b = build_bundle(
        question_pdf=QPDF_B,
        answer_pdf=APDF_B,
        version='V1.7B',
        version_slug='v1.7b',
        set_name='B',
        expected_qids=expected_b,
        answer_summary_pages=[2],
        explanation_page_indices=range(3, 34),
        visual_page_map={'22': 11, '23': 12, '32': 16},
    )
    (OUT / 'data' / 'istqb-v1.7b.json').write_text(json.dumps(bundle_b, ensure_ascii=False, indent=2), encoding='utf-8')

    a_data = json.loads(A_JSON.read_text(encoding='utf-8'))
    all_questions = a_data['questions'] + bundle_b['questions']
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
            'includedVersions': ['V1.7A', 'V1.7B'],
        },
        'questions': all_questions,
    }
    (OUT / 'data' / 'all.json').write_text(json.dumps(all_bundle, ensure_ascii=False, indent=2), encoding='utf-8')

    write_web_files()
    write_reports(diag_b, all_questions)
    write_readme()
    write_parser_tool()
    shutil.copy('/mnt/data/update_istqb_mvp_b.py', OUT / 'tools' / 'update_istqb_mvp_b.py')

    zip_path = shutil.make_archive('/mnt/data/istqb_foundation_mvp', 'zip', OUT)
    print('Wrote', zip_path)
    print('B diagnostics:', diag_b)
    print('All questions:', len(all_questions), Counter(x['version'] for x in all_questions))
