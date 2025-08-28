#!/bin/bash

# ======================================================================================
# 데이터베이스 상태 확인 스크립트 - check_database.sh
# ======================================================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 설정
APP_DIR="/opt/benefits-api"
DB_DIR="${APP_DIR}/data/cafe_vector_db"

echo "🔍 데이터베이스 상태 확인"
echo "======================"

# 1. 데이터베이스 디렉토리 확인
echo ""
echo "1️⃣ 데이터베이스 디렉토리 확인"
echo "----------------------------"
if [ -d "$DB_DIR" ]; then
    log_info "✅ 데이터베이스 디렉토리 존재: $DB_DIR"
    
    # 파일 개수 확인
    file_count=$(find "$DB_DIR" -type f 2>/dev/null | wc -l)
    echo "   📁 파일 개수: $file_count"
    
    if [ "$file_count" -gt 0 ]; then
        log_info "✅ 데이터베이스 파일들이 있습니다"
        echo "   📋 주요 파일들:"
        ls -la "$DB_DIR" | head -10
    else
        log_warning "⚠️ 데이터베이스 디렉토리가 비어있습니다"
    fi
else
    log_error "❌ 데이터베이스 디렉토리가 없습니다: $DB_DIR"
fi

# 2. 서비스 상태 확인
echo ""
echo "2️⃣ 서비스 상태 확인"
echo "------------------"
if systemctl is-active --quiet benefits-api; then
    log_info "✅ benefits-api 서비스 실행 중"
else
    log_warning "⚠️ benefits-api 서비스 중지됨"
fi

# 3. 헬스체크
echo ""
echo "3️⃣ 애플리케이션 헬스체크"
echo "----------------------"
health_response=$(curl -s http://localhost/health 2>/dev/null)
if [ $? -eq 0 ]; then
    log_info "✅ 애플리케이션 응답 정상"
    echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
else
    log_error "❌ 애플리케이션 응답 없음"
fi

# 4. API 테스트
echo ""
echo "4️⃣ 챗봇 API 테스트"
echo "-----------------"
api_response=$(curl -s -X POST http://localhost/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "스타벅스 혜택", "user_id": "test_user", "user_context": {"spending_history": []}}' 2>/dev/null)

if [ $? -eq 0 ] && echo "$api_response" | grep -q "success"; then
    log_info "✅ 챗봇 API 응답 정상"
    # 응답에서 success와 message 부분만 추출
    echo "$api_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Success: {data.get(\"success\", False)}')
    if 'response' in data and 'message' in data['response']:
        msg = data['response']['message'][:200]
        print(f'Message: {msg}...' if len(data['response']['message']) > 200 else f'Message: {msg}')
except:
    print('JSON 파싱 실패')
" 2>/dev/null || echo "$api_response"
else
    log_error "❌ 챗봇 API 응답 실패"
    echo "응답: $api_response"
fi

# 5. 로그 확인
echo ""
echo "5️⃣ 최근 로그 확인"
echo "----------------"
echo "🔍 최근 애플리케이션 로그 (마지막 5줄):"
journalctl -u benefits-api --no-pager -n 5 || echo "로그를 가져올 수 없습니다"

# 6. 진단 결과 요약
echo ""
echo "📊 진단 결과 요약"
echo "================"

# 문제 진단
issues=0

if [ ! -d "$DB_DIR" ] || [ "$(find "$DB_DIR" -type f 2>/dev/null | wc -l)" -eq 0 ]; then
    log_error "❌ 데이터베이스 문제 발견"
    echo "   해결 방법: bash setup_database.sh 실행"
    ((issues++))
fi

if ! systemctl is-active --quiet benefits-api; then
    log_error "❌ 서비스 중지됨"
    echo "   해결 방법: systemctl start benefits-api"
    ((issues++))
fi

if ! curl -s http://localhost/health > /dev/null 2>&1; then
    log_error "❌ 애플리케이션 응답 없음"
    echo "   해결 방법: journalctl -u benefits-api -f로 로그 확인"
    ((issues++))
fi

if [ "$issues" -eq 0 ]; then
    log_info "🎉 모든 검사 통과! 시스템이 정상 작동 중입니다."
else
    log_warning "⚠️ $issues개의 문제가 발견되었습니다. 위의 해결 방법을 참고하세요."
fi

echo ""
echo "🛠️ 유용한 명령어:"
echo "   • 서비스 재시작: systemctl restart benefits-api"
echo "   • 로그 실시간 확인: journalctl -u benefits-api -f"
echo "   • 데이터베이스 재구축: bash setup_database.sh"
echo "   • Nginx 재시작: systemctl restart nginx"
