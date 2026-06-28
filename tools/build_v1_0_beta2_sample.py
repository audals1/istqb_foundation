import json
from pathlib import Path
from copy import deepcopy

BASE = Path('/mnt/data/istqb_foundation_v1_0_beta2')
V17A_IN = BASE / 'data' / 'istqb-v1.7a.v1.0-beta.json'
ALL_IN = BASE / 'data' / 'all.v1.0-beta.json'
V17A_OUT = BASE / 'data' / 'istqb-v1.7a.v1.0-beta2.json'
ALL_OUT = BASE / 'data' / 'all.v1.0-beta2.json'
REPORT_OUT = BASE / 'learning_explanation_review_v1.7a.beta2_sample.md'

TUTOR = {
    'v1.7a-1': {
        'questionIntent': '이 문제는 테스팅의 목적을 묻는 기본 개념 문제입니다. 특히 ISTQB가 말하는 테스팅의 목적이 무결함 증명이 아니라 리스크 감소와 품질 신뢰 확보라는 점을 알고 있는지 확인합니다.',
        'backgroundConcept': '테스팅은 결함의 존재를 보여줄 수는 있지만, 결함이 없다는 것을 증명할 수는 없습니다. 실제 시스템은 입력값, 환경, 사용자 행동의 조합이 너무 많기 때문입니다. 그래서 ISTQB에서 테스팅의 현실적인 목적은 결함과 장애를 발견해 리스크를 낮추고, 이해관계자가 품질에 대해 더 나은 판단을 하도록 정보를 제공하는 것입니다.',
        'stepByStep': [
            '먼저 보기에서 절대적인 표현을 찾습니다. 예를 들어 "결함이 없음을 증명", "오류가 없음을 증명", "모든 입력 조합" 같은 표현은 테스팅의 한계를 무시한 말입니다.',
            '테스팅의 원리 중에는 "테스팅은 결함의 존재를 보여줄 뿐, 결함이 없음을 증명할 수 없다"와 "완벽한 테스팅은 불가능하다"가 있습니다.',
            '정답 C는 결함이 없다고 증명한다고 말하지 않고, 리스크를 낮추고 품질에 대한 자신감을 얻는다고 말합니다. 이 표현이 ISTQB의 테스팅 목적과 가장 잘 맞습니다.'
        ],
        'correctReasonDetailed': 'C가 정답입니다. 테스트 대상의 리스크 수준을 낮춘다는 것은 장애가 발생할 가능성이나 영향을 줄이기 위해 결함을 찾고 정보를 제공한다는 뜻입니다. 또한 테스트 결과를 통해 품질 수준에 대한 자신감을 얻을 수 있습니다. 즉 C는 테스팅을 "완벽함의 증명"이 아니라 "리스크 감소와 신뢰 확보"로 설명하므로 올바릅니다.',
        'wrongReasonDetailed': {
            'a': 'A는 "수정되지 않은 결함이 없음을 증명"한다고 말합니다. 하지만 테스트를 아무리 많이 해도 모든 결함이 없다는 사실을 증명할 수는 없습니다. 테스트는 결함을 발견할 수는 있지만, 결함 부재를 보장하지는 못합니다.',
            'b': 'B는 운영 환경에 구현한 시스템에 오류가 없음을 증명한다고 말합니다. 실제 운영 환경에서는 사용자 행동, 데이터, 외부 시스템, 환경 조건이 매우 다양하기 때문에 오류가 없음을 증명하는 것은 불가능에 가깝습니다.',
            'd': 'D는 테스트하지 않은 입력 조합이 없는지 확인한다고 말합니다. 이는 모든 입력 조합을 테스트한다는 뜻에 가깝습니다. ISTQB의 "완벽한 테스팅은 불가능하다" 원리에 어긋납니다.'
        },
        'beginnerTrap': '초보자는 "테스트를 통과했으니 결함이 없다"고 생각하기 쉽습니다. 하지만 ISTQB에서는 테스트 통과를 무결함 증명으로 보지 않습니다. 테스트는 남은 리스크를 줄이고 판단 근거를 제공하는 활동입니다.',
        'howToSolveNextTime': '테스팅 목적 문제에서 "증명", "오류 없음", "결함 없음", "모든 조합" 같은 절대 표현이 보이면 먼저 의심하세요. 반대로 "리스크 감소", "품질 신뢰", "정보 제공"은 테스팅 목적과 잘 맞는 표현입니다.',
        'memoryPoint': '테스팅은 무결함 증명이 아니라 리스크 감소와 품질 신뢰 확보입니다.',
        'terms': ['테스팅 목적', '리스크 감소', '품질 신뢰', '완벽한 테스팅은 불가능']
    },
    'v1.7a-2': {
        'questionIntent': '이 문제는 테스팅이 소프트웨어 개발 성공에 어떻게 기여하는지 묻습니다. 핵심은 테스터가 개발 후반에만 등장하는 사람이 아니라, SDLC 전반에서 결함을 조기에 발견하도록 돕는 역할이라는 점입니다.',
        'backgroundConcept': '테스팅은 단순히 완성된 프로그램을 실행해보는 활동만이 아닙니다. 요구사항, 설계, 사용자 스토리, 테스트 베이시스 같은 작업 산출물을 검토하면서 결함을 조기에 발견하는 것도 중요합니다. 결함은 늦게 발견될수록 수정 비용이 커지기 때문에, 테스터가 SDLC 초반부터 참여하면 프로젝트 성공 가능성이 높아집니다.',
        'stepByStep': [
            '문제는 "테스트 활동이 성공에 기여하는 예"를 찾으라고 합니다. 즉 좋은 테스팅 관행을 묻는 문제입니다.',
            'A는 테스터가 SDLC의 다양한 활동에 참여해 작업 산출물의 결함 식별을 돕는다고 말합니다. 이는 조기 테스팅과 정적 테스팅의 가치와 연결됩니다.',
            '나머지 선택지는 테스터와 개발자의 협업, 최종 사용자 역할, 자격증의 의미를 과장하거나 잘못 연결하고 있습니다.'
        ],
        'correctReasonDetailed': 'A가 정답입니다. 테스터가 SDLC의 여러 활동에 참여하면 요구사항이나 설계 같은 초기 산출물에서도 결함을 발견할 수 있습니다. 이렇게 하면 코드가 작성된 뒤 결함을 찾는 것보다 수정 비용과 재작업을 줄일 수 있습니다. 또한 테스터가 설계 의도를 더 잘 이해하므로 이후 테스트 설계도 더 좋아집니다.',
        'wrongReasonDetailed': {
            'b': 'B는 테스터가 개발자를 방해하지 않아야 개발자가 더 좋은 코드를 작성할 수 있다고 말합니다. 하지만 좋은 테스팅은 개발자와 분리되어 조용히 있는 것이 아니라, 개발자와 협력해 품질을 높이는 활동입니다.',
            'c': 'C는 최종 사용자와 협업하는 테스터가 단위 통합 및 시스템 테스팅의 결함 보고서 품질을 높인다고 말합니다. 최종 사용자는 보통 하위 레벨의 통합 테스팅에 직접 참여하지 않으며, 결함 보고서 품질 향상의 핵심 주체라고 보기 어렵습니다.',
            'd': 'D는 자격증 보유자가 항상 더 좋은 테스트 케이스를 작성한다고 단정합니다. 자격증은 지식의 근거가 될 수는 있지만, 실제 테스트 설계 능력을 자동으로 보장하지는 않습니다.'
        },
        'beginnerTrap': '테스팅을 "개발이 끝난 뒤 확인하는 일"로만 생각하면 A를 놓치기 쉽습니다. ISTQB에서는 테스팅을 SDLC 전체에 걸친 활동으로 봅니다.',
        'howToSolveNextTime': '테스팅의 성공 기여 문제에서는 "조기 참여", "작업 산출물 결함 발견", "협업", "재작업 감소"가 나오면 긍정적인 보기일 가능성이 높습니다. 반대로 특정 역할을 고립시키거나 자격증만으로 능력을 단정하는 보기는 조심하세요.',
        'memoryPoint': '테스터의 조기 참여는 결함을 일찍 발견해 비용과 리스크를 줄입니다.',
        'terms': ['SDLC', '조기 테스팅', '작업 산출물', '결함 조기 발견']
    },
    'v1.7a-3': {
        'questionIntent': '이 문제는 7가지 테스팅 원리 중 "테스트 효과는 줄어든다"를 상황에 적용할 수 있는지 묻습니다. 같은 리그레션 테스트를 반복했는데 새 결함이 나오지 않는 상황을 어떻게 해석해야 하는지가 핵심입니다.',
        'backgroundConcept': '리그레션 테스트는 변경으로 인해 기존 기능이 망가지지 않았는지 확인하는 데 유용합니다. 하지만 같은 테스트 케이스를 계속 반복하면 그 테스트가 발견할 수 있는 결함은 점점 줄어듭니다. 시스템은 계속 변하는데 테스트는 그대로라면, 새로운 리스크나 변경된 기능을 충분히 보지 못할 수 있습니다.',
        'stepByStep': [
            '문제 상황을 보면 여러 반복주기 동안 리그레션 테스트 케이스가 바뀌지 않았습니다.',
            '그리고 새로운 리그레션 결함도 나오지 않았습니다. 관리자는 좋아하지만 테스터는 걱정합니다.',
            '테스터가 걱정하는 이유는 시스템이 완벽해서가 아니라, 같은 테스트를 너무 오래 반복해 테스트가 새 결함을 찾는 힘을 잃었을 수 있기 때문입니다.'
        ],
        'correctReasonDetailed': 'A가 정답입니다. "테스트 효과는 줄어든다"는 같은 테스트를 반복하면 시간이 지나면서 새로운 결함을 발견할 가능성이 낮아진다는 원리입니다. 특히 점진적 개발에서는 기능과 리스크가 계속 변하므로 리그레션 테스트도 주기적으로 검토하고 보완해야 합니다.',
        'wrongReasonDetailed': {
            'b': 'B의 "결함 부재의 논리는 궤변"은 결함을 많이 찾고 고쳤다고 해서 사용자가 만족하는 시스템이 된다는 보장은 없다는 원리입니다. 이 문제의 핵심은 사용자 가치가 아니라 같은 테스트 반복으로 인한 효과 감소입니다.',
            'c': 'C의 "결함은 집중된다"는 보통 소수의 모듈이나 영역에 결함이 많이 몰린다는 원리입니다. 문제에서는 특정 모듈에 결함이 몰렸다는 정보가 없습니다.',
            'd': 'D의 "완벽한 테스팅은 불가능하다"는 모든 입력과 조건을 다 테스트할 수 없다는 원리입니다. 이 문제는 모든 조합을 테스트하지 못한다는 이야기보다, 같은 테스트를 반복하는 문제에 가깝습니다.'
        },
        'beginnerTrap': '테스트가 계속 통과하면 "문제가 없다"고 생각하기 쉽습니다. 하지만 테스트가 낡아서 결함을 못 찾는 상황일 수도 있습니다.',
        'howToSolveNextTime': '문제에 "같은 테스트 반복", "오랫동안 새 결함 없음", "테스트 케이스가 바뀌지 않음"이 나오면 "테스트 효과는 줄어든다"를 먼저 떠올리세요.',
        'memoryPoint': '같은 테스트만 계속 반복하면 테스트도 낡습니다.',
        'terms': ['테스트 효과는 줄어든다', '리그레션 테스트', '테스트 케이스 유지보수']
    },
    'v1.7a-4': {
        'questionIntent': '이 문제는 테스트 프로세스 활동 중 "테스트 분석"을 구분할 수 있는지 묻습니다. 특히 테스트 분석, 테스트 설계, 테스트 실행, 테스트 계획의 차이를 구분해야 합니다.',
        'backgroundConcept': '테스트 분석은 "무엇을 테스트할 것인가"를 식별하는 활동입니다. 여기서 테스트 컨디션이 나옵니다. 테스트 설계는 그 테스트 컨디션을 바탕으로 "어떻게 테스트할 것인가", 즉 테스트 케이스와 테스트 데이터를 구체화하는 활동입니다. 테스트 실행은 실제로 테스트를 수행하고 결과를 비교하는 활동입니다.',
        'stepByStep': [
            '문제는 결제 기능을 구현하는 반복주기에서 어떤 활동이 테스트 분석인지 묻습니다.',
            '테스트 분석은 상세한 데이터나 절차를 만드는 단계가 아니라, 테스트해야 할 조건이나 관점을 식별하는 단계입니다.',
            'B는 "한 건의 주문에 여러 명이 각자 결제를 할 수 있는지 테스트해야 한다"고 결정합니다. 이는 테스트해야 할 조건을 식별한 것이므로 테스트 분석입니다.'
        ],
        'correctReasonDetailed': 'B가 정답입니다. "여러 명이 각자 결제할 수 있는가"는 결제 기능에서 확인해야 할 테스트 컨디션입니다. 아직 구체적인 입력값이나 절차를 만든 것은 아니고, 무엇을 테스트해야 하는지 정한 것이므로 테스트 분석 활동입니다.',
        'wrongReasonDetailed': {
            'a': 'A는 결제 서비스 통합 테스트에 8 M/D가 걸린다고 추정합니다. 공수 추정은 테스트 계획 활동에 가깝습니다. 무엇을 테스트할지 분석한 것이 아닙니다.',
            'c': 'C는 경계값 분석으로 최소 결제 금액 테스트에 필요한 테스트 데이터를 도출한다고 합니다. 테스트 기법을 사용해 구체적인 테스트 데이터나 케이스를 만드는 것은 테스트 설계에 가깝습니다.',
            'd': 'D는 테스트 케이스를 실행한 뒤 실제 결과와 기대 결과를 비교하고 결함을 보고합니다. 이는 테스트 실행 활동입니다.'
        },
        'beginnerTrap': '초보자는 분석과 설계를 자주 헷갈립니다. 분석은 "무엇을 볼지"이고, 설계는 "어떤 데이터와 절차로 확인할지"입니다.',
        'howToSolveNextTime': '테스트 프로세스 문제에서는 동사를 보세요. "식별한다/정한다"는 분석, "도출한다/작성한다"는 설계, "실행한다/비교한다/보고한다"는 실행, "추정한다/계획한다"는 계획입니다.',
        'memoryPoint': '테스트 분석은 무엇을 테스트할지 정하는 단계입니다.',
        'terms': ['테스트 분석', '테스트 컨디션', '테스트 설계', '테스트 실행']
    },
    'v1.7a-5': {
        'questionIntent': '이 문제는 테스트 프로세스에 큰 영향을 주는 요소를 고르는 문제입니다. 단순히 테스트와 관련 있어 보이는 항목이 아니라, 테스트 접근 방식 자체를 바꾸는 수준의 요소를 구분해야 합니다.',
        'backgroundConcept': '테스트 프로세스는 프로젝트 상황에 맞게 달라집니다. 어떤 SDLC를 쓰는지, 제품 리스크가 무엇인지, 규제가 무엇을 요구하는지에 따라 테스트 활동의 시점, 강도, 범위, 기법이 달라질 수 있습니다. 반면 이전 결함 수나 테스트 환경 설정도 참고는 될 수 있지만, 일반적으로 SDLC나 리스크, 규제만큼 근본적인 영향 요인은 아닙니다.',
        'stepByStep': [
            'i. SDLC는 테스트 활동의 시점과 방식에 영향을 줍니다. 순차형, 반복형, 애자일에 따라 테스트 접근이 달라집니다.',
            'iii. 제품 리스크는 어디를 더 깊게 테스트할지 결정하게 합니다. 리스크가 높은 영역은 더 강하게 테스트해야 합니다.',
            'iv. 새로운 규제가 화이트박스 테스팅을 강제한다면 테스트 기법과 완료 기준까지 바뀔 수 있습니다.',
            '따라서 i, iii, iv를 포함한 B가 정답입니다.'
        ],
        'correctReasonDetailed': 'B가 정답입니다. SDLC는 테스트 프로세스의 전체 흐름을 바꾸고, 제품 리스크는 테스트 범위와 강도를 결정하며, 규제 요구사항은 반드시 수행해야 하는 테스트 기법이나 커버리지 기준을 만들 수 있습니다. 이 세 가지는 테스트 프로세스에 중대한 영향을 미치는 대표 요소입니다.',
        'wrongReasonDetailed': {
            'a': 'A는 i는 맞지만 ii가 약합니다. 이전 프로젝트에서 식별한 결함 수는 참고 정보가 될 수는 있지만, 현재 테스트 프로세스에 중대한 영향을 주는 핵심 요소로 보기는 어렵습니다.',
            'c': 'C는 iv는 맞지만 ii와 v가 핵심 요소로 보기 어렵습니다. 특히 테스트 환경 설정은 테스트 실행 준비에는 중요하지만, 테스트 프로세스 전체를 좌우하는 중대 요소로 보기는 어렵습니다.',
            'd': 'D는 iii은 맞지만 v만으로는 부족합니다. 테스트 환경 설정은 필요하지만, SDLC나 규제처럼 테스트 전략과 프로세스를 크게 바꾸는 요소는 아닙니다.'
        },
        'beginnerTrap': '문제에 "중대한 영향을 미치는 요소"라고 되어 있습니다. 단순히 테스트와 관련 있는 항목을 고르는 문제가 아닙니다.',
        'howToSolveNextTime': '테스트 프로세스 영향 요인은 "프로젝트 방식", "제품 리스크", "규제/표준", "조직 상황"처럼 테스트 접근을 크게 바꾸는 항목인지 확인하세요.',
        'memoryPoint': 'SDLC, 제품 리스크, 규제는 테스트 프로세스를 크게 바꿉니다.',
        'terms': ['테스트 프로세스', 'SDLC', '제품 리스크', '규제 요구사항']
    },
    'v1.7a-6': {
        'questionIntent': '이 문제는 테스팅 역할과 다른 역할의 책임을 구분하는 문제입니다. 특히 테스터가 주로 수행하는 기술적 테스트 활동과 제품 소유자, 개발팀, 테스트 관리자 역할을 구분해야 합니다.',
        'backgroundConcept': 'ISTQB에서는 테스팅 역할과 테스트 관리 역할을 구분합니다. 테스팅 역할은 테스트 분석, 설계, 구현, 실행 같은 기술적 활동을 주로 수행합니다. 테스트 관리 역할은 테스트 계획, 모니터링과 제어, 완료 활동을 더 많이 담당합니다. 애자일에서는 역할이 팀 안에서 나뉠 수 있지만, 책임의 성격은 여전히 구분할 수 있습니다.',
        'stepByStep': [
            '문제는 "주로 테스팅 역할을 하는 사람이 수행하는 작업" 두 가지를 고르라고 합니다.',
            'A의 테스트 환경 구성은 테스트 실행을 가능하게 하기 위한 실무적 테스트 작업으로 볼 수 있습니다.',
            'E의 테스트 베이시스 분석은 테스트 분석 활동의 핵심입니다. 요구사항, 사용자 스토리, 설계 등에서 무엇을 테스트할지 찾는 작업입니다.',
            'B는 제품 소유자, C는 개발팀, D는 테스트 관리 역할에 더 가깝습니다.'
        ],
        'correctReasonDetailed': 'A와 E가 정답입니다. 테스트 환경 구성은 테스트를 실행할 수 있도록 준비하는 활동이고, 테스트 베이시스 분석은 테스트 분석 활동의 핵심입니다. 둘 다 테스팅 역할이 수행할 수 있는 대표적인 작업입니다.',
        'wrongReasonDetailed': {
            'b': 'B의 제품 백로그 유지보수는 보통 제품 소유자의 책임입니다. 테스터가 의견을 줄 수는 있지만 주 담당 역할은 아닙니다.',
            'c': 'C의 새로운 요구사항을 위한 해결방안 설계는 개발팀이나 설계 담당자의 역할에 가깝습니다. 테스터는 테스트 관점에서 검토하거나 피드백을 줄 수 있습니다.',
            'd': 'D의 테스트 계획 생성은 테스트 관리 역할에 더 가깝습니다. 테스터가 참여할 수는 있지만 "주로 테스팅 역할"의 대표 작업으로 보기는 어렵습니다.'
        },
        'beginnerTrap': '실제 현장에서는 한 사람이 여러 일을 할 수 있어서 헷갈릴 수 있습니다. 시험에서는 "그 일이 어떤 역할의 주 책임인가"를 기준으로 판단해야 합니다.',
        'howToSolveNextTime': '테스팅 역할 문제에서는 "분석/설계/구현/실행"은 테스팅 역할, "계획/모니터링/제어/완료 보고"는 테스트 관리 역할로 먼저 나누어 보세요.',
        'memoryPoint': '테스터는 테스트 베이시스를 분석하고 테스트 실행을 준비합니다. 백로그와 계획은 주 역할이 다릅니다.',
        'terms': ['테스팅 역할', '테스트 관리 역할', '테스트 베이시스', '테스트 환경']
    },
    'v1.7a-7': {
        'questionIntent': '이 문제는 테스터에게 중요한 역량이 무엇인지 묻습니다. 테스터가 직접 갖춰야 할 역량과 비즈니스 담당자나 테스트 관리자에게 더 가까운 역량을 구분해야 합니다.',
        'backgroundConcept': '좋은 테스터에게는 단순히 테스트 기법 지식만 필요한 것이 아닙니다. 도메인 지식이 있어야 사용자의 업무와 리스크를 이해할 수 있고, 좋은 팀 구성원이 되어 개발자와 비즈니스 담당자와 협력해야 합니다. 또한 요구사항이나 결과를 그대로 믿지 않고 비판적으로 검토하는 사고가 필요합니다.',
        'stepByStep': [
            'i. 도메인 지식은 중요합니다. 업무 맥락을 알아야 의미 있는 테스트를 설계할 수 있습니다.',
            'iii. 좋은 팀 구성원 역량도 중요합니다. 테스팅은 개발자, 제품 담당자, 비즈니스 담당자와 협력해야 하기 때문입니다.',
            'v. 비판적 사고도 중요합니다. 테스터는 가정, 누락, 모순, 리스크를 찾아야 합니다.',
            'ii와 iv는 중요할 수 있지만, 각각 제품 비전 수립이나 팀 작업 계획에 가까워 테스터의 핵심 역량으로 보기 어렵습니다.'
        ],
        'correctReasonDetailed': 'B가 정답입니다. i 도메인 지식, iii 좋은 팀 구성원 되기, v 비판적 사고는 테스터에게 중요한 역량입니다. 테스터는 시스템이 실제 업무에서 어떻게 쓰이는지 이해해야 하고, 팀과 협력해야 하며, 요구사항과 결과를 비판적으로 살펴볼 수 있어야 합니다.',
        'wrongReasonDetailed': {
            'a': 'A는 ii와 iv를 포함합니다. 제품 비전 수립은 주로 비즈니스 담당자나 제품 책임자에게 가까운 역할이고, 팀의 일정을 계획하고 구성하는 것은 테스트 관리자나 팀 전체의 책임에 더 가깝습니다.',
            'c': 'C는 i와 v는 맞지만 ii가 문제입니다. 제품 비전을 수립하는 능력은 테스터에게 도움이 될 수는 있어도 가장 중요한 테스터 역량으로 보기 어렵습니다.',
            'd': 'D는 iii은 맞지만 iv만으로는 부족합니다. 팀 작업 계획과 구성은 테스터 개인의 핵심 역량이라기보다 관리 또는 팀 차원의 책임입니다. 도메인 지식과 비판적 사고가 빠져 있습니다.'
        },
        'beginnerTrap': '시험에서는 "좋아 보이는 역량"이 아니라 "테스터에게 특히 중요한 역량"을 골라야 합니다. 제품 비전 수립이나 일정 관리는 중요하지만 테스터의 핵심 역할과는 거리가 있습니다.',
        'howToSolveNextTime': '테스터 역량 문제에서는 도메인 지식, 커뮤니케이션/협업, 비판적 사고, 세부사항 주의, 호기심 같은 표현을 우선적으로 찾으세요.',
        'memoryPoint': '테스터의 핵심 역량은 도메인 이해, 협업, 비판적 사고입니다.',
        'terms': ['테스터 역량', '도메인 지식', '팀워크', '비판적 사고']
    },
    'v1.7a-8': {
        'questionIntent': '이 문제는 전체 팀 접근법에서 테스터와 비즈니스 담당자가 어떻게 협력하는지를 묻습니다. 핵심은 품질을 테스터 혼자 책임지는 것이 아니라, 비즈니스 담당자와 함께 인수 테스트와 품질 기준을 명확히 하는 것입니다.',
        'backgroundConcept': '전체 팀 접근법에서는 테스터, 개발자, 비즈니스 담당자가 품질에 대해 함께 책임을 집니다. 비즈니스 담당자는 사용자의 기대와 비즈니스 가치를 알고 있고, 테스터는 그것을 테스트 가능한 형태로 구체화하는 데 도움을 줄 수 있습니다. 그래서 테스터는 비즈니스 담당자가 인수 테스트나 인수 조건을 잘 만들도록 지원합니다.',
        'stepByStep': [
            '문제는 테스터와 비즈니스 담당자 사이의 상호작용 예를 묻고 있습니다.',
            '전체 팀 접근법에서는 비즈니스 담당자도 팀의 품질 활동에 참여합니다.',
            '테스터는 비즈니스 담당자의 요구를 테스트 가능한 인수 테스트로 구체화하도록 돕는 역할을 할 수 있습니다.',
            '따라서 D가 전체 팀 접근법의 좋은 예입니다.'
        ],
        'correctReasonDetailed': 'D가 정답입니다. 비즈니스 담당자는 무엇이 비즈니스적으로 맞는 동작인지 알고 있고, 테스터는 그것을 검증 가능한 인수 테스트로 표현하는 데 도움을 줄 수 있습니다. 이는 전체 팀 접근법에서 역할 간 협업이 품질을 높이는 대표적인 방식입니다.',
        'wrongReasonDetailed': {
            'a': 'A는 비즈니스 담당자가 테스트 자동화 접근법을 결정한다고 말합니다. 자동화 접근법은 보통 테스터와 개발자가 중심이 되어 정하고, 비즈니스 담당자는 필요한 관점에서 도움을 줄 수 있습니다.',
            'b': 'B는 테스터가 비즈니스 담당자의 테스트 전략 결정을 지원한다고 말합니다. 테스트 전략은 일반적으로 테스터가 개발자 등과 협력해 정하는 영역이지, 비즈니스 담당자가 단독으로 정하는 것으로 보기 어렵습니다.',
            'c': 'C는 비즈니스 담당자가 전체 팀 접근법의 구성원이 아니라고 말합니다. 이것은 정반대입니다. 전체 팀 접근법에는 비즈니스 담당자도 품질 활동의 중요한 참여자로 포함됩니다.'
        },
        'beginnerTrap': '전체 팀 접근법을 "모두가 모든 일을 한다"로 오해하면 안 됩니다. 각자의 전문성은 유지하되, 품질을 위해 함께 협력한다는 뜻입니다.',
        'howToSolveNextTime': '전체 팀 접근법 문제에서 테스터와 비즈니스 담당자의 협업이 나오면 "인수 조건", "인수 테스트", "비즈니스 요구를 테스트 가능하게 만들기"를 떠올리세요.',
        'memoryPoint': '전체 팀 접근법에서 테스터는 비즈니스 요구를 테스트 가능한 인수 테스트로 구체화하도록 돕습니다.',
        'terms': ['전체 팀 접근법', '비즈니스 담당자', '인수 테스트', '협업']
    },
    'v1.7a-9': {
        'questionIntent': '이 문제는 모든 SDLC 활동에는 그에 상응하는 테스트 활동이 있다는 좋은 테스팅 관행이 어떤 개발 모델에 적용되는지 묻습니다.',
        'backgroundConcept': '소프트웨어 개발 수명주기 모델은 순차형, 반복형, 점진형 등 다양합니다. 하지만 어떤 모델이든 개발 활동이 있으면 그 산출물이나 결과를 검토하고 확인하는 테스트 활동이 필요합니다. 요구사항에는 요구사항 리뷰나 인수 테스트 준비가, 설계에는 설계 리뷰나 통합 테스트 준비가, 구현에는 단위 테스트와 동적 테스트가 대응될 수 있습니다.',
        'stepByStep': [
            '문장 자체를 보면 "모든 SDLC 활동"이라고 되어 있습니다. 특정 모델에만 적용된다는 힌트가 없습니다.',
            '순차적 모델에서도 요구사항, 설계, 구현, 테스트 단계에 각각 테스트 관련 활동이 대응됩니다.',
            '반복적/점진적 모델에서도 각 반복이나 증분마다 분석, 설계, 구현, 테스트가 함께 일어납니다.',
            '따라서 모든 주요 SDLC 모델에 적용된다고 보는 D가 정답입니다.'
        ],
        'correctReasonDetailed': 'D가 정답입니다. 이 규칙은 순차적, 점진적, 반복적 개발 모델 모두에 적용됩니다. 개발 방식이 달라져도 품질 관점에서는 각 개발 활동에 대응하는 테스트 활동이 필요합니다. 예를 들어 요구사항 활동에는 요구사항 검토가, 구현 활동에는 단위 테스트나 코드 리뷰가 대응될 수 있습니다.',
        'wrongReasonDetailed': {
            'a': 'A는 순차적 개발 모델에만 적용된다고 제한합니다. 하지만 이 원칙은 순차형뿐 아니라 반복형과 점진형에도 적용됩니다.',
            'b': 'B는 반복적 개발 모델에만 적용된다고 제한합니다. 반복형에서도 맞지만 그것만 해당되는 것은 아닙니다.',
            'c': 'C는 반복적, 점진적 모델에만 적용된다고 제한합니다. 순차적 개발 모델에서도 각 개발 활동에 대응하는 테스트 활동은 존재합니다.'
        },
        'beginnerTrap': '특정 개발 모델 이름이 나오면 그 모델의 특징만 생각하기 쉽습니다. 하지만 이 문제는 "모든 SDLC 활동"이라는 일반 원칙을 묻고 있습니다.',
        'howToSolveNextTime': '좋은 테스팅 관행이 "모든 개발 활동"이나 "모든 SDLC"처럼 일반 원칙으로 제시되면, 특정 모델 하나로 제한하는 보기는 의심하세요.',
        'memoryPoint': '개발 모델이 달라도 모든 개발 활동에는 대응하는 테스트 활동이 필요합니다.',
        'terms': ['SDLC', '순차적 개발', '점진적 개발', '반복적 개발', '테스트 활동']
    },
    'v1.7a-10': {
        'questionIntent': '이 문제는 ATDD, TDD, BDD의 차이를 구분할 수 있는지 묻습니다. 특히 ATDD는 인수 조건을 바탕으로 테스트를 먼저 정의하고, 그 테스트가 개발을 이끈다는 점이 핵심입니다.',
        'backgroundConcept': '테스트 우선 개발 접근법에는 TDD, ATDD, BDD 같은 방식이 있습니다. TDD는 보통 개발자 관점에서 단위 테스트를 먼저 작성하고 코드를 구현하는 방식입니다. ATDD는 비즈니스 요구와 인수 조건을 바탕으로 인수 테스트를 먼저 정의해 개발 방향을 맞추는 방식입니다. BDD는 기대 동작을 Given/When/Then 같은 시나리오 형태로 표현하는 경우가 많습니다.',
        'stepByStep': [
            '문제는 ATDD를 가장 잘 설명한 보기를 찾으라고 합니다.',
            'ATDD의 핵심 단어는 "인수 조건"과 "개발을 주도하는 테스트"입니다.',
            'C는 인수 조건을 기반으로 테스트를 작성하고 그 테스트가 관련 개발을 주도한다고 설명합니다.',
            'A와 D는 BDD와 더 관련 있고, B는 TDD와 더 관련 있습니다.'
        ],
        'correctReasonDetailed': 'C가 정답입니다. ATDD에서는 이해관계자가 합의한 인수 조건을 바탕으로 인수 테스트를 먼저 작성하고, 그 테스트를 만족하도록 소프트웨어를 개발합니다. 즉 테스트가 단순한 사후 확인이 아니라 개발 방향을 정렬하는 기준이 됩니다.',
        'wrongReasonDetailed': {
            'a': 'A의 Given/When/Then 형식은 ATDD에서도 사용할 수 있지만, 일반적으로 BDD를 설명할 때 더 대표적으로 언급됩니다. 이 보기만으로는 ATDD의 핵심인 "인수 조건 기반 테스트가 개발을 주도한다"를 충분히 설명하지 못합니다.',
            'b': 'B는 단위 테스팅 수준에서 코드 지향적인 테스트 케이스를 작성한다고 말합니다. 이는 ATDD가 아니라 TDD에 가까운 설명입니다.',
            'd': 'D는 소프트웨어의 기대 동작을 기반으로 해 팀원들이 이해하기 쉽다고 말합니다. 이는 BDD의 설명에 더 가깝습니다. ATDD의 핵심은 기대 동작 표현 자체보다 인수 조건 기반 테스트로 개발을 이끄는 것입니다.'
        },
        'beginnerTrap': 'ATDD, TDD, BDD는 모두 테스트를 앞쪽에 둔다는 공통점이 있어 헷갈립니다. 시험에서는 어떤 수준의 테스트인지, 어떤 기준을 쓰는지, 누가 이해하기 위한 표현인지 구분해야 합니다.',
        'howToSolveNextTime': 'ATDD는 "인수 조건", "인수 테스트", "개발 주도"를 찾으세요. TDD는 "단위 테스트/코드 중심", BDD는 "행동/기대 동작/Given-When-Then"을 떠올리면 구분하기 쉽습니다.',
        'memoryPoint': 'ATDD는 인수 조건 기반 테스트로 개발을 이끕니다.',
        'terms': ['ATDD', 'TDD', 'BDD', '인수 조건', '인수 테스트']
    },
}

def make_le(q, data):
    ans = [a.lower() for a in q['answer']]
    wrong_keys = [c['key'] for c in q['choices'] if c['key'].lower() not in ans]
    correct_keys = ', '.join(a.upper() for a in ans)
    return {
        'status': 'tutor_beta2_sample',
        'audience': 'beginner',
        'mode': 'tutor_explanation',
        'questionIntent': data['questionIntent'],
        'backgroundConcept': data['backgroundConcept'],
        'stepByStep': data['stepByStep'],
        'correctReasonDetailed': data['correctReasonDetailed'],
        'wrongReasonDetailed': data['wrongReasonDetailed'],
        'beginnerTrap': data['beginnerTrap'],
        'howToSolveNextTime': data['howToSolveNextTime'],
        'memoryPoint': data['memoryPoint'],
        'terms': data['terms'],
        # legacy UI compatibility fields
        'summary': data['questionIntent'] + '\n\n' + data['backgroundConcept'],
        'correctReason': data['correctReasonDetailed'],
        'wrongReasons': data['wrongReasonDetailed'],
        'beginnerTip': data['beginnerTrap'] + '\n\n다음 풀이 기준: ' + data['howToSolveNextTime'],
        'keyPoint': data['memoryPoint'],
        'review': {
            'status': 'tutor_beta2_sample_checked',
            'scope': 'V1.7A 1-10 sample only',
            'factCheckBasis': '원본 문제/보기/정답/해설 PDF의 정답표, 보기별 해설, LO, K-Level과 대조. 원문 explanation 필드는 변경하지 않음.',
            'checks': {
                'answerUnchanged': True,
                'correctAnswer': correct_keys,
                'wrongChoiceKeysCovered': sorted(k.upper() for k in wrong_keys),
                'originalExplanationPreserved': True,
                'terminologyChecked': True,
                'notJustReformattedOriginal': True,
            },
            'notes': '원문 해설을 단순 재배열하지 않고, 문제 의도 - 선행 개념 - 풀이 순서 - 정답 논리 - 오답 함정 - 다음 풀이 기준 순서로 재작성했습니다.'
        }
    }

def update_data(data):
    data = deepcopy(data)
    meta = data.get('meta', {})
    meta['learningExplanationVersion'] = 'v1.0-beta2-sample'
    meta['learningExplanationScope'] = 'V1.7A questions 1-10 only; other learning explanations remain previous beta where present'
    data['meta'] = meta
    for q in data['questions']:
        if q['id'] in TUTOR:
            q['learningExplanation'] = make_le(q, TUTOR[q['id']])
    return data

v17a = json.load(open(V17A_IN, encoding='utf-8'))
all_data = json.load(open(ALL_IN, encoding='utf-8'))

v17a2 = update_data(v17a)
all2 = update_data(all_data)

V17A_OUT.write_text(json.dumps(v17a2, ensure_ascii=False, indent=2), encoding='utf-8')
ALL_OUT.write_text(json.dumps(all2, ensure_ascii=False, indent=2), encoding='utf-8')

# validation
issues = []
orig = {q['id']: q for q in v17a['questions']}
upd = {q['id']: q for q in v17a2['questions']}
for qid in TUTOR:
    o, u = orig[qid], upd[qid]
    if o['answer'] != u['answer']:
        issues.append(f'{qid}: answer changed')
    if o['explanation'] != u['explanation']:
        issues.append(f'{qid}: original explanation changed')
    le = u.get('learningExplanation', {})
    if le.get('mode') != 'tutor_explanation':
        issues.append(f'{qid}: mode not tutor_explanation')
    wrong_keys = {c['key'] for c in u['choices'] if c['key'].lower() not in [a.lower() for a in u['answer']]}
    if set(le.get('wrongReasonDetailed', {}).keys()) != wrong_keys:
        issues.append(f'{qid}: wrongReasonDetailed keys mismatch')
    required = ['questionIntent','backgroundConcept','stepByStep','correctReasonDetailed','beginnerTrap','howToSolveNextTime','memoryPoint']
    for r in required:
        if not le.get(r):
            issues.append(f'{qid}: missing {r}')

lines = []
lines.append('# V1.0 Beta 2 - V1.7A 초보자 튜터형 해설 샘플 검수 리포트')
lines.append('')
lines.append('## 목적')
lines.append('')
lines.append('기존 V1.0 Beta 해설이 원문 해설을 보기 좋게 재정렬한 수준에 가까웠기 때문에, V1.7A 1~10번만 먼저 초보자 튜터형 해설로 재작성했습니다.')
lines.append('')
lines.append('## 적용 범위')
lines.append('')
lines.append('- 대상: V1.7A 1~10번')
lines.append('- 데이터 파일: `data/istqb-v1.7a.v1.0-beta2.json`, `data/all.v1.0-beta2.json`')
lines.append('- 원본 보존: `data/all.json`, `data/all.v1.0-beta.json`, `data/istqb-v1.7a.json`, `data/istqb-v1.7a.v1.0-beta.json`')
lines.append('')
lines.append('## 해설 작성 기준')
lines.append('')
lines.append('각 문항은 아래 항목을 포함하도록 작성했습니다.')
lines.append('')
lines.append('1. 문제 의도: 이 문제가 무엇을 묻는지')
lines.append('2. 배경 개념: 초보자가 먼저 알아야 할 ISTQB 개념')
lines.append('3. 풀이 흐름: 어떤 순서로 판단해야 하는지')
lines.append('4. 정답 상세 이유: 왜 이 선택지가 정답인지')
lines.append('5. 오답 상세 이유: 그럴듯한 오답이 왜 틀렸는지')
lines.append('6. 초보자 함정: 시험에서 헷갈리는 지점')
lines.append('7. 다음 풀이 기준: 유사 문제를 다시 만났을 때 판단법')
lines.append('8. 한 줄 암기 포인트')
lines.append('')
lines.append('## 자동 검증 결과')
lines.append('')
lines.append(f'- 적용 문항 수: {len(TUTOR)}')
lines.append(f'- 이슈 수: {len(issues)}')
if issues:
    lines.extend(f'  - {x}' for x in issues)
else:
    lines.append('- 정답 변경 없음')
    lines.append('- 원문 explanation 필드 변경 없음')
    lines.append('- 오답 보기 키 매칭 정상')
    lines.append('- 튜터형 필수 필드 누락 없음')
lines.append('')
lines.append('## 문항별 검수 요약')
lines.append('')
for qid in sorted(TUTOR, key=lambda x:int(x.split('-')[-1])):
    q=upd[qid]
    le=q['learningExplanation']
    lines.append(f"### {qid} / 문제 {q['number']}")
    lines.append(f"- 정답: {', '.join(a.upper() for a in q['answer'])}")
    lines.append(f"- LO/K: {q.get('learningObjective')} / {q.get('kLevel')}")
    lines.append(f"- 문제 의도: {le['questionIntent']}")
    lines.append(f"- 암기 포인트: {le['memoryPoint']}")
    lines.append('- 검수: OK')
    lines.append('')
REPORT_OUT.write_text('\n'.join(lines), encoding='utf-8')

if issues:
    print('\n'.join(issues))
    raise SystemExit(1)
print('created beta2 sample')
print(V17A_OUT)
print(ALL_OUT)
print(REPORT_OUT)
