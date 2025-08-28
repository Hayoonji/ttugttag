#!/bin/bash

# ======================================================================================
# Docker 컨테이너 시작 시 데이터베이스 초기화 스크립트
# ======================================================================================

set -e

echo "🚀 데이터베이스 초기화 시작..."

# 프로젝트 루트 디렉토리
PROJECT_ROOT="/app"
DB_DIR="${PROJECT_ROOT}/enhanced_db"
CAFE_DB_DIR="${PROJECT_ROOT}/cafe_vector_db"

# 데이터베이스 디렉토리 생성
mkdir -p "$DB_DIR"
mkdir -p "$CAFE_DB_DIR"

echo "📁 데이터베이스 디렉토리 생성 완료"

# enhanced_db의 기존 데이터베이스 파일이 있다면 복사
if [ -f "${PROJECT_ROOT}/enhanced_db/ttugttag.db" ]; then
    echo "📋 기존 데이터베이스 파일 복사 중..."
    cp "${PROJECT_ROOT}/enhanced_db/ttugttag.db" "$DB_DIR/"
    echo "✅ 데이터베이스 파일 복사 완료"
else
    echo "⚠️ 기존 데이터베이스 파일이 없습니다. 새로 생성합니다."
    
    # Python 스크립트로 데이터베이스 초기화
    python3 << 'EOF'
import sqlite3
import os
import json
from datetime import datetime

# 데이터베이스 경로
db_path = "/app/enhanced_db/ttugttag.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# 데이터베이스 연결 및 테이블 생성
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 사용자 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    phone TEXT,
    name TEXT,
    birth_date TEXT,
    gender TEXT,
    preferences TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 브랜드 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    logo_url TEXT,
    website TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 혜택 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS benefits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    benefit_type TEXT,
    discount_rate REAL,
    discount_amount INTEGER,
    min_purchase INTEGER,
    max_discount INTEGER,
    start_date TEXT,
    end_date TEXT,
    conditions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands (id)
)
''')

# 사용자 선호도 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    brand_id INTEGER,
    score REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (brand_id) REFERENCES brands (id)
)
''')

# 소비 이력 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS spending_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    brand_id INTEGER,
    amount INTEGER,
    product_id TEXT,
    payment_method TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (brand_id) REFERENCES brands (id)
)
''')

# 채팅 로그 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_id TEXT,
    message_type TEXT,
    message_content TEXT,
    intent TEXT,
    entities TEXT,
    confidence_score REAL,
    response_time_ms INTEGER,
    suggested_benefits TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# 샘플 데이터 삽입
# 샘플 브랜드
brands_data = [
    ('스타벅스', '카페', '글로벌 커피 체인점', 'https://example.com/starbucks.png', 'https://www.starbucks.co.kr'),
    ('투썹플레이스', '카페', '국내 커피 체인점', 'https://example.com/twosome.png', 'https://www.twosome.co.kr'),
    ('할리스커피', '카페', '국내 커피 체인점', 'https://example.com/hollys.png', 'https://www.hollys.co.kr'),
    ('이디야커피', '카페', '국내 커피 체인점', 'https://example.com/ediya.png', 'https://www.ediya.com'),
    ('메가MGC커피', '카페', '국내 커피 체인점', 'https://example.com/mega.png', 'https://www.megacoffee.co.kr')
]

for brand in brands_data:
    cursor.execute('''
    INSERT OR IGNORE INTO brands (brand_name, category, description, logo_url, website)
    VALUES (?, ?, ?, ?, ?)
    ''', brand)

# 샘플 혜택
benefits_data = [
    (1, '신규 고객 할인', '신규 고객 20% 할인', 'discount', 0.2, None, 5000, 3000, '2024-01-01', '2024-12-31', '신규 고객만'),
    (1, '생일 축하 할인', '생일 당일 30% 할인', 'discount', 0.3, None, 10000, 5000, '2024-01-01', '2024-12-31', '생일 당일만'),
    (2, '첫 구매 할인', '첫 구매 15% 할인', 'discount', 0.15, None, 3000, 2000, '2024-01-01', '2024-12-31', '첫 구매 고객만'),
    (3, '주말 특가', '주말 25% 할인', 'discount', 0.25, None, 8000, 4000, '2024-01-01', '2024-12-31', '주말만'),
    (4, '이벤트 할인', '이벤트 기간 10% 할인', 'discount', 0.1, None, 5000, 2000, '2024-01-01', '2024-12-31', '이벤트 기간만'),
    (5, '새벽 할인', '새벽 시간 20% 할인', 'discount', 0.2, None, 3000, 1500, '2024-01-01', '2024-12-31', '새벽 2-6시')
]

for benefit in benefits_data:
    cursor.execute('''
    INSERT OR IGNORE INTO benefits (brand_id, title, description, benefit_type, discount_rate, discount_amount, min_purchase, max_discount, start_date, end_date, conditions)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', benefit)

# 샘플 사용자
users_data = [
    ('user001', 'user001@example.com', '010-1234-5678', '김철수', '1990-01-01', 'M', '{"favorite_category": "카페", "preferred_time": "오후"}'),
    ('user002', 'user002@example.com', '010-2345-6789', '이영희', '1992-05-15', 'F', '{"favorite_category": "카페", "preferred_time": "아침"}'),
    ('user003', 'user003@example.com', '010-3456-7890', '박민수', '1988-12-25', 'M', '{"favorite_category": "카페", "preferred_time": "저녁"}')
]

for user in users_data:
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, email, phone, name, birth_date, gender, preferences)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', user)

# 샘플 사용자 선호도
preferences_data = [
    (1, 1, 0.8),  # user001이 스타벅스 선호도 0.8
    (1, 2, 0.6),  # user001이 투썹플레이스 선호도 0.6
    (2, 1, 0.7),  # user002가 스타벅스 선호도 0.7
    (2, 3, 0.9),  # user002가 할리스 선호도 0.9
    (3, 4, 0.8),  # user003이 이디야 선호도 0.8
    (3, 5, 0.7)   # user003이 메가MGC 선호도 0.7
]

for pref in preferences_data:
    cursor.execute('''
    INSERT OR IGNORE INTO user_preferences (user_id, brand_id, score)
    VALUES (?, ?, ?)
    ''', pref)

# 샘플 소비 이력
spending_data = [
    (1, 1, 15000, 'COFFEE001', '카드', '강남점'),
    (1, 2, 12000, 'COFFEE002', '현금', '홍대점'),
    (2, 1, 18000, 'COFFEE003', '카드', '신촌점'),
    (2, 3, 14000, 'COFFEE004', '카드', '강남점'),
    (3, 4, 16000, 'COFFEE005', '현금', '홍대점'),
    (3, 5, 11000, 'COFFEE006', '카드', '신촌점')
]

for spending in spending_data:
    cursor.execute('''
    INSERT OR IGNORE INTO spending_history (user_id, brand_id, amount, product_id, payment_method, location)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', spending)

# 샘플 채팅 로그
chat_data = [
    (1, 'session001', 'user', '안녕하세요, 커피 추천해주세요', 'greeting', '{"intent": "coffee_recommendation"}', 0.9, 150, '["스타벅스 신규 고객 할인", "투썹플레이스 첫 구매 할인"]'),
    (1, 'session001', 'assistant', '안녕하세요! 커피 추천해드릴게요. 스타벅스 신규 고객 20% 할인과 투썹플레이스 첫 구매 15% 할인이 있어요.', 'assistant', '{"intent": "coffee_recommendation"}', 0.95, 200, '[]'),
    (2, 'session002', 'user', '생일 할인 혜택이 있나요?', 'benefit_inquiry', '{"intent": "birthday_discount"}', 0.8, 120, '["스타벅스 생일 축하 할인"]'),
    (2, 'session002', 'assistant', '네! 스타벅스에서 생일 당일 30% 할인 혜택을 제공하고 있어요. 1만원 이상 구매 시 최대 5천원 할인받을 수 있어요.', 'assistant', '{"intent": "birthday_discount"}', 0.9, 180, '[]')
]

for chat in chat_data:
    cursor.execute('''
    INSERT OR IGNORE INTO chat_logs (user_id, session_id, message_type, message_content, intent, entities, confidence_score, response_time_ms, suggested_benefits)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', chat)

conn.commit()
conn.close()

print("✅ 데이터베이스 초기화 완료")
print(f"📊 생성된 테이블: users, brands, benefits, user_preferences, spending_history, chat_logs")
print(f"📈 샘플 데이터: 5개 브랜드, 6개 혜택, 3명 사용자, 6개 선호도, 6개 소비이력, 4개 채팅로그")
EOF
fi

# cafe_vector_db 디렉토리도 초기화
if [ -d "${PROJECT_ROOT}/cafe_vector_db" ] && [ "$(ls -A ${PROJECT_ROOT}/cafe_vector_db 2>/dev/null)" ]; then
    echo "📋 cafe_vector_db 파일 복사 중..."
    cp -r "${PROJECT_ROOT}/cafe_vector_db"/* "$CAFE_DB_DIR/"
    echo "✅ cafe_vector_db 파일 복사 완료"
else
    echo "📁 cafe_vector_db 디렉토리 생성 완료"
fi

echo "🎉 데이터베이스 초기화 완료!"
echo "📊 데이터베이스 위치: $DB_DIR"
echo "☕ 카페 벡터 DB 위치: $CAFE_DB_DIR" 