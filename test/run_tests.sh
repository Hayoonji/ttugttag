#!/bin/bash

# API 테스트 실행 스크립트
# 사용법: ./run_tests.sh [test_type]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Python 가상환경 확인
check_python_env() {
    log_info "Python 환경 확인 중..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python이 설치되지 않았습니다."
        exit 1
    fi
    
    log_success "Python 명령어: $PYTHON_CMD"
    
    # 가상환경 확인
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        log_success "가상환경 활성화됨: $VIRTUAL_ENV"
    else
        log_warning "가상환경이 활성화되지 않았습니다."
        log_info "가상환경을 활성화하는 것을 권장합니다."
    fi
}

# 의존성 설치 확인
check_dependencies() {
    log_info "의존성 확인 중..."
    
    # requirements.txt 확인
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt 파일을 찾을 수 없습니다."
        exit 1
    fi
    
    # 필요한 패키지들 확인
    local missing_packages=()
    
    for package in requests pytest pillow python-dotenv; do
        if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        log_success "모든 의존성이 설치되어 있습니다."
    else
        log_warning "누락된 패키지: ${missing_packages[*]}"
        log_info "의존성을 설치하려면: pip install -r requirements.txt"
        
        read -p "지금 설치하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "의존성 설치 중..."
            pip install -r requirements.txt
        else
            log_warning "일부 테스트가 실패할 수 있습니다."
        fi
    fi
}

# 환경 설정 확인
check_environment() {
    log_info "환경 설정 확인 중..."
    
    # .env 파일 확인
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_warning ".env 파일이 없습니다. env.example을 복사합니다."
            cp env.example .env
            log_info "env.example을 .env로 복사했습니다. 필요에 따라 설정을 수정하세요."
        else
            log_warning ".env 파일이 없습니다. 기본 설정을 사용합니다."
        fi
    else
        log_success ".env 파일이 있습니다."
    fi
    
    # test_images 디렉토리 생성
    if [ ! -d "test_images" ]; then
        log_info "test_images 디렉토리 생성 중..."
        mkdir -p test_images
    fi
}

# 테스트 실행
run_tests() {
    local test_type=${1:-"smoke"}
    
    log_info "테스트 실행 중: $test_type"
    
    case $test_type in
        "smoke"|"health"|"chat"|"image_analysis"|"all")
            log_info "$test_type 테스트를 실행합니다..."
            $PYTHON_CMD run_all_tests.py "$test_type"
            ;;
        *)
            log_error "알 수 없는 테스트 타입: $test_type"
            log_info "사용 가능한 테스트 타입:"
            log_info "  - smoke: 스모크 테스트 (기본)"
            log_info "  - health: 헬스 체크 테스트"
            log_info "  - chat: 챗봇 API 테스트"
            log_info "  - image_analysis: 이미지 분석 API 테스트"
            log_info "  - all: 전체 테스트"
            exit 1
            ;;
    esac
}

# 메인 함수
main() {
    log_info "🚀 API 테스트 러너 시작"
    echo
    
    # 현재 디렉토리 확인
    if [ ! -f "run_all_tests.py" ]; then
        log_error "테스트 디렉토리에서 실행해야 합니다."
        log_info "cd test && ./run_tests.sh [test_type]"
        exit 1
    fi
    
    # 환경 확인
    check_python_env
    check_dependencies
    check_environment
    
    echo
    
    # 테스트 실행
    run_tests "$1"
    
    log_success "테스트 실행 완료!"
}

# 스크립트 실행
main "$@" 