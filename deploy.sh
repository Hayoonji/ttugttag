#!/bin/bash

# ======================================================================================
# EC2 서버 배포 스크립트 - deploy.sh
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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 설정 변수
APP_NAME="benefits-api"
APP_DIR="/opt/${APP_NAME}"
APP_USER="benefits"
VENV_DIR="${APP_DIR}/venv"
SERVICE_NAME="${APP_NAME}"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"

# 인수 파싱
SKIP_SYSTEM_SETUP=false
SKIP_DB_SETUP=false
UPDATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-system)
            SKIP_SYSTEM_SETUP=true
            shift
            ;;
        --skip-db)
            SKIP_DB_SETUP=true
            shift
            ;;
        --update-only)
            UPDATE_ONLY=true
            shift
            ;;
        -h|--help)
            echo "사용법: $0 [옵션]"
            echo "옵션:"
            echo "  --skip-system   시스템 설정 건너뛰기"
            echo "  --skip-db       데이터베이스 설정 건너뛰기"
            echo "  --update-only   앱 업데이트만 수행"
            echo "  -h, --help      도움말 표시"
            exit 0
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            exit 1
            ;;
    esac
done

# 루트 권한 확인
if [[ $EUID -ne 0 ]]; then
   log_error "이 스크립트는 root 권한이 필요합니다. sudo를 사용하세요."
   exit 1
fi

log_info "EC2 혜택 추천 API 배포 시작"
log_info "배포 대상: ${APP_DIR}"

# ======================================================================================
# 1. 시스템 패키지 설치 및 업데이트
# ======================================================================================
\

# ======================================================================================
# 2. 애플리케이션 사용자 생성
# ======================================================================================

if [[ "$UPDATE_ONLY" != true ]]; then
    log_step "애플리케이션 사용자 생성"
    if ! id "$APP_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
        log_info "사용자 '$APP_USER' 생성 완료"
    else
        log_info "사용자 '$APP_USER' 이미 존재"
    fi
fi

# ======================================================================================
# 3. 디렉토리 구조 생성
# ======================================================================================

log_step "디렉토리 구조 생성"
mkdir -p "${APP_DIR}"/{app,data,logs,backups}
mkdir -p /var/log/${APP_NAME}

# 권한 설정
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" /var/log/${APP_NAME}

# ======================================================================================
# 4. 애플리케이션 코드 배포
# ======================================================================================

log_step "애플리케이션 코드 배포"

# 현재 디렉토리의 모든 Python 파일을 앱 디렉토리로 복사
cp *.py "${APP_DIR}/app/"
cp requirements.txt "${APP_DIR}/app/"

# tools 폴더 복사 (모든 모듈이 tools에서 import됨)
if [ -d "tools" ]; then
    cp -r tools "${APP_DIR}/app/"
    log_info "tools 폴더 복사 완료"
else
    log_error "tools 폴더를 찾을 수 없습니다"
    exit 1
fi

# 환경 변수 파일 설정
if [ ! -f "${APP_DIR}/app/.env" ]; then
    cp env.example "${APP_DIR}/app/.env"
    log_warning "환경 변수 파일을 설정하세요: ${APP_DIR}/app/.env"
fi

# 권한 설정
chown -R "$APP_USER:$APP_USER" "${APP_DIR}/app"

# ======================================================================================
# 5. Python 가상환경 설정
# ======================================================================================

log_step "Python 가상환경 설정"

# 기존 가상환경이 있으면 제거
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
fi

# 새 가상환경 생성
sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"

# 의존성 설치
log_step "Python 의존성 설치"
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "${APP_DIR}/app/requirements.txt"

# ======================================================================================
# 6. 데이터베이스 설정
# ======================================================================================

if [[ "$SKIP_DB_SETUP" != true ]]; then
    log_step "벡터 데이터베이스 설정"
    
    # 데이터베이스 디렉토리 생성
    sudo -u "$APP_USER" mkdir -p "${APP_DIR}/data/cafe_vector_db"
    
    # 기존 데이터베이스 확인
    if [ -d "${APP_DIR}/data/cafe_vector_db" ] && [ "$(ls -A ${APP_DIR}/data/cafe_vector_db 2>/dev/null)" ]; then
        log_info "✅ 기존 데이터베이스 발견 - 건너뛰기"
    else
        log_warning "📊 데이터베이스가 비어있음 - 자동 구축 시도"
        
        # setup_database.sh 스크립트가 있으면 실행
        if [ -f "${PWD}/setup_database.sh" ]; then
            log_info "🚀 자동 데이터베이스 구축 시작..."
            chmod +x "${PWD}/setup_database.sh"
            bash "${PWD}/setup_database.sh"
        else
            log_warning "수동으로 데이터베이스를 설정하세요:"
            log_warning "1. bash setup_database.sh 실행"
            log_warning "2. 또는 기존 데이터베이스를 ${APP_DIR}/data/cafe_vector_db로 복사"
        fi
    fi
fi

# ======================================================================================
# 7. Systemd 서비스 설정
# ======================================================================================

log_step "Systemd 서비스 설정"

cat > "$SYSTEMD_SERVICE" << EOF
[Unit]
Description=Benefits API - Personalized Recommendation Service
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/app
Environment=PATH=$VENV_DIR/bin
EnvironmentFile=$APP_DIR/app/.env
ExecStart=$VENV_DIR/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --threads 2 --timeout 120 --preload --access-logfile /var/log/$APP_NAME/access.log --error-logfile /var/log/$APP_NAME/error.log app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

# 보안 설정
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR /var/log/$APP_NAME
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

# 서비스 등록 및 활성화
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# ======================================================================================
# 8. Nginx 설정
# ======================================================================================

if [[ "$UPDATE_ONLY" != true ]]; then
    log_step "Nginx 설정"

    cat > "$NGINX_CONF" << 'EOF'
server {
    listen 80;
    server_name _;  # 도메인이 있으면 여기에 입력

    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # 로그 설정
    access_log /var/log/nginx/benefits-api.access.log;
    error_log /var/log/nginx/benefits-api.error.log;

    # 정적 파일 처리 (필요시)
    location /static {
        alias /opt/benefits-api/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API 프록시
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 버퍼링 설정
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # 헬스체크 엔드포인트
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }

    # 파일 업로드 크기 제한
    client_max_body_size 10M;
}
EOF

    # Nginx 사이트 활성화
    ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
    
    # 기본 사이트 비활성화
    rm -f /etc/nginx/sites-enabled/default

    # Nginx 설정 테스트
    nginx -t

    # Nginx 재시작
    systemctl restart nginx
    systemctl enable nginx
fi

# ======================================================================================
# 9. 로그 로테이션 설정
# ======================================================================================

log_step "로그 로테이션 설정"

cat > "/etc/logrotate.d/${APP_NAME}" << EOF
/var/log/$APP_NAME/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0640 $APP_USER $APP_USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

# ======================================================================================
# 10. 방화벽 설정
# ======================================================================================

if [[ "$UPDATE_ONLY" != true ]]; then
    log_step "방화벽 설정"
    
    # UFW가 설치되어 있으면 설정
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp  # SSH
        ufw allow 80/tcp  # HTTP
        ufw allow 443/tcp # HTTPS
        # ufw --force enable  # 주석 해제하여 방화벽 활성화
        log_info "방화벽 규칙 설정 완료 (비활성화 상태)"
    fi
fi

# ======================================================================================
# 11. 서비스 시작
# ======================================================================================

log_step "서비스 시작"

# 애플리케이션 서비스 시작
systemctl restart "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager -l

# 잠시 대기 후 상태 확인
sleep 3

# 헬스체크
log_step "헬스체크 수행"
if curl -f http://localhost/health > /dev/null 2>&1; then
    log_info "✅ 애플리케이션이 정상적으로 실행 중입니다!"
else
    log_error "❌ 애플리케이션 헬스체크 실패"
    log_info "서비스 로그 확인: journalctl -u $SERVICE_NAME -f"
fi

# ======================================================================================
# 12. 배포 완료 안내
# ======================================================================================

echo ""
log_info "🎉 배포 완료!"
echo ""
echo "📋 서비스 정보:"
echo "   • 애플리케이션: http://서버IP/"
echo "   • 헬스체크: http://서버IP/health"
echo "   • API 문서: http://서버IP/api/info"
echo ""
echo "🔧 관리 명령어:"
echo "   • 서비스 상태: systemctl status $SERVICE_NAME"
echo "   • 서비스 재시작: systemctl restart $SERVICE_NAME"
echo "   • 로그 확인: journalctl -u $SERVICE_NAME -f"
echo "   • Nginx 재시작: systemctl restart nginx"
echo ""
echo "📁 중요 경로:"
echo "   • 애플리케이션: $APP_DIR/app"
echo "   • 환경 설정: $APP_DIR/app/.env"
echo "   • 데이터베이스: $APP_DIR/data"
echo "   • 로그: /var/log/$APP_NAME"
echo ""
echo "⚠️  추가 설정 필요:"
echo "   1. $APP_DIR/app/.env 파일의 API 키 설정"
echo "   2. 벡터 데이터베이스 구축 또는 복사"
echo "   3. 도메인이 있으면 Nginx 설정에서 server_name 수정"
echo "   4. SSL 인증서 설정 (Let's Encrypt): certbot --nginx"
echo ""

log_info "배포 스크립트 실행 완료 ✨"
