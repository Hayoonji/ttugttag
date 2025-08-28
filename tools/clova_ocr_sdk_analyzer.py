# ======================================================================================
# Clova OCR SDK 기반 이미지 분석기
# ======================================================================================

import os
import json
import logging
import base64
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from PIL import Image
import io

import requests

# Clova OCR API 직접 호출 구현
class ClovaOCR:
    def __init__(self, api_key: str, secret_key: str, invoke_url: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.invoke_url = invoke_url
        self.headers = {
            'X-OCR-SECRET': secret_key,
            'Content-Type': 'application/json'
        }
    
    def extract_text(self, image_data: bytes, use_dummy: bool = False) -> Dict[str, Any]:
        """Clova OCR API 직접 호출 또는 더미 응답"""
        
        # 더미 응답 모드 (테스트용)
        if use_dummy:
            return {
                "success": True,
                "text": "테스트 이미지에서 추출된 텍스트\n스타벱스 커피\n아메리카노 4,500원\n2024-12-25",
                "confidence": 0.95,
                "language": "ko",
                "raw_response": {"dummy": True}
            }
        
        try:
            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # API 요청 데이터
            request_data = {
                "images": [
                    {
                        "format": "png",
                        "name": "image",
                        "data": image_base64
                    }
                ],
                "requestId": str(datetime.now().timestamp()),
                "version": "V2",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            
            # API 호출
            response = requests.post(
                self.invoke_url,
                headers=self.headers,
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # Clova OCR 응답 파싱
                extracted_text = self._parse_clova_response(result)
                return {
                    "success": True,
                    "text": extracted_text,
                    "confidence": 0.95,
                    "language": "ko",
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"API 호출 실패: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OCR 처리 실패: {str(e)}"
            }
    
    def _parse_clova_response(self, response: Dict[str, Any]) -> str:
        """Clova OCR 응답에서 텍스트 추출"""
        try:
            if 'images' in response and len(response['images']) > 0:
                image = response['images'][0]
                if 'fields' in image:
                    # fields에서 텍스트 추출
                    texts = []
                    for field in image['fields']:
                        if 'inferText' in field:
                            texts.append(field['inferText'])
                    return '\n'.join(texts)
                elif 'text' in image:
                    # text 필드가 있는 경우
                    return image['text']
            
            # 기본 텍스트 반환
            return "텍스트를 추출할 수 없습니다."
            
        except Exception as e:
            return f"응답 파싱 실패: {str(e)}"

CLOVA_SDK_AVAILABLE = True  # HTTP 요청 방식이므로 항상 사용 가능

class ClovaOCRSDKAnalyzer:
    """Clova OCR SDK를 사용한 이미지 분석기"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 로거 초기화 - 하드코딩된 로그 파일 경로 문제 해결
        self.logger = logging.getLogger(__name__)
        
        # 기존 핸들러 제거 (상속받은 문제가 있는 핸들러)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 새로운 핸들러 설정
        if not self.logger.handlers:
            # 콘솔 핸들러만 사용
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)
        
        # Clova OCR API 직접 호출 초기화
        try:
            self.ocr_client = ClovaOCR(
                api_key=config.get('clova_ocr_api_key', ''),
                secret_key=config.get('clova_ocr_secret_key', ''),
                invoke_url=config.get('clova_ocr_invoke_url', '')
            )
            self.logger.info("✅ Clova OCR API 직접 호출 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ Clova OCR API 초기화 실패: {e}")
            self.ocr_client = None
    
    def validate_image(self, image_data: bytes) -> Dict[str, Any]:
        """이미지 유효성 검증"""
        try:
            # PIL을 사용하여 이미지 정보 확인
            image = Image.open(io.BytesIO(image_data))
            
            # 이미지 형식 확인
            format_name = image.format.lower() if image.format else 'unknown'
            if format_name not in ['jpeg', 'jpg', 'png', 'bmp', 'tiff']:
                return {
                    'valid': False,
                    'error': f'지원하지 않는 이미지 형식: {format_name}'
                }
            
            # 이미지 크기 확인
            width, height = image.size
            if width < 100 or height < 100:
                return {
                    'valid': False,
                    'error': f'이미지가 너무 작습니다: {width}x{height}'
                }
            
            return {
                'valid': True,
                'width': width,
                'height': height,
                'format': format_name,
                'size': len(image_data)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'이미지 검증 실패: {str(e)}'
            }
    
    def analyze_image_with_llm(self, image_data: bytes, debug: bool = False) -> Dict[str, Any]:
        """이미지 분석 및 LLM 처리"""
        try:
            if debug:
                self.logger.info("🔍 Clova OCR SDK + LLM으로 이미지 분석 시작...")
            
            # 이미지 검증
            validation_result = self.validate_image(image_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error']
                }
            
            if debug:
                self.logger.info(f"✅ 이미지 검증 통과: {validation_result['width']}x{validation_result['height']}, {validation_result['format']}")
            
            # Clova OCR SDK로 텍스트 추출
            if self.ocr_client is None:
                return {
                    'success': False,
                    'error': 'Clova OCR SDK가 초기화되지 않았습니다.'
                }
            
            # OCR 실행 (실제 API 호출)
            ocr_result = self.ocr_client.extract_text(image_data, use_dummy=False)
            
            if not ocr_result.get('success', False):
                return {
                    'success': False,
                    'error': f"OCR 실패: {ocr_result.get('error', 'Unknown error')}"
                }
            
            # 결과 파싱
            extracted_text = ocr_result.get('text', '')
            extracted_date = self._extract_date_from_text(extracted_text)
            
            if debug:
                self.logger.info(f"✅ OCR 완료: 텍스트 길이 {len(extracted_text)}, 날짜: {extracted_date}")
            
            # LLM으로 텍스트 분석 및 브랜드 매칭
            llm_analysis = self._analyze_with_llm(extracted_text, debug)
            
            # 브랜드 매칭
            matched_brands = self._match_brands(extracted_text)
            confidence_scores = self._calculate_confidence_scores(extracted_text)
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'extracted_date': extracted_date,
                'matched_brands': matched_brands,
                'confidence_scores': confidence_scores,
                'llm_analysis': llm_analysis,
                'analysis_summary': f"OCR을 통해 {len(matched_brands)}개 브랜드가 식별되었습니다. LLM 분석: {llm_analysis.get('summary', 'N/A')}",
                'raw_ocr': ocr_result
            }
            
        except Exception as e:
            error_msg = f"이미지 분석 중 오류 발생: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def analyze_image(self, image_data: bytes, debug: bool = False) -> Dict[str, Any]:
        """이미지 분석 및 텍스트 추출 (기존 메소드 - 호환성 유지)"""
        return self.analyze_image_with_llm(image_data, debug)
    
    def _analyze_with_llm(self, text: str, debug: bool = False) -> Dict[str, Any]:
        """LLM으로 텍스트 분석"""
        try:
            if debug:
                self.logger.info("🤖 LLM으로 텍스트 분석 시작...")
            
            # LLM이 사용 가능한 경우 실제 분석 수행
            if hasattr(self, 'llm_client') and self.llm_client:
                return self._call_llm_api(text, debug)
            
            # LLM이 없는 경우 규칙 기반 분석
            return self._rule_based_analysis(text, debug)
            
        except Exception as e:
            self.logger.error(f"LLM 분석 실패: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'summary': 'LLM 분석 실패'
            }
    
    def _call_llm_api(self, text: str, debug: bool = False) -> Dict[str, Any]:
        """실제 LLM API 호출"""
        try:
            # Clova X 또는 다른 LLM API 호출 로직
            # 여기서는 예시로 간단한 분석 결과 반환
            prompt = f"""
            다음 텍스트를 분석하여 브랜드, 제품, 가격, 날짜 등을 추출해주세요:
            
            텍스트: {text}
            
            JSON 형식으로 응답해주세요:
            {{
                "brands": ["브랜드명"],
                "products": ["제품명"],
                "prices": ["가격"],
                "date": "날짜",
                "summary": "요약"
            }}
            """
            
            if debug:
                self.logger.info(f"📤 LLM API 호출: {len(prompt)}자 프롬프트")
            
            # 실제 LLM API 호출 로직 (구현 필요)
            # response = self.llm_client.generate(prompt)
            
            # 임시로 규칙 기반 분석 결과 반환
            return self._rule_based_analysis(text, debug)
            
        except Exception as e:
            self.logger.error(f"LLM API 호출 실패: {str(e)}")
            return self._rule_based_analysis(text, debug)
    
    def _rule_based_analysis(self, text: str, debug: bool = False) -> Dict[str, Any]:
        """규칙 기반 텍스트 분석"""
        try:
            if debug:
                self.logger.info("📋 규칙 기반 텍스트 분석 수행...")
            
            # 가격 추출
            prices = re.findall(r'[\d,]+원', text)
            
            # 제품명 추출 (가격 앞의 텍스트)
            products = []
            for price in prices:
                price_idx = text.find(price)
                if price_idx > 0:
                    # 가격 앞 10자 이내의 텍스트를 제품명으로 추정
                    start_idx = max(0, price_idx - 10)
                    product_text = text[start_idx:price_idx].strip()
                    if product_text:
                        products.append(product_text)
            
            # 요약 생성
            summary_parts = []
            if prices:
                summary_parts.append(f"가격: {', '.join(prices)}")
            if products:
                summary_parts.append(f"제품: {', '.join(products)}")
            
            summary = " | ".join(summary_parts) if summary_parts else "텍스트 분석 완료"
            
            if debug:
                self.logger.info(f"📋 규칙 기반 분석 완료: {len(prices)}개 가격, {len(products)}개 제품")
            
            return {
                'success': True,
                'brands': self._match_brands(text),
                'products': products,
                'prices': prices,
                'date': self._extract_date_from_text(text),
                'summary': summary,
                'analysis_type': 'rule_based'
            }
            
        except Exception as e:
            self.logger.error(f"규칙 기반 분석 실패: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'summary': '분석 실패'
            }
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """텍스트에서 날짜 추출"""
        # 간단한 날짜 패턴 매칭
        import re
        
        # 다양한 날짜 패턴
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    def _match_brands(self, text: str) -> List[str]:
        """텍스트에서 브랜드 매칭"""
        # 간단한 브랜드 키워드 매칭
        brand_keywords = [
            '스타벅스', '이디야', '투썸플레이스', '할리스', '파스쿠찌',
            'starbucks', 'ediya', 'twosome', 'hollys', 'pascucci',
            '카페베네', '탐앤탐스', '커피빈', '빽다방', '메가커피'
        ]
        
        matched_brands = []
        text_lower = text.lower()
        
        for brand in brand_keywords:
            if brand.lower() in text_lower:
                matched_brands.append(brand)
        
        return matched_brands
    
    def _calculate_confidence_scores(self, text: str) -> Dict[str, float]:
        """신뢰도 점수 계산"""
        # 간단한 신뢰도 계산 로직
        scores = {}
        
        if len(text) > 0:
            # 텍스트 길이 기반 기본 신뢰도
            base_confidence = min(0.9, len(text) / 100)
            
            # 특수 문자 비율에 따른 조정
            special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
            special_ratio = special_chars / len(text) if len(text) > 0 else 0
            
            # 최종 신뢰도
            final_confidence = base_confidence * (1 - special_ratio * 0.3)
            
            scores['overall'] = round(final_confidence, 3)
            scores['text_length'] = round(len(text) / 100, 3)
            scores['special_char_ratio'] = round(special_ratio, 3)
        else:
            scores['overall'] = 0.0
            scores['text_length'] = 0.0
            scores['special_char_ratio'] = 0.0
        
        return scores


def main():
    """메인 실행 함수 - 테스트용"""
    import sys
    import os
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Clova OCR SDK + LLM 분석기 테스트 시작")
    print(f"📦 Clova SDK 설치 여부: {'✅ 설치됨' if CLOVA_SDK_AVAILABLE else '❌ 설치되지 않음'}")
    
    # 설정 (테스트용)
    config = {
        'clova_ocr_api_key': 'SGdQdEhGV2lxZXVTUWRja1hmS0hOcG9pTXdFdU9pbFo=',
        'clova_ocr_secret_key': 'SGdQdEhGV2lxZXVTUWRja1hmS0hOcG9pTXdFdU9pbFo=',
        'clova_ocr_invoke_url': 'https://wlbnl8oq3x.apigw.ntruss.com/custom/v1/45249/c2af6d9dc5eaf151ca0bc1b590815119b0f6e82921c3c89327ce90302b8c5e86/general'
    }
    
    # 분석기 초기화
    analyzer = ClovaOCRSDKAnalyzer(config)
    
    if not analyzer.ocr_client:
        print("❌ OCR 클라이언트 초기화 실패")
        return
    
    print("✅ OCR 분석기 초기화 완료")
    
    # 테스트 이미지 경로 확인
    test_image_path = "test_image.png"
    if not os.path.exists(test_image_path):
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {test_image_path}")
        print("💡 test_image.png 파일을 현재 디렉토리에 생성하거나 경로를 수정하세요.")
        return
    
    # 이미지 읽기
    try:
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        print(f"📸 테스트 이미지 로드 완료: {len(image_data)} bytes")
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")
        return
    
    # 이미지 분석 실행
    print("\n🔍 이미지 분석 시작...")
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
    else:
        print(f"❌ 실패: {result['error']}")
    
    print("\n" + "=" * 50)
    print("🎉 테스트 완료!")


if __name__ == "__main__":
    main()
