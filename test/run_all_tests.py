#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 API 테스트를 실행하는 통합 테스트 스크립트
"""

import sys
import os
import time
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_test_module(module_name: str, test_function: str):
    """개별 테스트 모듈 실행"""
    try:
        logger.info(f"🔄 {module_name} 테스트 실행 중...")
        
        # 모듈 import 및 실행
        if module_name == "health":
            from test_health import main as test_main
        elif module_name == "chat":
            from test_chat import main as test_main
        elif module_name == "image_analysis":
            from test_image_analysis import main as test_main
        else:
            logger.error(f"❌ 알 수 없는 테스트 모듈: {module_name}")
            return False
        
        # 테스트 실행
        start_time = time.time()
        result = test_main()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        if result:
            logger.info(f"✅ {module_name} 테스트 통과 (소요시간: {execution_time:.2f}초)")
        else:
            logger.error(f"❌ {module_name} 테스트 실패 (소요시간: {execution_time:.2f}초)")
        
        return result
        
    except ImportError as e:
        logger.error(f"❌ {module_name} 모듈 import 실패: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ {module_name} 테스트 실행 중 오류: {e}")
        return False

def run_smoke_test():
    """스모크 테스트 (기본 기능만 빠르게 테스트)"""
    logger.info("🚬 스모크 테스트 시작")
    
    from api_utils import APITester
    
    tester = APITester()
    
    # 1. 헬스 체크
    if not tester.health_check():
        logger.error("❌ 스모크 테스트 실패: API 서버 연결 불가")
        return False
    
    # 2. 상태 조회
    status_result = tester.test_endpoint("GET", "/api/status")
    if not status_result.get("success"):
        logger.error("❌ 스모크 테스트 실패: 상태 조회 실패")
        return False
    
    logger.info("✅ 스모크 테스트 통과")
    return True

def run_full_test_suite():
    """전체 테스트 스위트 실행"""
    logger.info("🚀 전체 API 테스트 스위트 시작")
    
    # 테스트 모듈 목록
    test_modules = [
        ("health", "헬스 체크"),
        ("chat", "챗봇 API"),
        ("image_analysis", "이미지 분석")
    ]
    
    # 스모크 테스트 먼저 실행
    if not run_smoke_test():
        logger.error("❌ 스모크 테스트 실패로 전체 테스트 중단")
        return False
    
    # 개별 테스트 모듈 실행
    test_results = []
    total_start_time = time.time()
    
    for module_name, display_name in test_modules:
        logger.info(f"\n{'='*50}")
        logger.info(f"📋 {display_name} 테스트 시작")
        logger.info(f"{'='*50}")
        
        result = run_test_module(module_name, display_name)
        test_results.append((module_name, display_name, result))
        
        # 테스트 간 간격
        time.sleep(1)
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    # 결과 요약
    logger.info(f"\n{'='*60}")
    logger.info("📊 전체 테스트 결과 요약")
    logger.info(f"{'='*60}")
    
    passed_tests = sum(1 for _, _, result in test_results if result)
    total_tests = len(test_results)
    
    for module_name, display_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {display_name}")
    
    logger.info(f"\n🎯 전체 결과: {passed_tests}/{total_tests} 통과")
    logger.info(f"⏱️ 총 소요시간: {total_execution_time:.2f}초")
    
    if passed_tests == total_tests:
        logger.info("🎉 모든 테스트 통과!")
        return True
    else:
        logger.error("💥 일부 테스트 실패")
        return False

def run_specific_test(test_name: str):
    """특정 테스트만 실행"""
    logger.info(f"🎯 특정 테스트 실행: {test_name}")
    
    if test_name == "smoke":
        return run_smoke_test()
    elif test_name in ["health", "chat", "image_analysis"]:
        return run_test_module(test_name, test_name)
    else:
        logger.error(f"❌ 알 수 없는 테스트: {test_name}")
        logger.info("사용 가능한 테스트:")
        logger.info("  - smoke: 스모크 테스트")
        logger.info("  - health: 헬스 체크 테스트")
        logger.info("  - chat: 챗봇 API 테스트")
        logger.info("  - image_analysis: 이미지 분석 API 테스트")
        logger.info("  - all: 전체 테스트")
        return False

def main():
    """메인 함수"""
    logger.info("🚀 API 테스트 러너 시작")
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "all":
            success = run_full_test_suite()
        else:
            success = run_specific_test(test_type)
    else:
        # 기본값: 스모크 테스트만 실행
        logger.info("📝 테스트 타입이 지정되지 않아 스모크 테스트를 실행합니다.")
        logger.info("사용법:")
        logger.info("  python run_all_tests.py [test_type]")
        logger.info("  test_type: smoke, health, chat, image_analysis, all")
        success = run_smoke_test()
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 