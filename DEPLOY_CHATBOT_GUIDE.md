# 🤖 챗봇 웹 인터페이스 배포 가이드

## 📋 개요

이 가이드는 API와 웹 인터페이스를 분리하여 배포하는 방법을 설명합니다.

### 🎯 접근 경로

- **웹 인터페이스**: `http://your-domain.com/` (루트 경로)
- **API 엔드포인트**: `http://your-domain.com/api/` (API 경로)
- **통합 AI**: `http://your-domain.com/unified-ai` (챗봇 전용)

## 🚀 배포 단계

### 1. Docker 컨테이너 실행

```bash
# ec2 디렉토리로 이동
cd ec2/

# 환경 변수 설정
cp env.example .env.docker
# .env.docker 파일을 편집하여 필요한 설정 추가

# Docker Compose로 실행
docker-compose up -d
```

### 2. 서비스 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f app
docker-compose logs -f nginx
```

### 3. 접근 테스트

#### 웹 인터페이스 테스트

```bash
curl http://localhost/
# 또는 브라우저에서 http://localhost 접속
```

#### API 테스트

```bash
# 헬스체크
curl http://localhost/api/info

# 챗봇 API
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요", "user_id": "test_user"}'
```

#### 통합 AI 테스트

```bash
curl -X POST http://localhost/unified-ai \
  -H "Content-Type: application/json" \
  -d '{"message": "스타벅스 혜택 알려주세요"}'
```

## 🌐 Nginx 라우팅 구조

```nginx
# API 요청
/api/chat          → Flask 앱의 /api/chat
/api/search        → Flask 앱의 /api/search
/api/recommend     → Flask 앱의 /api/recommend

# 특별 엔드포인트
/unified-ai        → Flask 앱의 /unified-ai

# 웹 인터페이스
/                  → Flask 앱의 / (static/index.html 서빙)
/health            → Flask 앱의 /health
```

## 🎨 챗봇 웹 인터페이스 기능

### 주요 기능

- 📱 반응형 디자인
- 💬 실시간 채팅 인터페이스
- 🔧 도구 사용 현황 표시
- ⚡ 퀵 리플라이 버튼
- 📊 실행 로그 표시

### 사용 방법

1. 브라우저에서 `http://your-domain.com` 접속
2. 메시지 입력창에 질문 입력
3. 전송 버튼 클릭 또는 Enter 키 누르기
4. AI 응답 및 도구 사용 현황 확인

## 🛠️ 파일 구조

```
ec2/
├── app.py                 # Flask 메인 애플리케이션
├── docker-compose.yml     # Docker 서비스 구성
├── Dockerfile             # 앱 컨테이너 이미지
└── docker/
    └── nginx/
        ├── nginx.conf     # Nginx 메인 설정
        └── conf.d/
            └── default.conf   # 추가 설정

static/
└── index.html             # 챗봇 웹 인터페이스
```

## 🔧 트러블슈팅

### 웹 페이지가 로드되지 않는 경우

```bash
# Flask 앱 로그 확인
docker-compose logs app

# Nginx 로그 확인
docker-compose logs nginx
```

### API 호출이 실패하는 경우

```bash
# 네트워크 연결 확인
docker network ls
docker network inspect benefits-network

# 컨테이너 내부 테스트
docker-compose exec app curl http://localhost:5000/health
```

### 챗봇 응답이 없는 경우

```bash
# RAG 시스템 상태 확인
curl http://localhost/api/info

# 데이터베이스 연결 확인
curl http://localhost/api/stats
```

## 📝 환경 변수

`.env.docker` 파일에서 설정할 수 있는 주요 변수들:

```bash
# Flask 설정
FLASK_DEBUG=false
ENVIRONMENT=production
PORT=5000

# RAG 시스템 설정
DATABASE_PATH=/app/data/benefits.db
COLLECTION_NAME=benefits_collection

# Redis 설정
REDIS_PASSWORD=your_redis_password
```

## 🚀 프로덕션 배포

### 1. SSL 인증서 설정

```bash
# Let's Encrypt 인증서 발급
sudo certbot --nginx -d your-domain.com
```

### 2. 프로덕션 설정 사용

```bash
# 프로덕션용 Docker Compose 사용
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 모니터링 설정

```bash
# 로그 로테이션 설정
sudo logrotate -f /etc/logrotate.d/nginx

# 시스템 서비스 등록
sudo systemctl enable benefits-api
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. Docker 컨테이너 상태
2. Nginx 설정 파일 문법
3. Flask 앱 로그
4. 네트워크 연결 상태

더 자세한 정보는 `README.md` 파일을 참조하세요.
