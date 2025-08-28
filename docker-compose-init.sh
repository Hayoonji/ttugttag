#!/bin/bash

# ======================================================================================
# TTUGTTAG Docker Compose 초기화 스크립트
# ======================================================================================

set -e

echo "🚀 TTUGTTAG Docker Compose 초기화 시작..."

# Docker Compose 실행
echo "📦 Docker Compose 서비스 시작 중..."
docker-compose up -d

# 데이터베이스 초기화 대기
echo "⏳ PostgreSQL 데이터베이스 초기화 대기 중..."
sleep 30

# 데이터베이스 연결 확인
echo "🔍 데이터베이스 연결 상태 확인 중..."
docker-compose exec postgres pg_isready -U ttugttag_user -d ttugttag

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL 데이터베이스 연결 성공!"
else
    echo "❌ PostgreSQL 데이터베이스 연결 실패"
    exit 1
fi

# 데이터 확인
echo "📊 데이터베이스 데이터 확인 중..."
docker-compose exec postgres psql -U ttugttag_user -d ttugttag -c "
SELECT 
    '브랜드' as table_name, COUNT(*) as count FROM brands
UNION ALL
SELECT '사용자', COUNT(*) FROM users
UNION ALL
SELECT '혜택', COUNT(*) FROM benefits
UNION ALL
SELECT '제품', COUNT(*) FROM products
UNION ALL
SELECT '사용자 선호도', COUNT(*) FROM user_preferences
UNION ALL
SELECT '소비 이력', COUNT(*) FROM spending_history
UNION ALL
SELECT '채팅 로그', COUNT(*) FROM chat_logs
ORDER BY table_name;
"

# 샘플 데이터 조회
echo "🔍 샘플 데이터 조회 중..."
echo "=== 브랜드 목록 ==="
docker-compose exec postgres psql -U ttugttag_user -d ttugttag -c "SELECT brand_name, category FROM brands ORDER BY category, brand_name;"

echo "=== 사용자 목록 ==="
docker-compose exec postgres psql -U ttugttag_user -d ttugttag -c "SELECT name, email, preferences->>'favorite_category' as favorite FROM users;"

echo "=== 혜택 목록 ==="
docker-compose exec postgres psql -U ttugttag_user -d ttugttag -c "SELECT b.benefit_name, br.brand_name, b.benefit_type, b.description FROM benefits b JOIN brands br ON b.brand_id = br.id ORDER BY br.brand_name;"

# 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
docker-compose ps

echo "🎉 TTUGTTAG Docker Compose 초기화 완료!"
echo ""
echo "📋 접속 정보:"
echo "- 애플리케이션: http://localhost:5001"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo ""
echo "🔧 유용한 명령어:"
echo "- 서비스 중지: docker-compose down"
echo "- 로그 확인: docker-compose logs -f"
echo "- 데이터베이스 접속: docker-compose exec postgres psql -U ttugttag_user -d ttugttag"
echo "- 서비스 재시작: docker-compose restart" 