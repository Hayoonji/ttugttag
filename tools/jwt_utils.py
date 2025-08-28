#!/usr/bin/env python3
"""
JWT 토큰 관리 유틸리티
"""
import jwt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)

class JWTManager:
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        """
        JWT 매니저 초기화
        
        Args:
            secret_key: JWT 서명용 비밀키 (None이면 자동 생성)
            algorithm: JWT 알고리즘 (기본값: HS256)
        """
        self.secret_key = secret_key or self._generate_secret_key()
        self.algorithm = algorithm
        self.token_expiry_hours = 24  # 토큰 만료 시간 (시간)
        
        logger.info(f"JWT 매니저 초기화 완료 (알고리즘: {algorithm})")
    
    def _generate_secret_key(self) -> str:
        """안전한 비밀키 생성"""
        return secrets.token_urlsafe(32)
    
    def generate_token(self, user_data: Dict) -> str:
        """
        사용자 데이터로 JWT 토큰 생성
        
        Args:
            user_data: 토큰에 포함할 사용자 정보
            
        Returns:
            JWT 토큰 문자열
        """
        try:
            payload = {
                'user_id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'nickname': user_data.get('nickname'),
                'iat': datetime.utcnow(),  # 토큰 발급 시간
                'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),  # 만료 시간
                'jti': secrets.token_urlsafe(16)  # JWT ID (중복 방지)
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"JWT 토큰 생성 완료: user_id={user_data.get('id')}")
            
            return token
            
        except Exception as e:
            logger.error(f"JWT 토큰 생성 실패: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        JWT 토큰 검증
        
        Args:
            token: 검증할 JWT 토큰
            
        Returns:
            검증 성공 시 페이로드, 실패 시 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.info(f"JWT 토큰 검증 성공: user_id={payload.get('user_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT 토큰 만료됨")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT 토큰 무효: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT 토큰 검증 중 오류: {e}")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        JWT 토큰 갱신
        
        Args:
            token: 갱신할 JWT 토큰
            
        Returns:
            새로운 JWT 토큰 또는 None
        """
        try:
            payload = self.verify_token(token)
            if payload:
                # 기존 페이로드에서 시간 정보만 업데이트
                payload.pop('iat', None)
                payload.pop('exp', None)
                payload.pop('jti', None)
                
                new_token = self.generate_token(payload)
                logger.info(f"JWT 토큰 갱신 완료: user_id={payload.get('user_id')}")
                return new_token
                
        except Exception as e:
            logger.error(f"JWT 토큰 갱신 실패: {e}")
            
        return None
    
    def get_token_from_header(self) -> Optional[str]:
        """
        HTTP 헤더에서 JWT 토큰 추출
        
        Returns:
            JWT 토큰 또는 None
        """
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None

# JWT 인증 데코레이터
def jwt_required(f):
    """
    JWT 토큰이 필요한 API 엔드포인트용 데코레이터
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # JWT 매니저 인스턴스 가져오기
            jwt_manager = current_app.config.get('JWT_MANAGER')
            if not jwt_manager:
                logger.error("JWT 매니저가 설정되지 않음")
                return jsonify({'error': 'JWT 설정 오류'}), 500
            
            # 헤더에서 토큰 추출
            token = jwt_manager.get_token_from_header()
            if not token:
                return jsonify({'error': 'JWT 토큰이 필요합니다', 'code': 'MISSING_TOKEN'}), 401
            
            # 토큰 검증
            payload = jwt_manager.verify_token(token)
            if not payload:
                return jsonify({'error': '유효하지 않은 JWT 토큰입니다', 'code': 'INVALID_TOKEN'}), 401
            
            # 요청에 사용자 정보 추가
            request.user = payload
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"JWT 인증 중 오류: {e}")
            return jsonify({'error': '인증 처리 중 오류가 발생했습니다'}), 500
    
    return decorated_function

# 선택적 JWT 인증 데코레이터 (토큰이 있으면 검증, 없으면 통과)
def jwt_optional(f):
    """
    JWT 토큰이 선택적인 API 엔드포인트용 데코레이터
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            jwt_manager = current_app.config.get('JWT_MANAGER')
            if jwt_manager:
                token = jwt_manager.get_token_from_header()
                if token:
                    payload = jwt_manager.verify_token(token)
                    if payload:
                        request.user = payload
                    else:
                        request.user = None
                else:
                    request.user = None
            else:
                request.user = None
                
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"JWT 선택적 인증 중 오류: {e}")
            request.user = None
            return f(*args, **kwargs)
    
    return decorated_function 