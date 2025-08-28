#!/bin/bash

# ======================================================================================
# TTUGTTAG 고도화된 데이터베이스 자동 구축 스크립트 - setup_database_enhanced.sh
# ======================================================================================

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_success() {
    echo -e "${PURPLE}[SUCCESS]${NC} $1"
}

# 설정 변수
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_DIR="${PROJECT_DIR}/enhanced_db"
SCHEMA_FILE="${PROJECT_DIR}/database_schema.sql"
VENV_DIR="${PROJECT_DIR}/test/venv"

log_info "🚀 TTUGTTAG 고도화된 데이터베이스 자동 구축 시작"
log_info "   프로젝트 디렉토리: $PROJECT_DIR"
log_info "   데이터베이스 디렉토리: $DB_DIR"

# ======================================================================================
# 1. 필수 파일 확인
# ======================================================================================

log_step "필수 파일 확인"

# 스키마 파일 확인
if [ ! -f "$SCHEMA_FILE" ]; then
    log_error "데이터베이스 스키마 파일을 찾을 수 없습니다: $SCHEMA_FILE"
    exit 1
fi

log_success "스키마 파일 확인 완료: $SCHEMA_FILE"

# ======================================================================================
# 2. Python 가상환경 확인 및 활성화
# ======================================================================================

log_step "Python 가상환경 확인 및 활성화"

if [ ! -d "$VENV_DIR" ]; then
    log_warning "가상환경이 존재하지 않습니다. 생성 중..."
    python3 -m venv "$VENV_DIR"
fi

# 가상환경 활성화
source "$VENV_DIR/bin/activate"
log_success "가상환경 활성화 완료: $VENV_DIR"

# 필요한 패키지 설치
log_info "필요한 패키지 설치 중..."
pip install sqlite3 2>/dev/null || pip install pysqlite3
pip install pandas numpy

# ======================================================================================
# 3. 기존 데이터베이스 확인 및 백업
# ======================================================================================

log_step "기존 데이터베이스 확인 및 백업"

if [ -d "$DB_DIR" ] && [ "$(ls -A $DB_DIR 2>/dev/null)" ]; then
    log_warning "기존 데이터베이스가 존재합니다: $DB_DIR"
    
    # 백업 디렉토리 생성
    BACKUP_DIR="${PROJECT_DIR}/db_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 기존 DB 백업
    cp -r "$DB_DIR"/* "$BACKUP_DIR/"
    log_success "기존 데이터베이스 백업 완료: $BACKUP_DIR"
    
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
# 4. 데이터베이스 디렉토리 생성
# ======================================================================================

log_step "데이터베이스 디렉토리 생성"

mkdir -p "$DB_DIR"
log_success "데이터베이스 디렉토리 생성 완료: $DB_DIR"

# ======================================================================================
# 5. SQLite 데이터베이스 초기화
# ======================================================================================

log_step "SQLite 데이터베이스 초기화"

DB_FILE="${DB_DIR}/ttugttag.db"
log_info "데이터베이스 파일 생성: $DB_FILE"

# SQLite 데이터베이스 생성 및 스키마 적용
sqlite3 "$DB_FILE" < "$SCHEMA_FILE"

if [ $? -eq 0 ]; then
    log_success "SQLite 데이터베이스 초기화 완료"
else
    log_error "SQLite 데이터베이스 초기화 실패"
    exit 1
fi

# ======================================================================================
# 6. 데이터베이스 검증
# ======================================================================================

log_step "데이터베이스 검증"

# 검증 스크립트 생성
cat > "${PROJECT_DIR}/verify_enhanced_db.py" << 'EOF'
#!/usr/bin/env python3

import sqlite3
import os
import sys

def verify_database():
    db_path = os.path.join(os.path.dirname(__file__), 'enhanced_db', 'ttugttag.db')
    
    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일을 찾을 수 없습니다")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 발견된 테이블: {len(tables)}개")
        
        total_records = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"  - {table_name}: {count}개 레코드")
        
        print(f"\n📊 총 레코드 수: {total_records}개")
        
        # 샘플 데이터 확인
        print("\n🔍 샘플 데이터 확인:")
        
        # 브랜드 데이터
        cursor.execute("SELECT brand_name, category FROM brands LIMIT 3")
        brands = cursor.fetchall()
        print("  브랜드:")
        for brand in brands:
            print(f"    - {brand[0]} ({brand[1]})")
        
        # 혜택 데이터
        cursor.execute("SELECT benefit_name, benefit_type FROM benefits LIMIT 3")
        benefits = cursor.fetchall()
        print("  혜택:")
        for benefit in benefits:
            print(f"    - {benefit[0]} ({benefit[1]})")
        
        conn.close()
        print("\n✅ 데이터베이스 검증 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 검증 실패: {e}")
        return False

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
EOF

chmod +x "${PROJECT_DIR}/verify_enhanced_db.py"

# 검증 실행
if python3 "${PROJECT_DIR}/verify_enhanced_db.py"; then
    log_success "데이터베이스 검증 완료"
else
    log_error "데이터베이스 검증 실패"
    exit 1
fi

# 검증 스크립트 제거
rm -f "${PROJECT_DIR}/verify_enhanced_db.py"

# ======================================================================================
# 7. 데이터베이스 관리 도구 생성
# ======================================================================================

log_step "데이터베이스 관리 도구 생성"

# 데이터베이스 관리 클래스 생성
cat > "${PROJECT_DIR}/tools/enhanced_database.py" << 'EOF'
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
            self.logger.info(f"데이터베이스 연결 성공: {self.db_path}")
        except Exception as e:
            self.logger.error(f"데이터베이스 연결 실패: {e}")
            raise
    
    def _get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
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
EOF

log_success "데이터베이스 관리 도구 생성 완료"

# ======================================================================================
# 8. 백엔드 통합 예시 생성
# ======================================================================================

log_step "백엔드 통합 예시 생성"

# 백엔드 통합 예시 파일 생성
cat > "${PROJECT_DIR}/backend_integration_example.py" << 'EOF'
#!/usr/bin/env python3
"""
TTUGTTAG 백엔드 통합 예시
고도화된 데이터베이스를 활용한 API 확장 예시
"""

from flask import Flask, request, jsonify
from tools.enhanced_database import EnhancedDatabase
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
db = EnhancedDatabase()

# ======================================================================================
# 사용자 관리 API
# ======================================================================================

@app.route('/api/users', methods=['POST'])
def create_user():
    """새 사용자 생성"""
    try:
        data = request.get_json()
        user_id = db.create_user(data)
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': '사용자가 성공적으로 생성되었습니다.'
        }), 201
    except Exception as e:
        logger.error(f"사용자 생성 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """사용자 정보 조회"""
    try:
        user = db.get_user(user_id)
        if user:
            return jsonify({
                'success': True,
                'user': user
            })
        else:
            return jsonify({
                'success': False,
                'error': '사용자를 찾을 수 없습니다.'
            }), 404
    except Exception as e:
        logger.error(f"사용자 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ======================================================================================
# 소셜 로그인 API
# ======================================================================================

@app.route('/api/auth/social/<provider>', methods=['POST'])
def social_login(provider):
    """소셜 로그인"""
    try:
        data = request.get_json()
        
        # 소셜 사용자 ID로 기존 계정 확인
        social_user = db.get_social_login(provider, data['social_user_id'])
        
        if social_user:
            # 기존 계정으로 로그인
            user = db.get_user(social_user['user_identifier'])
            return jsonify({
                'success': True,
                'user': user,
                'message': '기존 계정으로 로그인되었습니다.'
            })
        else:
            # 새 계정 생성
            user_data = {
                'user_id': f"{provider}_{data['social_user_id']}",
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'preferences': {}
            }
            
            user_id = db.create_user(user_data)
            
            # 소셜 로그인 정보 추가
            db.add_social_login(user_id, provider, data)
            
            user = db.get_user(user_data['user_id'])
            return jsonify({
                'success': True,
                'user': user,
                'message': '새 계정이 생성되었습니다.'
            }), 201
            
    except Exception as e:
        logger.error(f"소셜 로그인 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ======================================================================================
# 혜택 검색 및 추천 API
# ======================================================================================

@app.route('/api/benefits/search', methods=['GET'])
def search_benefits():
    """혜택 검색"""
    try:
        query = request.args.get('q', '')
        category = request.args.get('category')
        
        if not query:
            return jsonify({
                'success': False,
                'error': '검색어를 입력해주세요.'
            }), 400
        
        benefits = db.search_benefits(query, category)
        return jsonify({
            'success': True,
            'benefits': benefits,
            'count': len(benefits)
        })
        
    except Exception as e:
        logger.error(f"혜택 검색 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/benefits/recommend/<user_id>', methods=['GET'])
def recommend_benefits(user_id):
    """사용자 맞춤 혜택 추천"""
    try:
        # 사용자 선호도 기반 추천
        preferences = db.get_user_preferences(int(user_id))
        
        recommended_benefits = []
        for pref in preferences[:3]:  # 상위 3개 선호 브랜드
            benefits = db.get_benefits_for_brand(pref['brand_id'])
            recommended_benefits.extend(benefits[:2])  # 브랜드당 2개 혜택
        
        return jsonify({
            'success': True,
            'recommendations': recommended_benefits,
            'count': len(recommended_benefits)
        })
        
    except Exception as e:
        logger.error(f"혜택 추천 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ======================================================================================
# 사용자 행동 추적 API
# ======================================================================================

@app.route('/api/users/<user_id>/preferences', methods=['POST'])
def update_preference(user_id):
    """사용자 선호도 업데이트"""
    try:
        data = request.get_json()
        brand_id = data.get('brand_id')
        score = data.get('score', 0.5)
        
        db.update_user_preference(int(user_id), brand_id, score)
        
        return jsonify({
            'success': True,
            'message': '선호도가 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"선호도 업데이트 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<user_id>/spending', methods=['POST'])
def add_spending(user_id):
    """소비 이력 추가"""
    try:
        data = request.get_json()
        
        db.add_spending_history(
            user_id=int(user_id),
            brand_id=data['brand_id'],
            amount=data['amount'],
            product_id=data.get('product_id'),
            payment_method=data.get('payment_method'),
            location=data.get('location')
        )
        
        return jsonify({
            'success': True,
            'message': '소비 이력이 추가되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"소비 이력 추가 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ======================================================================================
# 채팅 로그 API
# ======================================================================================

@app.route('/api/chat/log', methods=['POST'])
def log_chat():
    """채팅 로그 저장"""
    try:
        data = request.get_json()
        
        db.add_chat_log(
            user_id=int(data['user_id']),
            session_id=data['session_id'],
            message_type=data['message_type'],
            message_content=data['message_content'],
            intent=data.get('intent'),
            entities=data.get('entities'),
            confidence_score=data.get('confidence_score'),
            response_time_ms=data.get('response_time_ms'),
            suggested_benefits=data.get('suggested_benefits')
        )
        
        return jsonify({
            'success': True,
            'message': '채팅 로그가 저장되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"채팅 로그 저장 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat/history/<user_id>', methods=['GET'])
def get_chat_history(user_id):
    """채팅 이력 조회"""
    try:
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        
        history = db.get_chat_history(int(user_id), session_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f"채팅 이력 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ======================================================================================
# 통계 API
# ======================================================================================

@app.route('/api/users/<user_id>/statistics', methods=['GET'])
def get_user_statistics(user_id):
    """사용자 통계 정보"""
    try:
        stats = db.get_user_statistics(int(user_id))
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"사용자 통계 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/brands/<brand_id>/statistics', methods=['GET'])
def get_brand_statistics(brand_id):
    """브랜드 통계 정보"""
    try:
        stats = db.get_brand_statistics(int(brand_id))
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"브랜드 통계 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)
EOF

log_success "백엔드 통합 예시 생성 완료"

# ======================================================================================
# 9. 최종 검증 및 완료
# ======================================================================================

log_step "최종 검증 및 완료"

echo ""
log_success "🎉 TTUGTTAG 고도화된 데이터베이스 구축 완료!"
echo ""
echo "📊 데이터베이스 정보:"
echo "   • 위치: $DB_DIR"
echo "   • 파일: ttugttag.db"
echo "   • 스키마: $SCHEMA_FILE"
echo ""
echo "🛠️ 생성된 도구:"
echo "   • tools/enhanced_database.py - 데이터베이스 관리 클래스"
echo "   • backend_integration_example.py - 백엔드 통합 예시"
echo ""
echo "🧪 테스트 방법:"
echo "   # 데이터베이스 연결 테스트"
echo "   python3 -c \"from tools.enhanced_database import EnhancedDatabase; db = EnhancedDatabase(); print('연결 성공')\""
echo ""
echo "   # 백엔드 예시 실행"
echo "   python3 backend_integration_example.py"
echo ""
echo "📚 주요 기능:"
echo "   • 사용자 관리 (회원가입, 프로필, 소셜 로그인)"
echo "   • 브랜드 및 혜택 관리"
echo "   • 사용자 선호도 및 행동 추적"
echo "   • 채팅 로그 및 상호작용 기록"
echo "   • 개인화된 혜택 추천"
echo "   • 통계 및 분석"
echo ""

# 권한 설정
chmod +x "${PROJECT_DIR}/setup_database_enhanced.sh"
chmod +x "${PROJECT_DIR}/backend_integration_example.py"

log_info "✅ 모든 작업이 완료되었습니다!" 