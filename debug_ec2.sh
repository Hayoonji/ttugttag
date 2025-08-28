#!/bin/bash

# ======================================================================================
# EC2 에러 디버깅 스크립트
# ======================================================================================

echo "🔍 EC2 에러 디버깅 시작"
echo "====================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "1️⃣ Docker 서비스 상태 확인"
echo "------------------------"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker 설치됨${NC}"
    docker --version
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose 설치됨${NC}"
        docker-compose --version
    else
        echo -e "${RED}❌ Docker Compose 설치 안됨${NC}"
    fi
else
    echo -e "${RED}❌ Docker 설치 안됨${NC}"
fi

echo ""
echo "2️⃣ 컨테이너 상태 확인"
echo "-------------------"
if [ -f "docker-compose.yml" ]; then
    echo "📋 Docker Compose 파일 존재"
    docker-compose ps
    echo ""
    
    echo "📊 실행 중인 모든 컨테이너:"
    docker ps -a
else
    echo -e "${YELLOW}⚠️ docker-compose.yml 파일이 없습니다${NC}"
fi

echo ""
echo "3️⃣ 포트 사용 상태 확인"
echo "--------------------"
echo "포트 80 (HTTP) 사용 상태:"
sudo netstat -tlnp | grep :80 || echo "포트 80 사용 안함"

echo ""
echo "포트 443 (HTTPS) 사용 상태:"
sudo netstat -tlnp | grep :443 || echo "포트 443 사용 안함"

echo ""
echo "포트 5000 (Flask) 사용 상태:"
sudo netstat -tlnp | grep :5000 || echo "포트 5000 사용 안함"

echo ""
echo "4️⃣ 디스크 용량 확인"
echo "------------------"
df -h

echo ""
echo "5️⃣ 메모리 사용량 확인"
echo "-------------------"
free -h

echo ""
echo "6️⃣ 환경 변수 파일 확인"
echo "--------------------"
if [ -f ".env.docker" ]; then
    echo -e "${GREEN}✅ .env.docker 파일 존재${NC}"
    echo "파일 크기: $(ls -lh .env.docker | awk '{print $5}')"
else
    echo -e "${YELLOW}⚠️ .env.docker 파일이 없습니다${NC}"
    if [ -f "env.example" ]; then
        echo "env.example 파일이 있습니다. 복사하세요:"
        echo "cp env.example .env.docker"
    fi
fi

echo ""
echo "7️⃣ 로그 확인"
echo "------------"
if [ -f "docker-compose.yml" ]; then
    echo "📝 최근 앱 로그 (마지막 20줄):"
    docker-compose logs --tail=20 app 2>/dev/null || echo "앱 컨테이너 로그 없음"
    
    echo ""
    echo "📝 최근 Nginx 로그 (마지막 20줄):"
    docker-compose logs --tail=20 nginx 2>/dev/null || echo "Nginx 컨테이너 로그 없음"
fi

echo ""
echo "8️⃣ 파일 권한 확인"
echo "----------------"
echo "현재 디렉토리 권한:"
ls -la . | head -10

echo ""
echo "Docker 관련 파일 권한:"
ls -la docker-compose.yml Dockerfile 2>/dev/null || echo "Docker 파일들이 없습니다"

echo ""
echo "9️⃣ 네트워크 상태 확인"
echo "-------------------"
echo "Docker 네트워크:"
docker network ls 2>/dev/null || echo "Docker 네트워크 정보 없음"

echo ""
echo "🔟 서비스 접근 테스트"
echo "-------------------"
echo "로컬 연결 테스트:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/ || echo "로컬 접속 실패"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/health || echo "헬스체크 실패"

echo ""
echo "🎯 일반적인 해결 방법"
echo "==================="
echo "1. 컨테이너 재시작:"
echo "   docker-compose down && docker-compose up -d"
echo ""
echo "2. 이미지 재빌드:"
echo "   docker-compose build --no-cache"
echo ""
echo "3. 볼륨 정리:"
echo "   docker-compose down -v"
echo ""
echo "4. 전체 정리 후 재시작:"
echo "   docker-compose down && docker system prune -f && docker-compose up -d"
echo ""
echo "5. 권한 문제 해결:"
echo "   sudo chown -R \$USER:\$USER ."
echo ""
echo "6. 포트 충돌 해결:"
echo "   sudo lsof -i :80"
echo "   sudo lsof -i :443"
echo ""

echo "✅ 디버깅 완료!"
echo "구체적인 에러 메시지를 알려주시면 더 정확한 해결책을 제공할 수 있습니다."
