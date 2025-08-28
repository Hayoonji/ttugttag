#!/usr/bin/env python3
"""
TTUGTTAG 고도화된 데이터베이스 관리 클래스
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class EnhancedDatabase:
    """고도화된 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 프로젝트 루트 기준으로 DB 경로 설정
            project_root = Path(__file__).parent.parent
            db_path = project_root / "enhanced_db" / "ttugttag.db"
        
        self.db_path = str(db_path)
        self.logger = logging.getLogger(__name__)
        
        # 데이터베이스 연결 테스트
        self._test_connection()
    
    def _test_connection(self):
        """데이터베이스 연결 테스트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1")
            print(f"데이터베이스 연결 성공: {self.db_path}")
        except Exception as e:
            print(f"데이터베이스 연결 실패: {e}")
            raise
    
    def _get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            print(f"데이터베이스 연결 테스트 실패: {e}")
            return False
    
    # ======================================================================================
    # 사용자 관리
    # ======================================================================================
    
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """새 사용자 생성"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, email, phone, name, birth_date, gender, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data.get('user_id'),
                user_data.get('email'),
                user_data.get('phone'),
                user_data.get('name'),
                user_data.get('birth_date'),
                user_data.get('gender'),
                json.dumps(user_data.get('preferences', {}))
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 정보 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """사용자 선호도 업데이트"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET preferences = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (json.dumps(preferences), user_id))
            conn.commit()
    
    # ======================================================================================
    # 소셜 로그인 관리
    # ======================================================================================
    
    def add_social_login(self, user_id: int, provider: str, social_data: Dict[str, Any]):
        """소셜 로그인 정보 추가"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO social_logins 
                (user_id, provider, social_user_id, access_token, refresh_token, 
                 expires_at, profile_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                provider,
                social_data.get('social_user_id'),
                social_data.get('access_token'),
                social_data.get('refresh_token'),
                social_data.get('expires_at'),
                json.dumps(social_data.get('profile_data', {}))
            ))
            conn.commit()
    
    def get_social_login(self, provider: str, social_user_id: str) -> Optional[Dict[str, Any]]:
        """소셜 로그인 정보 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sl.*, u.user_id as user_identifier
                FROM social_logins sl
                JOIN users u ON sl.user_id = u.id
                WHERE sl.provider = ? AND sl.social_user_id = ?
            """, (provider, social_user_id))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    # ======================================================================================
    # 브랜드 및 혜택 관리
    # ======================================================================================
    
    def get_brands_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 브랜드 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, 
                       GROUP_CONCAT(DISTINCT ben.benefit_name) as available_benefits
                FROM brands b
                LEFT JOIN brand_benefits bb ON b.id = bb.brand_id
                LEFT JOIN benefits ben ON bb.benefit_id = ben.id
                WHERE b.category = ? AND b.is_active = 1
                GROUP BY b.id
            """, (category,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_benefits_for_brand(self, brand_id: int) -> List[Dict[str, Any]]:
        """브랜드별 혜택 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, bb.priority
                FROM benefits b
                JOIN brand_benefits bb ON b.id = bb.benefit_id
                WHERE bb.brand_id = ? AND b.is_active = 1
                ORDER BY bb.priority DESC, b.created_at DESC
            """, (brand_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_benefits(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """혜택 검색"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute("""
                    SELECT DISTINCT b.*, br.brand_name, br.category
                    FROM benefits b
                    JOIN brand_benefits bb ON b.id = bb.benefit_id
                    JOIN brands br ON bb.brand_id = br.id
                    WHERE (b.benefit_name LIKE ? OR b.description LIKE ?)
                      AND br.category = ? AND b.is_active = 1
                    ORDER BY b.created_at DESC
                """, (f'%{query}%', f'%{query}%', category))
            else:
                cursor.execute("""
                    SELECT DISTINCT b.*, br.brand_name, br.category
                    FROM benefits b
                    JOIN brand_benefits bb ON b.id = bb.benefit_id
                    JOIN brands br ON bb.brand_id = br.id
                    WHERE (b.benefit_name LIKE ? OR b.description LIKE ?)
                      AND b.is_active = 1
                    ORDER BY b.created_at DESC
                """, (f'%{query}%', f'%{query}%'))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ======================================================================================
    # 사용자 선호도 및 이력 관리
    # ======================================================================================
    
    def update_user_preference(self, user_id: int, brand_id: int, score: float):
        """사용자 브랜드 선호도 업데이트"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, brand_id, preference_score, interaction_count, 
                 last_interaction_at, updated_at)
                VALUES (?, ?, ?, 
                        COALESCE((SELECT interaction_count + 1 FROM user_preferences 
                                 WHERE user_id = ? AND brand_id = ?), 1),
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, brand_id, score, user_id, brand_id))
            conn.commit()
    
    def get_user_preferences(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자 선호도 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT up.*, b.brand_name, b.category
                FROM user_preferences up
                JOIN brands b ON up.brand_id = b.id
                WHERE up.user_id = ?
                ORDER BY up.preference_score DESC, up.last_interaction_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_spending_history(self, user_id: int, brand_id: int, 
                           amount: float, product_id: int = None, 
                           payment_method: str = None, location: str = None):
        """사용자 소비 이력 추가"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_spending_history 
                (user_id, brand_id, product_id, amount, transaction_date, 
                 payment_method, location, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, brand_id, product_id, amount, payment_method, location))
            conn.commit()
    
    # ======================================================================================
    # 채팅 로그 관리
    # ======================================================================================
    
    def add_chat_log(self, user_id: int, session_id: str, message_type: str,
                     message_content: str, intent: str = None, entities: Dict = None,
                     confidence_score: float = None, response_time_ms: int = None,
                     suggested_benefits: List = None):
        """채팅 로그 추가"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_logs 
                (user_id, session_id, message_type, message_content, intent,
                 entities, confidence_score, response_time_ms, suggested_benefits,
                 message_timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                user_id, session_id, message_type, message_content, intent,
                json.dumps(entities) if entities else None,
                confidence_score, response_time_ms,
                json.dumps(suggested_benefits) if suggested_benefits else None
            ))
            conn.commit()
    
    def get_chat_history(self, user_id: int, session_id: str = None, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """채팅 이력 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if session_id:
                cursor.execute("""
                    SELECT * FROM chat_logs
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY message_timestamp DESC
                    LIMIT ?
                """, (user_id, session_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM chat_logs
                    WHERE user_id = ?
                    ORDER BY message_timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ======================================================================================
    # 통계 및 분석
    # ======================================================================================
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """사용자 통계 정보"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 총 소비 금액
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_spent
                FROM user_spending_history
                WHERE user_id = ?
            """, (user_id,))
            total_spent = cursor.fetchone()['total_spent']
            
            # 선호 브랜드
            cursor.execute("""
                SELECT b.brand_name, up.preference_score, up.interaction_count
                FROM user_preferences up
                JOIN brands b ON up.brand_id = b.id
                WHERE up.user_id = ?
                ORDER BY up.preference_score DESC
                LIMIT 5
            """, (user_id,))
            top_brands = [dict(row) for row in cursor.fetchall()]
            
            # 최근 거래
            cursor.execute("""
                SELECT ush.*, b.brand_name
                FROM user_spending_history ush
                JOIN brands b ON ush.brand_id = b.id
                WHERE ush.user_id = ?
                ORDER BY ush.transaction_date DESC
                LIMIT 10
            """, (user_id,))
            recent_transactions = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_spent': total_spent,
                'top_brands': top_brands,
                'recent_transactions': recent_transactions
            }
    
    def get_brand_statistics(self, brand_id: int) -> Dict[str, Any]:
        """브랜드 통계 정보"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 총 사용자 수
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as total_users
                FROM user_preferences
                WHERE brand_id = ?
            """, (brand_id,))
            total_users = cursor.fetchone()['total_users']
            
            # 평균 선호도 점수
            cursor.execute("""
                SELECT AVG(preference_score) as avg_preference
                FROM user_preferences
                WHERE brand_id = ?
            """, (brand_id,))
            avg_preference = cursor.fetchone()['avg_preference']
            
            # 총 소비 금액
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_spent
                FROM user_spending_history
                WHERE brand_id = ?
            """, (brand_id,))
            total_spent = cursor.fetchone()['total_spent']
            
            return {
                'total_users': total_users,
                'avg_preference': avg_preference,
                'total_spent': total_spent
            }

# 사용 예시
if __name__ == "__main__":
    # 데이터베이스 인스턴스 생성
    db = EnhancedDatabase()
    
    # 샘플 사용자 생성
    user_data = {
        'user_id': 'test_user_001',
        'email': 'test@example.com',
        'name': '테스트 사용자',
        'preferences': {'favorite_category': '카페', 'budget': 50000}
    }
    
    try:
        user_id = db.create_user(user_data)
        print(f"사용자 생성 성공: ID {user_id}")
        
        # 사용자 정보 조회
        user = db.get_user('test_user_001')
        print(f"사용자 정보: {user}")
        
        # 브랜드별 혜택 조회
        benefits = db.get_benefits_for_brand(1)  # 스타벅스
        print(f"스타벅스 혜택: {len(benefits)}개")
        
    except Exception as e:
        print(f"오류 발생: {e}") 