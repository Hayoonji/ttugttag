#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR API 테스트 스크립트
Docker 컨테이너가 실행된 후 OCR API를 테스트합니다.
"""

import requests
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image(text="Test OCR Image", width=400, height=200):
    """테스트용 이미지 생성"""
    try:
        # 새 이미지 생성
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 기본 폰트 사용
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # 텍스트 그리기
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # 이미지를 바이트로 변환
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return img_byte_arr
        
    except Exception as e:
        print(f"❌ 테스트 이미지 생성 실패: {e}")
        return None

def test_ocr_api(base_url="http://localhost:5001"):
    """OCR API 테스트"""
    print("🔍 OCR API 테스트 시작...")
    
    # 1. 헬스 체크
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"✅ 헬스 체크: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"   응답: {health_response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 헬스 체크 실패: {e}")
        return False
    
    # 2. 테스트 이미지 생성
    test_image_data = create_test_image("OCR Test Image 2024", 400, 200)
    if not test_image_data:
        print("❌ 테스트 이미지 생성 실패")
        return False
    
    print("✅ 테스트 이미지 생성 완료")
    
    # 3. OCR API 호출
    try:
        files = {'image': ('test_image.png', test_image_data, 'image/png')}
        data = {'debug': 'true'}
        
        print("📤 OCR API 요청 전송 중...")
        ocr_response = requests.post(
            f"{base_url}/api/analyze-image",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📥 OCR API 응답: {ocr_response.status_code}")
        
        if ocr_response.status_code == 200:
            result = ocr_response.json()
            print("✅ OCR API 성공!")
            print(f"   응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ OCR API 실패: {ocr_response.status_code}")
            try:
                error_detail = ocr_response.json()
                print(f"   에러 상세: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"   에러 내용: {ocr_response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ OCR API 요청 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 OCR API 테스트 시작")
    print("=" * 50)
    
    # Docker 컨테이너가 실행 중인지 확인
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker 데몬 실행 중")
            if 'ocr-api-test' in result.stdout:
                print("✅ OCR API 컨테이너 실행 중")
            else:
                print("⚠️ OCR API 컨테이너가 실행되지 않음")
                print("   docker-compose -f docker-compose.test.yml up -d 실행 필요")
                return
        else:
            print("❌ Docker 데몬이 실행되지 않음")
            print("   Docker Desktop을 시작해주세요")
            return
    except Exception as e:
        print(f"⚠️ Docker 상태 확인 실패: {e}")
    
    # OCR API 테스트 실행
    success = test_ocr_api()
    
    print("=" * 50)
    if success:
        print("🎉 OCR API 테스트 성공!")
    else:
        print("💥 OCR API 테스트 실패!")
        print("\n🔧 문제 해결 방법:")
        print("1. Docker Desktop이 실행 중인지 확인")
        print("2. docker-compose -f docker-compose.test.yml up -d 실행")
        print("3. 컨테이너 로그 확인: docker logs ocr-api-test")

if __name__ == "__main__":
    main()
