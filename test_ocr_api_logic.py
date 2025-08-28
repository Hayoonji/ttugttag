#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR API 로직 테스트 스크립트
Flask 없이도 OCR 분석기가 제대로 작동하는지 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.clova_ocr_sdk_analyzer import ClovaOCRSDKAnalyzer

def test_ocr_api_logic():
    """OCR API 로직 테스트"""
    print("🚀 OCR API 로직 테스트 시작")
    print("=" * 50)
    
    # 설정 (실제 API 키 사용)
    config = {
        'clova_ocr_api_key': 'SGdQdEhGV2lxZXVTUWRja1hmS0hOcG9pTXdFdU9pbFo=',
        'clova_ocr_secret_key': 'SGdQdEhGV2lxZXVTUWRja1hmS0hOcG9pTXdFdU9pbFo=',
        'clova_ocr_invoke_url': 'https://wlbnl8oq3x.apigw.ntruss.com/custom/v1/45249/c2af6d9dc5eaf151ca0bc1b590815119b0f6e82921c3c89327ce90302b8c5e86/general'
    }
    
    # OCR 분석기 초기화
    print("🔍 OCR 분석기 초기화 중...")
    analyzer = ClovaOCRSDKAnalyzer(config)
    
    if not analyzer.ocr_client:
        print("❌ OCR 클라이언트 초기화 실패")
        return False
    
    print("✅ OCR 분석기 초기화 완료")
    
    # 테스트 이미지 로드
    test_image_path = "test_image.png"
    if not os.path.exists(test_image_path):
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {test_image_path}")
        return False
    
    try:
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        print(f"📸 테스트 이미지 로드 완료: {len(image_data)} bytes")
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return False
    
    # 이미지 분석 실행 (API 로직과 동일)
    print("\n🔍 이미지 분석 시작 (API 로직 테스트)...")
    result = analyzer.analyze_image_with_llm(image_data, debug=True)
    
    # 결과 출력
    print("\n📊 분석 결과:")
    print("=" * 50)
    
    if result['success']:
        print(f"✅ 성공: {result['analysis_summary']}")
        print(f"📝 추출된 텍스트: {result['extracted_text'][:100]}...")
        print(f"📅 추출된 날짜: {result['extracted_date']}")
        print(f"🏷️ 매칭된 브랜드: {result['matched_brands']}")
        print(f"📊 신뢰도 점수: {result['confidence_scores']}")
        
        if 'llm_analysis' in result:
            llm_result = result['llm_analysis']
            print(f"\n🤖 LLM 분석 결과:")
            print(f"   📦 제품: {llm_result.get('products', [])}")
            print(f"   💰 가격: {llm_result.get('prices', [])}")
            print(f"   📋 요약: {llm_result.get('summary', 'N/A')}")
            print(f"   🔧 분석 타입: {llm_result.get('analysis_type', 'N/A')}")
        
        # API 응답 형식으로 출력 (Flask에서 반환할 형식)
        api_response = {
            "success": True,
            "data": {
                "extracted_text": result['extracted_text'],
                "extracted_date": result['extracted_date'],
                "matched_brands": result['matched_brands'],
                "confidence_scores": result['confidence_scores'],
                "llm_analysis": result.get('llm_analysis', {}),
                "analysis_summary": result['analysis_summary']
            },
            "message": f"이미지 분석 완료: {len(result['matched_brands'])}개 브랜드 매칭, LLM 분석: {result.get('llm_analysis', {}).get('summary', 'N/A')}"
        }
        
        print(f"\n📡 API 응답 형식:")
        print(f"   성공: {api_response['success']}")
        print(f"   메시지: {api_response['message']}")
        print(f"   데이터 키: {list(api_response['data'].keys())}")
        
        return True
        
    else:
        print(f"❌ 실패: {result['error']}")
        return False

if __name__ == "__main__":
    success = test_ocr_api_logic()
    print("\n" + "=" * 50)
    if success:
        print("🎉 OCR API 로직 테스트 성공!")
        print("✅ Flask API에서 이 로직을 호출할 준비가 완료되었습니다.")
    else:
        print("❌ OCR API 로직 테스트 실패!")
        print("🔧 문제를 해결한 후 다시 시도하세요.")
