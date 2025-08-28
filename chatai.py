# ======================================================================================
# 개인화된 혜택 추천 RAG 시스템 + Perplexity API 연동
# ======================================================================================

import json
import requests
import chromadb
import os
import sys
import re
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import math
from collections import defaultdict

# 기존 모듈 import
from multi_category_parser import MultiCategoryQueryParser
from multi_category_dummy_data import MULTI_CATEGORY_DATA

# 🔧 사용자 이력 모듈 import (단순 분리)
from user_history_data import create_sample_user_history


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


class PersonalizedBenefitRAG:
    """개인화된 혜택 추천 RAG 시스템 (브랜드 인식 및 개인화 요청 처리 개선)"""
    
    def __init__(self, db_path="./cafe_vector_db", collection_name="cafe_benefits"):
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
    
    def create_user_profile(self, user_spending_history: List[Dict]) -> Dict:
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
            print(f"🎯 개선된 개인화 검색 시작: {query}")
            print(f"👤 사용자 프로필: 총 {user_profile['total_transactions']}건, {user_profile['total_spending']:,.0f}원")
        
        # 🔧 1단계: 개인화 요청인지 먼저 확인
        is_personalization = self._is_personalization_query(query)
        if debug:
            print(f"🎯 개인화 요청 여부: {is_personalization}")
        
        # 2단계: 쿼리 분석
        analysis = MultiCategoryQueryParser.analyze_query_intent(query)
        filters, parsed_info = MultiCategoryQueryParser.build_multi_category_filters(query, debug)
        
        # 🔧 3단계: 개선된 브랜드 추출
        extracted_brands = self._extract_brands_from_query(query, debug)
        
        # 🔧 4단계: 개선된 검증 로직 (더 관대하게)
        validation_result = self._validate_query_improved(
            query, analysis, parsed_info, extracted_brands, is_personalization, debug
        )
        
        # 🔗 4.5단계: DB에 브랜드가 없거나 결과가 없을 경우 Perplexity API 사용
        if not validation_result['valid']:
            # 존재하지 않는 브랜드에 대한 실시간 검색
            if extracted_brands:
                brand_name = extracted_brands[0]  # 첫 번째 브랜드
                print(f"🔗 DB에 '{brand_name}' 브랜드가 없어 실시간 검색을 시도합니다...")
                return self._search_with_perplexity(query, brand_name)
            else:
                return validation_result['message']
        
        # 🔧 5단계: 검색 쿼리 준비 (필터 조건 완화)
        search_query = query
        search_filters = {}  # 필터 조건 완화 또는 제거
        
        if is_personalization and not extracted_brands:
            # 개인화 요청이면 사용자 선호 브랜드 기반으로 검색 확장
            enhanced_query = self._enhance_query_for_personalization(query, user_profile)
            if debug:
                print(f"🎯 개인화 쿼리 확장: '{enhanced_query}'")
            search_query = enhanced_query
        
        # 6단계: 개선된 벡터 검색 (직접 브랜드 검색 포함)
        base_results = self._execute_vector_search_readonly(search_query, search_filters, top_k * 2, debug)
        
        # 🔗 6.5단계: DB에서 결과가 없으면 Perplexity API 사용
        if not base_results:
            print("🔗 DB에서 결과가 없어 실시간 검색을 시도합니다...")
            if extracted_brands:
                return self._search_with_perplexity(query, extracted_brands[0])
            else:
                return self._search_with_perplexity(query)
        
        # 7단계: 개인화 스코어링
        personalized_results = self._apply_personalization_scoring_readonly(
            base_results, user_profile, parsed_info, debug
        )
        
        # 8단계: 최종 정렬 및 선택
        final_results = self._rank_and_select_results(
            personalized_results, user_profile, top_k, debug
        )
        
        if debug:
            print(f"📊 검색 결과: {len(base_results)}개 → 개인화 후: {len(final_results)}개")
        
        # 9단계: 결과 출력
        if not final_results:
            # 🔗 최종적으로도 결과가 없으면 Perplexity API 사용
            print("🔗 최종 결과가 없어 실시간 검색을 시도합니다...")
            if extracted_brands:
                return self._search_with_perplexity(query, extracted_brands[0])
            else:
                return self._search_with_perplexity(query)
        
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
            print("🔧 개선된 쿼리 검증 시작...")
            print(f"   🎯 개인화 요청: {is_personalization}")
            print(f"   🏪 추출된 브랜드: {extracted_brands}")
        
        # 🎯 1) 개인화 요청이면 무조건 통과
        if is_personalization:
            if debug:
                print("   ✅ 개인화 요청으로 인식 - 검색 진행")
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
                print(f"🔍 추출 결과 - 브랜드: {extracted_brands}, 카테고리: {extracted_categories}")
            
            # 🔧 1단계: 브랜드가 있으면 브랜드 우선 (카테고리 무시)
            if extracted_brands:
                brand_results = self._try_direct_brand_search(query, top_k, debug)
                if brand_results:
                    print(f"✅ 브랜드 우선 검색 성공: {len(brand_results)}개 결과 (브랜드: {extracted_brands})")
                    return brand_results
                else:
                    if debug:
                        print(f"⚠️ 브랜드 '{extracted_brands}' 직접 검색 실패, 벡터 검색으로 진행...")
            
            # 🔧 2단계: 브랜드가 없고 카테고리만 있으면 카테고리 검색
            elif extracted_categories:
                category_results = self._try_direct_category_search(query, extracted_categories, top_k, debug)
                if category_results:
                    print(f"✅ 카테고리 우선 검색 성공: {len(category_results)}개 결과 (카테고리: {extracted_categories})")
                    return category_results
                else:
                    if debug:
                        print(f"⚠️ 카테고리 '{extracted_categories}' 직접 검색 실패, 벡터 검색으로 진행...")
            
            # 🔧 3단계: 브랜드/카테고리 직접 검색 실패 시 벡터 검색
            search_query = query
            
            if debug:
                print(f"🔍 벡터 검색 시작: '{search_query}'")
            
            # 임베딩 생성
            try:
                request_data = {"text": search_query}
                query_vector = self.embedding_executor.execute(request_data)
                
                if not query_vector:
                    print("❌ 임베딩 생성 실패 - 텍스트 검색으로 전환")
                    return self._fallback_text_search(query, filters, top_k, debug)
                    
            except Exception as e:
                print(f"❌ 임베딩 API 오류: {e} - 텍스트 검색으로 전환")
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


# API 클래스들
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


# 메인 실행 함수
def main():
    """메인 실행 함수"""
    print("🎯 개선된 개인화 혜택 추천 RAG 시스템 + Perplexity API 연동")
    print("=" * 80)
    print("🔧 주요 기능:")
    print("   ✅ 기존 RAG 시스템 (DB 기반 검색)")
    print("   🔗 Perplexity API 연동 (실시간 검색)")
    print("   🎯 자동 전환: DB에 없는 브랜드 → 실시간 검색")
    print("   📊 개인화 추천 시스템")
    print("🚀 이제 모든 브랜드 정보를 실시간으로 검색 가능!")
    print("=" * 80)
    
    # RAG 시스템 초기화
    rag = PersonalizedBenefitRAG()
    
    # 데이터베이스 연결
    if not rag.connect_database():
        print("❌ 데이터베이스 연결 실패. 프로그램을 종료합니다.")
        return
    
    sample_history = create_sample_user_history()
    user_profile = rag.create_user_profile(sample_history)
    
    # 사용자 프로필 요약 출력
    print(f"   📊 총 소비: {user_profile['total_spending']:,.0f}원 ({user_profile['total_transactions']}건)")
    print(f"   ⭐ 선호 브랜드: {dict(list(sorted(user_profile['brand_counts'].items(), key=lambda x: x[1], reverse=True))[:3])}")
    print(f"   🏷️ 선호 카테고리: {dict(user_profile['preferred_categories'][:3])}")
    print(f"   📅 최근 1주일 소비: {len(user_profile.get('recent_brands', []))}건")
    
    debug_mode = False
    

    try:
        query = input("\n🔧 질문: ").strip()
        
        print("\n⏳ 연결된 RAG + Perplexity 검색 중...")
        
        # 🔗 개인화 혜택 검색 및 추천 (Perplexity 연동)
        answer = rag.search_personalized_benefits(query, user_profile, debug=debug_mode)
        
        print(f"\n🔗 추천 결과:\n{answer}")
        print("-" * 80)
        
    except KeyboardInterrupt:
        print("\n\n👋 사용자가 중단했습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        


if __name__ == "__main__":
    main()
