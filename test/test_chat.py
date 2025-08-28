#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
챗봇 API 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_utils import APITester, print_test_result
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chat_basic():
    """기본 챗봇 API 테스트"""
    logger.info("💬 기본 챗봇 API 테스트 시작")
    
    tester = APITester()
    
    # 기본 쿼리 테스트
    test_queries = [
        "안녕하세요",
        "할인 혜택이 있나요?",
        "카페 추천해주세요",
        "최근 인기 브랜드는?"
    ]
    
    success_count = 0
    total_count = len(test_queries)
    
    for query in test_queries:
        logger.info(f"   테스트 쿼리: {query}")
        
        result = tester.test_endpoint("POST", "/api/chat", json_data={
            "query": query,
            "debug": False
        })
        
        if result.get("success"):
            success_count += 1
            logger.info(f"   ✅ 응답 성공")
            
            # 응답 구조 검증
            if result.get("data"):
                data = result["data"]
                if "success" in data and "answer" in data:
                    logger.info(f"   ✅ 응답 구조 정상")
                else:
                    logger.warning(f"   ⚠️ 응답 구조 이상: {data}")
        else:
            logger.error(f"   ❌ 응답 실패: {result.get('error', '알 수 없는 오류')}")
    
    success_rate = success_count / total_count * 100
    logger.info(f"   📊 성공률: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    return success_rate >= 80  # 80% 이상 성공 시 통과

def test_chat_debug_mode():
    """디버그 모드 챗봇 API 테스트"""
    logger.info("🔍 디버그 모드 챗봇 API 테스트 시작")
    
    tester = APITester()
    
    result = tester.test_endpoint("POST", "/api/chat", json_data={
        "query": "디버그 모드 테스트",
        "debug": True
    })
    
    print_test_result("디버그 모드 챗봇", result)
    
    # 디버그 모드 응답 검증
    if result.get("success") and result.get("data"):
        data = result["data"]
        if "success" in data and "answer" in data:
            logger.info("   ✅ 디버그 모드 응답 정상")
            return True
        else:
            logger.error("   ❌ 디버그 모드 응답 구조 이상")
            return False
    
    return result.get("success", False)

def test_chat_error_handling():
    """에러 처리 테스트"""
    logger.info("⚠️ 에러 처리 테스트 시작")
    
    tester = APITester()
    
    # 1. 빈 쿼리 테스트
    result1 = tester.test_endpoint("POST", "/api/chat", json_data={})
    print_test_result("빈 쿼리 에러 처리", result1)
    
    # 2. 잘못된 JSON 테스트
    result2 = tester.test_endpoint("POST", "/api/chat", data="invalid json")
    print_test_result("잘못된 JSON 에러 처리", result2)
    
    # 3. 쿼리 필드 누락 테스트
    result3 = tester.test_endpoint("POST", "/api/chat", json_data={"debug": True})
    print_test_result("쿼리 필드 누락 에러 처리", result3)
    
    # 에러 처리 테스트는 적절한 에러 응답을 받아야 함
    error_handling_success = (
        not result1.get("success") and 
        not result2.get("success") and 
        not result3.get("success")
    )
    
    if error_handling_success:
        logger.info("   ✅ 에러 처리 정상 작동")
    else:
        logger.warning("   ⚠️ 일부 에러 처리가 예상과 다름")
    
    return error_handling_success

def test_chat_response_structure():
    """응답 구조 상세 검증"""
    logger.info("🏗️ 응답 구조 상세 검증 시작")
    
    tester = APITester()
    
    result = tester.test_endpoint("POST", "/api/chat", json_data={
        "query": "응답 구조 테스트",
        "debug": False
    })
    
    if not result.get("success"):
        logger.error("   ❌ 응답을 받을 수 없어 구조 검증 불가")
        return False
    
    data = result["data"]
    
    # 필수 필드 검증
    required_fields = ["success", "answer"]
    missing_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        logger.error(f"   ❌ 필수 필드 누락: {missing_fields}")
        return False
    
    # 응답 타입 검증
    if not isinstance(data["success"], bool):
        logger.error("   ❌ success 필드가 boolean 타입이 아님")
        return False
    
    if not isinstance(data["answer"], str):
        logger.error("   ❌ answer 필드가 string 타입이 아님")
        return False
    
    # 응답 길이 검증
    if len(data["answer"]) < 10:
        logger.warning("   ⚠️ answer가 너무 짧음")
    
    logger.info("   ✅ 응답 구조 검증 통과")
    return True

def main():
    """메인 테스트 실행"""
    logger.info("🚀 챗봇 API 테스트 시작")
    
    # 서버 연결 확인
    tester = APITester()
    if not tester.health_check():
        logger.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return False
    
    logger.info("✅ API 서버 연결 확인됨")
    
    # 테스트 실행
    test_results = []
    
    test_results.append(("기본 챗봇", test_chat_basic()))
    test_results.append(("디버그 모드", test_chat_debug_mode()))
    test_results.append(("에러 처리", test_chat_error_handling()))
    test_results.append(("응답 구조", test_chat_response_structure()))
    
    # 결과 요약
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    logger.info(f"\n📊 테스트 결과 요약:")
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {status} {test_name}")
    
    logger.info(f"\n🎯 전체 결과: {passed_tests}/{total_tests} 통과")
    
    if passed_tests == total_tests:
        logger.info("🎉 모든 챗봇 API 테스트 통과!")
    else:
        logger.error("💥 일부 테스트 실패")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 