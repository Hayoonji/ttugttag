#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
헬스 체크 API 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_utils import APITester, print_test_result
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_health_check():
    """헬스 체크 API 테스트"""
    logger.info("🏥 헬스 체크 API 테스트 시작")
    
    tester = APITester()
    
    # 1. 기본 헬스 체크
    result = tester.test_endpoint("GET", "/api/health")
    print_test_result("기본 헬스 체크", result)
    
    # 2. 응답 구조 검증
    if result.get("success") and result.get("data"):
        data = result["data"]
        required_fields = ["status", "timestamp", "service", "database_connected"]
        
        for field in required_fields:
            if field in data:
                logger.info(f"   ✅ {field}: {data[field]}")
            else:
                logger.error(f"   ❌ 필수 필드 누락: {field}")
    
    return result.get("success", False)

def test_status_endpoint():
    """상태 조회 API 테스트"""
    logger.info("📊 상태 조회 API 테스트 시작")
    
    tester = APITester()
    
    result = tester.test_endpoint("GET", "/api/status")
    print_test_result("상태 조회", result)
    
    # 응답 구조 검증
    if result.get("success") and result.get("data"):
        data = result["data"]
        required_fields = ["status", "database", "perplexity", "timestamp"]
        
        for field in required_fields:
            if field in data:
                logger.info(f"   ✅ {field}: {data[field]}")
            else:
                logger.error(f"   ❌ 필수 필드 누락: {field}")
    
    return result.get("success", False)

def main():
    """메인 테스트 실행"""
    logger.info("🚀 API 헬스 체크 테스트 시작")
    
    # 서버 연결 확인
    tester = APITester()
    if not tester.health_check():
        logger.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return False
    
    logger.info("✅ API 서버 연결 확인됨")
    
    # 테스트 실행
    health_success = test_health_check()
    status_success = test_status_endpoint()
    
    # 전체 결과
    overall_success = health_success and status_success
    
    if overall_success:
        logger.info("🎉 모든 헬스 체크 테스트 통과!")
    else:
        logger.error("💥 일부 테스트 실패")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 