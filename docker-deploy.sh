#!/bin/bash

# ======================================================================================
# Docker 배포 스크립트 - docker-deploy.sh
# ======================================================================================

set -e

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
ENVIRONMENT=${1:-development}
COMPOSE_FILE=""
PROJECT_NAME="benefits-api"

# 환경별 설정
case $ENVIRONMENT in
    development|dev)
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.docker"
        ;;
    production|prod)
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.docker"
        ;;
    *)
        log_error "지원되지 않는 환경: $ENVIRONMENT"
        log_error "사용법: $0 [development|production]"
        exit 1
        ;;
esac

# 도움말 출력
show_help() {
    echo "사용법: $0 [ENVIRONMENT] [OPTIONS]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  development, dev  - 개발 환경으로 배포"
    echo "  production, prod  - 프로덕션 환경으로 배포"
    echo ""
    echo "OPTIONS:"
    echo "  --build          - 이미지 강제 재빌드"
    echo "  --clean          - 기존 컨테이너 및 볼륨 정리"
    echo "  --logs           - 배포 후 로그 출력"
    echo "  --status         - 배포 후 상태 확인"
    echo "  -h, --help       - 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 development --build"
    echo "  $0 production --clean --logs"
}

# 인수 파싱
BUILD_FLAG=""
CLEAN_FLAG=false
SHOW_LOGS=false
SHOW_STATUS=false

while [[ $# -gt 1 ]]; do
    case $2 in
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --clean)
            CLEAN_FLAG=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --status)
            SHOW_STATUS=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "알 수 없는 옵션: $2"
            show_help
            exit 1
            ;;
    esac
done

# 메인 배포 함수
main() {
    log_info "🐳 Docker 배포 시작"
    log_info "환경: $ENVIRONMENT"
    log_info "Compose 파일: $COMPOSE_FILE"
    
    # 사전 체크
    check_prerequisites
    
    # 환경 변수 파일 확인
    check_env_file
    
    # 기존 컨테이너 정리 (옵션)
    if [ "$CLEAN_FLAG" = true ]; then
        clean_containers
    fi
    
    # Docker 이미지 빌드 및 컨테이너 시작
    deploy_containers
    
    # 배포 후 확인
    verify_deployment
    
    # 로그 출력 (옵션)
    if [ "$SHOW_LOGS" = true ]; then
        show_container_logs
    fi
    
    # 상태 확인 (옵션)
    if [ "$SHOW_STATUS" = true ]; then
        show_deployment_status
    fi
    
    log_info "🎉 배포 완료!"
    show_access_info
}

# 사전 요구사항 확인
check_prerequisites() {
    log_step "사전 요구사항 확인"
    
    # Docker 설치 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다"
        exit 1
    fi
    
    # Docker Compose 설치 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다"
        exit 1
    fi
    
    # Docker 서비스 상태 확인
    if ! docker info &> /dev/null; then
        log_error "Docker 서비스가 실행되지 않고 있습니다"
        exit 1
    fi
    
    # Compose 파일 존재 확인
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose 파일이 존재하지 않습니다: $COMPOSE_FILE"
        exit 1
    fi
    
    log_info "사전 요구사항 확인 완료"
}

# 환경 변수 파일 확인
check_env_file() {
    log_step "환경 변수 파일 확인"
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "환경 변수 파일이 없습니다: $ENV_FILE"
        
        if [ -f "env.docker.example" ]; then
            log_info "예시 파일에서 복사 중..."
            cp env.docker.example "$ENV_FILE"
            log_warning "⚠️  $ENV_FILE 파일을 편집하여 필요한 값들을 설정하세요"
            log_warning "특히 CLOVA_STUDIO_API_KEY는 필수입니다"
        else
            log_error "예시 환경 변수 파일도 없습니다: env.docker.example"
            exit 1
        fi
    fi
    
    # 필수 환경 변수 확인
    if ! grep -q "CLOVA_STUDIO_API_KEY=your_" "$ENV_FILE"; then
        if grep -q "CLOVA_STUDIO_API_KEY=" "$ENV_FILE"; then
            log_info "CLOVA_STUDIO_API_KEY가 설정되어 있습니다"
        else
            log_warning "CLOVA_STUDIO_API_KEY가 설정되지 않았을 수 있습니다"
        fi
    else
        log_warning "⚠️  CLOVA_STUDIO_API_KEY를 실제 값으로 변경해주세요"
    fi
}

# 기존 컨테이너 정리
clean_containers() {
    log_step "기존 컨테이너 정리"
    
    # 기존 컨테이너 중지 및 제거
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
    
    # 사용하지 않는 이미지 정리
    docker image prune -f
    
    # 사용하지 않는 볼륨 정리 (주의: 데이터 손실 가능)
    read -p "사용하지 않는 볼륨도 정리하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
        log_warning "볼륨이 정리되었습니다. 데이터가 손실될 수 있습니다."
    fi
    
    log_info "컨테이너 정리 완료"
}

# 컨테이너 배포
deploy_containers() {
    log_step "Docker 컨테이너 배포"
    
    # 환경 변수 파일 지정하여 컨테이너 시작
    export COMPOSE_FILE="$COMPOSE_FILE"
    
    # 컨테이너 시작
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d $BUILD_FLAG
    
    log_info "컨테이너 배포 완료"
}

# 배포 검증
verify_deployment() {
    log_step "배포 검증"
    
    # 컨테이너 상태 확인
    sleep 10  # 컨테이너 시작 대기
    
    # 헬스체크
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost/health > /dev/null 2>&1; then
            log_info "✅ 애플리케이션 헬스체크 성공"
            break
        else
            log_info "헬스체크 시도 $attempt/$max_attempts..."
            sleep 2
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "❌ 애플리케이션 헬스체크 실패"
        log_error "컨테이너 로그를 확인하세요: docker-compose -f $COMPOSE_FILE logs"
    fi
    
    # 컨테이너 상태 확인
    local unhealthy_containers=$(docker-compose -f "$COMPOSE_FILE" ps --filter health=unhealthy -q)
    if [ -n "$unhealthy_containers" ]; then
        log_warning "일부 컨테이너가 unhealthy 상태입니다"
        docker-compose -f "$COMPOSE_FILE" ps
    fi
}

# 컨테이너 로그 출력
show_container_logs() {
    log_step "컨테이너 로그 출력"
    
    echo "📋 최근 로그 (Ctrl+C로 중단):"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50 -f
}

# 배포 상태 출력
show_deployment_status() {
    log_step "배포 상태 확인"
    
    echo "📊 컨테이너 상태:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "💾 볼륨 상태:"
    docker volume ls | grep "$PROJECT_NAME"
    
    echo ""
    echo "🌐 네트워크 상태:"
    docker network ls | grep "$PROJECT_NAME"
    
    echo ""
    echo "📈 리소스 사용량:"
    docker stats --no-stream
}

# 접속 정보 출력
show_access_info() {
    echo ""
    log_info "🌐 서비스 접속 정보:"
    echo "   • 메인 애플리케이션: http://localhost/"
    echo "   • API 문서: http://localhost/api/info"
    echo "   • 헬스체크: http://localhost/health"
    
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "   • 직접 앱 접속: http://localhost:5000/"
        echo "   • Redis: localhost:6379"
        echo "   • Nginx 상태: http://localhost:8080/nginx_status"
    fi
    
    echo ""
    echo "🔧 관리 명령어:"
    echo "   • 로그 확인: docker-compose -f $COMPOSE_FILE logs -f [service]"
    echo "   • 컨테이너 재시작: docker-compose -f $COMPOSE_FILE restart [service]"
    echo "   • 컨테이너 중지: docker-compose -f $COMPOSE_FILE down"
    echo "   • 상태 확인: docker-compose -f $COMPOSE_FILE ps"
    echo ""
}

# 메인 함수 실행
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    main "$@"
fi
