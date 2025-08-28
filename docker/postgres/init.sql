-- ======================================================================================
-- TTUGTTAG PostgreSQL 데이터베이스 스키마 초기화
-- ======================================================================================

-- 데이터베이스 생성 (이미 생성되어 있음)
-- CREATE DATABASE ttugttag;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    name VARCHAR(100),
    birth_date DATE,
    gender VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    profile_image_url TEXT,
    preferences JSONB
);

-- 소셜 로그인 테이블
CREATE TABLE IF NOT EXISTS social_logins (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    provider VARCHAR(50) NOT NULL,
    social_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    profile_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(provider, social_user_id)
);

-- 브랜드 테이블
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    brand_name VARCHAR(100) UNIQUE NOT NULL,
    brand_code VARCHAR(50) UNIQUE,
    description TEXT,
    logo_url TEXT,
    website_url TEXT,
    category VARCHAR(100),
    parent_company VARCHAR(100),
    founded_year INTEGER,
    country VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 제품 테이블
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    brand_id INTEGER NOT NULL,
    product_code VARCHAR(100) UNIQUE,
    description TEXT,
    price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    tags JSONB,
    image_urls JSONB,
    specifications JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- 혜택 테이블
CREATE TABLE IF NOT EXISTS benefits (
    id SERIAL PRIMARY KEY,
    benefit_name VARCHAR(255) NOT NULL,
    benefit_type VARCHAR(50) NOT NULL,
    description TEXT,
    discount_rate DECIMAL(5, 2),
    discount_amount DECIMAL(10, 2),
    min_purchase_amount DECIMAL(10, 2),
    max_discount_amount DECIMAL(10, 2),
    point_multiplier DECIMAL(5, 2),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    conditions TEXT,
    brand_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- 사용자 선호도 테이블
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,
    score DECIMAL(3, 2) DEFAULT 0.50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE(user_id, brand_id)
);

-- 소비 이력 테이블
CREATE TABLE IF NOT EXISTS spending_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    product_id VARCHAR(100),
    payment_method VARCHAR(50),
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- 채팅 로그 테이블
CREATE TABLE IF NOT EXISTS chat_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(100),
    message_type VARCHAR(20),
    message_content TEXT,
    intent VARCHAR(100),
    entities JSONB,
    confidence_score DECIMAL(3, 2),
    response_time_ms INTEGER,
    suggested_benefits JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_brands_category ON brands(category);
CREATE INDEX IF NOT EXISTS idx_benefits_brand_id ON benefits(brand_id);
CREATE INDEX IF NOT EXISTS idx_benefits_type ON benefits(benefit_type);
CREATE INDEX IF NOT EXISTS idx_spending_history_user_id ON spending_history(user_id);
CREATE INDEX IF NOT EXISTS idx_spending_history_brand_id ON spending_history(brand_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id ON chat_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_session_id ON chat_logs(session_id);

-- 시퀀스 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_benefits_updated_at BEFORE UPDATE ON benefits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰 생성
CREATE OR REPLACE VIEW user_benefit_summary AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    b.brand_name,
    COUNT(sh.id) as visit_count,
    SUM(sh.amount) as total_spending,
    AVG(up.score) as preference_score
FROM users u
LEFT JOIN spending_history sh ON u.id = sh.user_id
LEFT JOIN brands b ON sh.brand_id = b.id
LEFT JOIN user_preferences up ON u.id = up.user_id AND b.id = up.brand_id
GROUP BY u.id, u.name, b.brand_name, b.id;

-- 권한 설정
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ttugttag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ttugttag_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ttugttag_user;

-- 스키마 생성 완료 로그
DO $$
BEGIN
    RAISE NOTICE 'TTUGTTAG 데이터베이스 스키마 생성 완료';
    RAISE NOTICE '생성된 테이블: users, social_logins, brands, products, benefits, user_preferences, spending_history, chat_logs';
END $$; 