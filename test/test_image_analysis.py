#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 분석 API 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_utils import APITester, print_test_result, create_test_image
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_image_analysis_basic():
    """기본 이미지 분석 API 테스트"""
    logger.info("🖼️ 기본 이미지 분석 API 테스트 시작")
    
    tester = APITester()
    
    # 테스트 이미지 생성
    test_image_path = create_test_image(200, 200, "Test Image")
    if not test_image_path:
        logger.error("   ❌ 테스트 이미지 생성 실패")
        return False
    
    try:
        # 이미지 파일로 테스트
        with open(test_image_path, 'rb') as image_file:
            result = tester.test_endpoint("POST", "/api/analyze-image", 
                                        files={'image': image_file},
                                        data={'debug': 'false'})
        
        print_test_result("기본 이미지 분석", result)
        
        # 응답 구조 검증
        if result.get("success") and result.get("data"):
            data = result["data"]
            required_fields = ["extracted_text", "extracted_date", "matched_brands", 
                             "confidence_scores", "analysis_summary"]
            
            missing_fields = []
            for field in required_fields:
                if field in data:
                    logger.info(f"   ✅ {field}: {data[field]}")
                else:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"   ❌ 필수 필드 누락: {missing_fields}")
                return False
            
            return True
        else:
            logger.error("   ❌ 응답 실패")
            return False
            
    finally:
        # 테스트 이미지 정리
        try:
            os.remove(test_image_path)
            logger.info(f"   🗑️ 테스트 이미지 정리: {test_image_path}")
        except:
            pass
    
    return False

def test_image_analysis_debug_mode():
    """디버그 모드 이미지 분석 API 테스트"""
    logger.info("🔍 디버그 모드 이미지 분석 API 테스트 시작")
    
    tester = APITester()
    
    # 테스트 이미지 생성
    test_image_path = create_test_image(150, 150, "Debug Test")
    if not test_image_path:
        logger.error("   ❌ 테스트 이미지 생성 실패")
        return False
    
    try:
        # 디버그 모드로 테스트
        with open(test_image_path, 'rb') as image_file:
            result = tester.test_endpoint("POST", "/api/analyze-image", 
                                        files={'image': image_file},
                                        data={'debug': 'true'})
        
        print_test_result("디버그 모드 이미지 분석", result)
        
        if result.get("success"):
            logger.info("   ✅ 디버그 모드 응답 성공")
            return True
        else:
            logger.error("   ❌ 디버그 모드 응답 실패")
            return False
            
    finally:
        # 테스트 이미지 정리
        try:
            os.remove(test_image_path)
        except:
            pass
    
    return False

def test_image_analysis_error_handling():
    """에러 처리 테스트"""
    logger.info("⚠️ 이미지 분석 에러 처리 테스트 시작")
    
    tester = APITester()
    
    # 1. 이미지 파일 없음 테스트
    result1 = tester.test_endpoint("POST", "/api/analyze-image", data={'debug': 'false'})
    print_test_result("이미지 파일 없음 에러 처리", result1)
    
    # 2. 빈 파일명 테스트
    result2 = tester.test_endpoint("POST", "/api/analyze-image", 
                                  files={'image': ('', b'')},
                                  data={'debug': 'false'})
    print_test_result("빈 파일명 에러 처리", result2)
    
    # 3. 잘못된 이미지 데이터 테스트
    result3 = tester.test_endpoint("POST", "/api/analyze-image", 
                                  files={'image': ('test.txt', b'invalid image data')},
                                  data={'debug': 'false'})
    print_test_result("잘못된 이미지 데이터 에러 처리", result3)
    
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

def test_image_analysis_response_structure():
    """응답 구조 상세 검증"""
    logger.info("🏗️ 이미지 분석 응답 구조 상세 검증 시작")
    
    tester = APITester()
    
    # 테스트 이미지 생성
    test_image_path = create_test_image(100, 100, "Structure Test")
    if not test_image_path:
        logger.error("   ❌ 테스트 이미지 생성 실패")
        return False
    
    try:
        with open(test_image_path, 'rb') as image_file:
            result = tester.test_endpoint("POST", "/api/analyze-image", 
                                        files={'image': image_file},
                                        data={'debug': 'false'})
        
        if not result.get("success"):
            logger.error("   ❌ 응답을 받을 수 없어 구조 검증 불가")
            return False
        
        data = result["data"]
        
        # 필수 필드 검증
        required_fields = ["extracted_text", "extracted_date", "matched_brands", 
                          "confidence_scores", "analysis_summary"]
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"   ❌ 필수 필드 누락: {missing_fields}")
            return False
        
        # 데이터 타입 검증
        if not isinstance(data["extracted_text"], str):
            logger.error("   ❌ extracted_text가 string 타입이 아님")
            return False
        
        if not isinstance(data["matched_brands"], list):
            logger.error("   ❌ matched_brands가 list 타입이 아님")
            return False
        
        if not isinstance(data["confidence_scores"], dict):
            logger.error("   ❌ confidence_scores가 dict 타입이 아님")
            return False
        
        logger.info("   ✅ 응답 구조 검증 통과")
        return True
        
    finally:
        # 테스트 이미지 정리
        try:
            os.remove(test_image_path)
        except:
            pass
    
    return False

def test_image_analysis_performance():
    """성능 테스트"""
    logger.info("⚡ 이미지 분석 성능 테스트 시작")
    
    tester = APITester()
    
    # 다양한 크기의 이미지로 테스트
    test_cases = [
        (50, 50, "Small"),
        (200, 200, "Medium"),
        (400, 400, "Large")
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for width, height, size_name in test_cases:
        logger.info(f"   테스트 이미지 크기: {width}x{height} ({size_name})")
        
        test_image_path = create_test_image(width, height, f"{size_name} Test")
        if not test_image_path:
            logger.error(f"   ❌ {size_name} 테스트 이미지 생성 실패")
            continue
        
        try:
            import time
            start_time = time.time()
            
            with open(test_image_path, 'rb') as image_file:
                result = tester.test_endpoint("POST", "/api/analyze-image", 
                                            files={'image': image_file},
                                            data={'debug': 'false'})
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if result.get("success"):
                success_count += 1
                logger.info(f"   ✅ {size_name} 이미지 분석 성공 (응답시간: {response_time:.2f}초)")
                
                # 응답 시간 검증 (5초 이내)
                if response_time > 5:
                    logger.warning(f"   ⚠️ {size_name} 이미지 응답시간이 길음: {response_time:.2f}초")
            else:
                logger.error(f"   ❌ {size_name} 이미지 분석 실패")
                
        finally:
            # 테스트 이미지 정리
            try:
                os.remove(test_image_path)
            except:
                pass
    
    success_rate = success_count / total_count * 100
    logger.info(f"   📊 성능 테스트 성공률: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    return success_rate >= 80  # 80% 이상 성공 시 통과

def main():
    """메인 테스트 실행"""
    logger.info("🚀 이미지 분석 API 테스트 시작")
    
    # 서버 연결 확인
    tester = APITester()
    if not tester.health_check():
        logger.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return False
    
    logger.info("✅ API 서버 연결 확인됨")
    
    # 테스트 실행
    test_results = []
    
    test_results.append(("기본 이미지 분석", test_image_analysis_basic()))
    test_results.append(("디버그 모드", test_image_analysis_debug_mode()))
    test_results.append(("에러 처리", test_image_analysis_error_handling()))
    test_results.append(("응답 구조", test_image_analysis_response_structure()))
    test_results.append(("성능 테스트", test_image_analysis_performance()))
    
    # 결과 요약
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    logger.info(f"\n📊 테스트 결과 요약:")
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {status} {test_name}")
    
    logger.info(f"\n🎯 전체 결과: {passed_tests}/{total_tests} 통과")
    
    if passed_tests == total_tests:
        logger.info("🎉 모든 이미지 분석 API 테스트 통과!")
    else:
        logger.error("💥 일부 테스트 실패")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 