-- ======================================================================================
-- TTUGTTAG 고도화된 데이터베이스 스키마
-- ======================================================================================

-- 기존 벡터 DB 구조 유지하면서 관계형 DB 추가
-- ChromaDB (벡터 검색용) + SQLite (관계형 데이터용)

-- ======================================================================================
-- 사용자 테이블 (User)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100) UNIQUE NOT NULL,  -- 고유 사용자 ID
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    name VARCHAR(100),
    birth_date DATE,
    gender VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    profile_image_url TEXT,
    preferences JSON  -- 사용자 선호도 (JSON 형태로 저장)
);

-- ======================================================================================
-- 소셜 로그인 테이블 (Social Login)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS social_logins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- 'naver', 'apple', 'google', 'kakao'
    social_user_id VARCHAR(255) NOT NULL,  -- 소셜 플랫폼의 사용자 ID
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    profile_data JSON,  -- 소셜 플랫폼에서 받은 프로필 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(provider, social_user_id)
);

-- ======================================================================================
-- 브랜드 테이블 (Brand)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name VARCHAR(100) UNIQUE NOT NULL,
    brand_code VARCHAR(50) UNIQUE,  -- 브랜드 코드 (기존 DB와 연동)
    description TEXT,
    logo_url TEXT,
    website_url TEXT,
    category VARCHAR(100),  -- 카테고리 (카페, 편의점, 쇼핑몰 등)
    parent_company VARCHAR(100),
    founded_year INTEGER,
    country VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================================================================================
-- 제품 테이블 (Product)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name VARCHAR(255) NOT NULL,
    brand_id INTEGER NOT NULL,
    product_code VARCHAR(100) UNIQUE,
    description TEXT,
    price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    tags JSON,  -- 제품 태그 (JSON 배열)
    image_urls JSON,  -- 제품 이미지 URL들 (JSON 배열)
    specifications JSON,  -- 제품 사양 (JSON)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- ======================================================================================
-- 혜택 테이블 (Benefit)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS benefits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benefit_name VARCHAR(255) NOT NULL,
    benefit_type VARCHAR(50) NOT NULL,  -- 'discount', 'coupon', 'point', 'gift', 'event'
    description TEXT,
    discount_rate DECIMAL(5, 2),  -- 할인율 (%)
    discount_amount DECIMAL(10, 2),  -- 할인 금액
    min_purchase_amount DECIMAL(10, 2),  -- 최소 구매 금액
    max_discount_amount DECIMAL(10, 2),  -- 최대 할인 금액
    point_multiplier DECIMAL(5, 2),  -- 포인트 적립 배수
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    terms_conditions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================================================================================
-- 브랜드-혜택 연결 테이블 (Brand-Benefit)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS brand_benefits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    benefit_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,  -- 혜택 우선순위
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (benefit_id) REFERENCES benefits(id) ON DELETE CASCADE,
    UNIQUE(brand_id, benefit_id)
);

-- ======================================================================================
-- 제품-혜택 연결 테이블 (Product-Benefit)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS product_benefits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    benefit_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (benefit_id) REFERENCES benefits(id) ON DELETE CASCADE,
    UNIQUE(product_id, benefit_id)
);

-- ======================================================================================
-- 사용자 선호도 테이블 (User Preference)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,
    preference_score DECIMAL(3, 2) DEFAULT 0.0,  -- 선호도 점수 (0.0 ~ 1.0)
    interaction_count INTEGER DEFAULT 0,  -- 상호작용 횟수
    last_interaction_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE(user_id, brand_id)
);

-- ======================================================================================
-- 사용자 소비 이력 테이블 (User Spending History)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS user_spending_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,
    product_id INTEGER,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    payment_method VARCHAR(50),  -- 'card', 'cash', 'mobile', 'online'
    location VARCHAR(255),  -- 거래 장소
    category VARCHAR(100),
    tags JSON,  -- 거래 태그
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- ======================================================================================
-- 채팅 로그 테이블 (Chat Log)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(100) NOT NULL,  -- 채팅 세션 ID
    message_type VARCHAR(20) NOT NULL,  -- 'user', 'bot', 'system'
    message_content TEXT NOT NULL,
    message_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    intent VARCHAR(100),  -- 사용자 의도
    entities JSON,  -- 추출된 엔티티들
    confidence_score DECIMAL(3, 2),  -- 의도 인식 신뢰도
    response_time_ms INTEGER,  -- 응답 시간 (밀리초)
    suggested_benefits JSON,  -- 추천된 혜택들
    user_feedback VARCHAR(20),  -- 'like', 'dislike', 'neutral'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ======================================================================================
-- 사용자 혜택 사용 이력 테이블 (User Benefit Usage)
-- ======================================================================================
CREATE TABLE IF NOT EXISTS user_benefit_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    benefit_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,
    usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount_saved DECIMAL(10, 2),  -- 절약된 금액
    status VARCHAR(20) DEFAULT 'used',  -- 'used', 'expired', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (benefit_id) REFERENCES benefits(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- ======================================================================================
-- 인덱스 생성
-- ======================================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_social_logins_provider_user ON social_logins(provider, social_user_id);
CREATE INDEX IF NOT EXISTS idx_brands_category ON brands(category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_benefits_type ON benefits(benefit_type);
CREATE INDEX IF NOT EXISTS idx_benefits_active ON benefits(is_active);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_brand ON user_preferences(brand_id);
CREATE INDEX IF NOT EXISTS idx_spending_history_user ON user_spending_history(user_id);
CREATE INDEX IF NOT EXISTS idx_spending_history_brand ON user_spending_history(brand_id);
CREATE INDEX IF NOT EXISTS idx_spending_history_date ON user_spending_history(transaction_date);
CREATE INDEX IF NOT EXISTS idx_chat_logs_user ON chat_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_timestamp ON chat_logs(message_timestamp);

-- ======================================================================================
-- 샘플 데이터 삽입
-- ======================================================================================

-- 브랜드 샘플 데이터
INSERT OR IGNORE INTO brands (brand_name, brand_code, category, description) VALUES
('스타벅스', 'SBUX', '카페', '글로벌 커피 체인점'),
('이마트', 'EMART', '마트', '대형 할인마트'),
('올리브영', 'OLIVEYOUNG', '화장품', '헬스&뷰티 전문점'),
('쿠팡', 'COUPANG', '온라인쇼핑', '온라인 커머스 플랫폼'),
('배스킨라빈스', 'BASKINROBBINS', '아이스크림', '아이스크림 전문점');

-- 혜택 샘플 데이터
INSERT OR IGNORE INTO benefits (benefit_name, benefit_type, description, discount_rate, start_date, end_date) VALUES
('신규 가입 할인', 'discount', '신규 고객 20% 할인', 20.00, '2025-01-01', '2025-12-31'),
('생일 축하 쿠폰', 'coupon', '생일 축하 5,000원 쿠폰', NULL, '2025-01-01', '2025-12-31'),
('포인트 적립 이벤트', 'point', '구매 금액의 10% 포인트 적립', NULL, '2025-01-01', '2025-12-31'),
('무료 배송', 'event', '3만원 이상 구매시 무료 배송', NULL, '2025-01-01', '2025-12-31');

-- 브랜드-혜택 연결
INSERT OR IGNORE INTO brand_benefits (brand_id, benefit_id) VALUES
(1, 1), (1, 2), (1, 3),  -- 스타벅스
(2, 1), (2, 3), (2, 4),  -- 이마트
(3, 1), (3, 2), (3, 3),  -- 올리브영
(4, 1), (4, 3), (4, 4),  -- 쿠팡
(5, 1), (5, 2), (5, 3);  -- 배스킨라빈스 