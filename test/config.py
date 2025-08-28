# API 테스트 설정 파일
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 서버 설정
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))

# 테스트 설정
TEST_DEBUG = os.getenv('TEST_DEBUG', 'false').lower() == 'true'
TEST_VERBOSE = os.getenv('TEST_VERBOSE', 'true').lower() == 'true'

# 테스트 이미지 경로
TEST_IMAGE_PATH = os.getenv('TEST_IMAGE_PATH', 'test_images/')

# 로깅 설정
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO') 