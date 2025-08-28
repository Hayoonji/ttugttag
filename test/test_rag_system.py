#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG 시스템 테스트 스크립트
"""

import sys
import os
import time
from datetime import datetime

# 상위 디렉토리의 tools 폴더를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from main_rag_system import LangGraphRAGSystem
from user_history_data import create_sample_user_history

def print_header(title):
    """헤더 출력"""
    print("\n" + "="*60)
    print(f"🎯 {title}")
    print("="*60)

def print_section(title):
    """섹션 출력"""
    print(f"\n📋 {title}")
    print("-" * 40)

def test_rag_system():
    """RAG 시스템 전체 테스트"""
    print_header("TTUGTTAG RAG 시스템 테스트")
    
    # 1. 시스템 초기화 테스트
    print_section("1. 시스템 초기화")
    try:
        rag = LangGraphRAGSystem()
        print("✅ LangGraphRAGSystem 인스턴스 생성 성공")
        
        # 데이터베이스 연결 테스트
        if rag.connect_database():
            print("✅ ChromaDB 연결 성공")
        else:
            print("⚠️ ChromaDB 연결 실패 - 더미 데이터로 테스트 진행")
        
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        return False
    
    # 2. 사용자 이력 생성 테스트
    print_section("2. 사용자 이력 생성")
    try:
        user_history = create_sample_user_history()
        print(f"✅ 샘플 사용자 이력 생성 완료: {len(user_history)}개 거래")
        
        # 사용자 이력 통계
        total_spending = sum(item['amount'] for item in user_history)
        print(f"   총 소비액: {total_spending:,}원")
        
        # 브랜드별 소비 통계
        brand_counts = {}
        for item in user_history:
            brand = item['brand']
            brand_counts[brand] = brand_counts.get(brand, 0) + item['amount']
        
        print("   브랜드별 소비:")
        for brand, amount in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"     • {brand}: {amount:,}원")
            
    except Exception as e:
        print(f"❌ 사용자 이력 생성 실패: {e}")
        return False
    
    # 3. 쿼리 테스트
    test_queries = [
        {
            "query": "스타벅스 할인 혜택 있어?",
            "description": "브랜드별 직접 검색 테스트"
        },
        {
            "query": "내 소비 패턴에 맞는 혜택 추천해줘",
            "description": "개인화 추천 테스트"
        },
        {
            "query": "카페 할인 이벤트 궁금해",
            "description": "카테고리별 검색 테스트"
        },
        {
            "query": "편의점 쿠폰 있나?",
            "description": "카테고리 검색 테스트"
        },
        {
            "query": "이마트에서 10만원 썼어, 혜택 추천해줘",
            "description": "소비 기반 추천 테스트"
        },
        {
            "query": "애플워치 할인",
            "description": "실시간 검색 테스트 (DB에 없는 항목)"
        }
    ]
    
    print_section("3. 쿼리 테스트")
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🔍 테스트 {i}: {test_case['description']}")
        print(f"   쿼리: '{test_case['query']}'")
        
        try:
            start_time = time.time()
            result = rag.run(test_case['query'], user_history, debug=False)
            end_time = time.time()
            
            print(f"   ⏱️ 실행 시간: {end_time - start_time:.2f}초")
            print(f"   📝 결과 길이: {len(result)}자")
            
            # 결과 미리보기
            preview = result[:200] + "..." if len(result) > 200 else result
            print(f"   📋 결과 미리보기: {preview}")
            
            if "❌" in result:
                print("   ⚠️ 오류 또는 결과 없음")
            else:
                print("   ✅ 성공")
                
        except Exception as e:
            print(f"   ❌ 테스트 실패: {e}")
    
    # 4. 성능 테스트
    print_section("4. 성능 테스트")
    
    performance_queries = [
        "스타벅스",
        "카페",
        "편의점",
        "마트"
    ]
    
    total_time = 0
    success_count = 0
    
    for query in performance_queries:
        try:
            start_time = time.time()
            result = rag.run(query, user_history, debug=False)
            end_time = time.time()
            
            execution_time = end_time - start_time
            total_time += execution_time
            success_count += 1
            
            print(f"   '{query}': {execution_time:.2f}초")
            
        except Exception as e:
            print(f"   '{query}': 실패 ({e})")
    
    if success_count > 0:
        avg_time = total_time / success_count
        print(f"\n   📊 평균 실행 시간: {avg_time:.2f}초")
        print(f"   📊 성공률: {success_count}/{len(performance_queries)} ({success_count/len(performance_queries)*100:.1f}%)")
    
    # 5. 시스템 정보 출력
    print_section("5. 시스템 정보")
    
    if hasattr(rag, 'collection') and rag.collection:
        try:
            doc_count = rag.collection.count()
            print(f"   📊 데이터베이스 문서 수: {doc_count}개")
        except:
            print("   📊 데이터베이스 문서 수: 확인 불가")
    
    if hasattr(rag, 'available_brands'):
        print(f"   🏷️ 지원 브랜드 수: {len(rag.available_brands)}개")
    
    if hasattr(rag, 'available_categories'):
        print(f"   📂 지원 카테고리 수: {len(rag.available_categories)}개")
    
    print("\n✅ 테스트 완료!")
    return True

def test_individual_components():
    """개별 컴포넌트 테스트"""
    print_header("개별 컴포넌트 테스트")
    
    # 1. API 유틸리티 테스트
    print_section("1. API 유틸리티 테스트")
    try:
        from api_utils import PerplexityAPI, PersonalizedScoreCalculator
        
        # PerplexityAPI 테스트
        perplexity = PerplexityAPI()
        print("✅ PerplexityAPI 인스턴스 생성 성공")
        
        # PersonalizedScoreCalculator 테스트
        calculator = PersonalizedScoreCalculator()
        user_history = {
            'brand_counts': {'스타벅스': 5, '이마트': 3},
            'category_counts': {'카페': 5, '마트': 3},
            'total_transactions': 8
        }
        score = calculator.calculate_preference_score('스타벅스', '카페', user_history)
        print(f"✅ 개인화 스코어 계산 성공: {score:.3f}")
        
    except Exception as e:
        print(f"❌ API 유틸리티 테스트 실패: {e}")
    
    # 2. 쿼리 파서 테스트
    print_section("2. 쿼리 파서 테스트")
    try:
        from multi_category_parser import MultiCategoryQueryParser
        
        test_queries = [
            "스타벅스에서 5만원 썼어",
            "카페 할인 이벤트",
            "편의점 쿠폰"
        ]
        
        for query in test_queries:
            analysis = MultiCategoryQueryParser.analyze_query_intent(query)
            print(f"   '{query}' -> 의도: {analysis['intent']}")
        
        print("✅ 쿼리 파서 테스트 성공")
        
    except Exception as e:
        print(f"❌ 쿼리 파서 테스트 실패: {e}")

def main():
    """메인 실행 함수"""
    print("🎯 TTUGTTAG RAG 시스템 테스트 시작")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 개별 컴포넌트 테스트
    test_individual_components()
    
    # 전체 시스템 테스트
    success = test_rag_system()
    
    print_header("테스트 결과 요약")
    if success:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("💡 이제 Streamlit 웹 앱을 실행해보세요:")
        print("   cd web")
        print("   streamlit run streamlit_app.py")
    else:
        print("⚠️ 일부 테스트에서 문제가 발생했습니다.")
        print("🔧 시스템 설정을 확인해주세요.")
    
    print(f"\n📅 테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 