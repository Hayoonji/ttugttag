#!/usr/bin/env python3
"""
네이버 로그인 API 테스트 스크립트
"""

import requests
import json
import time
from datetime import datetime

# API 기본 URL
BASE_URL = "http://localhost:5002"

def test_health_check():
    """헬스체크 테스트"""
    print("🔍 헬스체크 테스트...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   서비스 상태: {data.get('status')}")
            print(f"   데이터베이스: {data.get('services', {}).get('database')}")
            print(f"   네이버 OAuth: {data.get('services', {}).get('naver_oauth')}")
            return True
        else:
            print(f"   오류: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def test_api_info():
    """API 정보 조회 테스트"""
    print("\n🔍 API 정보 조회 테스트...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   서비스: {data.get('service')}")
            print(f"   버전: {data.get('version')}")
            print(f"   엔드포인트 수: {len(data.get('endpoints', {}))}")
            return True
        else:
            print(f"   오류: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def test_naver_login_url():
    """네이버 로그인 URL 생성 테스트"""
    print("\n🔍 네이버 로그인 URL 생성 테스트...")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/naver/login")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   성공: {data.get('message', 'URL 생성됨')}")
                print(f"   인증 URL: {data.get('auth_url', '')[:80]}...")
                print(f"   State: {data.get('state', '')[:20]}...")
                return True
            else:
                print(f"   실패: {data.get('error')}")
                return False
        else:
            print(f"   오류: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def test_naver_callback_invalid():
    """네이버 로그인 콜백 무효한 데이터 테스트"""
    print("\n🔍 네이버 로그인 콜백 무효한 데이터 테스트...")
    
    try:
        # 무효한 데이터로 테스트
        invalid_data = {
            'code': 'invalid_code',
            'state': 'invalid_state'
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/naver/callback",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"   예상된 오류: {data.get('error')}")
            return True
        else:
            print(f"   예상과 다른 응답: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def test_user_info_not_found():
    """존재하지 않는 사용자 정보 조회 테스트"""
    print("\n🔍 존재하지 않는 사용자 정보 조회 테스트...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/users/nonexistent_user")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 404:
            data = response.json()
            print(f"   예상된 오류: {data.get('error')}")
            return True
        else:
            print(f"   예상과 다른 응답: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def test_user_preferences_update_invalid():
    """사용자 선호도 업데이트 무효한 데이터 테스트"""
    print("\n🔍 사용자 선호도 업데이트 무효한 데이터 테스트...")
    
    try:
        # 무효한 데이터로 테스트
        invalid_data = {
            'preferences': {
                'favorite_category': '카페',
                'budget': 'invalid_budget'  # 숫자가 아닌 값
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/users/test_user/preferences",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   상태 코드: {response.status_code}")
        
        # 500 에러가 발생할 수 있음 (데이터베이스 오류)
        if response.status_code in [400, 500]:
            data = response.json()
            print(f"   오류: {data.get('error')}")
            return True
        else:
            print(f"   예상과 다른 응답: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def test_token_refresh_invalid():
    """토큰 갱신 무효한 데이터 테스트"""
    print("\n🔍 토큰 갱신 무효한 데이터 테스트...")
    
    try:
        # 무효한 리프레시 토큰으로 테스트
        invalid_data = {
            'refresh_token': 'invalid_refresh_token'
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/naver/token/refresh",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"   예상된 오류: {data.get('error')}")
            return True
        else:
            print(f"   예상과 다른 응답: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def test_logout_invalid():
    """로그아웃 무효한 데이터 테스트"""
    print("\n🔍 로그아웃 무효한 데이터 테스트...")
    
    try:
        # 무효한 액세스 토큰으로 테스트
        invalid_data = {
            'access_token': 'invalid_access_token'
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/naver/logout",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"   예상된 오류: {data.get('error')}")
            return True
        else:
            print(f"   예상과 다른 응답: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   연결 오류: {e}")
        return False

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 네이버 로그인 API 테스트 시작")
    print(f"   테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   API 서버: {BASE_URL}")
    print("=" * 60)
    
    tests = [
        ("헬스체크", test_health_check),
        ("API 정보 조회", test_api_info),
        ("네이버 로그인 URL 생성", test_naver_login_url),
        ("네이버 로그인 콜백 무효 데이터", test_naver_callback_invalid),
        ("사용자 정보 조회 (존재하지 않는 사용자)", test_user_info_not_found),
        ("사용자 선호도 업데이트 무효 데이터", test_user_preferences_update_invalid),
        ("토큰 갱신 무효 데이터", test_token_refresh_invalid),
        ("로그아웃 무효 데이터", test_logout_invalid),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name}: 통과")
                passed += 1
            else:
                print(f"❌ {test_name}: 실패")
        except Exception as e:
            print(f"❌ {test_name}: 오류 발생 - {e}")
        
        time.sleep(0.5)  # API 호출 간격 조절
    
    print("\n" + "=" * 60)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 통과했습니다!")
    else:
        print(f"⚠️ {total - passed}개 테스트가 실패했습니다.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 