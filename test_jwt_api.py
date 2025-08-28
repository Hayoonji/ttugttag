#!/usr/bin/env python3
"""
JWT 인증이 적용된 네이버 로그인 API 테스트 스크립트 (urllib.request 사용)
"""
import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5002"

def make_request(method, url, data=None, headers=None):
    """
    urllib.request를 사용한 HTTP 요청 헬퍼 함수
    
    Args:
        method: HTTP 메서드 ('GET', 'POST')
        url: 요청 URL
        data: POST 데이터 (딕셔너리)
        headers: 요청 헤더 (딕셔너리)
        
    Returns:
        (status_code, response_data) 튜플
    """
    try:
        if method == 'GET':
            request = urllib.request.Request(url)
        elif method == 'POST':
            if data:
                # JSON 데이터인지 확인 (콜백 API는 JSON을 기대)
                if url.endswith('/callback') or url.endswith('/verify') or url.endswith('/refresh'):
                    # JSON 데이터로 전송
                    data_encoded = json.dumps(data).encode('utf-8')
                    request = urllib.request.Request(url, data=data_encoded, method='POST')
                    request.add_header('Content-Type', 'application/json')
                else:
                    # 폼 데이터로 전송
                    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
                    request = urllib.request.Request(url, data=data_encoded, method='POST')
                    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                request = urllib.request.Request(url, method='POST')
        else:
            return None, None
        
        # 헤더 추가
        if headers:
            for key, value in headers.items():
                request.add_header(key, value)
        
        response = urllib.request.urlopen(request)
        status_code = response.getcode()
        response_body = response.read()
        
        try:
            response_data = json.loads(response_body.decode('utf-8'))
        except json.JSONDecodeError:
            response_data = response_body.decode('utf-8')
        
        return status_code, response_data
        
    except urllib.error.HTTPError as e:
        return e.code, None
    except urllib.error.URLError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

def test_health_check():
    """헬스체크 테스트"""
    print("🔍 헬스체크 테스트...")
    
    try:
        status_code, data = make_request('GET', f"{BASE_URL}/health")
        print(f"   상태 코드: {status_code}")
        
        if status_code == 200 and data:
            print(f"   서비스 상태: {data.get('status')}")
            print(f"   데이터베이스: {data.get('database')}")
            print(f"   네이버 OAuth: {data.get('naver_oauth')}")
            print(f"   JWT: {data.get('jwt')}")
            print("✅ 헬스체크: 통과")
            return True
        else:
            print(f"   오류: {data}")
            print("❌ 헬스체크: 실패")
            return False
            
    except Exception as e:
        print(f"   오류: {e}")
        print("❌ 헬스체크: 실패")
        return False

def test_api_info():
    """API 정보 조회 테스트"""
    print("🔍 API 정보 조회 테스트...")
    
    try:
        status_code, data = make_request('GET', f"{BASE_URL}/")
        print(f"   상태 코드: {status_code}")
        
        if status_code == 200 and data:
            print(f"   서비스: {data.get('service')}")
            print(f"   버전: {data.get('version')}")
            print(f"   인증 방식: {data.get('authentication')}")
            print(f"   엔드포인트 수: {len(data.get('endpoints', []))}")
            print("✅ API 정보 조회: 통과")
            return True
        else:
            print(f"   오류: {data}")
            print("❌ API 정보 조회: 실패")
            return False
            
    except Exception as e:
        print(f"   오류: {e}")
        print("❌ API 정보 조회: 실패")
        return False

def test_naver_login_url():
    """네이버 로그인 URL 생성 테스트"""
    print("🔍 네이버 로그인 URL 생성 테스트...")
    
    try:
        status_code, data = make_request('GET', f"{BASE_URL}/auth/naver/login")
        print(f"   상태 코드: {status_code}")
        
        if status_code == 200 and data:
            print(f"   성공: {data.get('success')}")
            print(f"   인증 URL: {data.get('auth_url', '')[:50]}...")
            print(f"   State: {data.get('state', '')[:20]}...")
            print("✅ 네이버 로그인 URL 생성: 통과")
            return True
        else:
            print(f"   오류: {data}")
            print("❌ 네이버 로그인 URL 생성: 실패")
            return False
            
    except Exception as e:
        print(f"   오류: {e}")
        print("❌ 네이버 로그인 URL 생성: 실패")
        return False

def test_jwt_token_verification():
    print("🔍 JWT 토큰 검증 테스트 (토큰 없음)...")
    data = {}  # 빈 JSON 객체
    status_code, data = make_request('POST', f"{BASE_URL}/auth/jwt/verify", data=data)
    
    if status_code == 401:
        print(f"   상태 코드: {status_code}")
        print(f"   예상된 응답: 401 Unauthorized")
        print("✅ JWT 토큰 검증 (토큰 없음): 통과")
        return True
    else:
        print(f"   상태 코드: {status_code}")
        print(f"   예상과 다른 응답: {data}")
        print("❌ JWT 토큰 검증 (토큰 없음): 실패")
        return False

def test_protected_endpoint_without_token():
    print("🔍 JWT 토큰 없이 보호된 엔드포인트 접근 테스트...")
    status_code, data = make_request('GET', f"{BASE_URL}/api/users/1")
    
    if status_code == 401:
        print(f"   상태 코드: {status_code}")
        print(f"   예상된 응답: 401 Unauthorized")
        print("✅ 보호된 엔드포인트 (토큰 없음): 통과")
        return True
    else:
        print(f"   상태 코드: {status_code}")
        print(f"   예상과 다른 응답: {data}")
        print("❌ 보호된 엔드포인트 (토큰 없음): 실패")
        return False

def test_invalid_jwt_token():
    print("🔍 잘못된 JWT 토큰으로 보호된 엔드포인트 접근 테스트...")
    headers = {'Authorization': 'Bearer invalid_token_here'}
    status_code, data = make_request('GET', f"{BASE_URL}/api/users/1", headers=headers)
    
    if status_code == 401:
        print(f"   상태 코드: {status_code}")
        print(f"   예상된 응답: 401 Unauthorized")
        print("✅ 보호된 엔드포인트 (잘못된 토큰): 통과")
        return True
    else:
        print(f"   상태 코드: {status_code}")
        print(f"   예상과 다른 응답: {data}")
        print("❌ 보호된 엔드포인트 (잘못된 토큰): 실패")
        return False

def test_naver_callback_invalid():
    print("🔍 네이버 로그인 콜백 무효한 데이터 테스트...")
    data = {'code': 'invalid_code', 'state': 'invalid_state'}
    status_code, response_data = make_request('POST', f"{BASE_URL}/auth/naver/callback", data=data)
    
    if status_code == 400:
        print(f"   상태 코드: {status_code}")
        print(f"   예상된 오류: 400 Bad Request")
        print("✅ 네이버 로그인 콜백 무효 데이터: 통과")
        return True
    else:
        print(f"   상태 코드: {status_code}")
        print(f"   예상과 다른 응답: {response_data}")
        print("❌ 네이버 로그인 콜백 무효 데이터: 실패")
        return False

def test_jwt_token_refresh_without_token():
    print("🔍 JWT 토큰 없이 토큰 갱신 테스트...")
    data = {}  # 빈 JSON 객체 (curl과 동일)
    status_code, data = make_request('POST', f"{BASE_URL}/auth/jwt/refresh", data=data)
    
    if status_code == 401:
        print(f"   상태 코드: {status_code}")
        print(f"   예상된 응답: 401 Unauthorized")
        print("✅ JWT 토큰 갱신 (토큰 없음): 통과")
        return True
    else:
        print(f"   상태 코드: {status_code}")
        print(f"   예상과 다른 응답: {data}")
        print("❌ JWT 토큰 갱신 (토큰 없음): 실패")
        return False

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 JWT 인증 네이버 로그인 API 테스트 시작 (urllib.request 사용)")
    print("   테스트 시간:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("   API 서버:", BASE_URL)
    print("=" * 60)
    
    tests = [
        test_health_check,
        test_api_info,
        test_naver_login_url,
        test_jwt_token_verification,
        test_protected_endpoint_without_token,
        test_invalid_jwt_token,
        test_naver_callback_invalid,
        test_jwt_token_refresh_without_token
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 통과했습니다!")
        return True
    else:
        print(f"⚠️ {total - passed}개 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 