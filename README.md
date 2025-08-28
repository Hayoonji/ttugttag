# 🎯 LangGraph 기반 개인화 혜택 추천 RAG 시스템

> **TTUGTTAG (The Ultimate Guide To The Best Offers & Deals)**

사용자의 소비 패턴을 분석하여 개인화된 혜택과 할인 정보를 추천하는 AI 기반 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 📋 목차

- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [시스템 아키텍처](#-시스템-아키텍처)
- [설치 및 실행](#-설치-및-실행)
- [웹 인터페이스](#-웹-인터페이스)
- [테스트](#-테스트)
- [사용법](#-사용법)
- [API 구조](#-api-구조)
- [데이터 구조](#-데이터-구조)
- [기술 스택](#-기술-스택)
- [프로젝트 구조](#-프로젝트-구조)
- [예시](#-예시)
- [기여하기](#-기여하기)

## 🎯 프로젝트 개요

이 시스템은 다음과 같은 특징을 가지고 있습니다:

- **개인화 추천**: 사용자의 과거 소비 이력을 기반으로 맞춤형 혜택 추천
- **다중 검색 전략**: 직접 검색 → 벡터 검색 → 텍스트 검색 → 실시간 검색의 단계적 접근
- **실시간 정보**: Perplexity API를 통한 최신 혜택 정보 제공
- **LangGraph 워크플로우**: 체계적이고 확장 가능한 검색 파이프라인
- **웹 인터페이스**: Streamlit 기반의 직관적인 채팅 인터페이스

## ✨ 주요 기능

### 🔍 지능형 검색 시스템
- **브랜드 기반 직접 검색**: 정확한 브랜드 매칭
- **벡터 유사도 검색**: 의미적 유사성을 통한 검색
- **텍스트 기반 폴백 검색**: 키워드 매칭을 통한 검색
- **실시간 검색**: Perplexity API를 통한 최신 정보 검색

### 👤 개인화 추천
- **소비 패턴 분석**: 브랜드별, 카테고리별 선호도 분석
- **시간 가중치**: 최근 소비에 높은 가중치 부여
- **개인화 스코어링**: 사용자 맞춤형 결과 순위 결정

### 🏷️ 다중 카테고리 지원
- **카페**: 스타벅스, 투썸플레이스, 이디야 등
- **편의점**: GS25, CU, 세븐일레븐 등
- **마트**: 이마트, 홈플러스 등
- **온라인쇼핑**: 쿠팡, 지마켓, 11번가 등
- **식당**: 맥도날드, KFC, 버거킹 등
- **뷰티**: 올리브영 등
- **의료**: 온누리약국 등
- **교통**: 지하철, 버스 등

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   사용자 쿼리   │───▶│  LangGraph      │───▶│   개인화 결과   │
│                 │    │  워크플로우     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  ChromaDB       │◀───│  임베딩 API     │───▶│  Perplexity API │
│  벡터 데이터베이스│    │  (CLOVA Studio) │    │  실시간 검색     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### LangGraph 워크플로우

1. **쿼리 분석** → 2. **사용자 프로필** → 3. **검증** → 4. **직접 검색** → 5. **벡터 검색** → 6. **텍스트 검색** → 7. **개인화** → 8. **결과 생성**

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install langgraph chromadb requests numpy tqdm streamlit
```

### 2. 데이터베이스 구축

```bash
cd tools
python build_database.py
```

### 3. 시스템 실행

#### 콘솔 모드
```bash
python main_rag_system.py
```

#### 웹 인터페이스
```bash
cd web
python run_app.py
# 또는
streamlit run streamlit_app.py
```

## 🌐 웹 인터페이스

### Streamlit 웹 앱 특징

- **채팅 형태 인터페이스**: 직관적인 대화형 UI
- **실시간 시스템 상태**: 데이터베이스 연결 상태, 사용자 이력 등
- **검색 과정 시각화**: 각 단계별 진행 상황 표시
- **개인화 통계**: 사용자 소비 패턴 분석 결과
- **예시 쿼리**: 원클릭 테스트 기능

### 웹 앱 실행 방법

1. **자동 실행 스크립트 사용**:
   ```bash
   cd web
   python run_app.py
   ```

2. **직접 Streamlit 실행**:
   ```bash
   cd web
   streamlit run streamlit_app.py
   ```

3. **브라우저에서 접속**: `http://localhost:8501`

### 웹 앱 기능

- **시스템 초기화**: RAG 시스템 및 데이터베이스 연결
- **채팅 인터페이스**: 질문 입력 및 응답 확인
- **실시간 통계**: 검색 횟수, 시스템 상태 등
- **디버그 모드**: 상세한 검색 과정 확인
- **사용자 이력**: 개인화된 소비 패턴 분석

## 🧪 테스트

### 자동 테스트 스크립트

```bash
cd test
python test_rag_system.py
```

### 테스트 내용

1. **시스템 초기화 테스트**: RAG 시스템 및 데이터베이스 연결
2. **사용자 이력 생성 테스트**: 샘플 데이터 생성 및 분석
3. **쿼리 테스트**: 다양한 검색 시나리오 테스트
4. **성능 테스트**: 응답 시간 및 성공률 측정
5. **개별 컴포넌트 테스트**: API, 파서 등 개별 모듈 테스트

### 테스트 시나리오

- 브랜드별 직접 검색
- 개인화 추천
- 카테고리별 검색
- 소비 기반 추천
- 실시간 검색 (DB에 없는 항목)

## 📖 사용법

### 기본 사용법

```python
from tools.main_rag_system import LangGraphRAGSystem

# 시스템 초기화
rag = LangGraphRAGSystem()

# 데이터베이스 연결
rag.connect_database()

# 쿼리 실행
result = rag.run("스타벅스 할인 혜택 있어?", debug=True)
print(result)
```

### 대화형 모드

```bash
python main_rag_system.py
```

실행 후 다음과 같은 쿼리를 입력할 수 있습니다:

- `"스타벅스 할인 혜택 있어?"`
- `"내 소비 패턴에 맞는 혜택 추천해줘"`
- `"카페 할인 이벤트 궁금해"`
- `"편의점 쿠폰 있나?"`

## 🔌 API 구조

### PerplexityAPI
```python
perplexity = PerplexityAPI()
result = perplexity.search("스타벅스 할인 혜택")
```

### EmbeddingExecutor
```python
executor = EmbeddingExecutor(host, api_key, request_id)
embedding = executor.execute({"text": "검색할 텍스트"})
```

### PersonalizedScoreCalculator
```python
calculator = PersonalizedScoreCalculator()
score = calculator.calculate_preference_score("스타벅스", "카페", user_history)
```

## 📊 데이터 구조

### 혜택 데이터 구조
```python
{
    "id": "unique_id",
    "brand": "스타벅스",
    "category": "카페",
    "title": "할인 이벤트",
    "benefit_type": "할인",
    "discount_rate": 10.0,
    "conditions": "조건 설명",
    "valid_from": "2025-08-01",
    "valid_to": "2025-08-31",
    "is_active": True,
    "text": "전체 텍스트 내용"
}
```

### 사용자 이력 구조
```python
{
    "brand": "스타벅스",
    "category": "카페",
    "amount": 50000,
    "date": "2025-08-01T10:00:00"
}
```

## 🛠️ 기술 스택

- **LangGraph**: 워크플로우 관리
- **ChromaDB**: 벡터 데이터베이스
- **CLOVA Studio**: 임베딩 생성
- **Perplexity API**: 실시간 검색
- **Streamlit**: 웹 인터페이스
- **Python**: 메인 프로그래밍 언어
- **NumPy**: 수치 계산
- **Requests**: HTTP 통신

## 📁 프로젝트 구조

```
ttugttag/
├── README.md
├── tools/
│   ├── main_rag_system.py          # 메인 RAG 시스템
│   ├── api_utils.py                # API 유틸리티
│   ├── rag_types.py                # 타입 정의
│   ├── multi_category_parser.py    # 쿼리 파서
│   ├── build_database.py           # 데이터베이스 구축
│   ├── multi_category_dummy_data.py # 더미 데이터
│   └── user_history_data.py        # 사용자 이력 데이터
├── web/
│   ├── streamlit_app.py            # Streamlit 웹 앱
│   ├── run_app.py                  # 앱 실행 스크립트
│   └── requirements.txt            # 웹 앱 의존성
└── test/
    └── test_rag_system.py          # 테스트 스크립트
```

### 파일별 역할

- **`tools/main_rag_system.py`**: LangGraph 기반 메인 시스템
- **`tools/api_utils.py`**: Perplexity API, 임베딩 API, 개인화 스코어링
- **`tools/rag_types.py`**: RAG 시스템의 상태 및 타입 정의
- **`tools/multi_category_parser.py`**: 다중 카테고리 쿼리 파싱
- **`tools/build_database.py`**: ChromaDB 벡터 데이터베이스 구축
- **`tools/multi_category_dummy_data.py`**: 테스트용 더미 데이터
- **`tools/user_history_data.py`**: 샘플 사용자 소비 이력
- **`web/streamlit_app.py`**: Streamlit 웹 인터페이스
- **`web/run_app.py`**: 웹 앱 실행 스크립트
- **`test/test_rag_system.py`**: 시스템 테스트 스크립트

## 💡 예시

### 예시 1: 브랜드별 검색
```
입력: "스타벅스 할인 혜택 있어?"
출력: 
🎯 개인화 혜택 추천 결과:

**[1] 스타벅스** (카페)
🎯 TWICE THE JOY
💰 쿠폰: 0% 할인
📝 조건: 보유 별 6개 → 프라푸치노/블렌디드 1+1 쿠폰 교환
📅 기간: 2025-08-11 ~ 2025-08-14
📊 개인화점수: 0.850
```

### 예시 2: 개인화 추천
```
입력: "내 소비 패턴에 맞는 혜택 추천해줘"
출력:
🎯 개인화 혜택 추천 결과:

**[1] 스타벅스** (카페)
🎯 STAR SUMMER
💰 혜택: 복합
📝 조건: 스타벅스 현대카드 특정 조건 충족
📅 기간: 2025-08-08 ~ 2025-08-31
📊 개인화점수: 0.920

**[2] 이마트** (마트)
🎯 여름 특가 이벤트
💰 할인: 15% 할인
📝 조건: 5만원 이상 구매 시
📅 기간: 2025-08-01 ~ 2025-08-31
📊 개인화점수: 0.850
```

### 예시 3: 실시간 검색
```
입력: "애플워치 할인"
출력:
🌐 실시간 검색 결과 (Perplexity):

2025년 8월 현재 애플워치 할인 혜택 이벤트 프로모션 쿠폰에 대한 정보입니다...

[실시간 검색 결과 내용]
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.

---

**TTUGTTAG** - The Ultimate Guide To The Best Offers & Deals 🎯