# ======================================================================================
# EC2 서버용 설정 관리 - config.py
# ======================================================================================

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일에서)
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

class EC2Config:
    """EC2 서버용 설정 관리 클래스"""
    
    # 기본 설정값
    DEFAULT_CONFIG = {
        'temperature': 0.1,
        'max_tokens': 1024,
        'top_k': 5,
        'similarity_threshold': 0.7,
        'personalization_weight': 0.3,
        'embedding_timeout': 15,
        'completion_timeout': 30,
        'max_retries': 3,
        'port': 5000,
        'debug': False
    }
    
    # API 엔드포인트
    API_ENDPOINTS = {
        'embedding': "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/clir-emb-dolphin",
        'completion': "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-007",
        'rag_reasoning': "https://clovastudio.stream.ntruss.com/v1/api-tools/rag-reasoning",
        'naver_search': "https://openapi.naver.com/v1/search/webkr.json",
        'clova_ocr': "https://wlbnl8oq3x.apigw.ntruss.com/custom/v1/45249/c2af6d9dc5eaf151ca0bc1b590815119b0f6e82921c3c89327ce90302b8c5e86/general",
        'clova_x': "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-007"
    }
    
    # 카테고리 매핑
    CATEGORIES = {
        '카페': ['카페', '커피', 'coffee', 'cafe', '커피숍', '스타벅스', '이디야', '투썸플레이스', '할리스', '컴포즈커피'],
        '마트': ['마트', 'mart', '슈퍼', '대형마트', '할인마트', '이마트', '홈플러스', '롯데마트', '코스트코'],
        '편의점': ['편의점', '편의', '컨비니', 'GS25', 'CU', '세븐일레븐', '이마트24', 'convenience'],
        '온라인쇼핑': ['온라인', '쇼핑', '인터넷', '쿠팡', '11번가', 'G마켓', '옥션', 'online', 'shopping'],
        '배달음식': ['배달', '음식', '치킨', '피자', '중국집', '배달의민족', '요기요', '쿠팡이츠', 'delivery'],
        '뷰티': ['뷰티', '화장품', '미용', '올리브영', '롭스', '부츠', 'beauty', 'cosmetic'],
        '패스트푸드': ['맥도날드', '버거킹', 'KFC', '롯데리아', '맘스터치', '서브웨이', 'fastfood'],
        '주유소': ['주유소', '기름', '휘발유', '경유', 'GS칼텍스', 'SK에너지', '현대오일뱅크', 'S-OIL']
    }
    
    @classmethod
    def get_env_config(cls) -> Dict[str, Any]:
        """환경 변수에서 설정 로드"""
        return {
            # 필수 설정
            'clova_api_key': os.environ.get('CLOVA_STUDIO_API_KEY'),
            'naver_client_id': os.environ.get('NAVER_CLIENT_ID'),
            'naver_client_secret': os.environ.get('NAVER_CLIENT_SECRET'),
            'clova_ocr_api_key': os.environ.get('CLOVA_OCR_API_KEY'),
            'clova_ocr_secret_key': os.environ.get('CLOVA_OCR_SECRET_KEY'),
            'clova_ocr': os.environ.get('CLOVA_OCR_INVOKE_URL', "https://naveropenapi.apigw.ntruss.com/ocr/v1/general"),
            'clova_x': os.environ.get('CLOVA_X_INVOKE_URL', "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-007"),
            
            # 데이터베이스 설정
            'db_path': os.environ.get('DB_PATH', './cafe_vector_db'),
            'collection_name': os.environ.get('COLLECTION_NAME', 'cafe_benefits'),
            
            # AI 모델 설정
            'temperature': float(os.environ.get('TEMPERATURE', cls.DEFAULT_CONFIG['temperature'])),
            'max_tokens': int(os.environ.get('MAX_TOKENS', cls.DEFAULT_CONFIG['max_tokens'])),
            'top_k': int(os.environ.get('TOP_K', cls.DEFAULT_CONFIG['top_k'])),
            
            # 검색 설정
            'similarity_threshold': float(os.environ.get('SIMILARITY_THRESHOLD', cls.DEFAULT_CONFIG['similarity_threshold'])),
            'personalization_weight': float(os.environ.get('PERSONALIZATION_WEIGHT', cls.DEFAULT_CONFIG['personalization_weight'])),
            
            # 타임아웃 설정 (EC2에서는 조금 더 여유롭게)
            'embedding_timeout': int(os.environ.get('EMBEDDING_TIMEOUT', cls.DEFAULT_CONFIG['embedding_timeout'])),
            'completion_timeout': int(os.environ.get('COMPLETION_TIMEOUT', cls.DEFAULT_CONFIG['completion_timeout'])),
            'max_retries': int(os.environ.get('MAX_RETRIES', cls.DEFAULT_CONFIG['max_retries'])),
            
            # 서버 설정
            'port': int(os.environ.get('PORT', cls.DEFAULT_CONFIG['port'])),
            'host': os.environ.get('HOST', '0.0.0.0'),
            'debug': os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
            
            # 로깅 설정
            'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
            'log_file': None,  # 로그 파일 사용하지 않음 - 콘솔만 사용
            
            # 환경 구분
            'environment': os.environ.get('ENVIRONMENT', 'development'),
            
            # 보안 설정
            'secret_key': os.environ.get('SECRET_KEY', 'dev-secret-key'),
            'allowed_origins': os.environ.get('ALLOWED_ORIGINS', '*'),
            
            # 성능 설정
            'workers': int(os.environ.get('WORKERS', 4)),
            'threads': int(os.environ.get('THREADS', 2)),
            'timeout': int(os.environ.get('TIMEOUT', 120))
        }
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> tuple[list, list]:
        """설정 유효성 검증"""
        required_fields = ['clova_api_key']
        missing_fields = []
        warnings = []
        
        # 필수 필드 확인
        for field in required_fields:
            if not config.get(field):
                missing_fields.append(field)
        
        # 선택적 필드 경고
        optional_fields = {
            'naver_client_id': '네이버 검색 기능 제한',
            'naver_client_secret': '네이버 검색 기능 제한'
        }
        
        for field, warning_msg in optional_fields.items():
            if not config.get(field):
                warnings.append(f"{field}: {warning_msg}")
        
        # 수치 값 검증
        if config.get('temperature', 0) < 0 or config.get('temperature', 0) > 1:
            warnings.append("temperature는 0과 1 사이의 값이어야 합니다")
        
        if config.get('port', 0) <= 0 or config.get('port', 0) > 65535:
            warnings.append("port는 1-65535 사이의 값이어야 합니다")
        
        if config.get('top_k', 0) <= 0:
            warnings.append("top_k는 양수여야 합니다")
        
        # 환경별 추가 검증
        if config.get('environment') == 'production':
            if config.get('debug'):
                warnings.append("프로덕션 환경에서는 debug 모드를 비활성화하는 것이 좋습니다")
            if config.get('secret_key') == 'dev-secret-key':
                warnings.append("프로덕션 환경에서는 보안을 위해 SECRET_KEY를 변경해주세요")
        
        return missing_fields, warnings
    
    @classmethod
    def get_api_headers(cls, config: Dict[str, Any], endpoint_type: str = 'completion') -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        base_headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f"Bearer {config['clova_api_key']}",
            'X-NCP-CLOVASTUDIO-REQUEST-ID': f"ec2-{endpoint_type}"
        }
        
        if endpoint_type == 'naver_search':
            return {
                'X-Naver-Client-Id': config.get('naver_client_id', ''),
                'X-Naver-Client-Secret': config.get('naver_client_secret', ''),
                'User-Agent': 'EC2-PersonalizedRAG/1.0'
            }
        
        return base_headers
    
    @classmethod
    def get_category_keywords(cls, category: str) -> list:
        """카테고리별 키워드 반환"""
        return cls.CATEGORIES.get(category, [category])
    
    @classmethod
    def detect_category_from_text(cls, text: str) -> Optional[str]:
        """텍스트에서 카테고리 감지"""
        text_lower = text.lower()
        
        for category, keywords in cls.CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return None
    
    @classmethod
    def setup_logging(cls, config: Dict[str, Any]):
        """로깅 설정"""
        log_level = getattr(logging, config.get('log_level', 'INFO').upper())
        
        # 로그 포맷
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 콘솔 로깅만 사용 (로그 파일 사용하지 않음)
        logging.basicConfig(
            level=log_level,
            format=log_format,
            force=True
        )
        
        if config.get('debug'):
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("🐛 디버그 모드 활성화")
        
        logger.info(f"📝 로깅 레벨: {config.get('log_level', 'INFO')}")
        logger.info("📄 로그 파일: 콘솔만 사용 (파일 로깅 비활성화)")
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """시스템 프롬프트 반환"""
        return """당신은 개인화된 혜택 추천 전문가입니다. 
사용자의 소비 패턴과 선호도를 분석하여 가장 적합한 혜택을 추천해주세요.

추천 시 다음 사항을 고려하세요:
1. 사용자의 과거 소비 이력
2. 선호하는 브랜드와 카테고리
3. 혜택의 실제 절약 효과
4. 혜택 조건의 달성 가능성
5. 유효 기간과 긴급성

답변은 친근하고 이해하기 쉽게 작성해주세요."""

# ======================================================================================
# EC2 전용 유틸리티 함수
# ======================================================================================

def get_ec2_config() -> Dict[str, Any]:
    """EC2용 통합 설정 로드"""
    config = EC2Config.get_env_config()
    
    # 설정 유효성 검증
    missing, warnings = EC2Config.validate_config(config)
    
    if missing:
        raise ValueError(f"필수 환경 변수가 설정되지 않음: {', '.join(missing)}")
    
    if warnings:
        for warning in warnings:
            logger.warning(f"⚠️ {warning}")
    
    # 로깅 설정
    EC2Config.setup_logging(config)
    
    logger.info("✅ EC2 설정 로드 완료")
    logger.info(f"🌍 환경: {config['environment']}")
    logger.info(f"🔧 디버그 모드: {config['debug']}")
    logger.info(f"🔌 포트: {config['port']}")
    
    return config

def get_api_endpoint(endpoint_name: str) -> str:
    """API 엔드포인트 URL 반환"""
    return EC2Config.API_ENDPOINTS.get(endpoint_name)

def create_request_payload(config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """API 요청 페이로드 생성"""
    payload = {
        'temperature': config['temperature'],
        'maxTokens': config['max_tokens']
    }
    payload.update(kwargs)
    return payload

def check_system_resources():
    """시스템 리소스 확인 (EC2 전용)"""
    try:
        import psutil
        
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk_percent,
            'disk_free_gb': disk.free / (1024**3),
            'status': 'healthy' if all([
                cpu_percent < 80,
                memory_percent < 85,
                disk_percent < 90
            ]) else 'warning'
        }
    except ImportError:
        logger.warning("psutil이 설치되지 않음. 시스템 리소스 모니터링 불가")
        return {"status": "unknown", "message": "psutil 필요"}
    except Exception as e:
        logger.error(f"시스템 리소스 확인 오류: {e}")
        return {"status": "error", "error": str(e)}

def get_network_info():
    """네트워크 정보 확인"""
    try:
        import socket
        
        # 호스트명
        hostname = socket.gethostname()
        
        # 로컬 IP
        try:
            # 외부 연결을 통해 로컬 IP 확인
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "localhost"
        
        return {
            'hostname': hostname,
            'local_ip': local_ip,
            'status': 'connected'
        }
    except Exception as e:
        logger.error(f"네트워크 정보 확인 오류: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
