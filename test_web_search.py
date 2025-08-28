#!/usr/bin/env python3

"""
웹 검색 보완 기능 테스트 스크립트
"""

import os
import sys
import json
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_web_search_fallback():
    """웹 검색 보완 기능 테스트"""
    
    print("🧪 웹 검색 보완 기능 테스트 시작")
    print("=" * 50)
    
    try:
        # 설정 로드
        from config import get_ec2_config
        from rag_system import EC2PersonalizedRAG
        
        config = get_ec2_config()
        rag = EC2PersonalizedRAG(config)
        
        # 데이터베이스 연결
        if not rag.connect_database():
            print("❌ 데이터베이스 연결 실패")
            return False
        
        # 테스트 케이스들
        test_cases = [
            {
                "query": "아마존 프라임 혜택",
                "description": "데이터베이스에 없을 가능성이 높은 검색어"
            },
            {
                "query": "신한카드 새로운 혜택",
                "description": "최신 정보가 필요한 검색어"
            },
            {
                "query": "테슬라 충전 할인",
                "description": "특수한 카테고리 검색어"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}️⃣ 테스트 케이스: {test_case['query']}")
            print(f"   설명: {test_case['description']}")
            print("-" * 30)
            
            # 검색 실행
            result = rag.search_benefits(
                query=test_case['query'],
                user_history=None,
                top_k=5,
                debug=True
            )
            
            if result.get('success'):
                total_results = len(result.get('results', []))
                web_search_used = result.get('web_search_used', False)
                
                print(f"✅ 검색 성공: {total_results}개 결과")
                print(f"🌐 웹 검색 사용: {'예' if web_search_used else '아니오'}")
                
                # 결과 상세 표시
                for j, res in enumerate(result['results'][:3], 1):
                    metadata = res.get('metadata', {})
                    search_type = res.get('search_type', 'unknown')
                    
                    print(f"   {j}. {metadata.get('title', 'N/A')}")
                    print(f"      브랜드: {metadata.get('brand', 'N/A')}")
                    print(f"      카테고리: {metadata.get('category', 'N/A')}")
                    print(f"      검색타입: {search_type}")
                    print(f"      점수: {res.get('similarity_score', 0):.2f}")
                    
                    if search_type == 'web_search':
                        print(f"      🔗 URL: {metadata.get('url', 'N/A')}")
                        print(f"      🔍 키워드: {metadata.get('search_keyword', 'N/A')}")
            else:
                print(f"❌ 검색 실패: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 50)
        print("🎉 웹 검색 보완 기능 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_keys():
    """API 키 설정 확인"""
    print("\n🔑 API 키 설정 확인")
    print("-" * 20)
    
    naver_client_id = os.getenv('NAVER_CLIENT_ID')
    naver_client_secret = os.getenv('NAVER_CLIENT_SECRET')
    
    if naver_client_id and naver_client_id != 'your_naver_client_id_here':
        print("✅ 네이버 Client ID 설정됨")
    else:
        print("⚠️ 네이버 Client ID 미설정 (일반 검색만 사용)")
    
    if naver_client_secret and naver_client_secret != 'your_naver_client_secret_here':
        print("✅ 네이버 Client Secret 설정됨")
    else:
        print("⚠️ 네이버 Client Secret 미설정 (일반 검색만 사용)")
    
    if (naver_client_id and naver_client_id != 'your_naver_client_id_here' and 
        naver_client_secret and naver_client_secret != 'your_naver_client_secret_here'):
        print("🌐 완전한 웹 검색 기능 사용 가능")
    else:
        print("🔄 제한된 웹 검색 기능 (일반 검색만)")

def simulate_low_results():
    """낮은 검색 결과 시뮬레이션"""
    print("\n🎯 낮은 검색 결과 시뮬레이션")
    print("-" * 30)
    
    # 데이터베이스에 없을 가능성이 높은 특수 검색어들
    special_queries = [
        "마이크로소프트 오피스 할인",
        "테슬라 모델 Y 혜택", 
        "애플 아이폰 14 할인",
        "구글 클라우드 크레딧",
        "우버 이츠 첫 주문 할인"
    ]
    
    try:
        from config import get_ec2_config
        from rag_system import EC2PersonalizedRAG
        
        config = get_ec2_config()
        rag = EC2PersonalizedRAG(config)
        
        if not rag.connect_database():
            print("❌ 데이터베이스 연결 실패")
            return
        
        for query in special_queries:
            print(f"\n🔍 검색: {query}")
            
            result = rag.search_benefits(query, top_k=5)
            
            if result.get('success'):
                results_count = len(result.get('results', []))
                web_used = result.get('web_search_used', False)
                
                print(f"   📊 결과: {results_count}개")
                print(f"   🌐 웹검색: {'사용' if web_used else '미사용'}")
                
                # 웹 검색 결과 확인
                web_results = [r for r in result.get('results', []) if r.get('search_type') == 'web_search']
                if web_results:
                    print(f"   🔗 웹검색 결과: {len(web_results)}개")
    
    except Exception as e:
        print(f"❌ 시뮬레이션 오류: {e}")

if __name__ == "__main__":
    print("🚀 웹 검색 보완 기능 종합 테스트")
    print("=" * 60)
    
    # 1. API 키 확인
    test_api_keys()
    
    # 2. 낮은 결과 시뮬레이션
    simulate_low_results()
    
    # 3. 전체 기능 테스트
    test_web_search_fallback()
    
    print("\n" + "=" * 60)
    print("📋 웹 검색 보완 기능 요약:")
    print("• 검색 결과가 3개 미만일 때 자동으로 웹 검색 보완")
    print("• 네이버 검색 API 우선 사용 (API 키 설정 시)")
    print("• API 미설정 시 일반 검색 결과 제공")
    print("• 웹 검색 결과는 RAG 형식으로 변환되어 통합 제공")
    print("• search_type: 'web_search' 또는 'generic_web'로 구분")
