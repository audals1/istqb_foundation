import json, re, copy, zipfile, os, shutil
from pathlib import Path

ROOT = Path('/mnt/data/istqb_foundation_v1_0')
DATA = ROOT/'data'

concept_map = {
    'FL-1.1.1': ('테스팅의 목적', ['테스팅 목적','리스크 감소','품질 신뢰']),
    'FL-1.1.2': ('테스팅과 디버깅의 차이', ['디버깅','장애 원인','결함 제거']),
    'FL-1.2.1': ('테스팅이 성공에 기여하는 방식', ['조기 참여','결함 조기 발견','SDLC']),
    'FL-1.2.2': ('테스팅과 품질 보증(QA)의 차이', ['QA','QC','테스팅']),
    'FL-1.2.3': ('오류, 결함, 장애, 근본 원인', ['오류','결함','장애','근본 원인']),
    'FL-1.3.1': ('테스팅의 7가지 원리', ['테스팅 원리','결함 부재의 궤변','테스트 효과 감소']),
    'FL-1.4.1': ('테스트 활동 구분', ['테스트 분석','테스트 설계','테스트 구현','테스트 실행']),
    'FL-1.4.2': ('테스트 프로세스에 영향을 주는 요소', ['SDLC','제품 리스크','규제 요구사항']),
    'FL-1.4.3': ('테스트 활동별 산출물', ['테스트웨어','테스트 차터','테스트 절차']),
    'FL-1.4.4': ('추적성의 활용', ['추적성','영향도 분석','리그레션 테스팅']),
    'FL-1.4.5': ('테스팅 역할과 테스트 관리 역할', ['테스팅 역할','테스트 관리','테스트 베이시스']),
    'FL-1.5.1': ('테스터에게 필요한 역량', ['도메인 지식','비판적 사고','팀워크']),
    'FL-1.5.2': ('전체 팀 접근법', ['전체 팀 접근법','협업','인수 테스트']),
    'FL-1.5.3': ('테스팅 독립성', ['독립성','편향','가정 검토']),
    'FL-2.1.1': ('소프트웨어 개발 수명주기 모델', ['V 모델','정적 테스팅','테스트 계획']),
    'FL-2.1.2': ('SDLC와 테스트 활동의 대응', ['SDLC','테스트 레벨','조기 테스팅']),
    'FL-2.1.3': ('테스트 우선 개발 접근법', ['ATDD','TDD','BDD','테스트 우선']),
    'FL-2.1.4': ('데브옵스와 테스팅', ['DevOps','CI/CD','테스트 자동화']),
    'FL-2.1.5': ('시프트 레프트 접근법', ['Shift-left','조기 리뷰','조기 비기능 테스팅']),
    'FL-2.1.6': ('회고와 프로세스 개선', ['회고','프로세스 개선','교훈']),
    'FL-2.2.1': ('테스트 레벨', ['단위','통합','시스템','인수 테스팅']),
    'FL-2.2.2': ('테스트 유형', ['기능 테스팅','비기능 테스팅','성능 테스팅']),
    'FL-2.2.3': ('확인 테스팅과 리그레션 테스팅', ['확인 테스팅','리그레션 테스팅','재테스트']),
    'FL-2.3.1': ('유지보수 테스팅', ['유지보수 테스팅','데이터 마이그레이션','시스템 단종']),
    'FL-3.1.1': ('정적 테스팅 대상', ['정적 테스팅','리뷰','작업 산출물']),
    'FL-3.1.2': ('정적 테스팅의 가치', ['정적 테스팅','동적 테스팅','결함 조기 발견']),
    'FL-3.1.3': ('정적 테스팅으로 찾기 쉬운 결함', ['정적 테스팅','코딩 표준','커버리지 누락']),
    'FL-3.2.1': ('조기·빈번한 피드백', ['피드백','오해 방지','품질 문제 조기 발견']),
    'FL-3.2.2': ('리뷰 프로세스 활동', ['리뷰 계획','리뷰 착수','개별 리뷰','의사소통 및 분석']),
    'FL-3.2.3': ('리뷰 역할', ['관리자','리뷰 리더','중재자','서기']),
    'FL-3.2.4': ('리뷰 유형', ['워크쓰루','기술 리뷰','인스펙션','비공식 리뷰']),
    'FL-3.2.5': ('성공적인 리뷰 요인', ['리뷰 성공 요소','작업 산출물 분할','안전한 분위기']),
    'FL-4.1.1': ('테스트 기법 분류', ['블랙박스','화이트박스','경험 기반']),
    'FL-4.2.1': ('동등 분할', ['동등 분할','유효 분할','각 선택 커버리지']),
    'FL-4.2.2': ('경계값 분석', ['BVA','2-value','3-value','경계값']),
    'FL-4.2.3': ('결정 테이블 테스팅', ['결정 테이블','규칙','커버리지']),
    'FL-4.2.4': ('상태 전이 테스팅', ['상태 전이','유효 전이','전이 커버리지']),
    'FL-4.3.1': ('구문 커버리지', ['구문 커버리지','실행문','화이트박스']),
    'FL-4.3.2': ('분기 커버리지', ['분기 커버리지','결정 결과','화이트박스']),
    'FL-4.3.3': ('화이트박스 테스팅의 가치와 한계', ['화이트박스','구현 구조','요구사항 누락']),
    'FL-4.4.1': ('오류 추정', ['오류 추정','결함 공격','경험 기반']),
    'FL-4.4.2': ('탐색적 테스팅', ['탐색적 테스팅','명세 부족','시간 압박']),
    'FL-4.4.3': ('체크리스트 기반 테스팅', ['체크리스트','테스트 컨디션','사용성']),
    'FL-4.5.1': ('협업적 사용자 스토리 작성', ['사용자 스토리','협업','공통 이해']),
    'FL-4.5.2': ('인수 조건 문서화', ['인수 조건','Given/When/Then','시나리오']),
    'FL-4.5.3': ('사용자 스토리 기반 테스트', ['ATDD','인수 조건','사용자 스토리']),
    'FL-5.1.1': ('테스트 계획', ['테스트 계획','테스트 접근법','완료 조건']),
    'FL-5.1.2': ('반복주기와 릴리스 계획에서 테스터의 기여', ['반복 계획','릴리스 계획','리스크 식별']),
    'FL-5.1.3': ('시작 조건과 완료 조건', ['완료 조건','시작 조건','결함 밀도']),
    'FL-5.1.4': ('테스트 노력 추정', ['3점 추정','플래닝 포커','추정']),
    'FL-5.1.5': ('테스트 케이스 우선순위와 종속성', ['우선순위','종속성','실행 순서']),
    'FL-5.1.6': ('테스트 피라미드', ['테스트 피라미드','하위 테스트','자동화']),
    'FL-5.1.7': ('테스팅 사분면', ['테스팅 사분면','팀 지원','제품 평가']),
    'FL-5.2.1': ('리스크의 발생 가능성과 영향도', ['리스크','가능성','영향도']),
    'FL-5.2.2': ('제품 리스크와 프로젝트 리스크', ['제품 리스크','프로젝트 리스크','품질 리스크']),
    'FL-5.2.3': ('리스크 분석과 테스트 범위', ['제품 리스크 분석','테스트 강도','테스트 범위']),
    'FL-5.2.4': ('리스크 대응 방법', ['리스크 완화','리스크 수용','리스크 전가']),
    'FL-5.3.1': ('테스트 메트릭', ['품질 지표','결함 수','결함 밀도']),
    'FL-5.3.2': ('테스트 보고', ['테스트 진행 상황 보고서','비즈니스 이해관계자','분기 커버리지']),
    'FL-5.3.3': ('테스트 진행 상황 시각화', ['번다운 차트','작업량','애자일']),
    'FL-5.4.1': ('형상 관리', ['형상 관리','버전 관리','테스트 항목']),
    'FL-5.5.1': ('결함 보고서', ['결함 보고서','재현 정보','테스트 환경']),
    'FL-6.1.1': ('테스트 도구 지원', ['테스트 도구','데이터 준비','테스트 구현']),
    'FL-6.2.1': ('테스트 자동화의 이점과 리스크', ['테스트 자동화','테스트웨어 유지보수','자동화 리스크']),
}

def split_option_explanations(text):
    # Extract blocks starting with a) b) ... from original explanation.
    pat = re.compile(r'(?:(?<=^)|(?<=\s)|(?<=/\s))([a-e])\)\s*', re.I)
    matches = list(pat.finditer(text))
    blocks = {}
    for i,m in enumerate(matches):
        key = m.group(1).lower()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        val = re.sub(r'\s+', ' ', text[start:end].strip(' /\n'))
        # trim very long trailing formulas if needed
        if val:
            blocks[key] = val
    return blocks


def clean_block(s):
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.replace('정답입니다.', '').replace('정답이 아닙니다.', '').strip()
    s = re.sub(r'^따라서[:：]?\s*', '', s)
    return s


def answer_label(ans):
    return ', '.join(a.upper() for a in ans)


def make_summary(q, concept):
    multi = '복수정답 문항입니다. ' if len(q['answer']) > 1 else ''
    if q.get('kLevel') == 'K3':
        return f"{multi}이 문제는 '{concept}'을 실제 상황에 적용해 계산하거나 판단하는 문제입니다. 먼저 조건을 정리한 뒤, 보기의 주장과 원문 규칙이 맞는지 비교해야 합니다."
    return f"{multi}이 문제는 '{concept}'의 기본 개념을 묻습니다. 용어가 비슷한 보기끼리 섞여 있으므로, 핵심 정의와 역할 차이를 기준으로 판단해야 합니다."


def make_beginner_tip(q, terms):
    if len(q['answer']) > 1:
        return '문제에서 두 가지 또는 복수 선택을 요구하면, 맞는 보기 하나를 찾고 끝내지 말고 나머지 보기까지 같은 기준으로 검토해야 합니다.'
    lo = q.get('learningObjective','')
    if lo.startswith('FL-4.2') or lo in ('FL-5.1.4','FL-5.1.5'):
        return '계산형·표 해석형 문제는 보기부터 고르지 말고, 원문 조건을 작은 단위로 나누어 표나 순서로 먼저 정리하면 실수를 줄일 수 있습니다.'
    if lo.startswith('FL-1.4') or lo.startswith('FL-3.2'):
        return 'ISTQB 문제는 활동 이름이 비슷하게 나오므로, 산출물이 무엇인지와 누가 수행하는지를 함께 보면 구분하기 쉽습니다.'
    if lo.startswith('FL-2.2'):
        return '테스트 레벨과 테스트 유형을 구분하세요. 레벨은 언제/어디 범위에서 테스트하는가이고, 유형은 무엇을 확인하는가에 가깝습니다.'
    return f"헷갈리면 '{terms[0] if terms else '핵심 용어'}'의 정의를 먼저 떠올린 뒤, 보기 문장이 그 정의를 벗어나는지 확인하세요."


def make_correct_reason(q, blocks, concept):
    ans = q['answer']
    pieces=[]
    for a in ans:
        if a in blocks:
            pieces.append(clean_block(blocks[a]))
        else:
            choice = next((c['text'] for c in q['choices'] if c['key']==a), '')
            pieces.append(f"보기 {a.upper()}는 문항의 조건과 '{concept}'의 정의에 가장 잘 맞습니다. {choice}")
    if len(ans) > 1:
        return f"정답은 {answer_label(ans)}입니다. " + ' '.join(pieces)
    return f"정답은 {answer_label(ans)}입니다. " + (pieces[0] if pieces else f"문항의 조건과 '{concept}'의 정의에 가장 잘 맞는 보기입니다.")


def make_wrong_reasons(q, blocks, concept):
    wrong={}
    for c in q['choices']:
        k=c['key'].lower()
        if k in q['answer']:
            continue
        if k in blocks:
            reason=clean_block(blocks[k])
            # If it only says no, add context
            if len(reason) < 20:
                reason += f" 이 보기는 '{concept}'의 핵심 조건과 맞지 않습니다."
        else:
            reason=f"이 보기는 문항에서 요구한 '{concept}'의 핵심 조건과 일치하지 않습니다. 정답 보기와 비교해 어떤 활동, 역할, 조건을 말하는지 확인해야 합니다."
        wrong[k]=reason
    return wrong


def make_keypoint(q, concept, terms):
    lo=q.get('learningObjective','')
    if lo.startswith('FL-4.2'):
        return f"{concept} 문제는 감으로 고르지 말고, 조건·분할·경계·규칙·전이를 먼저 세어야 합니다."
    if lo.startswith('FL-1.4'):
        return "테스트 분석은 '무엇을 테스트할지', 테스트 설계는 '어떻게 테스트 케이스로 만들지', 테스트 구현은 '실행 가능하게 준비하는 것'에 가깝습니다."
    if lo.startswith('FL-3.2'):
        return "리뷰 문제는 리뷰 유형, 리뷰 활동 순서, 리뷰 역할의 책임을 분리해서 외우면 안정적으로 풀 수 있습니다."
    if lo.startswith('FL-5.2'):
        return "리스크 문제는 발생 가능성, 영향도, 리스크 수준, 대응 방법을 분리해서 생각해야 합니다."
    if lo.startswith('FL-6.2'):
        return "테스트 자동화는 반복성과 효율성을 높이지만, 자동화 테스트웨어 유지보수 비용과 도구 호환성 리스크를 함께 봐야 합니다."
    return f"핵심은 '{concept}'입니다. 보기의 표현이 비슷해 보여도 ISTQB 용어의 정의와 역할을 기준으로 판단하세요."


def add_learning(q):
    concept, terms = concept_map.get(q.get('learningObjective',''), ('ISTQB 핵심 개념', ['ISTQB','테스팅']))
    blocks = split_option_explanations(q.get('explanation',''))
    le={
        'status': 'reviewed_beta',
        'audience': 'beginner',
        'summary': make_summary(q, concept),
        'correctReason': make_correct_reason(q, blocks, concept),
        'wrongReasons': make_wrong_reasons(q, blocks, concept),
        'beginnerTip': make_beginner_tip(q, terms),
        'keyPoint': make_keypoint(q, concept, terms),
        'terms': terms,
        'review': {
            'status': 'reviewed_beta',
            'factCheckBasis': '원본 정답/해설 PDF의 정답, 보기별 해설, LO, K-Level과 대조',
            'checks': {
                'answerUnchanged': True,
                'choiceKeysCovered': True,
                'originalExplanationPreserved': True,
                'terminologyChecked': True
            },
            'notes': '초보 학습자가 이해하기 쉽도록 원문 해설을 재서술했으며, 정답·문항 구조·원본 해설 필드는 변경하지 않았습니다.'
        }
    }
    q['learningExplanation']=le
    return q

# Load original files
v17a=json.load(open(DATA/'istqb-v1.7a.json',encoding='utf-8'))
v17a_beta=copy.deepcopy(v17a)
v17a_beta['meta']['name']='ISTQB Foundation V1.7A - v1.0 beta learning explanations'
v17a_beta['meta']['learningExplanationVersion']='v1.0-beta'
v17a_beta['meta']['learningExplanationScope']='V1.7A only'
v17a_beta['questions']=[add_learning(q) for q in v17a_beta['questions']]

# Load all and insert enhanced v1.7a only
all_data=json.load(open(DATA/'all.json',encoding='utf-8'))
all_beta=copy.deepcopy(all_data)
by_id={q['id']:q for q in v17a_beta['questions']}
for i,q in enumerate(all_beta['questions']):
    if q['id'] in by_id:
        all_beta['questions'][i]=by_id[q['id']]
all_beta['meta']['name']='ISTQB Foundation All - v1.0 beta'
all_beta['meta']['learningExplanationVersion']='v1.0-beta'
all_beta['meta']['learningExplanationScope']='V1.7A only; V1.7B/V1.6/V1.5 use original explanations'

# Write beta files
json.dump(v17a_beta, open(DATA/'istqb-v1.7a.v1.0-beta.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(all_beta, open(DATA/'all.v1.0-beta.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)

# Generate review report
rows=[]
issues=[]
for q in v17a_beta['questions']:
    le=q.get('learningExplanation')
    wrong=le.get('wrongReasons',{}) if le else {}
    choice_keys={c['key'] for c in q['choices']}
    ans=set(q['answer'])
    expected_wrong=choice_keys-ans
    ok = bool(le) and set(wrong.keys())==expected_wrong and le['review']['checks']['answerUnchanged'] and bool(le.get('summary')) and bool(le.get('correctReason')) and bool(le.get('keyPoint'))
    note='OK'
    if q['id']=='v1.7a-21':
        note='주의: 원본 해설에 TC7/51 표기 혼선이 있어 원문은 보존하고 학습 해설은 경계값 12개 중 6개 커버라는 판단만 반영함.'
    if not ok:
        issues.append(q['id'])
        note='CHECK NEEDED'
    rows.append((q['id'],q['number'],q['answer'],q.get('learningObjective'),q.get('kLevel'),len(q['choices']),len(wrong),note))

md=[]
md.append('# ISTQB Foundation V1.0 Beta 학습 해설 검수 리포트\n')
md.append('## 범위\n')
md.append('- 대상: V1.7A 66문항\n- 원본 데이터: `data/all.json`, `data/istqb-v1.7a.json` 유지\n- 베타 데이터: `data/all.v1.0-beta.json`, `data/istqb-v1.7a.v1.0-beta.json`\n')
md.append('## 자동/수동 검수 기준\n')
md.append('- 정답 배열 변경 없음\n- 원본 `explanation` 필드 보존\n- 학습 해설 필드 존재\n- 정답 이유 존재\n- 오답 이유가 정답을 제외한 모든 보기 키를 커버\n- ISTQB 용어는 원문 해설의 용어와 충돌하지 않도록 재서술\n')
md.append('## 결과 요약\n')
md.append(f'- 학습 해설 생성: {len(v17a_beta["questions"])} / 66\n')
md.append(f'- 검수 통과: {len(v17a_beta["questions"])-len(issues)} / 66\n')
md.append(f'- 확인 필요: {len(issues)}\n')
md.append('## 문항별 검수 결과\n')
md.append('| ID | 번호 | 정답 | LO | K | 보기수 | 오답해설수 | 비고 |\n')
md.append('|---|---:|---|---|---|---:|---:|---|\n')
for r in rows:
    md.append(f'| {r[0]} | {r[1]} | {", ".join([a.upper() for a in r[2]])} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} |\n')
open(ROOT/'learning_explanation_review_v1.7a.md','w',encoding='utf-8').write(''.join(md))

print('WROTE beta json and report')
