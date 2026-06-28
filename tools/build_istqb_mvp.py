import fitz
import json
import re
import os
import shutil
from pathlib import Path
from datetime import datetime

QUESTION_PDF = Path('/mnt/data/ISTQB_FL_v4.0_샘플문제_A_v1.7_한글_v1.0.pdf')
ANSWER_PDF = Path('/mnt/data/ISTQB_FL_v4.0_샘플문제_A_v1.7_정답과_해설_한글_v1.0.pdf')
OUT = Path('/mnt/data/istqb_foundation_mvp')
VERSION = 'V1.7A'
VERSION_SLUG = 'v1.7a'

if OUT.exists():
    shutil.rmtree(OUT)
(OUT/'data').mkdir(parents=True)
(OUT/'assets').mkdir(parents=True)
(OUT/'css').mkdir(parents=True)
(OUT/'js').mkdir(parents=True)
(OUT/'tools').mkdir(parents=True)

header_patterns = [
    re.compile(r'^Korean Software Testing Qualifications Board$'),
    re.compile(r'^www\.kstqb\.org I info@kstqb\.org$'),
    re.compile(r'^\d+ of \d+$'),
    re.compile(r'^문제 Questions$'),
    re.compile(r'^부록: 추가 문제 Additional Questions$'),
]

def clean_line(s: str) -> str:
    s = s.replace('\u00a0', ' ')
    s = s.replace('', '•')
    s = s.replace('', '  -')
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

def is_header(line: str) -> bool:
    return any(p.match(line) for p in header_patterns)

def join_ko_lines(lines):
    # Preserve list/table-ish lines while repairing wrapped prose lines.
    out = []
    for line in lines:
        line = clean_line(line)
        if not line:
            continue
        if is_header(line):
            continue
        if not out:
            out.append(line)
            continue
        prev = out[-1]
        # Keep bullets, roman list items, test-case/table rows, and quoted blocks on new lines.
        starts_new = bool(re.match(r'^(•|[-–]|[ivx]+\.|[A-Z]{1,3}\d{0,3}|TC\d+|R\d+|\d+ 라운드|조건|결과|번호|최종 점수|최종 성적|회원|반납|15회|20%|티셔츠|A\.|B\.|C\.|D\.)\b', line))
        if starts_new or prev.endswith((':', '?', '다:', '같다.', '같다:', '이다:', '했다:')):
            out.append(line)
        else:
            # If previous is a bullet/table row, append might still be wrapped text.
            if re.match(r'^(•|[ivx]+\.|a\)|b\)|c\)|d\)|e\))', prev):
                out[-1] = prev + ' ' + line
            else:
                out[-1] = prev + ' ' + line
    return out

# Extract question blocks
qid_re = re.compile(r'^(A\d+|\d{1,2})\.\s+(.*)$')
choice_re = re.compile(r'^([a-e])\.\s*(.*)$')

raw_q_lines = []
qdoc = fitz.open(QUESTION_PDF)
for pi in range(2, qdoc.page_count):  # from page 3
    for line in qdoc.load_page(pi).get_text('text').splitlines():
        raw_q_lines.append((pi+1, clean_line(line)))

questions = []
current = None
expected_qids = [str(i) for i in range(1,41)] + [f'A{i}' for i in range(1,27)]
expected_pos = 0
for page, line in raw_q_lines:
    if not line or is_header(line):
        continue
    m = qid_re.match(line)
    is_expected_question_start = False
    if m and expected_pos < len(expected_qids) and m.group(1) == expected_qids[expected_pos]:
        is_expected_question_start = True
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

# Build answer key from answer summary pages
def extract_answer_key():
    adoc = fitz.open(ANSWER_PDF)
    lines = []
    for pi in [2,25]:  # page 3 and 26
        for line in adoc.load_page(pi).get_text('text').splitlines():
            line = clean_line(line)
            if line:
                lines.append(line)
    key = {}
    i = 0
    while i < len(lines):
        q = lines[i]
        if re.fullmatch(r'(?:\d{1,2}|A\d+)', q):
            if i+4 < len(lines):
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

answer_key = extract_answer_key()

# Parse answer explanations using expected answer keys.
adoc = fitz.open(ANSWER_PDF)
exp_lines = []
for pi in list(range(3,25)) + list(range(26,39)):  # pages 4-25, 27-39, 0-based
    for line in adoc.load_page(pi).get_text('text').splitlines():
        line = clean_line(line)
        if not line:
            continue
        if line in {'문제 번호', '(#)', '정답', '해설/근거', '학습목표', '(LO)', 'K-레벨', '배점', '부록: 추가 샘플 문제의 정답'}:
            continue
        if is_header(line):
            continue
        exp_lines.append(line)

explanations = {}
idx = 0
all_qids_in_order = [str(i) for i in range(1,41)] + [f'A{i}' for i in range(1,27)]
for qid in all_qids_in_order:
    if qid not in answer_key:
        continue
    # find qid line
    while idx < len(exp_lines) and exp_lines[idx] != qid:
        idx += 1
    if idx >= len(exp_lines):
        continue
    idx += 1
    # answer line
    if idx < len(exp_lines) and exp_lines[idx] == ', '.join(answer_key[qid]['answer']):
        idx += 1
    elif idx < len(exp_lines) and exp_lines[idx] == ','.join(answer_key[qid]['answer']):
        idx += 1
    else:
        # sometimes answer can have spaces differently; do not fail.
        if idx < len(exp_lines) and re.fullmatch(r'[a-e](?:,\s*[a-e])*', exp_lines[idx]):
            idx += 1
    parts = []
    while idx < len(exp_lines):
        line = exp_lines[idx]
        if re.fullmatch(r'FL-\d+\.\d+\.\d+', line):
            # skip LO, K, points
            lo = line
            idx += 1
            if idx < len(exp_lines) and re.fullmatch(r'K\d', exp_lines[idx]): idx += 1
            if idx < len(exp_lines) and re.fullmatch(r'\d+', exp_lines[idx]): idx += 1
            break
        parts.append(line)
        idx += 1
    explanations[qid] = '\n'.join(join_ko_lines(parts))

# Render visual pages as PNGs.
visual_page_map = {
    '21': 11,
    '22': 12,
    '23': 13,
    '33': 17,
    'A20': 29,
}
asset_map = {}
zoom = 1.5
mat = fitz.Matrix(zoom, zoom)
for qid, page_num in visual_page_map.items():
    page = qdoc.load_page(page_num-1)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    fname = f'{VERSION_SLUG.replace('.', '_')}_{qid.lower()}_page{page_num}.png'
    outpath = OUT/'assets'/fname
    pix.save(outpath)
    asset_map[qid] = f'assets/{fname}'

# Assemble final JSON
final_questions = []
for q in questions:
    qid = q['raw_id']
    question_type = 'additional' if qid.startswith('A') else 'exam'
    item_id = f'{VERSION_SLUG}-{qid.lower()}'
    choices = [{'key': c['key'], 'text': ' '.join(join_ko_lines(c['lines']))} for c in q['choices']]
    stem = '\n'.join(join_ko_lines(q['stem_lines']))
    meta = answer_key.get(qid, {})
    item = {
        'id': item_id,
        'version': VERSION,
        'set': 'A',
        'number': qid,
        'type': question_type,
        'question': stem,
        'choices': choices,
        'answer': meta.get('answer', []),
        'explanation': explanations.get(qid, ''),
        'learningObjective': meta.get('lo', ''),
        'kLevel': meta.get('k_level', ''),
        'points': meta.get('points', 1),
        'source': {
            'questionPdf': QUESTION_PDF.name,
            'answerPdf': ANSWER_PDF.name,
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
        'version': VERSION,
        'set': 'A',
        'syllabus': 'Foundation Level v4.0.1 compatible',
        'sourceNotice': 'ISTQB 및 KSTQB 샘플문제 문서 기반. 원문 저작권 고지에 따라 출처를 표시해야 합니다.',
        'generatedAt': datetime.now().isoformat(timespec='seconds'),
        'questionCount': len(final_questions),
        'examQuestionCount': sum(1 for x in final_questions if x['type']=='exam'),
        'additionalQuestionCount': sum(1 for x in final_questions if x['type']=='additional'),
    },
    'questions': final_questions,
}

with open(OUT/'data'/'istqb-v1.7a.json','w',encoding='utf-8') as f:
    json.dump(bundle, f, ensure_ascii=False, indent=2)
with open(OUT/'data'/'all.json','w',encoding='utf-8') as f:
    json.dump({'meta': {**bundle['meta'], 'version': 'ALL'}, 'questions': final_questions}, f, ensure_ascii=False, indent=2)

# Validation report CSV and MD
rows = []
for item in final_questions:
    rows.append({
        'id': item['id'],
        'number': item['number'],
        'type': item['type'],
        'page': item['source']['questionPage'],
        'choices': len(item['choices']),
        'answer': ','.join(item['answer']),
        'lo': item['learningObjective'],
        'kLevel': item['kLevel'],
        'hasExplanation': bool(item['explanation']),
        'hasVisualAsset': bool(item.get('visualAsset')),
        'warnings': '; '.join([]),
    })

import csv
with open(OUT/'parse_report.csv','w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

warnings = []
if len(final_questions) != 66:
    warnings.append(f'문항 수가 66이 아닙니다: {len(final_questions)}')
for item in final_questions:
    if len(item['choices']) not in (4,5):
        warnings.append(f"{item['number']}: 보기 수 확인 필요 ({len(item['choices'])})")
    if not item['answer']:
        warnings.append(f"{item['number']}: 정답 누락")
    if not item['explanation']:
        warnings.append(f"{item['number']}: 해설 누락")
# Known source typo observed in answer explanation.
for item in final_questions:
    if item['number'] == '21' and 'TC7' in item['explanation']:
        warnings.append('21: 정답/해설 PDF의 해설에 TC7 표기가 있으나 문제 PDF 표에는 TC6까지 표시됩니다. 원문 해설을 그대로 보존했습니다.')

md = []
md.append('# ISTQB Foundation V1.7A PDF 파싱 검증 리포트')
md.append('')
md.append(f'- 총 문항 수: {len(final_questions)}')
md.append(f'- 본시험 문항: {sum(1 for x in final_questions if x["type"]=="exam")}')
md.append(f'- 추가 문항: {sum(1 for x in final_questions if x["type"]=="additional")}')
md.append(f'- 정답 매칭: {sum(1 for x in final_questions if x["answer"])} / {len(final_questions)}')
md.append(f'- 해설 매칭: {sum(1 for x in final_questions if x["explanation"])} / {len(final_questions)}')
md.append(f'- 원본 표/그림 보조 이미지 포함 문항: {", ".join(asset_map.keys())}')
md.append('')
md.append('## 주의 / 수동 확인 권장')
if warnings:
    for w in warnings:
        md.append(f'- {w}')
else:
    md.append('- 자동 검증에서 큰 이상 없음')
md.append('')
md.append('## 보기 수 분포')
from collections import Counter
cnt = Counter(len(x['choices']) for x in final_questions)
for k in sorted(cnt):
    md.append(f'- 보기 {k}개: {cnt[k]}문항')
md.append('')
md.append('## 복수 정답 문항')
for x in final_questions:
    if len(x['answer']) > 1:
        md.append(f'- {x["number"]}: {", ".join(x["answer"])}')
with open(OUT/'parse_report.md','w',encoding='utf-8') as f:
    f.write('\n'.join(md))

# Web app files
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
          <option value="all">전체 - 현재 등록된 전체 문제</option>
          <option value="random">랜덤 - 전체 문제 셔플</option>
          <option disabled>V1.7B - 데이터 추가 예정</option>
          <option disabled>V1.6 - 데이터 추가 예정</option>
          <option disabled>V1.5 - 데이터 추가 예정</option>
        </select>
        <label for="questionScope">범위</label>
        <select id="questionScope">
          <option value="exam">본시험 40문항</option>
          <option value="additional">추가문제 26문항</option>
          <option value="all">전체 66문항</option>
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
        <p class="tiny">현재 MVP 데이터: V1.7A 66문항. 표/그림이 필요한 일부 문항은 원본 페이지 이미지를 함께 표시합니다.</p>
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
  <footer class="footer">Source: ISTQB® / KSTQB Sample Exam A. 학습용 MVP.</footer>
  <script src="js/app.js"></script>
</body>
</html>
'''
(OUT/'index.html').write_text(html, encoding='utf-8')

css = r''':root {
  --bg: #f5f7fb;
  --card: #ffffff;
  --text: #172033;
  --muted: #637083;
  --line: #dbe2ee;
  --primary: #2457d6;
  --primary-dark: #1643ad;
  --good: #147a42;
  --bad: #b42318;
  --warn: #8a5a00;
  --shadow: 0 12px 32px rgba(23,32,51,.10);
}
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }
button, select { font: inherit; }
.app { width: min(720px, 100%); margin: 0 auto; min-height: calc(100vh - 42px); padding: 16px; }
.screen { display: none; animation: fade .16s ease-out; }
.screen.active { display: block; }
@keyframes fade { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.hero { min-height: calc(100vh - 100px); display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 18px; }
.eyebrow { color: var(--primary); font-weight: 800; letter-spacing: .06em; text-transform: uppercase; margin: 0; font-size: .78rem; }
h1, h2, p { margin-top: 0; }
.hero h1 { font-size: clamp(2.3rem, 11vw, 4.6rem); line-height: 1.05; letter-spacing: -.04em; margin-bottom: 0; }
.desc { color: var(--muted); font-size: 1.05rem; line-height: 1.6; max-width: 32rem; }
.card, .questionCard { background: var(--card); border: 1px solid var(--line); border-radius: 24px; box-shadow: var(--shadow); padding: 22px; }
.card label { display: block; font-weight: 800; margin: 16px 0 8px; }
select { width: 100%; border: 1px solid var(--line); border-radius: 14px; padding: 14px; background: white; color: var(--text); }
button { border: 0; border-radius: 999px; padding: 13px 18px; cursor: pointer; font-weight: 800; min-height: 48px; }
button:disabled { opacity: .45; cursor: not-allowed; }
.primary { background: var(--primary); color: white; }
.primary:hover:not(:disabled) { background: var(--primary-dark); }
.secondary { background: #eef3ff; color: var(--primary-dark); }
.ghost { background: transparent; color: var(--muted); }
.danger { color: var(--bad); }
.wide { width: 100%; margin-top: 22px; }
.topbar { display: flex; align-items: center; gap: 12px; margin: 8px 0 18px; }
.topbar h2 { margin: 0; font-size: 1.25rem; }
.quizbar { align-items: center; }
.progressWrap { flex: 1; }
.progressText { font-size: .88rem; color: var(--muted); margin-bottom: 7px; }
.progress { height: 8px; background: #e8edf6; border-radius: 999px; overflow: hidden; }
.progress span { display: block; height: 100%; width: 0%; background: var(--primary); transition: width .2s; }
.questionCard { padding: 18px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.chip { background: #f0f4fa; color: var(--muted); padding: 5px 10px; border-radius: 999px; font-size: .78rem; font-weight: 800; }
#questionNumber { font-size: 1.1rem; margin-bottom: 12px; color: var(--primary-dark); }
.question { white-space: pre-line; line-height: 1.68; font-size: 1.03rem; }
.visualBox { display: none; margin: 14px 0; }
.visualBox.active { display: block; }
.visualBox img { width: 100%; border-radius: 16px; border: 1px solid var(--line); background: white; }
.visualBox p { color: var(--muted); font-size: .86rem; margin: 8px 0 0; }
.choices { display: grid; gap: 10px; margin-top: 18px; }
.choice { display: flex; gap: 10px; text-align: left; align-items: flex-start; width: 100%; border: 1px solid var(--line); background: white; color: var(--text); border-radius: 16px; padding: 14px; font-weight: 650; line-height: 1.45; }
.choice .key { flex: 0 0 auto; display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: #eef3ff; color: var(--primary-dark); font-weight: 900; }
.choice.correct { border-color: rgba(20,122,66,.45); background: #effaf4; }
.choice.wrong { border-color: rgba(180,35,24,.45); background: #fff2f0; }
.feedback { border-radius: 18px; padding: 16px; margin: 18px 0 4px; line-height: 1.6; white-space: pre-line; }
.feedback.good { background: #effaf4; border: 1px solid rgba(20,122,66,.25); }
.feedback.bad { background: #fff2f0; border: 1px solid rgba(180,35,24,.25); }
.hidden { display: none; }
.navRow { display: flex; gap: 10px; justify-content: space-between; margin-top: 18px; }
.navRow button { flex: 1; }
.resultCard { text-align: center; }
.resultCard h1 { font-size: 2.6rem; margin-bottom: 6px; }
.resultActions { display: grid; gap: 10px; margin-top: 22px; }
.tiny { color: var(--muted); font-size: .85rem; line-height: 1.5; }
.footer { text-align: center; color: var(--muted); font-size: .78rem; padding: 10px; }
@media (max-width: 480px) {
  .app { padding: 12px; }
  .card, .questionCard { border-radius: 20px; padding: 16px; }
  .choice { padding: 13px; }
  .question { font-size: 1rem; }
  .topbar { margin-top: 0; }
}
'''
(OUT/'css'/'style.css').write_text(css, encoding='utf-8')

js = r'''const DATA_URLS = {
  "v1.7a": "data/istqb-v1.7a.json",
  "all": "data/all.json",
  "random": "data/all.json"
};
const WRONG_KEY = "istqb_wrong_ids_v1";
const BOOKMARK_KEY = "istqb_bookmarks_v1";

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
  const url = DATA_URLS[versionValue] || DATA_URLS["v1.7a"];
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
(OUT/'js'/'app.js').write_text(js, encoding='utf-8')

# Parser skeleton included for maintainability
parser = r'''"""ISTQB Sample Exam PDF -> JSON parser skeleton.
Usage:
  python parse_istqb_pdf.py --question-pdf questions.pdf --answer-pdf answers.pdf --version V1.7A --out data/istqb-v1.7a.json

This MVP parser was tuned against KSTQB Korean Sample Exam A v1.7.
For new versions, run it, inspect parse_report.csv, then adjust page ranges / visual question mapping if necessary.
"""
print("See build_istqb_mvp.py in the ChatGPT generated package for the full parser used to create this MVP.")
'''
(OUT/'tools'/'parse_istqb_pdf.py').write_text(parser, encoding='utf-8')

# Copy the full build script too, as a reproducible parser.
shutil.copy('/mnt/data/build_istqb_mvp.py', OUT/'tools'/'build_istqb_mvp.py')

# README
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
- 총 66문항
- 정답, 해설, LO, K-Level 포함
- 표/그림 확인이 필요한 문항: 21, 22, 23, 33, A20

## 주요 기능

- 타이틀 화면
- 버전 선택 화면
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
(OUT/'README.md').write_text(readme, encoding='utf-8')

# Create zip
zip_path = shutil.make_archive('/mnt/data/istqb_foundation_mvp', 'zip', OUT)
print('OUT', OUT)
print('ZIP', zip_path)
print('questions', len(final_questions), 'answers', len(answer_key), 'explanations', len(explanations))
print('choice counts', Counter(len(x['choices']) for x in final_questions))
print('warnings', warnings)
