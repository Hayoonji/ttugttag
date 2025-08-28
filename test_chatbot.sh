#!/bin/bash

# ======================================================================================
# 챗봇 웹 인터페이스 테스트 스크립트
# ======================================================================================

echo "🤖 챗봇 웹 인터페이스 테스트 시작"
echo "================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 서버 URL (필요에 따라 수정)
BASE_URL="${1:-http://localhost}"

echo "🌐 테스트 대상: $BASE_URL"
echo ""

# 1. 웹 인터페이스 접근 테스트
echo "1️⃣ 웹 인터페이스 접근 테스트"
echo "----------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ 웹 인터페이스 접근 성공 (HTTP $response)${NC}"
else
    echo -e "${RED}❌ 웹 인터페이스 접근 실패 (HTTP $response)${NC}"
fi
echo ""

# 2. API 정보 확인
echo "2️⃣ API 정보 확인"
echo "----------------"
response=$(curl -s "$BASE_URL/api/info")
if echo "$response" | grep -q "service_name"; then
    echo -e "${GREEN}✅ API 정보 조회 성공${NC}"
    echo "$response" | python3 -m json.tool | head -10
else
    echo -e "${RED}❌ API 정보 조회 실패${NC}"
    echo "$response"
fi
echo ""

# 3. 헬스체크
echo "3️⃣ 헬스체크"
echo "----------"
response=$(curl -s "$BASE_URL/health")
if echo "$response" | grep -q "healthy"; then
    echo -e "${GREEN}✅ 헬스체크 성공${NC}"
    echo "$response" | python3 -m json.tool
else
    echo -e "${RED}❌ 헬스체크 실패${NC}"
    echo "$response"
fi
echo ""

# 4. 챗봇 API 테스트
echo "4️⃣ 챗봇 API 테스트"
echo "-------------------"
chat_response=$(curl -s -X POST "$BASE_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "안녕하세요", "user_id": "test_user", "user_context": {"spending_history": []}}')

if echo "$chat_response" | grep -q "success"; then
    echo -e "${GREEN}✅ 챗봇 API 테스트 성공${NC}"
    echo "$chat_response" | python3 -m json.tool | head -20
else
    echo -e "${RED}❌ 챗봇 API 테스트 실패${NC}"
    echo "$chat_response"
fi
echo ""

# 5. 통합 AI 엔드포인트 테스트
echo "5️⃣ 통합 AI 엔드포인트 테스트"
echo "----------------------------"
unified_response=$(curl -s -X POST "$BASE_URL/unified-ai" \
    -H "Content-Type: application/json" \
    -d '{"message": "스타벅스 혜택 알려주세요"}')

if echo "$unified_response" | grep -q "success"; then
    echo -e "${GREEN}✅ 통합 AI 테스트 성공${NC}"
    echo "$unified_response" | python3 -m json.tool | head -15
else
    echo -e "${RED}❌ 통합 AI 테스트 실패${NC}"
    echo "$unified_response"
fi
echo ""

# 6. Docker 컨테이너 상태 확인 (로컬인 경우)
if [ "$BASE_URL" = "http://localhost" ]; then
    echo "6️⃣ Docker 컨테이너 상태 확인"
    echo "----------------------------"
    if command -v docker-compose &> /dev/null; then
        echo "🐳 Docker Compose 서비스 상태:"
        docker-compose ps
    else
        echo -e "${YELLOW}⚠️ docker-compose 명령을 찾을 수 없습니다${NC}"
    fi
    echo ""
fi

# 7. 브라우저 테스트 안내
echo "7️⃣ 브라우저 테스트"
echo "-------------------"
echo "🖥️ 브라우저에서 다음 URL로 접속하여 수동 테스트하세요:"
echo "   $BASE_URL"
echo ""
echo "✨ 테스트할 챗봇 질문 예시:"
echo "   • 스타벅스에서 자주 소비하는데 어떤 혜택이 있을까요?"
echo "   • 배달음식 할인 쿠폰 정보 알려주세요"
echo "   • 겨울 시즌 특별 혜택 알려주세요"
echo "   • 카페 혜택 비교해주세요"
echo ""

echo "🎉 테스트 완료!"
echo "문제가 발생하면 다음 명령으로 로그를 확인하세요:"
echo "  docker-compose logs -f app"
echo "  docker-compose logs -f nginx"
