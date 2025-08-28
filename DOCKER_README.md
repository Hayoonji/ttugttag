# 🐳 Docker 배포용 개인화된 혜택 추천 API

Docker와 Docker Compose를 사용하여 컨테이너 환경에서 배포할 수 있는 Flask 기반의 개인화된 혜택 추천 시스템입니다.

## 🌟 Docker 배포의 장점

- **🔄 환경 일관성**: 개발, 테스트, 프로덕션 환경 동일화
- **📦 간편한 배포**: 원클릭 배포 및 롤백
- **🚀 빠른 확장**: 수평적 스케일링 지원
- **🔧 의존성 관리**: 모든 의존성 컨테이너에 포함
- **🔒 격리된 환경**: 보안 강화 및 충돌 방지
- **📊 모니터링**: 컨테이너 기반 모니터링 도구 활용

## 📋 시스템 요구사항

### 최소 요구사항

- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **CPU**: 2 vCPU 이상
- **RAM**: 4GB 이상
- **Storage**: 20GB 이상 (SSD 권장)

### 권장 사양

- **CPU**: 4 vCPU
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **네트워크**: 1Gbps 이상

## 🚀 빠른 시작

### 1. 소스 코드 준비

```bash
# 소스 코드 클론 또는 다운로드
git clone <repository-url>
cd ec2/

# 또는 기존 소스가 있는 경우
cd /path/to/your/benefits-api/ec2/
```

### 2. 환경 변수 설정

```bash
# Docker용 환경 변수 파일 생성
cp env.docker.example .env.docker

# 환경 변수 편집
nano .env.docker

# 필수: CLOVA Studio API 키 설정
# CLOVA_STUDIO_API_KEY=your_api_key_here
```

### 3. 개발 환경 시작

```bash
# 개발용 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f app
```

### 4. 프로덕션 환경 시작

```bash
# 프로덕션용 컨테이너 시작
docker-compose -f docker-compose.prod.yml up -d

# 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

## 📁 Docker 파일 구조

```
ec2/
├── Dockerfile                    # 메인 애플리케이션 이미지
├── docker-compose.yml            # 개발환경 구성
├── docker-compose.prod.yml       # 프로덕션환경 구성
├── .dockerignore                 # Docker 빌드 제외 파일
├── env.docker.example            # 환경 변수 템플릿
├── docker/
│   ├── entrypoint.sh            # 컨테이너 시작 스크립트
│   ├── nginx/
│   │   ├── nginx.conf           # 개발용 Nginx 설정
│   │   └── nginx.prod.conf      # 프로덕션용 Nginx 설정
│   └── redis/
│       └── redis.conf           # Redis 설정 (선택적)
└── DOCKER_README.md             # 이 문서
```

## 🏗️ 컨테이너 구성

### 개발 환경 (docker-compose.yml)

1. **app**: Flask 애플리케이션 (포트 5000)
2. **nginx**: 리버스 프록시 (포트 80, 443)
3. **redis**: 캐싱 및 세션 저장 (포트 6379)

### 프로덕션 환경 (docker-compose.prod.yml)

1. **app**: Flask 애플리케이션 (복제 2개)
2. **nginx**: 리버스 프록시 + 로드밸런서
3. **redis**: 캐싱 및 세션 저장
4. **postgres**: 메타데이터 저장 (선택적)
5. **watchtower**: 자동 업데이트
6. **filebeat**: 로그 수집 (선택적)

## ⚙️ 환경 설정

### 필수 환경 변수

```bash
# CLOVA Studio API 키 (필수)
CLOVA_STUDIO_API_KEY=your_api_key

# 환경 구분
ENVIRONMENT=production  # development, staging, production

# 서버 설정
PORT=5000
HOST=0.0.0.0
```

### 선택적 환경 변수

```bash
# Naver Search API
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# 보안 설정
SECRET_KEY=your-secret-key
REDIS_PASSWORD=your_redis_password
POSTGRES_PASSWORD=your_postgres_password

# 성능 튜닝
WORKERS=4
THREADS=2
TIMEOUT=120
```

## 🔧 Docker 명령어

### 기본 명령어

```bash
# 컨테이너 시작
docker-compose up -d

# 컨테이너 중지
docker-compose down

# 컨테이너 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f [service_name]

# 상태 확인
docker-compose ps
```

### 빌드 및 이미지 관리

```bash
# 이미지 빌드
docker-compose build

# 이미지 강제 재빌드
docker-compose build --no-cache

# 사용하지 않는 이미지 정리
docker image prune -f

# 모든 컨테이너 및 볼륨 정리
docker-compose down -v --remove-orphans
```

### 개별 컨테이너 관리

```bash
# 특정 서비스만 시작
docker-compose up -d app

# 컨테이너 내부 접속
docker-compose exec app bash

# 애플리케이션 로그만 확인
docker-compose logs -f app

# 컨테이너 리소스 사용량 확인
docker stats
```

## 🗄️ 데이터 관리

### 볼륨 구성

```bash
# 볼륨 목록 확인
docker volume ls

# 볼륨 상세 정보
docker volume inspect benefits-app-data

# 데이터 백업
docker run --rm -v benefits-app-data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz /data

# 데이터 복원
docker run --rm -v benefits-app-data:/data -v $(pwd):/backup alpine tar xzf /backup/data-backup.tar.gz -C /
```

### 벡터 데이터베이스 설정

```bash
# 기존 데이터베이스 복사 (호스트 → 컨테이너)
docker cp ./cafe_vector_db benefits-api-app:/app/data/

# 데이터베이스 새로 구축
docker-compose exec app python tools/build_database.py

# 데이터베이스 상태 확인
docker-compose exec app ls -la /app/data/cafe_vector_db/
```

## 🔒 보안 설정

### SSL/TLS 인증서 설정

```bash
# SSL 디렉토리 생성
mkdir -p ssl

# Let's Encrypt 인증서 발급 (예시)
docker run --rm -v $(pwd)/ssl:/etc/letsencrypt certbot/certbot certonly \
  --standalone \
  --email your-email@example.com \
  --agree-tos \
  --domains yourdomain.com

# 인증서 파일을 ssl/ 디렉토리에 복사
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
```

### 보안 설정 검증

```bash
# 컨테이너 보안 스캔
docker scan benefits-api:latest

# 실행 중인 컨테이너 보안 체크
docker-compose exec app ps aux
docker-compose exec app whoami
```

## 📊 모니터링 및 로그

### 로그 관리

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 시간대 로그
docker-compose logs --since=1h app

# 로그 파일 직접 확인
docker-compose exec app tail -f /app/logs/error.log

# Nginx 로그
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### 헬스체크 및 모니터링

```bash
# 헬스체크 상태 확인
curl http://localhost/health

# 컨테이너 리소스 모니터링
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# 서비스 상태 확인
docker-compose ps
```

### 메트릭 수집 (Prometheus + Grafana)

```yaml
# docker-compose.monitoring.yml (선택적)
version: "3.8"
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🚀 확장 및 스케일링

### 수평적 스케일링

```bash
# 앱 인스턴스 증가
docker-compose up -d --scale app=3

# 로드밸런서 설정 확인
docker-compose exec nginx nginx -t
```

### Docker Swarm 배포

```bash
# Swarm 모드 초기화
docker swarm init

# 스택 배포
docker stack deploy -c docker-compose.prod.yml benefits-api

# 서비스 스케일링
docker service scale benefits-api_app=5

# 서비스 상태 확인
docker service ls
docker service ps benefits-api_app
```

### Kubernetes 배포 (선택적)

```bash
# Kubernetes 매니페스트 생성
kompose convert -f docker-compose.prod.yml

# Kubernetes 배포
kubectl apply -f benefits-api-deployment.yaml

# 서비스 스케일링
kubectl scale deployment benefits-api-app --replicas=5
```

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 컨테이너가 시작되지 않는 경우

```bash
# 상세 로그 확인
docker-compose logs app

# 컨테이너 내부 확인
docker-compose exec app bash

# 이미지 재빌드
docker-compose build --no-cache app
```

#### 2. 데이터베이스 연결 실패

```bash
# 벡터 데이터베이스 확인
docker-compose exec app ls -la /app/data/cafe_vector_db/

# 권한 확인
docker-compose exec app ls -la /app/data/

# 볼륨 마운트 확인
docker volume inspect benefits-app-data
```

#### 3. Nginx 502 Bad Gateway

```bash
# 앱 컨테이너 상태 확인
docker-compose ps app

# Nginx 설정 테스트
docker-compose exec nginx nginx -t

# 네트워크 연결 확인
docker-compose exec nginx ping app
```

#### 4. 메모리 부족

```bash
# 메모리 사용량 확인
docker stats

# 불필요한 컨테이너 정리
docker container prune

# 메모리 제한 설정
# docker-compose.yml에서 deploy.resources.limits.memory 설정
```

### 로그 레벨 조정

```bash
# 디버그 모드 활성화
echo "LOG_LEVEL=DEBUG" >> .env.docker
docker-compose restart app

# 환경 변수 확인
docker-compose exec app env | grep LOG_LEVEL
```

## 🔄 CI/CD 파이프라인

### GitHub Actions 예시

```yaml
# .github/workflows/docker-deploy.yml
name: Docker Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t benefits-api:latest .

      - name: Run tests
        run: docker run --rm benefits-api:latest python -m pytest

      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: |
          docker-compose -f docker-compose.prod.yml up -d
```

### GitLab CI/CD 예시

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - docker-compose -f docker-compose.prod.yml up -d
  only:
    - main
```

## 📈 성능 최적화

### Docker 이미지 최적화

```dockerfile
# 멀티 스테이지 빌드 (선택적)
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["gunicorn", "app:app"]
```

### 캐싱 전략

```yaml
# docker-compose.yml에 Redis 캐시 추가
services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 리소스 제한

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
```

## 📞 지원 및 문의

- **헬스체크**: [http://localhost/health](http://localhost/health)
- **API 문서**: [http://localhost/api/info](http://localhost/api/info)
- **Grafana 대시보드**: [http://localhost:3000](http://localhost:3000) (모니터링 설정시)

## 📄 관련 문서

- [EC2 배포 가이드](README.md)
- [Firebase Functions 가이드](../FIREBASE_README.md)
- [챗봇 API 가이드](../CHATBOT_API_GUIDE.md)

---

**🐳 Docker 배포 버전**: 2.1.0  
**📅 최종 업데이트**: 2024년 1월  
**🏗️ 플랫폼**: Docker + Docker Compose
