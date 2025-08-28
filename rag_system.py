# ======================================================================================
# EC2 서버용 개인화된 RAG 시스템 - rag_system.py
# ======================================================================================

import json
import requests
import chromadb
import os
import re
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
import math
from collections import defaultdict

from config import EC2Config, get_ec2_config

# 로깅 설정
logger = logging.getLogger(__name__)

# ======================================================================================
# 개인화 점수 계산기 (EC2 최적화)
# ======================================================================================

class EC2ScoreCalculator:
    """EC2용 점수 계산기"""
    
    @staticmethod
    def calculate_preference_score(brand: str, category: str, user_history: Dict) -> float:
        """사용자 선호도 점수 계산"""
        score = 0.0
        
        # 브랜드 선호도 (최대 0.6점)
        if brand in user_history.get('brand_counts', {}):
            brand_count = user_history['brand_counts'][brand]
            total_transactions = user_history.get('total_transactions', 1)
            brand_preference = min(brand_count / total_transactions, 0.6)
            score += brand_preference
        
        # 카테고리 선호도 (최대 0.4점)
        category_prefs = dict(user_history.get('preferred_categories', []))
        if category in category_prefs:
            category_count = category_prefs[category]
            total_transactions = user_history.get('total_transactions', 1)
            category_preference = min(category_count / total_transactions, 0.4)
            score += category_preference
        
        return min(score, 1.0)
    
    @staticmethod
    def calculate_potential_savings(benefit_type: str, discount_rate: float, 
                                  user_avg_spending: float) -> float:
        """절약 가능 금액 계산"""
        if benefit_type == "할인":
            return user_avg_spending * (discount_rate / 100)
        elif benefit_type == "적립":
            return user_avg_spending * (discount_rate / 100) * 0.5  # 적립은 할인의 절반 가치
        else:
            return user_avg_spending * 0.05  # 기본 5% 가치
    
    @staticmethod
    def calculate_recency_weight(spending_date: str, current_date: datetime = None) -> float:
        """최근성 가중치 계산"""
        if current_date is None:
            current_date = datetime.now()
        
        try:
            if isinstance(spending_date, str):
                date = datetime.fromisoformat(spending_date.replace('Z', '+00:00'))
            else:
                date = spending_date
            
            days_diff = (current_date - date).days
            
            if days_diff <= 7:
                return 1.0  # 최근 1주일: 최대 가중치
            elif days_diff <= 30:
                return 0.8  # 최근 1개월: 높은 가중치
            elif days_diff <= 90:
                return 0.5  # 최근 3개월: 중간 가중치
            else:
                return 0.2  # 3개월 이상: 낮은 가중치
                
        except Exception as e:
            logger.error(f"최근성 가중치 계산 오류: {e}")
            return 0.2

# ======================================================================================
# EC2 최적화된 RAG 시스템
# ======================================================================================

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
    
    def search_personalized_benefits(self, query: str, user_profile: Dict, 
                                   top_k: int = 10, debug: bool = False) -> str:
        """개인화된 혜택 검색 (간소화 버전)"""
        try:
            logger.info(f"🔍 혜택 검색 시작: {query}")
            
            # 간단한 텍스트 검색 수행
            if not self.collection:
                return "❌ 데이터베이스가 연결되지 않았습니다."
            
            # ChromaDB 검색
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, 10),
                include=["metadatas", "distances", "documents"]
            )
            
            if not results['ids'][0]:
                return f"'{query}'와 관련된 혜택을 찾지 못했습니다. 다른 키워드로 검색해보세요."
            
            # 결과 포맷팅
            formatted_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                # 개인화 점수 계산
                personalization_score = self.score_calculator.calculate_preference_score(
                    metadata.get('brand', ''), 
                    metadata.get('category', ''), 
                    user_profile
                )
                
                formatted_results.append({
                    "metadata": metadata,
                    "distance": distance,
                    "personalization_score": personalization_score,
                    "final_score": (1 - distance) * 0.7 + personalization_score * 0.3
                })
            
            # 최종 점수로 정렬
            formatted_results.sort(key=lambda x: x["final_score"], reverse=True)
            
            # 응답 생성
            return self._generate_response(formatted_results[:top_k], user_profile, query)
            
        except Exception as e:
            logger.error(f"검색 오류: {e}")
            return f"검색 중 오류가 발생했습니다: {str(e)}"
    
    def _generate_response(self, results: List[Dict], user_profile: Dict, query: str) -> str:
        """검색 결과 응답 생성"""
        if not results:
            return f"'{query}'와 관련된 혜택을 찾지 못했습니다."
        
        # 사용자 정보 요약
        total_spending = user_profile.get('total_spending', 0)
        total_transactions = user_profile.get('total_transactions', 0)
        top_brands = dict(list(sorted(user_profile.get('brand_counts', {}).items(), 
                                    key=lambda x: x[1], reverse=True))[:3])
        
        response = f"💡 **개인화된 혜택 추천** ('{query}' 검색 결과)\n\n"
        response += f"👤 **고객님 프로필**: 총 {total_spending:,.0f}원 ({total_transactions}건 이용)\n"
        if top_brands:
            response += f"⭐ **주요 이용 브랜드**: {', '.join(top_brands.keys())}\n\n"
        response += "🎯 **맞춤 혜택 목록**:\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            personalization_score = result['personalization_score']
            
            response += f"{i}. **{metadata.get('title', '혜택')}**\n"
            response += f"   🏪 브랜드: {metadata.get('brand', '알 수 없음')} | 📂 카테고리: {metadata.get('category', '알 수 없음')}\n"
            response += f"   💰 혜택: {metadata.get('benefit_type', '혜택')} ({metadata.get('discount_rate', '상세 확인')})\n"
            
            if metadata.get('conditions'):
                response += f"   📋 조건: {metadata['conditions']}\n"
            
            if personalization_score > 0.5:
                response += f"   ⭐ **고객님께 특히 추천!** (개인화 점수: {personalization_score:.1f})\n"
            
            if metadata.get('valid_from') and metadata.get('valid_to'):
                response += f"   📅 유효기간: {metadata['valid_from']} ~ {metadata['valid_to']}\n"
            
            response += "\n"
        
        # 추가 제안
        response += "💡 **추가 팁**:\n"
        response += "- 자주 이용하시는 브랜드의 멤버십 가입을 고려해보세요\n"
        response += "- 결제 방법을 바꾸면 더 많은 혜택을 받을 수 있어요\n"
        
        return response
    
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
                    logger.debug(f"브랜드 '{brand}': {count}개 결과")
        
        except Exception as e:
            logger.error(f"브랜드 검색 오류: {e}")
        
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
            
            if debug:
                logger.debug(f"벡터 검색: {len(vector_results)}개 결과")
            
            return vector_results
            
        except Exception as e:
            logger.error(f"벡터 검색 오류: {e}")
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
            logger.error(f"개인화 적용 오류: {e}")
        
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
            logger.error(f"결과 검증 오류: {e}")
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
            logger.error(f"결과 정리 오류: {e}")
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

# ======================================================================================
# EC2 전용 헬퍼 함수들
# ======================================================================================

def create_user_profile_from_history(spending_history: List[Dict]) -> Dict[str, Any]:
    """소비 이력에서 사용자 프로필 생성"""
    try:
        brand_counts = defaultdict(int)
        category_counts = defaultdict(int)
        total_spending = defaultdict(float)
        recent_transactions = []
        
        current_date = datetime.now()
        
        for transaction in spending_history:
            brand = transaction.get('brand', '')
            category = transaction.get('category', '')
            amount = float(transaction.get('amount', 0))
            date_str = transaction.get('date', '')
            
            if brand:
                brand_counts[brand] += 1
                total_spending[brand] += amount
            
            if category:
                category_counts[category] += 1
            
            # 최근 90일 이내 거래만 포함
            try:
                transaction_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if (current_date - transaction_date).days <= 90:
                    recent_transactions.append(transaction)
            except:
                pass
        
        # 평균 소비액 계산
        average_spending = {}
        for category in category_counts:
            category_transactions = [t for t in spending_history if t.get('category') == category]
            if category_transactions:
                avg = sum(float(t.get('amount', 0)) for t in category_transactions) / len(category_transactions)
                average_spending[category] = avg
        
        profile = {
            'brand_counts': dict(brand_counts),
            'category_counts': dict(category_counts),
            'total_transactions': len(spending_history),
            'average_spending': average_spending,
            'recent_transactions': recent_transactions,
            'preferred_brands': sorted(brand_counts.keys(), key=brand_counts.get, reverse=True)[:5],
            'preferred_categories': sorted(category_counts.keys(), key=category_counts.get, reverse=True)[:3],
            'total_amount': sum(float(t.get('amount', 0)) for t in spending_history),
            'profile_created_at': datetime.now().isoformat()
        }
        
        logger.debug(f"사용자 프로필 생성 완료: {profile['total_transactions']}건 거래, {len(profile['preferred_brands'])}개 선호 브랜드")
        
        return profile
        
    except Exception as e:
        logger.error(f"사용자 프로필 생성 오류: {e}")
        return {
            'brand_counts': {},
            'category_counts': {},
            'total_transactions': 0,
            'average_spending': {},
            'recent_transactions': [],
            'preferred_brands': [],
            'preferred_categories': [],
            'error': str(e)
        }


# ======================================================================================
# 웹 검색 보완 기능을 위한 메서드 확장
# ======================================================================================

# EC2PersonalizedRAG 클래스에 웹 검색 메서드 추가
def _supplement_with_web_search(self, query: str, categories: List[str], brands: List[str], needed: int) -> List[Dict]:
    """웹 검색을 통한 결과 보완"""
    try:
        web_results = []
        
        # 웹 검색 키워드 준비
        search_keywords = self._prepare_web_search_keywords(query, categories, brands)
        
        logger.info(f"🔍 웹 검색 키워드: {search_keywords}")
        
        # 네이버 검색 API 사용
        for keyword in search_keywords[:2]:  # 최대 2개 키워드로 제한
            try:
                naver_results = self._search_naver_api(keyword, min(needed, 3))
                processed_results = self._process_web_search_results(naver_results, keyword)
                web_results.extend(processed_results)
                
                if len(web_results) >= needed:
                    break
                    
            except Exception as e:
                logger.warning(f"네이버 검색 실패: {e}")
                continue
        
        # 결과가 부족하면 일반 검색 시도
        if len(web_results) < needed:
            try:
                generic_results = self._generic_web_search(query, needed - len(web_results))
                web_results.extend(generic_results)
            except Exception as e:
                logger.warning(f"일반 웹 검색 실패: {e}")
        
        logger.info(f"🌐 웹 검색 완료: {len(web_results)}개 결과 획득")
        return web_results[:needed]
        
    except Exception as e:
        logger.error(f"웹 검색 보완 오류: {e}")
        return []

def _prepare_web_search_keywords(self, query: str, categories: List[str], brands: List[str]) -> List[str]:
    """웹 검색용 키워드 준비"""
    keywords = []
    
    # 기본 쿼리에 "혜택" 추가
    base_query = f"{query} 혜택"
    keywords.append(base_query)
    
    # 카테고리 + 혜택 조합
    for category in categories:
        keywords.append(f"{category} 할인 혜택")
        keywords.append(f"{category} 쿠폰")
    
    # 브랜드 + 혜택 조합
    for brand in brands:
        keywords.append(f"{brand} 혜택")
        keywords.append(f"{brand} 할인")
    
    # 중복 제거
    return list(dict.fromkeys(keywords))

def _search_naver_api(self, keyword: str, count: int = 3) -> List[Dict]:
    """네이버 검색 API 호출"""
    try:
        # API 키 확인
        client_id = os.getenv('NAVER_CLIENT_ID')
        client_secret = os.getenv('NAVER_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.warning("네이버 API 키가 설정되지 않음")
            return []
        
        # 검색 요청
        import urllib.parse
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://openapi.naver.com/v1/search/webkr.json?query={encoded_keyword}&display={count}"
        
        headers = {
            'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret': client_secret
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        else:
            logger.warning(f"네이버 API 오류: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"네이버 API 호출 오류: {e}")
        return []

def _process_web_search_results(self, naver_results: List[Dict], keyword: str) -> List[Dict]:
    """네이버 검색 결과를 RAG 형식으로 변환"""
    processed = []
    
    for i, item in enumerate(naver_results):
        try:
            # HTML 태그 제거
            import re
            title = re.sub(r'<[^>]+>', '', item.get('title', ''))
            description = re.sub(r'<[^>]+>', '', item.get('description', ''))
            
            # RAG 형식으로 변환
            result = {
                "id": f"web_{keyword}_{i}",
                "metadata": {
                    "title": title,
                    "brand": self._extract_brand_from_text(title + " " + description),
                    "category": self._extract_category_from_text(title + " " + description),
                    "benefit_type": "웹검색",
                    "discount_rate": "상세정보 확인 필요",
                    "conditions": "웹사이트 확인 필요",
                    "valid_from": datetime.now().strftime("%Y-%m-%d"),
                    "valid_to": "상세정보 확인 필요",
                    "source": "웹검색",
                    "url": item.get('link', ''),
                    "search_keyword": keyword
                },
                "document": f"{title}. {description}",
                "similarity_score": 0.7,  # 웹 검색 결과는 중간 점수
                "search_type": "web_search"
            }
            
            processed.append(result)
            
        except Exception as e:
            logger.warning(f"웹 검색 결과 처리 오류: {e}")
            continue
    
    return processed

def _extract_brand_from_text(self, text: str) -> str:
    """텍스트에서 브랜드 추출"""
    text_lower = text.lower()
    
    # 알려진 브랜드들 확인
    known_brands = [
        '스타벅스', '이디야', '투썸플레이스', '할리스', '컴포즈커피',
        '맥도날드', '버거킹', 'kfc', '롯데리아', '맘스터치',
        '이마트', '홈플러스', '롯데마트', '코스트코', 'gs25', 'cu'
    ]
    
    for brand in known_brands:
        if brand.lower() in text_lower:
            return brand
    
    return "기타"

def _extract_category_from_text(self, text: str) -> str:
    """텍스트에서 카테고리 추출"""
    text_lower = text.lower()
    
    for category, keywords in EC2Config.CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return category
    
    return "기타"

def _generic_web_search(self, query: str, needed: int) -> List[Dict]:
    """일반 웹 검색 (네이버 API 실패 시 대안)"""
    try:
        # 간단한 검색 결과 생성 (실제 웹 스크래핑 대신)
        generic_results = []
        
        search_terms = [
            f"{query} 할인 혜택",
            f"{query} 쿠폰",
            f"{query} 적립"
        ]
        
        for i, term in enumerate(search_terms[:needed]):
            result = {
                "id": f"generic_web_{i}",
                "metadata": {
                    "title": f"{term} 관련 혜택",
                    "brand": "기타",
                    "category": "기타", 
                    "benefit_type": "웹검색",
                    "discount_rate": "검색 결과 확인 필요",
                    "conditions": "각 업체별 상이",
                    "valid_from": datetime.now().strftime("%Y-%m-%d"),
                    "valid_to": "업체별 상이",
                    "source": "일반검색",
                    "search_keyword": term
                },
                "document": f"{term}에 대한 최신 정보를 확인해보세요. 다양한 혜택이 제공될 수 있습니다.",
                "similarity_score": 0.5,
                "search_type": "generic_web"
            }
            generic_results.append(result)
        
        return generic_results
        
    except Exception as e:
        logger.error(f"일반 웹 검색 오류: {e}")
        return []

# ======================================================================================
# 사용자 프로필 생성 함수
# ======================================================================================

def create_user_profile_from_history(spending_history: List[Dict]) -> Dict[str, Any]:
    """사용자 소비 이력으로부터 프로필 생성"""
    from collections import defaultdict
    
    profile = {
        'brand_counts': defaultdict(int),
        'category_counts': defaultdict(int),
        'brand_spending': defaultdict(float),
        'category_spending': defaultdict(float),
        'total_transactions': 0,
        'total_spending': 0.0,
        'recent_brands': [],
        'preferred_categories': [],
        'avg_spending_per_brand': {},
        'spending_timeline': []
    }
    
    current_date = datetime.now()
    recent_threshold = current_date - timedelta(days=7)
    
    for transaction in spending_history:
        brand = transaction['brand']
        category = transaction.get('category', 'Unknown')
        amount = transaction['amount']
        date = transaction['date']
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        # 기본 통계
        profile['brand_counts'][brand] += 1
        profile['category_counts'][category] += 1
        profile['brand_spending'][brand] += amount
        profile['category_spending'][category] += amount
        profile['total_transactions'] += 1
        profile['total_spending'] += amount
        
        # 최근 브랜드
        if date >= recent_threshold:
            profile['recent_brands'].append({
                'brand': brand,
                'category': category,
                'amount': amount,
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
    
    # 선호 카테고리 정렬
    profile['preferred_categories'] = sorted(
        profile['category_counts'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return dict(profile)

def create_sample_user_history() -> List[Dict]:
    """샘플 사용자 소비 이력 생성"""
    from datetime import datetime, timedelta
    
    return [
        {"brand": "스타벅스", "category": "카페", "amount": 50000, "date": datetime.now() - timedelta(days=3)},
        {"brand": "이마트", "category": "마트", "amount": 150000, "date": datetime.now() - timedelta(days=5)},
        {"brand": "쿠팡", "category": "온라인쇼핑", "amount": 80000, "date": datetime.now() - timedelta(days=6)},
        {"brand": "스타벅스", "category": "카페", "amount": 35000, "date": datetime.now() - timedelta(days=15)},
        {"brand": "GS25", "category": "편의점", "amount": 25000, "date": datetime.now() - timedelta(days=18)},
        {"brand": "이디야", "category": "카페", "amount": 28000, "date": datetime.now() - timedelta(days=20)},
        {"brand": "홈플러스", "category": "마트", "amount": 120000, "date": datetime.now() - timedelta(days=25)},
    ]

# 메서드를 클래스에 바인딩
EC2PersonalizedRAG._supplement_with_web_search = _supplement_with_web_search
EC2PersonalizedRAG._prepare_web_search_keywords = _prepare_web_search_keywords
EC2PersonalizedRAG._search_naver_api = _search_naver_api
EC2PersonalizedRAG._process_web_search_results = _process_web_search_results
EC2PersonalizedRAG._extract_brand_from_text = _extract_brand_from_text
EC2PersonalizedRAG._extract_category_from_text = _extract_category_from_text
EC2PersonalizedRAG._generic_web_search = _generic_web_search
