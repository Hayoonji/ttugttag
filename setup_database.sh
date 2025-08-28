#!/bin/bash

# ======================================================================================
# 혜택 데이터베이스 자동 구축 스크립트 - setup_database.sh
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
DATA_DIR="${APP_DIR}/data"
DB_DIR="${DATA_DIR}/cafe_vector_db"
SOURCE_DATA_DIR="../benefits_db"

log_info "🚀 혜택 데이터베이스 자동 구축 시작"

# 권한 확인
if [[ $EUID -ne 0 ]]; then
   log_error "이 스크립트는 root 권한이 필요합니다. sudo를 사용하세요."
   exit 1
fi

# 애플리케이션 디렉토리 존재 확인
if [ ! -d "$APP_DIR" ]; then
    log_error "애플리케이션 디렉토리가 없습니다: $APP_DIR"
    log_error "먼저 deploy.sh를 실행하세요"
    exit 1
fi

# ======================================================================================
# 1. 기존 데이터베이스 확인
# ======================================================================================

log_step "기존 데이터베이스 확인"

if [ -d "$DB_DIR" ] && [ "$(ls -A $DB_DIR 2>/dev/null)" ]; then
    log_warning "기존 데이터베이스가 존재합니다: $DB_DIR"
    echo "기존 데이터베이스를 삭제하고 새로 구축하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "기존 데이터베이스 삭제 중..."
        rm -rf "$DB_DIR"/*
    else
        log_info "기존 데이터베이스를 유지합니다"
        exit 0
    fi
fi

# ======================================================================================
# 2. 소스 데이터 확인
# ======================================================================================

log_step "소스 데이터 확인"

# 현재 스크립트 위치에서 benefits_db 디렉토리 찾기
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POSSIBLE_PATHS=(
    "${SCRIPT_DIR}/../benefits_db"
    "${SCRIPT_DIR}/../../benefits_db" 
    "/opt/benefits-api/benefits_db"
    "/tmp/benefits_db"
)

SOURCE_DATA_DIR=""
for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -d "$path" ] && [ "$(ls -A $path/*.json 2>/dev/null)" ]; then
        SOURCE_DATA_DIR="$path"
        log_info "소스 데이터 발견: $SOURCE_DATA_DIR"
        break
    fi
done

if [ -z "$SOURCE_DATA_DIR" ]; then
    log_error "혜택 JSON 데이터를 찾을 수 없습니다"
    log_error "다음 위치에 *.json 파일들이 있는지 확인하세요:"
    for path in "${POSSIBLE_PATHS[@]}"; do
        echo "  - $path"
    done
    exit 1
fi

# ======================================================================================
# 3. tools/build_database.py 복사 및 수정
# ======================================================================================

log_step "데이터베이스 구축 도구 준비"

# build_database.py를 앱 디렉토리로 복사
if [ -f "${SCRIPT_DIR}/../tools/build_database.py" ]; then
    cp "${SCRIPT_DIR}/../tools/build_database.py" "${APP_DIR}/app/"
    chown "$APP_USER:$APP_USER" "${APP_DIR}/app/build_database.py"
    log_info "build_database.py 복사 완료"
else
    log_error "build_database.py를 찾을 수 없습니다: ${SCRIPT_DIR}/../tools/build_database.py"
    exit 1
fi

# ======================================================================================
# 4. 임시 구축 스크립트 생성
# ======================================================================================

log_step "데이터베이스 구축 스크립트 생성"

cat > "${APP_DIR}/app/run_build_db.py" << 'EOF'
#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 혜택 데이터베이스 구축 시작")
    
    try:
        # build_database.py에서 main 함수 import
        from build_database import main as build_main
        
        # 환경 변수 설정
        os.environ['DATABASE_PATH'] = '/opt/benefits-api/data/cafe_vector_db'
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        print("📊 데이터베이스 구축 시작...")
        result = build_main()
        
        if result:
            print("✅ 데이터베이스 구축 완료!")
            return True
        else:
            print("❌ 데이터베이스 구축 실패")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chown "$APP_USER:$APP_USER" "${APP_DIR}/app/run_build_db.py"
chmod +x "${APP_DIR}/app/run_build_db.py"

# ======================================================================================
# 5. 데이터베이스 구축 실행
# ======================================================================================

log_step "데이터베이스 구축 실행"

# 서비스 임시 중지
systemctl stop "$APP_NAME" 2>/dev/null || true

# 데이터 디렉토리 생성 및 권한 설정
sudo -u "$APP_USER" mkdir -p "$DB_DIR"

# 소스 데이터를 임시 위치에 복사
TEMP_DATA_DIR="${APP_DIR}/temp_benefits_data"
sudo -u "$APP_USER" mkdir -p "$TEMP_DATA_DIR"
sudo -u "$APP_USER" cp -r "$SOURCE_DATA_DIR"/* "$TEMP_DATA_DIR/"

# 환경 변수 설정
export DATABASE_PATH="$DB_DIR"
export BENEFITS_DATA_DIR="$TEMP_DATA_DIR"

# Python 가상환경에서 데이터베이스 구축
log_info "🔨 데이터베이스 구축 중... (시간이 걸릴 수 있습니다)"

cd "${APP_DIR}/app"
if sudo -u "$APP_USER" -E "$VENV_DIR/bin/python" run_build_db.py; then
    log_info "✅ 데이터베이스 구축 성공!"
else
    log_error "❌ 데이터베이스 구축 실패"
    # 임시 파일 정리
    rm -rf "$TEMP_DATA_DIR"
    exit 1
fi

# 임시 파일 정리
rm -rf "$TEMP_DATA_DIR"
rm -f "${APP_DIR}/app/run_build_db.py"
rm -f "${APP_DIR}/app/build_database.py"

# ======================================================================================
# 6. 데이터베이스 검증
# ======================================================================================

log_step "데이터베이스 검증"

# 간단한 검증 스크립트 실행
cat > "${APP_DIR}/app/verify_db.py" << 'EOF'
#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    
    db_path = "/opt/benefits-api/data/cafe_vector_db"
    client = chromadb.PersistentClient(path=db_path)
    
    collections = client.list_collections()
    print(f"📋 발견된 컬렉션: {len(collections)}개")
    
    for collection in collections:
        count = collection.count()
        print(f"  - {collection.name}: {count}개 문서")
    
    if collections and any(c.count() > 0 for c in collections):
        print("✅ 데이터베이스 검증 성공!")
        sys.exit(0)
    else:
        print("❌ 데이터베이스가 비어있습니다")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ 데이터베이스 검증 실패: {e}")
    sys.exit(1)
EOF

chown "$APP_USER:$APP_USER" "${APP_DIR}/app/verify_db.py"

if sudo -u "$APP_USER" "$VENV_DIR/bin/python" "${APP_DIR}/app/verify_db.py"; then
    log_info "✅ 데이터베이스 검증 완료"
else
    log_error "❌ 데이터베이스 검증 실패"
fi

# 검증 스크립트 제거
rm -f "${APP_DIR}/app/verify_db.py"

# ======================================================================================
# 7. 서비스 재시작
# ======================================================================================

log_step "서비스 재시작"

systemctl start "$APP_NAME"
sleep 3
systemctl status "$APP_NAME" --no-pager -l

# 헬스체크
log_step "헬스체크 수행"
if curl -f http://localhost/health > /dev/null 2>&1; then
    log_info "✅ 서비스가 정상적으로 실행 중입니다!"
else
    log_warning "⚠️ 헬스체크 실패 - 로그를 확인하세요"
    log_info "로그 확인: journalctl -u $APP_NAME -f"
fi

echo ""
log_info "🎉 혜택 데이터베이스 구축 완료!"
echo ""
echo "📊 데이터베이스 정보:"
echo "   • 위치: $DB_DIR"
echo "   • 상태: 구축 완료"
echo ""
echo "🧪 테스트 방법:"
echo "   curl -X POST http://localhost/api/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"스타벅스 혜택 알려주세요\", \"user_id\": \"test\"}'"
echo ""
