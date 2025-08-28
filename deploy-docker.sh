#!/bin/bash

# ======================================================================================
# Docker Compose 배포 스크립트 - deploy-docker.sh
# 지금까지 작업한 모든 내용을 자동화
# ======================================================================================

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 시작 메시지
echo "=============================================="
echo "🚀 Docker Compose 배포 스크립트 시작"
echo "=============================================="

# 1단계: 환경 확인
log_step "1. 환경 확인"
log_info "Docker 버전 확인..."
docker --version || { log_error "Docker가 설치되지 않았습니다!"; exit 1; }

log_info "Docker Compose 버전 확인..."
docker compose version || { log_error "Docker Compose v2가 설치되지 않았습니다!"; exit 1; }

# 2단계: 기존 컨테이너 정리
log_step "2. 기존 컨테이너 정리"
log_info "기존 Docker Compose 서비스 중지 및 정리..."
docker compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true

log_info "Docker 시스템 정리..."
docker system prune -f --volumes

# 3단계: 환경변수 파일 확인
log_step "3. 환경변수 파일 확인"
if [ ! -f ".env.docker" ]; then
    log_warn ".env.docker 파일이 없습니다. env.docker.example에서 복사합니다..."
    cp env.docker.example .env.docker
    log_info ".env.docker 파일을 생성했습니다. 필요한 환경변수를 설정해주세요."
fi

# 4단계: 필수 디렉토리 생성
log_step "4. 필수 디렉토리 생성"
log_info "로그 디렉토리 생성..."
mkdir -p logs

log_info "Docker 설정 디렉토리 생성..."
mkdir -p docker/nginx docker/redis docker/postgres

# 5단계: Nginx 설정 파일 생성 (없는 경우)
log_step "5. 설정 파일 확인"
if [ ! -f "docker/nginx/nginx.prod.conf" ]; then
    log_info "Nginx 설정 파일 생성..."
    cat > docker/nginx/nginx.prod.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:5001;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /health {
            proxy_pass http://app/health;
        }
    }
}
EOF
fi

# 6단계: Docker 이미지 빌드 및 실행
log_step "6. Docker Compose 빌드 및 실행"
log_info "Docker 이미지 빌드 중... (시간이 걸릴 수 있습니다)"
docker compose -f docker-compose.prod.yml build

log_info "Docker Compose 서비스 시작..."
docker compose -f docker-compose.prod.yml up -d

# 7단계: 서비스 상태 확인
log_step "7. 서비스 상태 확인"
sleep 5  # 서비스 시작 대기

log_info "실행 중인 컨테이너 확인..."
docker compose -f docker-compose.prod.yml ps

# 8단계: 헬스체크
log_step "8. 헬스체크"
log_info "Flask 앱 헬스체크 (최대 30초 대기)..."

for i in {1..30}; do
    if curl -s http://localhost:5001/health > /dev/null; then
        log_info "✅ Flask 앱이 정상적으로 실행 중입니다!"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "❌ Flask 앱 헬스체크 실패"
        log_info "로그 확인: docker compose -f docker-compose.prod.yml logs app"
        exit 1
    fi
    sleep 1
done

# 9단계: 최종 확인
log_step "9. 최종 배포 확인"
log_info "서비스 접속 정보:"
echo "  - Flask API: http://localhost:5001"
echo "  - Health Check: http://localhost:5001/health"
echo "  - Redis: localhost:6379"
echo "  - PostgreSQL: localhost:5432"

log_info "서비스 관리 명령어:"
echo "  - 로그 확인: docker compose -f docker-compose.prod.yml logs -f"
echo "  - 서비스 중지: docker compose -f docker-compose.prod.yml down"
echo "  - 재시작: docker compose -f docker-compose.prod.yml restart"

echo "=============================================="
log_info "🎉 Docker Compose 배포 완료!"
echo "=============================================="

# 10단계: 실시간 로그 표시 (선택사항)
read -p "실시간 로그를 확인하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "실시간 로그 표시... (Ctrl+C로 종료)"
    docker compose -f docker-compose.prod.yml logs -f
fi 