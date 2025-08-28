# API 테스트 유틸리티 함수들
import requests
import json
import logging
from typing import Dict, Any, Optional
from config import API_BASE_URL, API_TIMEOUT, TEST_VERBOSE

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APITester:
    """API 테스트를 위한 유틸리티 클래스"""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or API_BASE_URL
        self.timeout = timeout or API_TIMEOUT
        self.session = requests.Session()
        
    def _log_request(self, method: str, endpoint: str, data: Any = None):
        """요청 로깅"""
        if TEST_VERBOSE:
            logger.info(f"🌐 {method} {self.base_url}{endpoint}")
            if data:
                logger.info(f"📤 Request Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    def _log_response(self, response: requests.Response):
        """응답 로깅"""
        if TEST_VERBOSE:
            logger.info(f"📥 Response Status: {response.status_code}")
            try:
                response_data = response.json()
                logger.info(f"📥 Response Data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except:
                logger.info(f"📥 Response Text: {response.text[:200]}...")
    
    def get(self, endpoint: str, params: Dict = None) -> requests.Response:
        """GET 요청"""
        url = f"{self.base_url}{endpoint}"
        self._log_request("GET", endpoint, params)
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        self._log_response(response)
        return response
    
    def post(self, endpoint: str, data: Dict = None, json_data: Dict = None, files: Dict = None) -> requests.Response:
        """POST 요청"""
        url = f"{self.base_url}{endpoint}"
        self._log_request("POST", endpoint, data or json_data)
        
        response = self.session.post(
            url, 
            data=data, 
            json=json_data, 
            files=files,
            timeout=self.timeout
        )
        self._log_response(response)
        return response
    
    def health_check(self) -> bool:
        """API 서버 헬스 체크"""
        try:
            response = self.get("/api/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ 헬스 체크 실패: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """엔드포인트 테스트 실행"""
        try:
            if method.upper() == "GET":
                response = self.get(endpoint, **kwargs)
            elif method.upper() == "POST":
                response = self.post(endpoint, **kwargs)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response": response,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
        except Exception as e:
            logger.error(f"❌ {method} {endpoint} 테스트 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "response": None,
                "data": None
            }

def create_test_image(width: int = 100, height: int = 100, text: str = "Test") -> str:
    """테스트용 이미지 생성 (PIL 사용)"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 이미지 생성
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 텍스트 추가
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 10), text, fill='black', font=font)
        
        # 임시 파일로 저장
        import tempfile
        import os
        
        temp_dir = "test_images"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, f"test_image_{width}x{height}.png")
        image.save(temp_path)
        
        return temp_path
        
    except ImportError:
        logger.warning("PIL이 설치되지 않아 테스트 이미지를 생성할 수 없습니다.")
        return None
    except Exception as e:
        logger.error(f"테스트 이미지 생성 실패: {e}")
        return None

def print_test_result(test_name: str, result: Dict[str, Any]):
    """테스트 결과 출력"""
    status = "✅ PASS" if result.get("success") else "❌ FAIL"
    logger.info(f"{status} {test_name}")
    
    if not result.get("success"):
        if result.get("error"):
            logger.error(f"   오류: {result['error']}")
        if result.get("status_code"):
            logger.error(f"   상태 코드: {result['status_code']}")
        if result.get("data"):
            logger.error(f"   응답: {result['data']}") 