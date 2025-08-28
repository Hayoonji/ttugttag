# API 테스트 스위트

이 폴더는 혜택 추천 API의 모든 엔드포인트를 테스트하기 위한 테스트 스크립트들을 포함합니다.

## 📁 파일 구조

```
test/
├── README.md                 # 이 파일
├── requirements.txt          # 테스트에 필요한 Python 패키지들
├── config.py                # 테스트 설정 파일
├── api_utils.py             # API 테스트 유틸리티 함수들
├── test_health.py           # 헬스 체크 API 테스트
├── test_chat.py             # 챗봇 API 테스트
├── test_image_analysis.py   # 이미지 분석 API 테스트
├── run_all_tests.py         # 통합 테스트 실행 스크립트
├── run_tests.sh             # Bash 테스트 실행 스크립트
├── env.example              # 환경 설정 예시 파일
└── test_images/             # 테스트용 이미지 저장 디렉토리
```

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
cd test
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
# 환경 설정 파일 복사
cp env.example .env

# .env 파일을 편집하여 API 서버 URL 설정
# API_BASE_URL=http://your-api-server:5000
```

### 3. 테스트 실행

#### Bash 스크립트 사용 (권장)
```bash
# 스모크 테스트 (기본)
./run_tests.sh

# 특정 테스트 실행
./run_tests.sh health          # 헬스 체크만
./run_tests.sh chat            # 챗봇 API만
./run_tests.sh image_analysis  # 이미지 분석만
./run_tests.sh all             # 전체 테스트
```

#### Python 스크립트 직접 실행
```bash
# 스모크 테스트
python run_all_tests.py

# 특정 테스트
python run_all_tests.py health
python run_all_tests.py chat
python run_all_tests.py image_analysis
python run_all_tests.py all
```

## 🧪 테스트 종류

### 1. 스모크 테스트 (`smoke`)
- API 서버 연결 확인
- 기본 헬스 체크
- 빠른 기능 검증

### 2. 헬스 체크 테스트 (`health`)
- `/api/health` 엔드포인트 테스트
- `/api/status` 엔드포인트 테스트
- 응답 구조 검증

### 3. 챗봇 API 테스트 (`chat`)
- 기본 챗봇 기능 테스트
- 디버그 모드 테스트
- 에러 처리 테스트
- 응답 구조 검증

### 4. 이미지 분석 API 테스트 (`image_analysis`)
- 이미지 업로드 및 분석 테스트
- 다양한 이미지 크기 테스트
- 에러 처리 테스트
- 성능 테스트

### 5. 전체 테스트 (`all`)
- 모든 테스트를 순차적으로 실행
- 종합적인 API 검증

## ⚙️ 설정 옵션

### 환경 변수 (.env 파일)

```bash
# API 서버 설정
API_BASE_URL=http://localhost:5000    # API 서버 URL
API_TIMEOUT=30                        # 요청 타임아웃 (초)

# 테스트 설정
TEST_DEBUG=false                      # 디버그 모드
TEST_VERBOSE=true                     # 상세 로깅
TEST_IMAGE_PATH=test_images/          # 테스트 이미지 경로

# 로깅 설정
LOG_LEVEL=INFO                        # 로그 레벨
```

## 📊 테스트 결과

### 로그 파일
- 테스트 실행 시 자동으로 로그 파일이 생성됩니다
- 형식: `test_results_YYYYMMDD_HHMMSS.log`

### 콘솔 출력
- 실시간 테스트 진행 상황 표시
- 색상 구분된 결과 표시
- 상세한 오류 정보 제공

## 🔧 문제 해결

### 일반적인 문제들

#### 1. API 서버 연결 실패
```bash
# 서버가 실행 중인지 확인
curl http://localhost:5000/api/health

# .env 파일의 API_BASE_URL 확인
cat .env
```

#### 2. 의존성 문제
```bash
# 가상환경 활성화
source venv/bin/activate  # 또는 해당하는 가상환경

# 패키지 재설치
pip install -r requirements.txt --force-reinstall
```

#### 3. 권한 문제
```bash
# 실행 권한 부여
chmod +x run_tests.sh
```

#### 4. 이미지 테스트 실패
```bash
# PIL 설치 확인
python -c "from PIL import Image; print('PIL 설치됨')"

# 테스트 이미지 디렉토리 확인
ls -la test_images/
```

## 📝 테스트 추가하기

### 새로운 API 엔드포인트 테스트 추가

1. `test_[endpoint_name].py` 파일 생성
2. `run_all_tests.py`에 모듈 추가
3. `run_tests.sh`에 테스트 타입 추가

### 예시 구조
```python
#!/usr/bin/env python3
def test_basic():
    """기본 기능 테스트"""
    pass

def test_error_handling():
    """에러 처리 테스트"""
    pass

def main():
    """메인 테스트 실행"""
    test_results = []
    test_results.append(("기본 기능", test_basic()))
    test_results.append(("에러 처리", test_error_handling()))
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## 🤝 기여하기

테스트 개선이나 새로운 테스트 추가를 원하시면:

1. 이슈 생성 또는 기존 이슈 확인
2. 테스트 코드 작성
3. 테스트 실행하여 정상 작동 확인
4. Pull Request 생성

## 📞 지원

테스트 실행 중 문제가 발생하면:

1. 로그 파일 확인
2. 환경 설정 확인
3. API 서버 상태 확인
4. 이슈 생성 (상세한 오류 정보 포함)
