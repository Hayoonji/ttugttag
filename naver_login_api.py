#!/usr/bin/env python3
"""
네이버 OAuth2 로그인 API
"""

import os
import logging
import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from tools.enhanced_database import EnhancedDatabase
from tools.naver_oauth import NaverOAuth
from tools.jwt_utils import JWTManager, jwt_required, jwt_optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 환경 변수 로드
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
NAVER_REDIRECT_URI = os.environ.get('NAVER_REDIRECT_URI', 'http://localhost:3000/auth/naver/callback')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')  # JWT 비밀키 (없으면 자동 생성)

# 데이터베이스 및 OAuth 초기화
try:
    db = EnhancedDatabase()
    naver_oauth = NaverOAuth(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, db)
    
    # JWT 매니저 초기화
    jwt_manager = JWTManager(secret_key=JWT_SECRET_KEY)
    app.config['JWT_MANAGER'] = jwt_manager
    
    print("네이버 OAuth 및 데이터베이스 초기화 성공")
except Exception as e:
    print(f"초기화 실패: {e}")
    db = None
    naver_oauth = None
    jwt_manager = None

# 환경 변수 경고
if not NAVER_CLIENT_ID:
    print("NAVER_CLIENT_ID가 설정되지 않았습니다. 환경 변수를 확인하세요.")
if not NAVER_CLIENT_SECRET:
    print("NAVER_CLIENT_SECRET이 설정되지 않았습니다. 환경 변수를 확인하세요.")

# ======================================================================================
# 네이버 로그인 관련 API
# ======================================================================================

@app.route('/auth/naver/login', methods=['GET'])
def naver_login_url():
    """네이버 로그인 URL 생성"""
    try:
        if not naver_oauth:
            return jsonify({'error': 'OAuth 서비스가 초기화되지 않았습니다'}), 500
        
        # state 값 생성 (CSRF 방지)
        state = secrets.token_urlsafe(32)
        
        # 네이버 로그인 URL 생성
        auth_url = naver_oauth.get_authorization_url(NAVER_REDIRECT_URI, state)
        
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'state': state
        })
        
    except Exception as e:
        print(f"로그인 URL 생성 실패: {e}")
        return jsonify({'error': '로그인 URL 생성에 실패했습니다'}), 500

@app.route('/auth/naver/callback', methods=['POST'])
def naver_login_callback():
    """네이버 로그인 콜백 처리: 인가 코드를 받아 액세스 토큰 획득 및 사용자 로그인/등록"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '요청 데이터가 없습니다'}), 400
        
        code = data.get('code')
        state = secrets.token_urlsafe(32)
                
        if not code or not state:
            return jsonify({'error': '필수 파라미터가 누락되었습니다: code, state'}), 400
        
        # 네이버 로그인 처리
        success, user_data, message = naver_oauth.process_naver_login(code, state, NAVER_REDIRECT_URI)
        
        if success and user_data:
            # JWT 토큰 생성
            jwt_token = jwt_manager.generate_token(user_data)
            
            return jsonify({
                'success': True,
                'message': message,
                'user': user_data,
                'jwt_token': jwt_token,
                'token_type': 'Bearer',
                'expires_in': jwt_manager.token_expiry_hours * 3600  # 초 단위
            })
        else:
            return jsonify({
                'success': False,
                'error': 'login_failed',
                'message': message
            }), 400
            
    except Exception as e:
        print(f"로그인 콜백 처리 실패: {e}")
        return jsonify({'error': '로그인 처리 중 오류가 발생했습니다'}), 500

@app.route('/auth/naver/token/refresh', methods=['POST'])
@jwt_required  # JWT 토큰 필요
def naver_token_refresh():
    """네이버 액세스 토큰 갱신"""
    try:
        current_user = request.user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '요청 데이터가 없습니다'}), 400
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': '리프레시 토큰이 필요합니다'}), 400
        
        # 네이버 토큰 갱신
        token_data = naver_oauth.refresh_access_token(refresh_token)
        
        if token_data:
            return jsonify({
                'success': True,
                'token_data': token_data
            })
        else:
            return jsonify({'error': '토큰 갱신에 실패했습니다'}), 400
            
    except Exception as e:
        print(f"토큰 갱신 실패: {e}")
        return jsonify({'error': '토큰 갱신 중 오류가 발생했습니다'}), 500

@app.route('/auth/naver/logout', methods=['POST'])
@jwt_required  # JWT 토큰 필요
def naver_logout():
    """네이버 로그아웃 (토큰 폐기)"""
    try:
        # 현재 사용자 정보
        current_user = request.user
        
        data = request.get_json() or {}
        access_token = data.get('access_token')
        
        if access_token:
            # 네이버 토큰 폐기
            naver_oauth.revoke_token(access_token)
        
        return jsonify({
            'success': True,
            'message': '로그아웃되었습니다'
        })
        
    except Exception as e:
        print(f"로그아웃 실패: {e}")
        return jsonify({'error': '로그아웃 중 오류가 발생했습니다'}), 500

# ======================================================================================
# 사용자 정보 관리 API
# ======================================================================================

@app.route('/api/users/<user_id>', methods=['GET'])
@jwt_required  # JWT 토큰 필요
def get_user_info(user_id):
    """사용자 정보 조회"""
    try:
        # 현재 사용자 확인 (자신의 정보만 조회 가능)
        current_user = request.user
        if str(current_user.get('user_id')) != str(user_id):
            return jsonify({'error': '다른 사용자의 정보를 조회할 수 없습니다'}), 403
        
        user = db.get_user(user_id)
        if user:
            return jsonify({
                'success': True,
                'user': user
            })
        else:
            return jsonify({
                'success': False,
                'error': 'user_not_found',
                'message': '사용자를 찾을 수 없습니다'
            }), 404
            
    except Exception as e:
        print(f"사용자 정보 조회 실패: {e}")
        return jsonify({'error': '사용자 정보 조회 중 오류가 발생했습니다'}), 500

@app.route('/api/users/<user_id>/preferences', methods=['PUT'])
@jwt_required  # JWT 토큰 필요
def update_user_preferences(user_id):
    """사용자 선호도 업데이트"""
    try:
        # 현재 사용자 확인
        current_user = request.user
        if str(current_user.get('user_id')) != str(user_id):
            return jsonify({'error': '다른 사용자의 선호도를 수정할 수 없습니다'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '업데이트할 데이터가 없습니다'}), 400
        
        # 선호도 업데이트
        success = db.update_user_preferences(user_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '사용자 선호도가 업데이트되었습니다'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'update_failed',
                'message': '선호도 업데이트에 실패했습니다'
            }), 400
            
    except Exception as e:
        print(f"사용자 선호도 업데이트 실패: {e}")
        return jsonify({'error': '선호도 업데이트 중 오류가 발생했습니다'}), 500

# ======================================================================================
# JWT 토큰 관련 API
# ======================================================================================

@app.route('/auth/jwt/refresh', methods=['POST'])
@jwt_required  # JWT 토큰 필요
def refresh_jwt_token():
    """JWT 토큰 갱신"""
    try:
        current_user = request.user
        
        # 새로운 JWT 토큰 생성
        new_token = jwt_manager.generate_token(current_user)
        
        return jsonify({
            'success': True,
            'jwt_token': new_token,
            'token_type': 'Bearer',
            'expires_in': jwt_manager.token_expiry_hours * 3600
        })
        
    except Exception as e:
        print(f"JWT 토큰 갱신 실패: {e}")
        return jsonify({'error': '토큰 갱신 중 오류가 발생했습니다'}), 500

@app.route('/auth/jwt/verify', methods=['POST'])
@jwt_required  # JWT 토큰 필요 (선택적에서 필수로 변경)
def verify_jwt_token():
    """JWT 토큰 검증"""
    try:
        current_user = request.user
        return jsonify({
            'success': True,
            'valid': True,
            'user': current_user
        })
    except Exception as e:
        print(f"JWT 토큰 검증 실패: {e}")
        return jsonify({'error': '토큰 검증 중 오류가 발생했습니다'}), 500

# ======================================================================================
# 헬스체크 및 상태 확인
# ======================================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """서비스 상태 확인"""
    try:
        from datetime import datetime
        
        # 데이터베이스 연결만 확인
        db_status = "OK" if db and hasattr(db, 'test_connection') and db.test_connection() else "ERROR"
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    """API 정보"""
    return jsonify({
        'service': 'TTUGTTAG 네이버 로그인 API',
        'version': '1.0.0',
        'authentication': 'JWT Bearer Token (모든 API 보호됨)',
        'endpoints': [
            'GET  / - API 정보 (인증 불필요)',
            'GET  /health - 서비스 상태 (인증 불필요)',
            'GET  /auth/naver/login - 네이버 로그인 URL 생성 (인증 불필요)',
            'POST /auth/naver/callback - 네이버 로그인 콜백 (인증 불필요, JWT 발급)',
            'POST /auth/naver/token/refresh - 네이버 토큰 갱신 (JWT 필요)',
            'POST /auth/naver/logout - 네이버 로그아웃 (JWT 필요)',
            'GET  /api/users/<id> - 사용자 정보 조회 (JWT 필요)',
            'PUT  /api/users/<id>/preferences - 사용자 선호도 업데이트 (JWT 필요)',
            'POST /auth/jwt/refresh - JWT 토큰 갱신 (JWT 필요)',
            'POST /auth/jwt/verify - JWT 토큰 검증 (JWT 필요)'
        ],
        'note': 'JWT 토큰은 Authorization 헤더에 "Bearer <token>" 형식으로 전송. 로그인 후 모든 API 호출 시 필요.'
    })

# ======================================================================================
# 에러 핸들러
# ======================================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '요청한 리소스를 찾을 수 없습니다.'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '서버 내부 오류가 발생했습니다.'
    }), 500

if __name__ == '__main__':
    from datetime import datetime
    
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print("🚀 네이버 로그인 API 서버 시작")
    print(f"   포트: {port}")
    print(f"   디버그: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 