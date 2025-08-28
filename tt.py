import json
import logging
import datetime
import requests
from flask import jsonify, request
import re
from typing import Dict, Any, List, Optional

class EC2ScoreCalculator:
    """EC2 서버용 개인화 점수 계산기"""
    
    @staticmethod
    def calculate_preference_score(brand: str, category: str, user_history: Dict) -> float:
        """개인 선호도 점수 계산 (0-1)"""
        try:
            brand_count = user_history.get('brand_counts', {}).get(brand, 0)
            category_count = user_history.get('category_counts', {}).get(category, 0) 
            total_transactions = user_history.get('total_transactions', 1)
            
            if total_transactions == 0:
                return 0.0
            
            # 브랜드 선호도 (가중치 70%)
            brand_preference = brand_count / total_transactions
            
            # 카테고리 선호도 (가중치 30%)
            category_preference = category_count / total_transactions
            
            return (brand_preference * 0.7) + (category_preference * 0.3)
            
        except Exception as e:
            logger.error(f"선호도 점수 계산 오류: {e}")
            return 0.0
    
    @staticmethod
    def calculate_potential_savings(benefit_type: str, discount_rate: float, 
                                  user_avg_spending: float) -> float:
        """예상 절감액 계산 (원 단위)"""
        try:
            discount_rate = float(discount_rate) if discount_rate != 'N/A' else 0
            user_avg_spending = float(user_avg_spending) if user_avg_spending else 0
            
            if benefit_type == "할인":
                return user_avg_spending * (discount_rate / 100)
            elif benefit_type == "적립":
                return user_avg_spending * (discount_rate / 100) * 0.5
            elif benefit_type == "증정":
                return user_avg_spending * 0.2
            else:
                return user_avg_spending * 0.1
                
        except Exception as e:
            logger.error(f"절감액 계산 오류: {e}")
            return 0.0
    
    @staticmethod
    def calculate_recency_weight(spending_date: str, current_date: datetime = None) -> float:
        """최근성 가중치 계산 (0-1)"""
        try:
            if current_date is None:
                current_date = datetime.now()
            
            # 문자열 날짜를 datetime으로 변환
            if isinstance(spending_date, str):
                try:
                    spending_dt = datetime.fromisoformat(spending_date.replace('Z', '+00:00'))
                except:
                    spending_dt = datetime.strptime(spending_date, '%Y-%m-%d')
            else:
                spending_dt = spending_date
            
            days_diff = (current_date - spending_dt).days
            
            if days_diff <= 7:
                return 1.0
            elif days_diff <= 30:
                return 0.8
            elif days_diff <= 90:
                return 0.5
            else:
                return 0.2
                
        except Exception as e:
            
            return 0.2


class EC2PersonalizedRAG:
    """EC2 서버에 최적화된 개인화 RAG 시스템"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config['db_path']
        self.collection_name = config['collection_name']
        self.client = None
        self.collection = None
        self.score_calculator = EC2ScoreCalculator()
        
        # 캐시된 메타데이터
        self.available_brands: Set[str] = set()
        self.available_categories: Set[str] = set()
        self.db_metadata_loaded = False
        
        logger.info("🚀 EC2PersonalizedRAG 초기화 완료")
    
    def connect_database(self) -> bool:
        """벡터 데이터베이스 연결"""
        try:
            # 데이터베이스 경로 확인 및 생성
            if not os.path.exists(self.db_path):
                logger.warning(f"데이터베이스 경로가 존재하지 않습니다: {self.db_path}")
                # 디렉토리 생성 시도
                try:
                    os.makedirs(self.db_path, exist_ok=True)
                    logger.info(f"데이터베이스 디렉토리 생성: {self.db_path}")
                except Exception as e:
                    logger.error(f"데이터베이스 디렉토리 생성 실패: {e}")
                    return False
            
            # ChromaDB 연결
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            try:
                # 기존 컬렉션 로드 시도
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"✅ 기존 컬렉션 로드 성공: {self.collection_name}")
            except Exception:
                # 컬렉션이 없으면 생성
                logger.warning(f"기존 컬렉션이 없습니다. 새 컬렉션 생성: {self.collection_name}")
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "ip"}
                )
                logger.info(f"✅ 새 컬렉션 생성 완료: {self.collection_name}")
            
            # 메타데이터 로드
            self._load_database_metadata()
            
            logger.info(f"✅ 데이터베이스 연결 성공: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            return False
    
    def _load_database_metadata(self):
        """데이터베이스 메타데이터 로드"""
        try:
            if not self.collection:
                return
            
            # 컬렉션이 비어있는지 확인
            count = self.collection.count()
            if count == 0:
                logger.warning("데이터베이스가 비어있습니다. 데이터를 추가해주세요.")
                return
            
            # 샘플 메타데이터 가져오기
            sample_results = self.collection.get(
                limit=min(1000, count),  # 최대 1000개 또는 전체 개수
                include=['metadatas']
            )
            
            if sample_results and sample_results.get('metadatas'):
                for metadata in sample_results['metadatas']:
                    if metadata.get('brand'):
                        self.available_brands.add(metadata['brand'])
                    if metadata.get('category'):
                        self.available_categories.add(metadata['category'])
            
            self.db_metadata_loaded = True
            logger.info(f"📊 메타데이터 로드 완료: 브랜드 {len(self.available_brands)}개, 카테고리 {len(self.available_categories)}개, 총 문서 {count}개")
            
        except Exception as e:
            logger.error(f"메타데이터 로드 오류: {e}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """텍스트 임베딩 생성"""
        try:
            headers = EC2Config.get_api_headers(self.config, 'embedding')
            url = EC2Config.API_ENDPOINTS['embedding']
            
            # 요청 데이터 준비
            payload = {"text": text}
            
            # API 호출
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config['embedding_timeout']
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status', {}).get('code') == '20000':
                    embedding = result.get('result', {}).get('embedding')
                    if embedding:
                        logger.debug(f"임베딩 생성 성공: 텍스트 길이 {len(text)}, 벡터 차원 {len(embedding)}")
                        return embedding
            
            logger.error(f"임베딩 생성 실패: HTTP {response.status_code}")
            return None
            
        except requests.exceptions.Timeout:
            logger.error(f"임베딩 API 타임아웃 ({self.config['embedding_timeout']}초)")
            return None
        except Exception as e:
            logger.error(f"임베딩 API 오류: {e}")
            return None
    
    def search_benefits(self, query: str, user_history: Optional[Dict] = None, 
                       top_k: int = None, debug: bool = False) -> Dict[str, Any]:
        """혜택 검색 및 개인화 추천"""
        try:
            if top_k is None:
                top_k = self.config['top_k']
            
            logger.info(f"🔍 혜택 검색 시작: '{query}' (top_k={top_k})")
            
            # 1. 카테고리 추출 시도
            categories = self._extract_categories_from_query(query, debug)
            
            # 2. 브랜드 추출 시도
            brands = self._extract_brands_from_query(query, debug)
            
            # 3. 검색 전략 결정 및 실행
            results = []
            
            # 카테고리 기반 직접 검색
            if categories:
                direct_results = self._direct_category_search(categories, top_k, debug)
                results.extend(direct_results)
            
            # 브랜드 기반 직접 검색
            if brands:
                brand_results = self._direct_brand_search(brands, top_k, debug)
                results.extend(brand_results)
            
            # 벡터 검색 (임베딩 기반)
            if len(results) < top_k:
                vector_results = self._vector_search(query, top_k - len(results), debug)
                results.extend(vector_results)
            
            # 4. 개인화 점수 적용
            if user_history:
                results = self._apply_personalization(results, user_history, debug)
            
            # 5. 결과 정리 및 반환
            final_results = self._finalize_results(results, top_k)
            
            # 6. 웹 검색 보완 (결과가 3개 미만인 경우)
            if len(final_results) < 3:
                logger.info(f"🌐 검색 결과 부족 ({len(final_results)}개) - 웹 검색으로 보완")
                web_results = self._supplement_with_web_search(query, categories, brands, 5 - len(final_results))
                final_results.extend(web_results)
                logger.info(f"🔄 웹 검색 보완 후: {len(final_results)}개 결과")
            
            logger.info(f"✅ 검색 완료: {len(final_results)}개 결과 반환")
            
            return {
                "success": True,
                "query": query,
                "extracted_categories": categories,
                "extracted_brands": brands,
                "results": final_results,
                "total_found": len(final_results),
                "search_strategy": self._get_search_strategy_info(categories, brands),
                "web_search_used": len(final_results) > len(self._finalize_results(results, top_k)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"검색 오류: {e}")
            return self._generate_error_response(str(e), query)
    
    def _extract_categories_from_query(self, query: str, debug: bool = False) -> List[str]:
        """쿼리에서 카테고리 추출"""
        found_categories = []
        query_lower = query.lower()
        
        for category, keywords in EC2Config.CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    found_categories.append(category)
                    if debug:
                        logger.debug(f"카테고리 발견: {category} (키워드: {keyword})")
                    break
        
        return list(set(found_categories))
    
    def _extract_brands_from_query(self, query: str, debug: bool = False) -> List[str]:
        """쿼리에서 브랜드 추출"""
        found_brands = []
        query_lower = query.lower()
        
        # 데이터베이스에서 로드된 브랜드들 확인
        for brand in self.available_brands:
            if brand.lower() in query_lower:
                found_brands.append(brand)
                if debug:
                    logger.debug(f"브랜드 발견: {brand}")
        
        return list(set(found_brands))
    
    def _direct_category_search(self, categories: List[str], top_k: int, debug: bool = False) -> List[Dict]:
        """카테고리 기반 직접 검색"""
        results = []
        
        try:
            for category in categories:
                category_results = self.collection.get(
                    where={"category": {"$eq": category}},
                    limit=top_k,
                    include=["metadatas", "documents"]
                )
                
                if category_results and category_results.get('metadatas'):
                    for i, metadata in enumerate(category_results['metadatas']):
                        if self._validate_result(metadata):
                            results.append({
                                "id": f"cat_{category}_{i}",
                                "metadata": metadata,
                                "document": category_results['documents'][i] if category_results.get('documents') else "",
                                "distance": 0.0,  # 직접 매칭
                                "similarity_score": 1.0,
                                "search_type": "category_direct"
                            })
                
                if debug:
                    count = len(category_results['metadatas']) if category_results and category_results.get('metadatas') else 0
                    logger.debug(f"카테고리 '{category}': {count}개 결과")
        
        except Exception as e:
            logger.error(f"카테고리 검색 오류: {e}")
        
        return results
    
    def _direct_brand_search(self, brands: List[str], top_k: int, debug: bool = False) -> List[Dict]:
        """브랜드 기반 직접 검색"""
        results = []
        
        try:
            for brand in brands:
                brand_results = self.collection.get(
                    where={"brand": {"$eq": brand}},
                    limit=top_k,
                    include=["metadatas", "documents"]
                )
                
                if brand_results and brand_results.get('metadatas'):
                    for i, metadata in enumerate(brand_results['metadatas']):
                        if self._validate_result(metadata):
                            results.append({
                                "id": f"brand_{brand}_{i}",
                                "metadata": metadata,
                                "document": brand_results['documents'][i] if brand_results.get('documents') else "",
                                "distance": 0.0,
                                "similarity_score": 1.0,
                                "search_type": "brand_direct"
                            })
                
                if debug:
                    count = len(brand_results['metadatas']) if brand_results and brand_results.get('metadatas') else 0
                    
        
        except Exception as e:
            return
        
        return results  
    
    def _vector_search(self, query: str, top_k: int, debug: bool = False) -> List[Dict]:
        """벡터 기반 검색"""
        try:
            embedding = self.generate_embedding(query)
            if not embedding:
                if debug:
                    logger.debug("임베딩 생성 실패, 벡터 검색 생략")
                return []
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            vector_results = []
            if results.get('documents') and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    if self._validate_result(metadata):
                        similarity = self._calculate_similarity_score(distance)
                        vector_results.append({
                            "id": f"vector_{i}",
                            "metadata": metadata,
                            "document": doc,
                            "distance": distance,
                            "similarity_score": similarity,
                            "search_type": "vector"
                        })
            
            
            
            return vector_results
            
        except Exception as e:
            
            return []
    
    def _calculate_similarity_score(self, distance: float) -> float:
        """거리값을 유사도 점수로 변환"""
        try:
            # 거리값이 음수인 경우 (Inner Product)
            if distance < 0:
                # -1000 ~ 0 범위를 0 ~ 1로 정규화
                return max(0, min(1, (distance + 1000) / 1000))
            else:
                # 일반적인 거리값 (L2, Cosine)
                return max(0, min(1, 1 - distance))
        except:
            return 0.5
    
    def _apply_personalization(self, results: List[Dict], user_history: Dict, debug: bool = False) -> List[Dict]:
        """개인화 점수 적용"""
        try:
            for result in results:
                metadata = result.get('metadata', {})
                
                # 기본 점수들 계산
                preference_score = self.score_calculator.calculate_preference_score(
                    metadata.get('brand', ''),
                    metadata.get('category', ''),
                    user_history
                )
                
                # 예상 절감액 계산
                user_avg_spending = user_history.get('average_spending', {}).get(
                    metadata.get('category', ''), 50000
                )
                potential_savings = self.score_calculator.calculate_potential_savings(
                    metadata.get('benefit_type', ''),
                    metadata.get('discount_rate', 0),
                    user_avg_spending
                )
                
                # 최종 개인화 점수 계산
                base_score = result.get('similarity_score', 0.5)
                personalization_weight = self.config['personalization_weight']
                
                final_score = (base_score * (1 - personalization_weight)) + (preference_score * personalization_weight)
                
                # 결과에 점수들 추가
                result.update({
                    'preference_score': preference_score,
                    'potential_savings': potential_savings,
                    'personalized_score': final_score,
                    'base_similarity': base_score
                })
                
                if debug:
                    logger.debug(f"개인화 점수 - {metadata.get('brand', 'N/A')}: {final_score:.3f}")
            
            # 개인화 점수로 정렬
            results.sort(key=lambda x: x.get('personalized_score', 0), reverse=True)
            
        except Exception as e:
            
        
            return results
    
    def _validate_result(self, metadata: Dict) -> bool:
        """결과 유효성 검증"""
        try:
            # 활성 상태 확인
            if not metadata.get('is_active', True):
                return False
            
            # 유효 기간 확인
            valid_to = metadata.get('valid_to')
            if valid_to and valid_to != 'N/A':
                try:
                    end_date = datetime.fromisoformat(valid_to.replace('Z', '+00:00'))
                    if end_date < datetime.now():
                        return False
                except:
                    pass
            
            return True
            
        except Exception as e:
            
            return True  # 오류 시 기본적으로 유효하다고 가정
    
    def _finalize_results(self, results: List[Dict], top_k: int) -> List[Dict]:
        """최종 결과 정리"""
        try:
            # 중복 제거 (브랜드 + 제목 기준)
            seen = set()
            unique_results = []
            
            for result in results:
                metadata = result.get('metadata', {})
                key = (metadata.get('brand', ''), metadata.get('title', ''))
                
                if key not in seen:
                    seen.add(key)
                    
                    # 최종 결과 포맷팅
                    formatted_result = {
                        "rank": len(unique_results) + 1,
                        "title": metadata.get('title', 'N/A'),
                        "brand": metadata.get('brand', 'N/A'),
                        "category": metadata.get('category', 'N/A'),
                        "benefit_type": metadata.get('benefit_type', 'N/A'),
                        "discount_rate": metadata.get('discount_rate', 'N/A'),
                        "conditions": metadata.get('conditions', 'N/A'),
                        "valid_from": metadata.get('valid_from', 'N/A'),
                        "valid_to": metadata.get('valid_to', 'N/A'),
                        "is_active": metadata.get('is_active', True),
                        "content": result.get('document', ''),
                        "similarity_score": result.get('similarity_score', 0),
                        "personalized_score": result.get('personalized_score', result.get('similarity_score', 0)),
                        "search_type": result.get('search_type', 'unknown'),
                        "potential_savings": result.get('potential_savings', 0)
                    }
                    
                    unique_results.append(formatted_result)
                    
                    if len(unique_results) >= top_k:
                        break
            
            return unique_results
            
        except Exception as e:
            
            return results[:top_k]
    
    def _get_search_strategy_info(self, categories: List[str], brands: List[str]) -> Dict[str, Any]:
        """검색 전략 정보 반환"""
        return {
            "used_categories": categories,
            "used_brands": brands,
            "strategy": "hybrid" if (categories or brands) else "vector_only"
        }
    
    def _generate_error_response(self, error_msg: str, query: str = "") -> Dict[str, Any]:
        """오류 응답 생성"""
        return {
            "success": False,
            "query": query,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }


def initialize_rag_system():
    """RAG 시스템 초기화"""
    global rag_system, config, database_connected
    
    if rag_system is None:
        try:
            # 설정 로드
            config = get_ec2_config()
            
            # RAG 시스템 초기화
            rag_system = EC2PersonalizedRAG(config)
            
            # 데이터베이스 연결
            database_connected = rag_system.connect_database()
            
            if database_connected:
                logger.info("🎯 RAG 시스템 초기화 및 DB 연결 완료")
            else:
                logger.warning("⚠️ RAG 시스템 초기화 완료, DB 연결 실패 (제한된 기능)")
                
        except Exception as e:

            # EC2에서는 예외를 발생시키지 않고 제한된 기능으로 동작
            rag_system = None
    
    return rag_system
def create_sample_user_history() -> List[Dict]:
    """샘플 사용자 소비 이력 생성"""
    return [
        # 최근 1주일 소비 (높은 가중치)
        {"brand": "스타벅스", "category": "카페", "amount": 50000, "date": datetime.now() - timedelta(days=3)},
        {"brand": "이마트", "category": "마트", "amount": 150000, "date": datetime.now() - timedelta(days=5)},
        {"brand": "쿠팡", "category": "온라인쇼핑", "amount": 80000, "date": datetime.now() - timedelta(days=6)},
        
        # 지난 한달 소비
        {"brand": "스타벅스", "category": "카페", "amount": 35000, "date": datetime.now() - timedelta(days=15)},
        {"brand": "스타벅스", "category": "카페", "amount": 42000, "date": datetime.now() - timedelta(days=20)},
        {"brand": "GS25", "category": "편의점", "amount": 25000, "date": datetime.now() - timedelta(days=18)},
        {"brand": "올리브영", "category": "뷰티", "amount": 120000, "date": datetime.now() - timedelta(days=25)},
        {"brand": "맥도날드", "category": "식당", "amount": 15000, "date": datetime.now() - timedelta(days=28)},
        
        # 지난 3개월 소비 (낮은 가중치)
        {"brand": "이마트", "category": "마트", "amount": 200000, "date": datetime.now() - timedelta(days=40)},
        {"brand": "스타벅스", "category": "카페", "amount": 60000, "date": datetime.now() - timedelta(days=45)},
        {"brand": "홈플러스", "category": "마트", "amount": 180000, "date": datetime.now() - timedelta(days=50)},
        {"brand": "쿠팡", "category": "온라인쇼핑", "amount": 95000, "date": datetime.now() - timedelta(days=55)},
        {"brand": "CU", "category": "편의점", "amount": 30000, "date": datetime.now() - timedelta(days=60)},
        {"brand": "지마켓", "category": "온라인쇼핑", "amount": 75000, "date": datetime.now() - timedelta(days=65)},
        {"brand": "스타벅스", "category": "카페", "amount": 38000, "date": datetime.now() - timedelta(days=70)},
        {"brand": "이디야", "category": "카페", "amount": 28000, "date": datetime.now() - timedelta(days=75)},
        {"brand": "KFC", "category": "식당", "amount": 22000, "date": datetime.now() - timedelta(days=80)},
        {"brand": "온누리약국", "category": "의료", "amount": 45000, "date": datetime.now() - timedelta(days=85)},
    ]


class PersonalizedScoreCalculator:
    """개인화 스코어 계산기"""
    
    @staticmethod
    def calculate_preference_score(brand: str, category: str, user_history: Dict) -> float:
        """개인 선호도 점수 계산 (0-1)"""
        brand_count = user_history.get('brand_counts', {}).get(brand, 0)
        category_count = user_history.get('category_counts', {}).get(category, 0) 
        total_transactions = user_history.get('total_transactions', 1)
        
        # 브랜드 선호도 (가중치 70%)
        brand_preference = brand_count / total_transactions if total_transactions > 0 else 0
        
        # 카테고리 선호도 (가중치 30%)
        category_preference = category_count / total_transactions if total_transactions > 0 else 0
        
        return (brand_preference * 0.7) + (category_preference * 0.3)
    
    @staticmethod
    def calculate_potential_savings(benefit_type: str, discount_rate: float, 
                                  user_avg_spending: float) -> float:
        """예상 절감액 계산 (원 단위)"""
        if benefit_type == "할인":
            return user_avg_spending * (discount_rate / 100)
        elif benefit_type == "적립":
            return user_avg_spending * (discount_rate / 100) * 0.5  # 적립은 할인의 50% 가치
        elif benefit_type == "증정":
            return user_avg_spending * 0.2  # 증정품 가치를 평균 소비의 20%로 가정
        else:
            return user_avg_spending * 0.1  # 기타 혜택
    
    @staticmethod
    def calculate_recency_weight(spending_date: datetime, current_date: datetime) -> float:
        """최근성 가중치 계산 (0-1)"""
        days_diff = (current_date - spending_date).days
        if days_diff <= 7:
            return 1.0
        elif days_diff <= 30:
            return 0.8
        elif days_diff <= 90:
            return 0.5
        else:
            return 0.2


class EmbeddingExecutor:
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key
        self._request_id = request_id

    def execute(self, request_data):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': self._api_key,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id
        }

        response = requests.post(
            f"https://{self._host}/v1/api-tools/embedding/clir-emb-dolphin",
            headers=headers,
            json=request_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['status']['code'] == '20000':
                return result['result']['embedding']
        
        raise Exception(f"임베딩 API 오류: {response.status_code}")

     
class CompletionExecutor:
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key
        self._request_id = request_id

    def execute(self, completion_request):
        headers = {
            'Authorization': self._api_key,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/event-stream'
        }

        final_answer = ""
        
        with requests.post(
            self._host + '/v3/chat-completions/HCX-005',
            headers=headers,
            json=completion_request,
            stream=True
        ) as r:
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    
                    if decoded_line.startswith("data:"):
                        if decoded_line.endswith("[DONE]"):
                            break
                            
                        try:
                            json_str = decoded_line[5:]
                            event_data = json.loads(json_str)
                            
                            if (event_data.get('finishReason') == 'stop' and 
                                'message' in event_data and 
                                'content' in event_data['message']):
                                final_answer = event_data['message']['content']
                                break
                                
                        except json.JSONDecodeError:
                            continue
        
        return final_answer

class PerplexityAPI:
    def __init__(self, api_key=None):
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.api_key = api_key or self.get_api_key()
        
    def get_api_key(self):
        """API 키 입력받기"""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not api_key:
            print("💡 Perplexity API 키가 필요합니다!")
            print("1. https://www.perplexity.ai/settings/api 에서 API 키 생성")
            print("2. Pro 구독자는 매월 $5 크레딧 무료 제공")
            api_key = input("\n🔑 Perplexity API 키: ").strip()
        
        return api_key
    
    def search(self, query, model="sonar", max_tokens=2000):
        """실시간 검색 수행"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 사용 가능한 모델들
        models = {
            "sonar": "sonar",
            "sonar-pro": "sonar-pro",
            "online": "llama-3.1-sonar-large-128k-online",
            "chat": "llama-3.1-sonar-large-128k-chat"
        }
        
        data = {
            "model": models.get(model, "sonar"),
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 실시간 정보를 검색하는 AI입니다. 최신 정보를 정확하고 상세하게 제공하고, 가능한 경우 출처를 포함해주세요."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "return_citations": True
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'content': content,
                    'usage': result.get('usage', {}),
                    'model': models.get(model, "sonar")
                }
            else:
                return {
                    'success': False,
                    'error': f"API 오류 {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"요청 오류: {str(e)}"
            }


class PerplexityAPI:
    """Perplexity API 클래스 (두번째 코드에서 가져옴)"""
    def __init__(self, api_key=None):
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.api_key = api_key or self.get_api_key()
        
    def get_api_key(self):
        """API 키 입력받기"""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not api_key:
            print("💡 Perplexity API 키가 필요합니다!")
            print("1. https://www.perplexity.ai/settings/api 에서 API 키 생성")
            print("2. Pro 구독자는 매월 $5 크레딧 무료 제공")
            api_key = input("\n🔑 Perplexity API 키: ").strip()
        
        return api_key
    
    def search(self, query, model="sonar", max_tokens=2000):
        """실시간 검색 수행"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 사용 가능한 모델들
        models = {
            "sonar": "sonar",
            "sonar-pro": "sonar-pro",
            "online": "llama-3.1-sonar-large-128k-online",
            "chat": "llama-3.1-sonar-large-128k-chat"
        }
        
        data = {
            "model": models.get(model, "sonar"),
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 실시간 정보를 검색하는 AI입니다. 최신 정보를 정확하고 상세하게 제공하고, 가능한 경우 출처를 포함해주세요."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "return_citations": True
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'content': content,
                    'usage': result.get('usage', {}),
                    'model': models.get(model, "sonar")
                }
            else:
                return {
                    'success': False,
                    'error': f"API 오류 {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"요청 오류: {str(e)}"
            }



class PersonalizedBenefitRAG:
    """개인화된 혜택 추천 RAG 시스템 (브랜드 인식 및 개인화 요청 처리 개선)"""
    
    def __init__(self, db_path="/opt/benefits-api/data/cafe_vector_db", collection_name="cafe_benefits"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.score_calculator = PersonalizedScoreCalculator()
        self.vector_space_type = "unknown"  # DB에서 자동 감지
        
        # 🔍 DB 브랜드/카테고리 캐시
        self.available_brands: Set[str] = set()
        self.available_categories: Set[str] = set()
        self.db_metadata_loaded = False
        
        # 🔗 Perplexity API 추가
        self.perplexity_api = None
        self._init_perplexity_api()
        
        # API 실행자 초기화
        api_key = 'Bearer nv-53f7a8c4abe74e20ab90446ed46ba79fvozJ'
        
        self.embedding_executor = EmbeddingExecutor(
            host='clovastudio.stream.ntruss.com',
            api_key=api_key,
            request_id='93ae6593a47d4437b634f2cbc5282896'
        )
        
        self.completion_executor = CompletionExecutor(
            host="https://clovastudio.stream.ntruss.com",
            api_key=api_key,
            request_id='a8a2aebe279a445f8425e0e2aa8c118d'
        )

    def _init_perplexity_api(self):
        """🔗 Perplexity API 초기화"""
        try:
            # 환경 변수에서 API 키 확인
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if api_key:
                self.perplexity_api = PerplexityAPI(api_key)
                print("🔗 Perplexity API 연결 성공")
            else:
                print("💡 Perplexity API 키가 없습니다. 환경 변수 PERPLEXITY_API_KEY 설정하거나 나중에 입력하세요.")
        except Exception as e:
            print(f"⚠️ Perplexity API 초기화 실패: {e}")
            self.perplexity_api = None

    def _search_with_perplexity(self, query: str, brand: str = None) -> str:
        """🔗 Perplexity API로 실시간 검색"""
        try:
            # API가 없으면 초기화 시도
            if not self.perplexity_api:
                try:
                    self.perplexity_api = PerplexityAPI()
                except:
                    return "❌ Perplexity API를 사용할 수 없습니다. 올바른 API 키를 설정해주세요."
            
            # 검색 쿼리 구성
            if brand:
                search_query = f"2025년 8월 현재 {brand} 할인 혜택 이벤트 프로모션 쿠폰"
            else:
                search_query = f"2025년 8월 현재 {query} 할인 혜택 이벤트 프로모션"
            
            print(f"🔍 Perplexity 검색 중: {search_query}")
            
            # 실시간 검색 수행
            result = self.perplexity_api.search(search_query, model="sonar")  # sonar-pro 대신 sonar 사용
            
            if result['success']:
                content = result['content']
                
                # 결과 포맷팅
                response = f"🌐 실시간 검색 결과 (Perplexity):\n\n"
                response += content
                
                return response
            else:
                return f"❌ 실시간 검색 실패: {result['error']}"
                
        except Exception as e:
            return f"❌ 실시간 검색 오류: {e}"

    def _extract_categories_from_query(self, query: str, debug: bool = False) -> List[str]:
        """🔧 쿼리에서 카테고리 추출"""
        
        if debug:
            print(f"🔍 카테고리 추출 시작: '{query}'")
        
        found_categories = []
        
        # 확실한 카테고리 패턴 매칭
        known_category_patterns = {
            '카페': [r'카페', r'커피', r'coffee', r'cafe', r'커피숍', r'커피점', r'아메리카노', r'라떼'],
            '마트': [r'마트', r'mart', r'슈퍼', r'대형마트', r'할인마트', r'쇼핑몰', r'생필품'],
            '편의점': [r'편의점', r'편의', r'컨비니', r'convenience'],
            '온라인쇼핑': [r'온라인', r'쇼핑', r'인터넷', r'online', r'shopping', r'이커머스', r'배송'],
            '식당': [r'식당', r'음식점', r'레스토랑', r'restaurant', r'음식', r'먹거리', r'dining', r'치킨', r'버거', r'햄버거'],
            '뷰티': [r'뷰티', r'화장품', r'미용', r'beauty', r'cosmetic', r'스킨케어', r'메이크업'],
            '의료': [r'의료', r'약국', r'병원', r'pharmacy', r'medical', r'health', r'건강', r'영양제', r'비타민'],
            '교통': [r'교통', r'지하철', r'버스', r'택시', r'전철', r'대중교통', r'metro', r'정기권']
        }
        
        query_lower = query.lower()
        
        # 확실한 카테고리 패턴 매칭
        for category_name, patterns in known_category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    found_categories.append(category_name)
                    if debug:
                        print(f"   ✅ 카테고리 발견: '{category_name}' (패턴: {pattern})")
                    break
        
        # 중복 제거
        unique_categories = list(set(found_categories))
        
        if debug:
            print(f"   🎯 최종 추출된 카테고리: {unique_categories}")
        
        return unique_categories

    def _try_direct_category_search(self, query: str, categories: List[str], top_k: int, debug: bool = False) -> List[Dict]:
        """🎯 카테고리 기반 직접 검색 (간단 버전)"""
        try:
            if debug:
                print(f"🎯 직접 카테고리 검색 시도: {categories}")
            
            all_results = []
            
            for category in categories:
                try:
                    category_results = self.collection.get(
                        where={"category": {"$eq": category}},
                        include=["metadatas", "documents"]
                    )
                    
                    if category_results and category_results.get('metadatas'):
                        for i, metadata in enumerate(category_results['metadatas']):
                            # 유효성 검증
                            if self._validate_result(metadata, datetime.now()):
                                all_results.append({
                                    "id": f"direct_cat_{category}_{i}",
                                    "metadata": metadata,
                                    "distance": 0.0,  # 직접 카테고리 매칭이므로 최고 점수
                                    "document": category_results['documents'][i] if category_results.get('documents') else "",
                                    "vector_rank": i + 1
                                })
                    
                    if debug:
                        count = len(category_results['metadatas']) if category_results and category_results.get('metadatas') else 0
                        print(f"   '{category}': {count}개 결과")
                        
                except Exception as e:
                    if debug:
                        print(f"   '{category}' 검색 실패: {e}")
                    continue
            
            # 결과 제한
            if all_results:
                limited_results = all_results[:top_k]
                if debug:
                    print(f"🎯 직접 카테고리 검색 성공: {len(limited_results)}개 반환")
                return limited_results
            
            return []
            
        except Exception as e:
            if debug:
                print(f"❌ 직접 카테고리 검색 오류: {e}")
            return []
    def calculate_vector_similarity_universal(self, distance: float, all_distances: List[float] = None) -> float:
        """🔧 만능 벡터 유사도 계산 (음수 거리값 처리)"""
        
        # 음수 거리값 처리 (IP 방식)
        if distance < 0:
            # Inner Product: 음수가 나올 수 있음
            # -800대 값을 0-1 범위로 정규화
            if all_distances:
                min_dist = min(all_distances)
                max_dist = max(all_distances)
                range_dist = max_dist - min_dist
                
                if range_dist > 0:
                    # 상대적 위치 계산 (IP는 높을수록 유사하므로 역전)
                    relative_pos = (distance - min_dist) / range_dist
                    similarity = 1 - relative_pos  # 높은 값 = 높은 유사도
                else:
                    similarity = 0.5  # 모두 동일하면 중간값
            else:
                # 단순 정규화 (-1000 ~ -800 범위 가정)
                normalized = max(0, min(1, (distance + 1000) / 200))
                similarity = normalized
        
        # 양수 거리값 처리 (cosine/l2 방식)
        else:
            if self.vector_space_type == "cosine":
                # Cosine 거리: 0=일치, 2=반대
                similarity = max(0, 1 - (distance / 2))
            elif self.vector_space_type == "l2":
                # L2 거리: 0=일치, sqrt(2)=최대 (정규화된 벡터)
                similarity = max(0, 1 - (distance / 1.414))
            else:
                # 기본값
                similarity = max(0, 1 - distance)
        
        return max(0, min(similarity, 1))  # 0-1 범위 보장
    
    def connect_database(self) -> bool:
        """데이터베이스 연결 (읽기 전용)"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ 데이터베이스가 없습니다: {self.db_path}")
                return False
            
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # 🔍 모든 컬렉션 이름 확인
            try:
                collections = self.client.list_collections()
                print(f"🔍 발견된 컬렉션들: {[c.name for c in collections]}")
                
                if collections:
                    # 첫 번째 컬렉션 사용
                    self.collection = collections[0]
                    self.collection_name = collections[0].name
                    print(f"✅ 자동 선택된 컬렉션: {self.collection_name}")
                else:
                    print("❌ 컬렉션이 없습니다")
                    return False
                    
            except Exception as e:
                # 기존 방식 시도
                print(f"컬렉션 목록 조회 실패, 기본 이름으로 시도: {e}")
                self.collection = self.client.get_collection(name=self.collection_name)
            
            # 벡터 공간 타입 감지
            metadata = self.collection.metadata
            self.vector_space_type = metadata.get("hnsw:space", "unknown")
            
            count = self.collection.count()
            print(f"✅ RAG DB 연결 성공 (총 {count}개 문서, {self.vector_space_type.upper()} 거리)")
            print("🔒 읽기 전용 모드 - DB 수정하지 않음")
            
            # 🔍 DB 메타데이터 로드
            self._load_database_metadata()
            
            return True
            
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False
    
    def _load_database_metadata(self) -> None:
        """🔍 DB에서 사용 가능한 브랜드/카테고리 목록 로드"""
        try:
            print("🔍 DB 메타데이터 로딩 중...")
            
            # 모든 문서 메타데이터 조회 (벡터 없이)
            all_results = self.collection.get(
                include=["metadatas"]
            )
            
            if not all_results or not all_results.get('metadatas'):
                print("❌ DB 메타데이터 로드 실패")
                return
            
            # 브랜드/카테고리 추출
            for metadata in all_results['metadatas']:
                if metadata:
                    brand = metadata.get('brand')
                    category = metadata.get('category')
                    
                    if brand:
                        self.available_brands.add(brand.strip())
                    if category:
                        self.available_categories.add(category.strip())
            
            self.db_metadata_loaded = True
            
            print(f"✅ DB 메타데이터 로드 완료:")
            print(f"   📦 사용 가능한 브랜드: {len(self.available_brands)}개")
            print(f"   🏷️ 사용 가능한 카테고리: {len(self.available_categories)}개")
            
            # 주요 브랜드 미리보기
            if self.available_brands:
                sample_brands = list(self.available_brands)[:10]
                print(f"   🔍 브랜드 예시: {', '.join(sample_brands)}")
            
        except Exception as e:
            print(f"❌ DB 메타데이터 로드 오류: {e}")
            self.db_metadata_loaded = False
    
    def _check_brand_existence(self, brands: List[str], debug: bool = False) -> Dict[str, bool]:
        """🔍 브랜드가 DB에 존재하는지 확인"""
        if not self.db_metadata_loaded:
            if debug:
                print("⚠️ DB 메타데이터가 로드되지 않음 - 존재 여부 확인 불가")
            return {brand: True for brand in brands}  # 안전하게 통과
        
        result = {}
        for brand in brands:
            # 정확한 매칭
            exact_match = brand in self.available_brands
            
            # 유사한 브랜드 찾기 (대소문자 무시, 부분 매칭)
            similar_match = any(
                brand.lower() in available_brand.lower() or 
                available_brand.lower() in brand.lower()
                for available_brand in self.available_brands
            )
            
            exists = exact_match or similar_match
            result[brand] = exists
            
            if debug:
                status = "✅ 존재" if exists else "❌ 없음"
                print(f"   🔍 '{brand}': {status}")
        
        return result
    
    def _check_category_existence(self, categories: List[str], debug: bool = False) -> Dict[str, bool]:
        """🔍 카테고리가 DB에 존재하는지 확인"""
        if not self.db_metadata_loaded:
            if debug:
                print("⚠️ DB 메타데이터가 로드되지 않음 - 존재 여부 확인 불가")
            return {category: True for category in categories}  # 안전하게 통과
        
        result = {}
        for category in categories:
            # 정확한 매칭
            exact_match = category in self.available_categories
            
            # 유사한 카테고리 찾기
            similar_match = any(
                category.lower() in available_category.lower() or 
                available_category.lower() in category.lower()
                for available_category in self.available_categories
            )
            
            exists = exact_match or similar_match
            result[category] = exists
            
            if debug:
                status = "✅ 존재" if exists else "❌ 없음"
                print(f"   🔍 '{category}': {status}")
        
        return result
    
    
    def create_user_profile(self,user_spending_history: List[Dict]) -> Dict:
        """사용자 프로필 생성"""
        profile = {
            'brand_counts': defaultdict(int),
            'category_counts': defaultdict(int),
            'brand_spending': defaultdict(float),
            'category_spending': defaultdict(float),
            'total_transactions': 0,
            'total_spending': 0.0,
            'recent_brands': [],  # 최근 1주일
            'preferred_categories': [],
            'avg_spending_per_brand': {},
            'spending_timeline': []
        }
        
        current_date = datetime.now()
        recent_threshold = current_date - timedelta(days=7)
        
        for transaction in user_spending_history:
            brand = transaction['brand']
            category = transaction.get('category', 'Unknown')
            amount = transaction['amount']
            date = datetime.fromisoformat(transaction['date']) if isinstance(transaction['date'], str) else transaction['date']
            
            # 기본 통계
            profile['brand_counts'][brand] += 1
            profile['category_counts'][category] += 1
            profile['brand_spending'][brand] += amount
            profile['category_spending'][category] += amount
            profile['total_transactions'] += 1
            profile['total_spending'] += amount
            
            # 최근 브랜드 (가중치 적용)
            if date >= recent_threshold:
                recency_weight = self.score_calculator.calculate_recency_weight(date, current_date)
                profile['recent_brands'].append({
                    'brand': brand,
                    'category': category,
                    'amount': amount,
                    'weight': recency_weight,
                    'date': date
                })
            
            # 시간순 기록
            profile['spending_timeline'].append({
                'brand': brand,
                'category': category, 
                'amount': amount,
                'date': date
            })
        
        # 브랜드별 평균 소비액 계산
        for brand, total_amount in profile['brand_spending'].items():
            count = profile['brand_counts'][brand]
            profile['avg_spending_per_brand'][brand] = total_amount / count
        
        # 선호 카테고리 정렬 (소비 빈도 기준)
        profile['preferred_categories'] = sorted(
            profile['category_counts'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return dict(profile)  # defaultdict를 일반 dict로 변환

    def _is_personalization_query(self, query: str) -> bool:
        """🎯 개인화 요청인지 판단"""
        personalization_patterns = [
            # 명시적 개인화 요청
            r'내\s*소비.*패턴', r'내.*맞는', r'나.*맞는', r'우리.*맞는',
            r'개인화.*추천', r'맞춤.*추천', r'맞춤형.*혜택',
            
            # 소비 이력 기반 요청
            r'지난.*소비', r'최근.*소비', r'저번.*소비',
            r'지난주.*썼', r'저번주.*썼', r'최근.*썼',
            r'내가.*자주', r'내가.*많이', r'내가.*주로',
            
            # 일반적인 추천 요청 (브랜드 없이)
            r'^(?!.*[가-힣A-Za-z]{2,}\s*(혜택|이벤트|할인)).*추천.*해.*줘',
            r'^(?!.*[가-힣A-Za-z]{2,}\s*(혜택|이벤트|할인)).*혜택.*있.*어',
            
            # 패턴 기반 요청
            r'패턴.*기반', r'이력.*기반', r'히스토리.*기반'
        ]
        
        for pattern in personalization_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    def _try_direct_brand_search(self, query: str, top_k: int, debug: bool = False) -> List[Dict]:
        """🎯 브랜드 기반 직접 검색 (벡터 검색 전에 시도)"""
        try:
            # 쿼리에서 브랜드 추출
            extracted_brands = self._extract_brands_from_query(query, debug)
            
            if not extracted_brands:
                return []
            
            if debug:
                print(f"🎯 직접 브랜드 검색 시도: {extracted_brands}")
            
            # 각 브랜드별로 직접 검색
            all_results = []
            
            for brand in extracted_brands:
                # DB에서 해당 브랜드 직접 찾기
                try:
                    brand_results = self.collection.get(
                        where={"brand": {"$eq": brand}},
                        include=["metadatas", "documents"]
                    )
                    
                    if brand_results and brand_results.get('metadatas'):
                        for i, metadata in enumerate(brand_results['metadatas']):
                            # 유효성 검증
                            if self._validate_result(metadata, datetime.now()):
                                all_results.append({
                                    "id": f"direct_{brand}_{i}",
                                    "metadata": metadata,
                                    "distance": 0.0,  # 직접 매칭이므로 최고 점수
                                    "document": brand_results['documents'][i] if brand_results.get('documents') else "",
                                    "vector_rank": i + 1
                                })
                    
                    if debug:
                        count = len(brand_results['metadatas']) if brand_results and brand_results.get('metadatas') else 0
                        print(f"   '{brand}': {count}개 결과")
                        
                except Exception as e:
                    if debug:
                        print(f"   '{brand}' 검색 실패: {e}")
                    continue
            
            # 결과 제한
            if all_results:
                limited_results = all_results[:top_k]
                if debug:
                    print(f"🎯 직접 브랜드 검색 성공: {len(limited_results)}개 반환")
                return limited_results
            
            return []
            
        except Exception as e:
            if debug:
                print(f"❌ 직접 브랜드 검색 오류: {e}")
            return []

    def _fallback_text_search(self, query: str, filters: Dict, top_k: int, debug: bool = False) -> List[Dict]:
        """🔄 텍스트 기반 폴백 검색 (개선된 버전)"""
        try:
            if debug:
                print("🔄 텍스트 폴백 검색 시작...")
            
            # 모든 문서 가져오기
            all_results = self.collection.get(
                include=["metadatas", "documents"]
            )
            
            if not all_results or not all_results.get('metadatas'):
                print("❌ DB에 데이터 없음")
                return []
            
            # 텍스트 매칭 점수 계산
            scored_results = []
            query_lower = query.lower()
            query_words = query_lower.split()
            
            for i, metadata in enumerate(all_results['metadatas']):
                if not metadata:
                    continue
                
                # 유효성 검증
                if not self._validate_result(metadata, datetime.now()):
                    continue
                
                # 텍스트 매칭 점수 계산
                score = 0.0
                
                # 브랜드 매칭 (가장 중요 - 60%)
                brand = metadata.get('brand', '').lower()
                if brand:
                    if brand in query_lower:
                        score += 0.6
                    elif any(word in brand for word in query_words):
                        score += 0.4
                    elif any(brand in word for word in query_words):
                        score += 0.3
                
                # 카테고리 매칭 (20%)
                category = metadata.get('category', '').lower()
                if category and category in query_lower:
                    score += 0.2
                
                # 제목 매칭 (15%)
                title = metadata.get('title', '').lower()
                if title:
                    matching_words = sum(1 for word in query_words if word in title)
                    score += 0.15 * (matching_words / len(query_words))
                
                # 혜택 타입 매칭 (5%)
                benefit_type = metadata.get('benefit_type', '').lower()
                benefit_keywords = ['할인', '적립', '쿠폰', '혜택', '이벤트', '증정']
                if any(keyword in query_lower for keyword in benefit_keywords):
                    if benefit_type in query_lower:
                        score += 0.05
                
                if score > 0:
                    scored_results.append({
                        "id": f"text_match_{i}",
                        "metadata": metadata,
                        "distance": 1.0 - score,  # 점수를 거리로 변환
                        "document": all_results['documents'][i] if all_results.get('documents') else "",
                        "vector_rank": 0,
                        "text_score": score
                    })
            
            # 점수순 정렬
            scored_results.sort(key=lambda x: x['text_score'], reverse=True)
            
            # 상위 결과만 반환
            final_results = scored_results[:top_k]
            
            if debug:
                print(f"🔄 텍스트 검색 완료: {len(final_results)}개 결과")
                for i, result in enumerate(final_results[:3]):
                    brand = result['metadata'].get('brand', 'Unknown')
                    score = result.get('text_score', 0)
                    print(f"   [{i+1}] {brand}: 점수 {score:.3f}")
            
            return final_results
            
        except Exception as e:
            if debug:
                print(f"❌ 텍스트 검색 오류: {e}")
            return []
    def _extract_brands_from_query(self, query: str, debug: bool = False) -> List[str]:
        """🔧 개선된 브랜드 추출 (정확도 향상)"""
        
        if debug:
            print(f"🔍 브랜드 추출 시작: '{query}'")
        
        found_brands = []
        
        # 1단계: 확실한 브랜드 패턴 매칭 (한국 유명 브랜드들)
        known_brand_patterns = {
            # 카페/음식
            '스타벅스': [r'스타벅스', r'starbucks'],
            '이디야': [r'이디야', r'ediya'],
            '투썸플레이스': [r'투썸', r'투썸플레이스', r'twosome'],
            '맥도날드': [r'맥도날드', r'맥날', r'mcdonald'],
            '버거킹': [r'버거킹', r'burgerking'],
            'KFC': [r'kfc', r'케이에프씨'],
            
            # 마트/쇼핑
            '이마트': [r'이마트', r'emart'],
            '홈플러스': [r'홈플러스', r'homeplus'],
            '롯데마트': [r'롯데마트', r'lotte'],
            '쿠팡': [r'쿠팡', r'coupang'],
            '지마켓': [r'지마켓', r'gmarket'],
            '11번가': [r'11번가', r'십일번가'],
            
            # 편의점
            'GS25': [r'gs25', r'지에스'],
            'CU': [r'cu', r'씨유'],
            '세븐일레븐': [r'세븐일레븐', r'7-eleven', r'세븐'],
            '이마트24': [r'이마트24', r'이마트이십사'],
            
            # 뷰티/기타
            '올리브영': [r'올리브영', r'oliveyoung'],
            '네이버': [r'네이버', r'naver'],
            '카카오': [r'카카오', r'kakao'],
            '삼성': [r'삼성', r'samsung'],
            '애플': [r'애플', r'apple'],  # 🔧 애플 추가
            'LG': [r'lg', r'엘지'],
            '현대': [r'현대', r'hyundai']
        }
        
        query_lower = query.lower()
        
        # 확실한 브랜드 패턴 매칭
        for brand_name, patterns in known_brand_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    found_brands.append(brand_name)
                    if debug:
                        print(f"   ✅ 확실한 브랜드 발견: '{brand_name}' (패턴: {pattern})")
                    break
        
        # 2단계: 🔧 더 엄격한 일반 브랜드명 추출
        # 확실한 브랜드가 없을 때만 일반 추출 시도
        if not found_brands:
            # 🔧 브랜드 후보 조건을 더 엄격하게
            words = query.split()
            for word in words:
                # 명확한 브랜드명 특징을 가진 단어만
                if self._is_potential_brand_name(word):
                    # 🔧 확장된 일반 단어 필터링
                    if not self._is_common_word(word):
                        found_brands.append(word)
                        if debug:
                            print(f"   🤔 잠재적 브랜드: '{word}'")
        
        # 중복 제거
        unique_brands = list(set(found_brands))
        
        if debug:
            print(f"   🎯 최종 추출된 브랜드: {unique_brands}")
        
        return unique_brands

    def _is_potential_brand_name(self, word: str) -> bool:
        """🔧 잠재적 브랜드명인지 판단 (더 엄격하게)"""
        # 한글 브랜드: 2-6자 (더 엄격하게)
        if re.match(r'^[가-힣]{2,6}$', word):
            return True
        
        # 영문 브랜드: 대문자로 시작하거나 전체 대문자, 3-12자
        if re.match(r'^[A-Z][a-zA-Z]{2,11}$', word) or re.match(r'^[A-Z]{2,8}$', word):
            return True
        
        return False

    def _is_common_word(self, word: str) -> bool:
        """🔧 일반 단어인지 판단 (확장된 필터링)"""
        common_words = {
            # 기본 단어들
            '혜택', '할인', '이벤트', '쿠폰', '적립', '증정', '세일', '특가', '추천', '찾아', '알려', '있어', '해줘',
            
            # 장소/카테고리
            '카페', '마트', '식당', '편의점', '온라인', '쇼핑', '뷰티', '의료', '병원', '약국', '은행', '금융',
            
            # 설명 단어들
            '소비', '패턴', '맞는', '어디', '뭐가', '어떤', '좋은', '괜찮은', '저렴한', '비싼', '최고', '인기',
            
            # 대명사/지시어
            '내가', '우리', '사람', '고객', '회원', '가격', '돈', '원', '만원', '천원', '정도', '정말', '진짜',
            
            # 부사/접속사
            '그냥', '좀', '조금', '많이', '자주', '가끔', '항상', '보통', '최근', '요즘', '오늘', '어제', '내일',
            
            # 시간 관련
            '지금', '현재', '이번', '다음', '저번', '올해', '작년', '내년', '월', '일', '주', '때문', '위해',
            
            # 동사/형용사 어간
            '통해', '대해', '관련', '관한', '가능', '불가능', '필요', '중요', '유용', '편리', '간단', '복잡',
            
            # 🔧 새로 추가된 필터링 단어들
            '알려줘', '해줘', '보여줘', '찾아줘', '추천해줘', '말해줘',
            '패턴에', '소비에', '이력에', '기반에', '맞게', '따라',
            '어떻게', '어디서', '언제', '왜', '무엇', '누구',
            '있나', '있어', '없어', '됐어', '좋아', '싫어'
        }
        
        return word in common_words
    
    def search_personalized_benefits(self, query: str, user_profile: Dict, 
                                top_k: int = 10, debug: bool = False) -> str:
        """🔗 개인화된 혜택 검색 및 추천 (Perplexity API 연동)"""
        if debug:
            logger.info(f"🎯 개선된 개인화 검색 시작: {query}")
            # print(f"👤 사용자 프로필: 총 {user_profile['total_transactions']}건, {user_profile['total_spending']:,.0f}원")
        
        # 🔧 1단계: 개인화 요청인지 먼저 확인
        is_personalization = self._is_personalization_query(query)
        if debug:
            logger.info(f"🎯 개인화 요청 여부: {is_personalization}")
        
        # 2단계: 쿼리 분석
        analysis = MultiCategoryQueryParser.analyze_query_intent(query)
        filters, parsed_info = MultiCategoryQueryParser.build_multi_category_filters(query, debug)
        logger.info(f"🔧 2단계: 쿼리 분석: {analysis}")
        logger.info(f"🔧 2단계: 쿼리 분석: {filters}")
        logger.info(f"🔧 2단계: 쿼리 분석: {parsed_info}")
        
        # 🔧 3단계: 개선된 브랜드 추출
        extracted_brands = self._extract_brands_from_query(query, debug)
        logger.info(f"🔧 3단계: 개선된 브랜드 추출: {extracted_brands}")
        # 🔧 4단계: 개선된 검증 로직 (더 관대하게)
        validation_result = self._validate_query_improved(
            query, analysis, parsed_info, extracted_brands, is_personalization, debug
        )
        logger.info(f"🔧 4단계: 개선된 검증 로직: {validation_result}")
        # 🔗 4.5단계: DB에 브랜드가 없거나 결과가 없을 경우 Perplexity API 사용
        if not validation_result['valid']:
            # 존재하지 않는 브랜드에 대한 실시간 검색
            if extracted_brands:
                brand_name = extracted_brands[0]  # 첫 번째 브랜드
                logger.info(f"🔗 DB에 '{brand_name}' 브랜드가 없어 실시간 검색을 시도합니다...")
                return self._search_with_perplexity(query, brand_name)
            else:
                return validation_result['message']
        
        # 🔧 5단계: 검색 쿼리 준비 (필터 조건 완화)
        search_query = query
        logger.info(f"🔧 5단계: 검색 쿼리 준비: {search_query}")
        search_filters = {}  # 필터 조건 완화 또는 제거
        
        if is_personalization and not extracted_brands:
            # 개인화 요청이면 사용자 선호 브랜드 기반으로 검색 확장
            enhanced_query = self._enhance_query_for_personalization(query, user_profile)
            if debug:
                logger.info(f"🎯 개인화 쿼리 확장: '{enhanced_query}'")
            search_query = enhanced_query
        logger.info(f"🔧 6단계: 개선된 벡터 검색: {search_query}")
        # 6단계: 개선된 벡터 검색 (직접 브랜드 검색 포함)
        base_results = self._execute_vector_search_readonly(search_query, search_filters, top_k * 2, debug)
        
        # 🔗 6.5단계: DB에서 결과가 없으면 Perplexity API 사용
        if not base_results:
            logger.info("🔗 DB에서 결과가 없어 실시간 검색을 시도합니다...")
            if extracted_brands:
                return self._search_with_perplexity(query, extracted_brands[0])
            else:
                return self._search_with_perplexity(query)
        
        # 7단계: 개인화 스코어링
        personalized_results = self._apply_personalization_scoring_readonly(
            base_results, user_profile, parsed_info, debug
        )
        logger.info(f"🔧 7단계: 개인화 스코어링: {personalized_results}")
        # 8단계: 최종 정렬 및 선택
        final_results = self._rank_and_select_results(
            personalized_results, user_profile, top_k, debug
        )
        logger.info(f"🔧 8단계: 최종 정렬 및 선택: {final_results}")
        if debug:
            logger.info(f"📊 검색 결과: {len(base_results)}개 → 개인화 후: {len(final_results)}개")
        
        # 9단계: 결과 출력
        if not final_results:
            # 🔗 최종적으로도 결과가 없으면 Perplexity API 사용
            logger.info("🔗 최종 결과가 없어 실시간 검색을 시도합니다...")
            if extracted_brands:
                return self._search_with_perplexity(query, extracted_brands[0])
            else:
                return self._search_with_perplexity(query)
        logger.info(f"🔧 9단계: 결과 출력: {final_results}")
        return self._generate_results_readonly(final_results, user_profile, parsed_info)

    def _enhance_query_for_personalization(self, query: str, user_profile: Dict) -> str:
        """🎯 개인화 요청을 위한 쿼리 확장"""
        # 사용자 최다 이용 브랜드 3개 추가
        top_brands = sorted(
            user_profile.get('brand_counts', {}).items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        # 사용자 최다 이용 카테고리 2개 추가
        top_categories = user_profile.get('preferred_categories', [])[:2]
        
        enhanced_parts = [query]
        
        if top_brands:
            brand_names = [brand for brand, _ in top_brands]
            enhanced_parts.append(' '.join(brand_names))
        
        if top_categories:
            category_names = [category for category, _ in top_categories]
            enhanced_parts.append(' '.join(category_names))
        
        enhanced_parts.append('혜택 할인 이벤트 추천')
        
        return ' '.join(enhanced_parts)

    def _validate_query_improved(self, query: str, analysis: Dict, parsed_info: Dict, 
                               extracted_brands: List[str], is_personalization: bool, debug: bool) -> Dict[str, Any]:
        """🔧 개선된 쿼리 검증 (브랜드 인식 및 개인화 요청 처리 개선)"""
        
        if debug:
            logger.info("🔧 개선된 쿼리 검증 시작...")
            logger.info(f"   🎯 개인화 요청: {is_personalization}")
            logger.info(f"   🏪 추출된 브랜드: {extracted_brands}")
        
        # 🎯 1) 개인화 요청이면 무조건 통과
        if is_personalization:
            if debug:
                logger.info("   ✅ 개인화 요청으로 인식 - 검색 진행")
            return {'valid': True}
        
        # 2) 명시적 소비 데이터가 있으면 브랜드 존재 확인
        if parsed_info.get('spending_data'):
            brands = list(parsed_info['spending_data'].keys())
            brand_existence = self._check_brand_existence(brands, debug)
            
            missing_brands = [brand for brand, exists in brand_existence.items() if not exists]
            if missing_brands:
                if debug:
                    print(f"   ❌ 소비 데이터의 브랜드 '{', '.join(missing_brands)}'가 DB에 없음")
                return {
                    'valid': False,
                    'message': self._generate_missing_brands_message(missing_brands, 'spending_data')
                }
            
            if debug:
                print("   ✅ 소비 데이터의 모든 브랜드가 DB에 존재 - 검색 진행")
            return {'valid': True}
        
        # 🔧 3) 추출된 브랜드가 있을 때만 존재 확인
        if extracted_brands:
            brand_existence = self._check_brand_existence(extracted_brands, debug)
            missing_brands = [brand for brand, exists in brand_existence.items() if not exists]
            
            # 🔧 모든 브랜드가 없을 때만 차단 (Perplexity로 넘김)
            if missing_brands and len(missing_brands) == len(extracted_brands):
                if debug:
                    print(f"   ❌ 추출된 모든 브랜드 '{', '.join(missing_brands)}'가 DB에 없음 - Perplexity로 전환")
                return {
                    'valid': False,
                    'message': f"브랜드 '{', '.join(missing_brands)}'에 대한 정보를 실시간으로 검색합니다."
                }
            elif missing_brands:
                if debug:
                    existing_brands = [b for b in extracted_brands if b not in missing_brands]
                    print(f"   ⚠️ 일부 브랜드만 존재: 존재={existing_brands}, 없음={missing_brands}")
                    print("   ✅ 존재하는 브랜드 기준으로 검색 진행")
            else:
                if debug:
                    print("   ✅ 추출된 모든 브랜드가 DB에 존재 - 검색 진행")
            return {'valid': True}
        
        # 4) 혜택 키워드나 일반적인 추천 요청이면 항상 통과
        benefit_keywords = ['혜택', '할인', '이벤트', '적립', '쿠폰', '증정', '특가', '세일', '추천']
        general_keywords = ['맞는', '패턴', '소비', '내', '우리', '좋은', '괜찮은', '어떤', '뭐가']
        
        has_benefit_keyword = any(keyword in query for keyword in benefit_keywords)
        has_general_keyword = any(keyword in query for keyword in general_keywords)
        
        if has_benefit_keyword or has_general_keyword:
            if debug:
                if has_benefit_keyword:
                    print("   ✅ 혜택 키워드 인식됨 - 일반 검색 진행")
                if has_general_keyword:
                    print("   ✅ 일반 추천 요청 인식됨 - 검색 진행")
            return {'valid': True}
        
        # 5) 빈 브랜드/카테고리도 통과 (사용자가 모르고 물어볼 수 있음)
        if debug:
            print("   ✅ 브랜드/카테고리 없는 일반 질문 - 전체 검색 진행")
        return {'valid': True}

    def _execute_vector_search_readonly(self, query: str, filters: Dict, top_k: int, debug: bool = False) -> List[Dict]:
        """🔒 개선된 벡터 검색 (브랜드 > 카테고리 우선순위)"""
        try:
            # 🔧 브랜드와 카테고리 모두 추출
            extracted_brands = self._extract_brands_from_query(query, debug)
            extracted_categories = self._extract_categories_from_query(query, debug)
            
            if debug:
                logger.info(f"🔍 추출 결과 - 브랜드: {extracted_brands}, 카테고리: {extracted_categories}")
            
            # 🔧 1단계: 브랜드가 있으면 브랜드 우선 (카테고리 무시)
            if extracted_brands:
                brand_results = self._try_direct_brand_search(query, top_k, debug)
                if brand_results:
                    logger.info(f"✅ 브랜드 우선 검색 성공: {len(brand_results)}개 결과 (브랜드: {extracted_brands})")
                    return brand_results
                else:
                    if debug:
                        logger.info(f"⚠️ 브랜드 '{extracted_brands}' 직접 검색 실패, 벡터 검색으로 진행...")
            
            # 🔧 2단계: 브랜드가 없고 카테고리만 있으면 카테고리 검색
            elif extracted_categories:
                category_results = self._try_direct_category_search(query, extracted_categories, top_k, debug)
                if category_results:
                    logger.info(f"✅ 카테고리 우선 검색 성공: {len(category_results)}개 결과 (카테고리: {extracted_categories})")
                    return category_results
                else:
                    if debug:
                        logger.info(f"⚠️ 카테고리 '{extracted_categories}' 직접 검색 실패, 벡터 검색으로 진행...")
            
            # 🔧 3단계: 브랜드/카테고리 직접 검색 실패 시 벡터 검색
            search_query = query
            
            if debug:
                logger.info(f"🔍 벡터 검색 시작: '{search_query}'")
            
            # 임베딩 생성
            try:
                request_data = {"text": search_query}
                query_vector = self.embedding_executor.execute(request_data)
                
                if not query_vector:
                    logger.info("❌ 임베딩 생성 실패 - 텍스트 검색으로 전환")
                    return self._fallback_text_search(query, filters, top_k, debug)
                    
            except Exception as e:
                logger.info(f"❌ 임베딩 API 오류: {e} - 텍스트 검색으로 전환")
                return self._fallback_text_search(query, filters, top_k, debug)
            
            # 벡터 정규화
            try:
                query_vector_array = np.array(query_vector)
                norm = np.linalg.norm(query_vector_array)
                
                if norm > 0:
                    normalized_query_vector = (query_vector_array / norm).tolist()
                else:
                    normalized_query_vector = query_vector
                    
            except Exception as e:
                print(f"⚠️ 벡터 정규화 오류: {e}")
                normalized_query_vector = query_vector
            
            # 벡터 검색 실행
            try:
                results = self.collection.query(
                    query_embeddings=[normalized_query_vector],
                    n_results=top_k * 3,
                    include=["metadatas", "distances", "documents"]
                )
                
                if debug:
                    result_count = len(results['ids'][0]) if results and results.get('ids') else 0
                    print(f"🔍 일반 벡터 검색 결과: {result_count}개")
                    
            except Exception as e:
                print(f"❌ 벡터 검색 실패: {e} - 텍스트 검색으로 전환")
                return self._fallback_text_search(query, filters, top_k, debug)
            
            # 결과가 없으면 텍스트 검색
            if not results or not results.get('ids') or not results['ids'][0]:
                print("❌ 벡터 검색 결과 없음 - 텍스트 검색으로 전환")
                return self._fallback_text_search(query, filters, top_k, debug)
            
            # 결과 포맷팅
            formatted_results = []
            ids = results['ids'][0]
            metadatas = results['metadatas'][0] 
            distances = results['distances'][0]
            documents = results['documents'][0]
            
            for i in range(len(ids)):
                formatted_results.append({
                    "id": ids[i],
                    "metadata": metadatas[i],
                    "distance": distances[i],
                    "document": documents[i],
                    "vector_rank": i + 1
                })
            
            print(f"✅ 벡터 검색 완료: {len(formatted_results)}개 결과")
            return formatted_results
            
        except Exception as e:
            print(f"❌ 벡터 검색 전체 실패: {e} - 텍스트 검색으로 전환")
            return self._fallback_text_search(query, filters, top_k, debug)

    def _apply_personalization_scoring_readonly(self, results: List[Dict], user_profile: Dict, 
                                              parsed_info: Dict, debug: bool) -> List[Dict]:
        """🔒 개인화 스코어링 (읽기 전용)"""
        if not results:
            print("❌ 개인화 스코어링: 입력 결과 없음")
            return []
        
        print(f"🔄 개인화 스코어링: {len(results)}개 결과")
        
        scored_results = []
        current_date = datetime.now()
        
        # 전체 거리값 수집 (상대적 계산용)
        all_distances = [result.get('distance', 0) for result in results]
        
        for i, result in enumerate(results):
            try:
                metadata = result.get('metadata', {})
                brand = metadata.get('brand')
                category = metadata.get('category')
                benefit_type = metadata.get('benefit_type')
                discount_rate = float(metadata.get('discount_rate', 0))
                
                # 기본 검증
                if not self._validate_result(metadata, current_date):
                    continue
                
                # 개인화 점수 계산
                vector_score = self.calculate_vector_similarity_universal(result.get('distance', 0), all_distances)
                
                # 최종 개인화 점수 계산 (간단화)
                personalized_score = vector_score * 0.8 + 0.2  # 벡터 유사도 80% + 기본 점수 20%
                
                # 결과에 점수 저장
                result['personalized_score'] = personalized_score
                result['vector_score'] = vector_score
                
                scored_results.append(result)
                
            except Exception as e:
                if debug:
                    print(f"      ❌ 오류: {e}")
                continue
        
        print(f"✅ 개인화 스코어링 완료: {len(scored_results)}/{len(results)}개 처리")
        return scored_results
    
    def _validate_result(self, metadata: Dict, current_date: datetime) -> bool:
        """결과 유효성 검증"""
        # 필수 필드 검증
        if not all([metadata.get('brand'), metadata.get('category'), 
                   metadata.get('title'), metadata.get('benefit_type')]):
            return False
        
        # 활성 상태 검증
        if not metadata.get('is_active', False):
            return False
        
        # 날짜 유효성 검증
        if metadata.get('valid_to'):
            try:
                valid_to = datetime.fromisoformat(metadata['valid_to'])
                if valid_to < current_date:
                    return False
            except:
                return False
        
        return True
    
    def _rank_and_select_results(self, results: List[Dict], user_profile: Dict, 
                               top_k: int, debug: bool) -> List[Dict]:
        """최종 순위 결정 및 결과 선택"""
        if not results:
            return []
        
        # 개인화 점수로 정렬
        try:
            sorted_results = sorted(results, key=lambda x: x.get('personalized_score', 0), reverse=True)
        except Exception as e:
            return results[:top_k]
        
        return sorted_results[:top_k]
    
    def _generate_results_readonly(self, results: List[Dict], user_profile: Dict, parsed_info: Dict = None) -> str:
        """🔒 검색 결과 생성 (읽기 전용)"""
        if not results:
            return "❌ 해당 조건에 맞는 혜택 정보가 없습니다."
        
        try:
            message = f"🎯 개인화 혜택 추천 결과:\n\n"
            
            for i, result in enumerate(results[:5], 1):
                metadata = result.get('metadata', {})
                score = result.get('personalized_score', 0)
                
                message += f"**[{i}] {metadata.get('brand', 'Unknown')}** ({metadata.get('category', 'Unknown')})\n"
                message += f"🎯 {metadata.get('title', 'Unknown')}\n"
                
                # 혜택 정보
                benefit_type = metadata.get('benefit_type', 'Unknown')
                discount_rate = metadata.get('discount_rate', 0)
                
                try:
                    discount_rate = float(discount_rate) if discount_rate else 0
                except:
                    discount_rate = 0
                
                if benefit_type == "할인" and discount_rate > 0:
                    message += f"💰 {benefit_type}: {discount_rate}% 할인\n"
                elif benefit_type == "적립" and discount_rate > 0:
                    message += f"💰 {benefit_type}: {discount_rate}배 적립\n"
                else:
                    message += f"💰 혜택: {benefit_type}\n"
                
                conditions = metadata.get('conditions', '조건 없음')
                message += f"📝 조건: {conditions}\n"
                
                valid_from = metadata.get('valid_from', 'Unknown')
                valid_to = metadata.get('valid_to', 'Unknown') 
                message += f"📅 기간: {valid_from} ~ {valid_to}\n"
                message += f"📊 개인화점수: {score:.3f}\n\n"
            
            return message.strip()
            
        except Exception as e:
            return f"📋 검색 결과: {len(results)}개의 혜택을 찾았지만 출력 중 오류가 발생했습니다."
    
    def _generate_no_results_message_enhanced(self, parsed_info: Dict, user_profile: Dict, analysis: Dict) -> str:
        """🔍 향상된 결과 없음 메시지"""
        return "❌ 해당 조건에 맞는 혜택 정보가 데이터베이스에 없습니다."

    def _generate_missing_brands_message(self, missing_brands: List[str], context: str) -> str:
        """존재하지 않는 브랜드에 대한 메시지 생성"""
        if len(missing_brands) == 1:
            brand = missing_brands[0]
            message = f"❌ '{brand}' 브랜드는 현재 혜택 데이터베이스에 등록되어 있지 않습니다."
        else:
            brand_list = "', '".join(missing_brands)
            message = f"❌ '{brand_list}' 브랜드들은 현재 혜택 데이터베이스에 등록되어 있지 않습니다."
        
        return message



def chatbot_message():
    """챗봇 메시지 처리"""
    rag = initialize_rag_system()
    if not rag:
        return jsonify({
            "success": False,
            "error": "RAG 시스템이 초기화되지 않았습니다."
        }), 503
    
    
    
    sample_history = create_sample_user_history()
    # rag_system.py의 독립 함수 사용
    ra = PersonalizedBenefitRAG()
    user_profile = ra.create_user_profile(sample_history)
    
    
    # 사용자 프로필 요약 출력
    print(f"   📊 총 소비: {user_profile['total_spending']:,.0f}원 ({user_profile['total_transactions']}건)")
    print(f"   ⭐ 선호 브랜드: {dict(list(sorted(user_profile['brand_counts'].items(), key=lambda x: x[1], reverse=True))[:3])}")
    print(f"   🏷️ 선호 카테고리: {dict(user_profile['preferred_categories'][:3])}")
    print(f"   📅 최근 1주일 소비: {len(user_profile.get('recent_brands', []))}건")
    
    debug_mode = True
    
    # 기본 응답 초기화
    answer = "죄송합니다. 요청을 처리할 수 없습니다."

    try:
        # 웹 요청에서 메시지 가져오기
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "잘못된 JSON 형식입니다."
            }), 400
        
        query = data.get('message', '').strip()
        if not query:
            return jsonify({
                "success": False,
                "error": "message 파라미터가 필요합니다."
            }), 400
        
        logger.info(f"🔧 질문: {query}")
        logger.info("⏳ 연결된 RAG + Perplexity 검색 중...")
        
        # 🔗 개인화 혜택 검색 및 추천 (Perplexity 연동)
        rag_instance = PersonalizedBenefitRAG()
        answer = rag_instance.search_personalized_benefits(query, user_profile, debug=debug_mode)
        
        logger.info(f"🔗 추천 결과:\n{answer}")
        
        # 성공 응답 반환
        return jsonify({
            "success": True,
            "response": {
                "message": answer,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "total_results": 1,
                    "web_search_used": False,
                    "suggestions": ["다른 혜택도 알려주세요", "카테고리별 혜택 보기"]
                }
            }
        })

    except Exception as e:
        
        return jsonify({
            "success": False,
            "error": f"처리 중 오류가 발생했습니다: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500
