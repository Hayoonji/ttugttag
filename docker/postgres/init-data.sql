-- ======================================================================================
-- TTUGTTAG PostgreSQL 샘플 데이터 삽입
-- ======================================================================================

-- 샘플 브랜드 데이터 삽입
INSERT INTO brands (brand_name, brand_code, description, logo_url, website_url, category, parent_company, founded_year, country) VALUES
('스타벅스', 'SB', '글로벌 커피 체인점', 'https://example.com/starbucks.png', 'https://www.starbucks.co.kr', '카페', '스타벅스 코퍼레이션', 1971, '미국'),
('투썹플레이스', 'TS', '국내 커피 체인점', 'https://example.com/twosome.png', 'https://www.twosome.co.kr', '카페', 'CJ푸드빌', 2002, '대한민국'),
('할리스커피', 'HL', '국내 커피 체인점', 'https://example.com/hollys.png', 'https://www.hollys.co.kr', '카페', '할리스커피', 1998, '대한민국'),
('이디야커피', 'ED', '국내 커피 체인점', 'https://example.com/ediya.png', 'https://www.ediya.com', '카페', '이디야커피', 2001, '대한민국'),
('메가MGC커피', 'MG', '국내 커피 체인점', 'https://example.com/mega.png', 'https://www.megacoffee.co.kr', '카페', '메가MGC커피', 2007, '대한민국'),
('GS25', 'GS', '편의점 체인', 'https://example.com/gs25.png', 'https://www.gs25.com', '편의점', 'GS리테일', 1990, '대한민국'),
('CU', 'CU', '편의점 체인', 'https://example.com/cu.png', 'https://www.cu.co.kr', '편의점', 'BGF리테일', 1990, '대한민국'),
('세븐일레븐', '7E', '편의점 체인', 'https://example.com/seven.png', 'https://www.7-eleven.co.kr', '편의점', '한국세븐일레븐', 1989, '대한민국'),
('이마트', 'EM', '대형 할인마트', 'https://example.com/emart.png', 'https://www.emart.com', '마트', '신세계', 1993, '대한민국'),
('홈플러스', 'HP', '대형 할인마트', 'https://example.com/homeplus.png', 'https://www.homeplus.co.kr', '마트', '홈플러스', 1999, '대한민국')
ON CONFLICT (brand_name) DO NOTHING;

-- 샘플 사용자 데이터 삽입
INSERT INTO users (user_id, email, phone, name, birth_date, gender, preferences) VALUES
('user001', 'user001@example.com', '010-1234-5678', '김철수', '1990-01-01', 'M', '{"favorite_category": "카페", "preferred_time": "오후", "budget_range": "10000-30000"}'),
('user002', 'user002@example.com', '010-2345-6789', '이영희', '1992-05-15', 'F', '{"favorite_category": "카페", "preferred_time": "아침", "budget_range": "5000-20000"}'),
('user003', 'user003@example.com', '010-3456-7890', '박민수', '1988-12-25', 'M', '{"favorite_category": "편의점", "preferred_time": "저녁", "budget_range": "3000-15000"}'),
('user004', 'user004@example.com', '010-4567-8901', '최지영', '1995-08-20', 'F', '{"favorite_category": "마트", "preferred_time": "주말", "budget_range": "50000-100000"}'),
('user005', 'user005@example.com', '010-5678-9012', '정현우', '1991-03-10', 'M', '{"favorite_category": "카페", "preferred_time": "새벽", "budget_range": "8000-25000"}')
ON CONFLICT (user_id) DO NOTHING;

-- 샘플 혜택 데이터 삽입
INSERT INTO benefits (benefit_name, benefit_type, description, discount_rate, discount_amount, min_purchase_amount, max_discount_amount, start_date, end_date, conditions, brand_id) VALUES
('신규 고객 할인', 'discount', '신규 고객 20% 할인', 0.20, NULL, 5000, 3000, '2024-01-01', '2024-12-31', '신규 고객만', 1),
('생일 축하 할인', 'discount', '생일 당일 30% 할인', 0.30, NULL, 10000, 5000, '2024-01-01', '2024-12-31', '생일 당일만', 1),
('첫 구매 할인', 'discount', '첫 구매 15% 할인', 0.15, NULL, 3000, 2000, '2024-01-01', '2024-12-31', '첫 구매 고객만', 2),
('주말 특가', 'discount', '주말 25% 할인', 0.25, NULL, 8000, 4000, '2024-01-01', '2024-12-31', '주말만', 3),
('이벤트 할인', 'discount', '이벤트 기간 10% 할인', 0.10, NULL, 5000, 2000, '2024-01-01', '2024-12-31', '이벤트 기간만', 4),
('새벽 할인', 'discount', '새벽 시간 20% 할인', 0.20, NULL, 3000, 1500, '2024-01-01', '2024-12-31', '새벽 2-6시', 5),
('편의점 쿠폰', 'coupon', '5000원 구매 시 1000원 할인', NULL, 1000, 5000, 1000, '2024-01-01', '2024-12-31', '모든 고객', 6),
('편의점 포인트', 'point', '구매 금액의 5% 포인트 적립', NULL, NULL, 1000, NULL, '2024-01-01', '2024-12-31', '회원만', 7),
('마트 할인', 'discount', '10만원 이상 구매 시 5% 할인', 0.05, NULL, 100000, 10000, '2024-01-01', '2024-12-31', '모든 고객', 9),
('마트 적립', 'point', '구매 금액의 3% 적립', NULL, NULL, 50000, NULL, '2024-01-01', '2024-12-31', '회원만', 10)
ON CONFLICT DO NOTHING;

-- 샘플 사용자 선호도 데이터 삽입
INSERT INTO user_preferences (user_id, brand_id, score) VALUES
(1, 1, 0.85),  -- 김철수 - 스타벅스 선호도 0.85
(1, 2, 0.70),  -- 김철수 - 투썹플레이스 선호도 0.70
(2, 1, 0.75),  -- 이영희 - 스타벅스 선호도 0.75
(2, 3, 0.90),  -- 이영희 - 할리스 선호도 0.90
(3, 6, 0.80),  -- 박민수 - GS25 선호도 0.80
(3, 7, 0.65),  -- 박민수 - CU 선호도 0.65
(4, 9, 0.95),  -- 최지영 - 이마트 선호도 0.95
(4, 10, 0.70), -- 최지영 - 홈플러스 선호도 0.70
(5, 1, 0.60),  -- 정현우 - 스타벅스 선호도 0.60
(5, 5, 0.85)   -- 정현우 - 메가MGC 선호도 0.85
ON CONFLICT (user_id, brand_id) DO UPDATE SET score = EXCLUDED.score;

-- 샘플 소비 이력 데이터 삽입
INSERT INTO spending_history (user_id, brand_id, amount, product_id, payment_method, location) VALUES
(1, 1, 15000, 'COFFEE001', '카드', '강남점'),
(1, 2, 12000, 'COFFEE002', '현금', '홍대점'),
(1, 1, 18000, 'COFFEE003', '카드', '신촌점'),
(2, 1, 14000, 'COFFEE004', '카드', '강남점'),
(2, 3, 16000, 'COFFEE005', '현금', '홍대점'),
(2, 3, 11000, 'COFFEE006', '카드', '신촌점'),
(3, 6, 8000, 'CONV001', '카드', '강남점'),
(3, 7, 12000, 'CONV002', '현금', '홍대점'),
(3, 6, 15000, 'CONV003', '카드', '신촌점'),
(4, 9, 85000, 'MART001', '카드', '강남점'),
(4, 10, 120000, 'MART002', '카드', '홍대점'),
(4, 9, 95000, 'MART003', '현금', '신촌점'),
(5, 1, 22000, 'COFFEE007', '카드', '강남점'),
(5, 5, 18000, 'COFFEE008', '현금', '홍대점'),
(5, 5, 14000, 'COFFEE009', '카드', '신촌점')
ON CONFLICT DO NOTHING;

-- 샘플 채팅 로그 데이터 삽입
INSERT INTO chat_logs (user_id, session_id, message_type, message_content, intent, entities, confidence_score, response_time_ms, suggested_benefits) VALUES
(1, 'session001', 'user', '안녕하세요, 커피 추천해주세요', 'greeting', '{"intent": "coffee_recommendation"}', 0.90, 150, '["스타벅스 신규 고객 할인", "투썹플레이스 첫 구매 할인"]'),
(1, 'session001', 'assistant', '안녕하세요! 커피 추천해드릴게요. 스타벅스 신규 고객 20% 할인과 투썹플레이스 첫 구매 15% 할인이 있어요.', 'assistant', '{"intent": "coffee_recommendation"}', 0.95, 200, '[]'),
(2, 'session002', 'user', '생일 할인 혜택이 있나요?', 'benefit_inquiry', '{"intent": "birthday_discount"}', 0.85, 120, '["스타벅스 생일 축하 할인"]'),
(2, 'session002', 'assistant', '네! 스타벅스에서 생일 당일 30% 할인 혜택을 제공하고 있어요. 1만원 이상 구매 시 최대 5천원 할인받을 수 있어요.', 'assistant', '{"intent": "birthday_discount"}', 0.90, 180, '[]'),
(3, 'session003', 'user', '편의점 할인 혜택 알려주세요', 'benefit_inquiry', '{"intent": "convenience_discount"}', 0.80, 100, '["GS25 편의점 쿠폰", "CU 편의점 포인트"]'),
(3, 'session003', 'assistant', '편의점 할인 혜택을 알려드릴게요! GS25에서는 5000원 구매 시 1000원 할인, CU에서는 5% 포인트 적립 혜택이 있어요.', 'assistant', '{"intent": "convenience_discount"}', 0.88, 160, '[]'),
(4, 'session004', 'user', '마트에서 10만원 썼어, 혜택 추천해줘', 'benefit_inquiry', '{"intent": "mart_discount", "amount": 100000}', 0.92, 140, '["이마트 5% 할인", "홈플러스 3% 적립"]'),
(4, 'session004', 'assistant', '10만원 구매하셨군요! 이마트에서는 5% 할인(최대 1만원), 홈플러스에서는 3% 포인트 적립 혜택을 받을 수 있어요.', 'assistant', '{"intent": "mart_discount"}', 0.94, 190, '[]'),
(5, 'session005', 'user', '새벽에 커피 마실 수 있는 곳 있어?', 'location_inquiry', '{"intent": "late_night_coffee", "time": "새벽"}', 0.87, 110, '["메가MGC 새벽 할인"]'),
(5, 'session005', 'assistant', '새벽에도 커피를 마실 수 있어요! 메가MGC에서 새벽 2-6시에 20% 할인 혜택을 제공하고 있어요.', 'assistant', '{"intent": "late_night_coffee"}', 0.91, 170, '[]')
ON CONFLICT DO NOTHING;

-- 샘플 제품 데이터 삽입
INSERT INTO products (product_name, brand_id, product_code, description, price, original_price, category, subcategory, tags, image_urls, specifications) VALUES
('아메리카노', 1, 'SB_AMERICANO', '스타벅스 시그니처 아메리카노', 4500, 4500, '음료', '커피', '["커피", "아메리카노", "시그니처"]', '["https://example.com/americano1.jpg", "https://example.com/americano2.jpg"]', '{"size": "Tall", "temperature": "Hot", "caffeine": "150mg"}'),
('카페라떼', 1, 'SB_LATTE', '부드러운 우유와 에스프레소의 조화', 5000, 5000, '음료', '커피', '["커피", "라떼", "우유"]', '["https://example.com/latte1.jpg"]', '{"size": "Tall", "temperature": "Hot", "caffeine": "150mg"}'),
('카푸치노', 2, 'TS_CAPPUCCINO', '투썹플레이스 특제 카푸치노', 4800, 4800, '음료', '커피', '["커피", "카푸치노", "특제"]', '["https://example.com/cappuccino1.jpg"]', '{"size": "Regular", "temperature": "Hot", "caffeine": "120mg"}'),
('에스프레소', 3, 'HL_ESPRESSO', '할리스커피 강렬한 에스프레소', 3500, 3500, '음료', '커피', '["커피", "에스프레소", "강렬"]', '["https://example.com/espresso1.jpg"]', '{"size": "Single", "temperature": "Hot", "caffeine": "80mg"}'),
('아이스 아메리카노', 4, 'ED_ICED_AMERICANO', '이디야커피 시원한 아이스 아메리카노', 4000, 4000, '음료', '커피', '["커피", "아이스", "아메리카노"]', '["https://example.com/iced_americano1.jpg"]', '{"size": "Regular", "temperature": "Cold", "caffeine": "150mg"}'),
('메가 아메리카노', 5, 'MG_AMERICANO', '메가MGC커피 기본 아메리카노', 3500, 3500, '음료', '커피', '["커피", "아메리카노", "기본"]', '["https://example.com/mega_americano1.jpg"]', '{"size": "Regular", "temperature": "Hot", "caffeine": "150mg"}'),
('삼각김밥', 6, 'GS_TRIANGLE', 'GS25 신선한 삼각김밥', 1500, 1500, '식품', '김밥', '["김밥", "삼각김밥", "신선"]', '["https://example.com/triangle1.jpg"]', '{"weight": "120g", "expiry": "24시간", "ingredients": "쌀, 김, 소고기"}'),
('도시락', 7, 'CU_LUNCHBOX', 'CU 맛있는 도시락', 4500, 4500, '식품', '도시락', '["도시락", "점심", "한식"]', '["https://example.com/lunchbox1.jpg"]', '{"weight": "350g", "expiry": "24시간", "ingredients": "쌀, 반찬"}'),
('생수', 8, '7E_WATER', '세븐일레븐 생수 2L', 1200, 1200, '음료', '생수', '["생수", "2L", "깨끗"]', '["https://example.com/water1.jpg"]', '{"volume": "2L", "mineral": "칼슘, 마그네슘"}'),
('과일', 9, 'EM_FRUIT', '이마트 신선한 과일 세트', 15000, 18000, '식품', '과일', '["과일", "신선", "세트"]', '["https://example.com/fruit1.jpg"]', '{"weight": "1kg", "variety": "사과, 바나나, 오렌지"}'),
('생선', 10, 'HP_FISH', '홈플러스 신선한 생선', 25000, 30000, '식품', '수산물', '["생선", "신선", "수산물"]', '["https://example.com/fish1.jpg"]', '{"weight": "500g", "type": "고등어", "origin": "국내산"}')
ON CONFLICT (product_code) DO NOTHING;

-- 데이터 삽입 완료 로그
DO $$
BEGIN
    RAISE NOTICE 'TTUGTTAG 샘플 데이터 삽입 완료';
    RAISE NOTICE '삽입된 데이터:';
    RAISE NOTICE '- 브랜드: %개', (SELECT COUNT(*) FROM brands);
    RAISE NOTICE '- 사용자: %개', (SELECT COUNT(*) FROM users);
    RAISE NOTICE '- 혜택: %개', (SELECT COUNT(*) FROM benefits);
    RAISE NOTICE '- 제품: %개', (SELECT COUNT(*) FROM products);
    RAISE NOTICE '- 사용자 선호도: %개', (SELECT COUNT(*) FROM user_preferences);
    RAISE NOTICE '- 소비 이력: %개', (SELECT COUNT(*) FROM spending_history);
    RAISE NOTICE '- 채팅 로그: %개', (SELECT COUNT(*) FROM chat_logs);
END $$; 