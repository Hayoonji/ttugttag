#!/usr/bin/env python3
"""
네이버 OAuth2 인증 및 사용자 관리
"""
import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from .enhanced_database import EnhancedDatabase

logger = logging.getLogger(__name__)

class NaverOAuth:
    def __init__(self, client_id: str, client_secret: str, db: EnhancedDatabase):
        """
        네이버 OAuth 초기화
        
        Args:
            client_id: 네이버 애플리케이션 클라이언트 ID
            client_secret: 네이버 애플리케이션 클라이언트 시크릿
            db: 데이터베이스 인스턴스
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.db = db
        
        # 네이버 OAuth2 API 엔드포인트
        self.auth_url = "https://nid.naver.com/oauth2.0/authorize"
        self.token_url = "https://nid.naver.com/oauth2.0/token"
        self.profile_url = "https://openapi.naver.com/v1/nid/me"
        self.revoke_url = "https://nid.naver.com/oauth2.0/token"
        
        logger.info("네이버 OAuth 초기화 완료")
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """
        네이버 로그인 인증 URL 생성
        
        Args:
            redirect_uri: 리다이렉트 URI
            state: CSRF 방지용 state 값
            
        Returns:
            네이버 로그인 URL
        """
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'state': state
        }
        
        # URL 파라미터 구성
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    def get_access_token(self, authorization_code: str, state: str, redirect_uri: str) -> Optional[Dict]:
        """
        인가 코드로 액세스 토큰 획득
        
        Args:
            authorization_code: 네이버에서 받은 인가 코드
            state: CSRF 방지용 state 값
            redirect_uri: 리다이렉트 URI
            
        Returns:
            토큰 정보 딕셔너리 또는 None
        """
        try:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'state': state
            }
            
            # urllib.request를 사용한 POST 요청
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(self.token_url, data=data_encoded)
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            response = urllib.request.urlopen(request)
            rescode = response.getcode()
            
            if rescode == 200:
                response_body = response.read()
                token_data = json.loads(response_body.decode('utf-8'))
                logger.info("액세스 토큰 획득 성공")
                return token_data
            else:
                logger.error(f"액세스 토큰 획득 실패: HTTP {rescode}")
                return None
                
        except urllib.error.URLError as e:
            logger.error(f"액세스 토큰 획득 네트워크 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"액세스 토큰 처리 중 오류: {e}")
            return None
    
    def get_user_profile(self, access_token: str) -> Optional[Dict]:
        """
        액세스 토큰으로 사용자 프로필 조회 (네이버 공식 API 예제 기반)
        
        Args:
            access_token: 네이버 액세스 토큰
            
        Returns:
            사용자 프로필 정보 또는 None
        """
        try:
            # Bearer 토큰 헤더 구성
            header = "Bearer " + access_token
            
            # urllib.request를 사용한 GET 요청
            request = urllib.request.Request(self.profile_url)
            request.add_header("Authorization", header)
            
            response = urllib.request.urlopen(request)
            rescode = response.getcode()
            
            if rescode == 200:
                response_body = response.read()
                profile_data = json.loads(response_body.decode('utf-8'))
                
                if profile_data.get('resultcode') == '00':
                    user_info = profile_data.get('response', {})
                    logger.info(f"사용자 프로필 조회 성공: {user_info.get('email', 'Unknown')}")
                    return user_info
                else:
                    logger.error(f"프로필 조회 실패: {profile_data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"프로필 조회 HTTP 오류: {rescode}")
                return None
                
        except urllib.error.URLError as e:
            logger.error(f"프로필 조회 네트워크 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"프로필 조회 처리 중 오류: {e}")
            return None
    
    def process_naver_login(self, authorization_code: str, state: str, redirect_uri: str) -> Tuple[bool, Dict, str]:
        """
        네이버 로그인 처리: 기존 사용자 확인 후 로그인 또는 새 사용자 생성
        
        Args:
            authorization_code: 네이버에서 받은 인가 코드
            state: CSRF 방지용 state 값
            redirect_uri: 리다이렉트 URI
            
        Returns:
            (성공 여부, 사용자 데이터, 메시지)
        """
        try:
            # 1. 액세스 토큰 획득
            token_data = self.get_access_token(authorization_code, state, redirect_uri)
            if not token_data:
                return False, {}, "액세스 토큰 획득에 실패했습니다."
            
            access_token = token_data.get('access_token')
            if not access_token:
                return False, {}, "액세스 토큰이 없습니다."
            
            # 2. 사용자 프로필 조회
            profile = self.get_user_profile(access_token)
            if not profile:
                return False, {}, "사용자 프로필 조회에 실패했습니다."
            
            # 3. 네이버 사용자 ID 추출
            naver_id = profile.get('id')
            if not naver_id:
                return False, {}, "네이버 사용자 ID를 찾을 수 없습니다."
            
            # 4. 기존 사용자 확인
            existing_user = self.db.get_social_login('naver', naver_id)
            
            if existing_user:
                # 기존 사용자 로그인
                user = self.db.get_user(existing_user['user_id'])
                if user:
                    # 소셜 로그인 정보 업데이트
                    self.db.add_social_login(
                        existing_user['user_id'], 
                        'naver', 
                        {
                            'naver_id': naver_id,
                            'access_token': access_token,
                            'refresh_token': token_data.get('refresh_token'),
                            'expires_at': datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
                        }
                    )
                    
                    logger.info(f"기존 사용자 로그인: {user['email']}")
                    return True, user, "기존 계정으로 로그인되었습니다."
            
            # 5. 새 사용자 생성
            user_data = {
                'email': profile.get('email'),
                'name': profile.get('name'),
                'nickname': profile.get('nickname'),
                'birth_year': profile.get('birthyear'),
                'gender': profile.get('gender', 'U'),
                'created_at': datetime.now()
            }
            
            # 사용자 생성
            user_id = self.db.create_user(user_data)
            if not user_id:
                return False, {}, "사용자 계정 생성에 실패했습니다."
            
            # 소셜 로그인 정보 추가
            self.db.add_social_login(
                user_id, 
                'naver', 
                {
                    'naver_id': naver_id,
                    'access_token': access_token,
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_at': datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
                }
            )
            
            # 생성된 사용자 정보 조회
            new_user = self.db.get_user(user_id)
            
            logger.info(f"새 사용자 생성 및 로그인: {new_user['email']}")
            return True, new_user, "새 계정이 생성되었습니다."
            
        except Exception as e:
            logger.error(f"네이버 로그인 처리 중 오류: {e}")
            return False, {}, f"로그인 처리 중 오류가 발생했습니다: {str(e)}"
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        리프레시 토큰으로 액세스 토큰 갱신
        
        Args:
            refresh_token: 리프레시 토큰
            
        Returns:
            새로운 토큰 정보 또는 None
        """
        try:
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token
            }
            
            # urllib.request를 사용한 POST 요청
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(self.token_url, data=data_encoded)
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            response = urllib.request.urlopen(request)
            rescode = response.getcode()
            
            if rescode == 200:
                response_body = response.read()
                token_data = json.loads(response_body.decode('utf-8'))
                logger.info("액세스 토큰 갱신 성공")
                return token_data
            else:
                logger.error(f"액세스 토큰 갱신 실패: HTTP {rescode}")
                return None
                
        except urllib.error.URLError as e:
            logger.error(f"액세스 토큰 갱신 네트워크 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"토큰 갱신 처리 중 오류: {e}")
            return None
    
    def revoke_token(self, access_token: str) -> bool:
        """
        액세스 토큰 폐기
        
        Args:
            access_token: 폐기할 액세스 토큰
            
        Returns:
            폐기 성공 여부
        """
        try:
            data = {
                'grant_type': 'delete',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'access_token': access_token,
                'service_provider': 'NAVER'
            }
            
            # urllib.request를 사용한 POST 요청
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(self.revoke_url, data=data_encoded)
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            response = urllib.request.urlopen(request)
            rescode = response.getcode()
            
            if rescode == 200:
                logger.info("액세스 토큰 폐기 성공")
                return True
            else:
                logger.error(f"액세스 토큰 폐기 실패: HTTP {rescode}")
                return False
                
        except urllib.error.URLError as e:
            logger.error(f"액세스 토큰 폐기 네트워크 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"토큰 폐기 처리 중 오류: {e}")
            return False
    
    def _parse_birthday(self, birthday: str) -> Optional[str]:
        """
        생일 문자열 파싱 (YYYY-MM-DD 형식)
        
        Args:
            birthday: 생일 문자열
            
        Returns:
            파싱된 생일 또는 None
        """
        try:
            if not birthday:
                return None
            
            # 다양한 형식 지원
            if '-' in birthday:
                parts = birthday.split('-')
                if len(parts) >= 2:
                    return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2) if len(parts) > 2 else '01'}"
            
            return birthday
            
        except Exception as e:
            logger.warning(f"생일 파싱 실패: {birthday}, 오류: {e}")
            return None 