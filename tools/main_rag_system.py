# ======================================================================================
# LangGraph 기반 개인화 혜택 추천 RAG 시스템 - 메인 클래스
# ======================================================================================
import json
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

# LangGraph imports
from langgraph.graph import StateGraph, END
#from langgraph.checkpoint.sqlite import SqliteSaver

# 로컬 imports
from tools.api_utils import PerplexityAPI, EmbeddingExecutor, PersonalizedScoreCalculator
from tools.rag_types import RAGState

# 기존 모듈들 (동일한 디렉토리에 있다고 가정)
from tools.multi_category_parser import MultiCategoryQueryParser
from tools.multi_category_dummy_data import MULTI_CATEGORY_DATA
from tools.user_history_data import create_sample_user_history


class LangGraphRAGSystem:
    """LangGraph 기반 RAG 시스템"""
    
    def __init__(self, db_path="./cafe_vector_db", collection_name="cafe_events"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.score_calculator = PersonalizedScoreCalculator()
        self.perplexity_api = PerplexityAPI()
        
        # 임베딩 API 설정
        api_key = 'Bearer nv-53f7a8c4abe74e20ab90446ed46ba79fvozJ'
        self.embedding_executor = EmbeddingExecutor(
            host='clovastudio.stream.ntruss.com',
            api_key=api_key,
            request_id='93ae6593a47d4437b634f2cbc5282896'
        )
        
        # DB 브랜드/카테고리 캐시
        self.available_brands: Set[str] = set()
        self.available_categories: Set[str] = set()
        self.db_metadata_loaded = False
        
        # LangGraph 초기화
        self.graph = self._build_graph()
        
    def connect_database(self) -> bool:
        """데이터베이스 연결"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ 데이터베이스가 없습니다: {self.db_path}")
                return False
            
            self.client = chromadb.PersistentClient(path=self.db_path)
            collections = self.client.list_collections()
            
            if collections:
                self.collection = collections[0]
                self.collection_name = collections[0].name
                self._load_database_metadata()
                print(f"✅ RAG DB 연결 성공 (총 {self.collection.count()}개 문서)")
                return True
            else:
                print("❌ 컬렉션이 없습니다")
                return False
                
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False

    def _load_database_metadata(self) -> None:
        """DB 메타데이터 로드"""
        try:
            all_results = self.collection.get(include=["metadatas"])
            
            if all_results and all_results.get('metadatas'):
                for metadata in all_results['metadatas']:
                    if metadata:
                        brand = metadata.get('brand')
                        category = metadata.get('category')
                        
                        if brand:
                            self.available_brands.add(brand.strip())
                        if category:
                            self.available_categories.add(category.strip())
                
                self.db_metadata_loaded = True
                print(f"✅ DB 메타데이터 로드 완료: 브랜드 {len(self.available_brands)}개, 카테고리 {len(self.available_categories)}개")
                
        except Exception as e:
            print(f"❌ DB 메타데이터 로드 오류: {e}")
            self.db_metadata_loaded = False

    # ======================================================================================
    # LangGraph 노드들
    # ======================================================================================
    
    def analyze_query_node(self, state: RAGState) -> RAGState:
        """쿼리 분석 노드"""
        query = state["query"]
        debug = state.get("debug", False)
        
        if debug:
            print(f"🔍 쿼리 분석 시작: {query}")
        
        # 쿼리 분석
        analysis = MultiCategoryQueryParser.analyze_query_intent(query)
        filters, parsed_info = MultiCategoryQueryParser.build_multi_category_filters(query, debug)
        
        # 브랜드/카테고리 추출
        extracted_brands = self._extract_brands_from_query(query, debug)
        extracted_categories = self._extract_categories_from_query(query, debug)
        
        # 개인화 요청 판단
        is_personalization = self._is_personalization_query(query)
        
        state.update({
            "query_analysis": analysis,
            "parsed_info": parsed_info,
            "filters": filters,
            "extracted_brands": extracted_brands,
            "extracted_categories": extracted_categories,
            "is_personalization": is_personalization,
            "next_action": "create_user_profile"
        })
        
        if debug:
            print(f"✅ 쿼리 분석 완료: 브랜드={extracted_brands}, 카테고리={extracted_categories}, 개인화={is_personalization}")
        
        return state

    def create_user_profile_node(self, state: RAGState) -> RAGState:
        """사용자 프로필 생성 노드"""
        user_history = state["user_history"]
        debug = state.get("debug", False)
        
        if debug:
            print("👤 사용자 프로필 생성 중...")
        
        user_profile = self.create_user_profile(user_history)
        
        state.update({
            "user_profile_data": user_profile,
            "next_action": "validate_query"
        })
        
        if debug:
            print(f"✅ 사용자 프로필 생성 완료: 총 소비 {user_profile['total_spending']:,.0f}원")
        
        return state

    def validate_query_node(self, state: RAGState) -> RAGState:
        """쿼리 검증 노드"""
        query = state["query"]
        analysis = state["query_analysis"]
        parsed_info = state["parsed_info"]
        extracted_brands = state["extracted_brands"]
        is_personalization = state["is_personalization"]
        debug = state.get("debug", False)
        
        if debug:
            print("🔧 쿼리 검증 시작...")
        
        validation_result = self._validate_query_improved(
            query, analysis, parsed_info, extracted_brands, is_personalization, debug
        )
        
        state.update({
            "validation_result": validation_result
        })
        
        if validation_result['valid']:
            state["next_action"] = "perform_direct_search"
            if debug:
                print("✅ 쿼리 검증 통과 - 검색 진행")
        else:
            state["next_action"] = "perform_perplexity_search"
            if debug:
                print("❌ 쿼리 검증 실패 - Perplexity 검색으로 전환")
        
        return state

    def perform_direct_search_node(self, state: RAGState) -> RAGState:
        """직접 검색 노드 (브랜드/카테고리)"""
        query = state["query"]
        extracted_brands = state["extracted_brands"]
        extracted_categories = state["extracted_categories"]
        debug = state.get("debug", False)
        
        if debug:
            print("🎯 직접 검색 시도...")
        
        results = []
        
        # 브랜드 우선 검색
        if extracted_brands:
            results = self._try_direct_brand_search(query, 10, debug)
            if results:
                if debug:
                    print(f"✅ 브랜드 직접 검색 성공: {len(results)}개")
                state.update({
                    "direct_search_results": results,
                    "next_action": "apply_personalization"
                })
                return state
        
        # 카테고리 검색
        if extracted_categories:
            results = self._try_direct_category_search(query, extracted_categories, 10, debug)
            if results:
                if debug:
                    print(f"✅ 카테고리 직접 검색 성공: {len(results)}개")
                state.update({
                    "direct_search_results": results,
                    "next_action": "apply_personalization"
                })
                return state
        
        # 직접 검색 실패
        state.update({
            "direct_search_results": [],
            "next_action": "perform_vector_search"
        })
        
        if debug:
            print("⚠️ 직접 검색 실패 - 벡터 검색으로 진행")
        
        return state

    def perform_vector_search_node(self, state: RAGState) -> RAGState:
        """벡터 검색 노드"""
        query = state["query"]
        filters = state["filters"]
        debug = state.get("debug", False)
        
        if debug:
            print("🔍 벡터 검색 시작...")
        
        try:
            # 임베딩 생성
            request_data = {"text": query}
            query_vector = self.embedding_executor.execute(request_data)
            
            if not query_vector:
                raise Exception("임베딩 생성 실패")
            
            # 벡터 정규화
            query_vector_array = np.array(query_vector)
            norm = np.linalg.norm(query_vector_array)
            if norm > 0:
                normalized_query_vector = (query_vector_array / norm).tolist()
            else:
                normalized_query_vector = query_vector
            
            # 벡터 검색 실행
            results = self.collection.query(
                query_embeddings=[normalized_query_vector],
                n_results=20,
                include=["metadatas", "distances", "documents"]
            )
            
            if results and results.get('ids') and results['ids'][0]:
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
                
                state.update({
                    "vector_search_results": formatted_results,
                    "next_action": "apply_personalization"
                })
                
                if debug:
                    print(f"✅ 벡터 검색 성공: {len(formatted_results)}개")
                
                return state
            else:
                raise Exception("벡터 검색 결과 없음")
                
        except Exception as e:
            if debug:
                print(f"❌ 벡터 검색 실패: {e}")
            
            state.update({
                "vector_search_results": [],
                "next_action": "perform_text_search"
            })
            
            return state

    def perform_text_search_node(self, state: RAGState) -> RAGState:
        """텍스트 폴백 검색 노드"""
        query = state["query"]
        filters = state["filters"]
        debug = state.get("debug", False)
        
        if debug:
            print("🔄 텍스트 폴백 검색 시작...")
        
        try:
            results = self._fallback_text_search(query, filters, 10, debug)
            
            if results:
                state.update({
                    "text_search_results": results,
                    "next_action": "apply_personalization"
                })
                
                if debug:
                    print(f"✅ 텍스트 검색 성공: {len(results)}개")
            else:
                state.update({
                    "text_search_results": [],
                    "next_action": "perform_perplexity_search"
                })
                
                if debug:
                    print("❌ 텍스트 검색도 실패 - Perplexity로 전환")
                    
        except Exception as e:
            if debug:
                print(f"❌ 텍스트 검색 오류: {e}")
            
            state.update({
                "text_search_results": [],
                "next_action": "perform_perplexity_search"
            })
        
        return state
    def perform_perplexity_search_node(self, state: RAGState) -> RAGState:
        """Perplexity 실시간 검색 노드 - JSON 형식으로 반환"""
        query = state["query"]
        debug = state.get("debug", False)
        
        if debug:
            print("🔗 Perplexity 실시간 JSON 검색 시작...")
        
        # Perplexity가 직접 분석하여 JSON 형식으로 답변하도록 프롬프트 수정
        search_query = f"""사용자 질문을 분석해서 관련된 브랜드를 찾아, 2025년 8월 현재 진행중인 최신 혜택 정보를 찾아줘.
        
        사용자 질문: "{query}"

        - 반드시 유효한 JSON 형식으로만 답변해야 해.
        - 다른 설명, 인사, 코드 블록(```json) 없이 순수한 JSON 내용만 출력해줘.
        - 만약 여러 브랜드 혜택을 찾으면, 가장 관련성 높은 혜택 하나만 JSON 객체로 만들어줘.
        - 정보가 없거나 질문과 관련 없는 내용이면 빈 JSON 객체 {{}}를 반환해.
        - 날짜가 지난 이벤트는 제외하고 현재 유효한 정보만 포함해줘.

        JSON 형식:
        {{
        "brand": "[브랜드명]",
        "eventName": "[이벤트나 프로모션 이름]",
        "benefit": "[할인율, 쿠폰 등 혜택 핵심 내용]",
        "period": "[시작일 ~ 종료일, 예: 2025-08-01 ~ 2025-08-31]"
        }}
        """
        
        # 최종적으로 state에 저장될 내용
        final_content = {}

        try:
            result = self.perplexity_api.search(search_query)
            
            if result.get('success'):
                raw_content = result.get('content', '{}')
                
                # Perplexity가 반환한 문자열을 JSON 객체로 파싱
                # LLM이 완벽한 JSON을 생성하지 못할 수 있으므로 예외 처리 필수
                try:
                    parsed_json = json.loads(raw_content)
                    # 성공적으로 파싱되면 해당 내용을 final_content로 사용
                    final_content = parsed_json
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시, 원본 텍스트를 포함한 에러 메시지 생성
                    final_content = {
                        "error": "Perplexity가 반환한 응답을 JSON으로 파싱하는데 실패했습니다.",
                        "raw_response": raw_content
                    }
            else:
                # API 호출 자체가 실패한 경우
                final_content = {
                    "error": "Perplexity API 검색에 실패했습니다.",
                    "details": result.get('error', 'Unknown error')
                }
        except Exception as e:
            # 그 외 예외 처리
            final_content = {
                "error": "Perplexity 검색 노드 실행 중 오류가 발생했습니다.",
                "details": str(e)
            }

        # 최종 결과를 보기 좋은 형태의 JSON 문자열로 변환
        response_str = json.dumps(final_content, ensure_ascii=False, indent=4)
        
        state.update({
            "perplexity_results": response_str, # 일관성을 위해 문자열 저장
            "response": response_str,
            "next_action": "end"
        })
        
        if debug:
            print("✅ Perplexity 검색 완료")
            
        return state
        

    def apply_personalization_node(self, state: RAGState) -> RAGState:
        """개인화 스코어링 노드"""
        user_profile = state["user_profile_data"]
        parsed_info = state["parsed_info"]
        debug = state.get("debug", False)
        
        # 검색 결과 통합
        all_results = []
        all_results.extend(state.get("direct_search_results", []))
        all_results.extend(state.get("vector_search_results", []))
        all_results.extend(state.get("text_search_results", []))
        
        if debug:
            print(f"🔄 개인화 스코어링: {len(all_results)}개 결과")
        
        if not all_results:
            state.update({
                "personalized_results": [],
                "next_action": "perform_perplexity_search"
            })
            return state
        
        # 개인화 스코어링 적용
        scored_results = self._apply_personalization_scoring_readonly(
            all_results, user_profile, parsed_info, debug
        )
        
        state.update({
            "personalized_results": scored_results,
            "next_action": "generate_final_results"
        })
        
        if debug:
            print(f"✅ 개인화 스코어링 완료: {len(scored_results)}개")
        
        return state

    def generate_final_results_node(self, state: RAGState) -> RAGState:
        """결과 생성 노드"""
        personalized_results = state["personalized_results"]
        user_profile = state["user_profile_data"]
        parsed_info = state["parsed_info"]
        debug = state.get("debug", False)
        
        if debug:
            print("📋 최종 결과 생성 중...")
        
        # 최종 순위 결정 및 결과 선택
        final_results = self._rank_and_select_results(
            personalized_results, user_profile, 5, debug
        )
        
        # 결과 출력 생성
        if final_results:
            response = self._generate_results_readonly(final_results, user_profile, parsed_info)
        else:
            response = "❌ 해당 조건에 맞는 혜택 정보가 없습니다."
            
        state.update({
            "final_results": final_results,
            "response": response,
            "next_action": "end"
        })
        
        if debug:
            print("✅ 최종 결과 생성 완료")
        
        return state

    # ======================================================================================
    # 라우팅 함수
    # ======================================================================================
    
    def route_next_action(self, state: RAGState) -> str:
        """다음 액션으로 라우팅"""
        next_action = state.get("next_action", "end")
        
        if next_action == "end":
            return END
        
        return next_action

    # ======================================================================================
    # 그래프 구성
    # ======================================================================================
    
    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        workflow = StateGraph(RAGState)
        
        # 노드 추가
        workflow.add_node("analyze_query", self.analyze_query_node)
        workflow.add_node("create_user_profile", self.create_user_profile_node)
        workflow.add_node("validate_query", self.validate_query_node)
        workflow.add_node("perform_direct_search", self.perform_direct_search_node)
        workflow.add_node("perform_vector_search", self.perform_vector_search_node)
        workflow.add_node("perform_text_search", self.perform_text_search_node)
        workflow.add_node("perform_perplexity_search", self.perform_perplexity_search_node)
        workflow.add_node("apply_personalization", self.apply_personalization_node)
        workflow.add_node("generate_final_results", self.generate_final_results_node)
        
        # 엣지 추가
        workflow.set_entry_point("analyze_query")
        
        workflow.add_conditional_edges(
            "analyze_query",
            self.route_next_action,
            {
                "create_user_profile": "create_user_profile",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "create_user_profile",
            self.route_next_action,
            {
                "validate_query": "validate_query",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "validate_query",
            self.route_next_action,
            {
                "perform_direct_search": "perform_direct_search",
                "perform_perplexity_search": "perform_perplexity_search",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "perform_direct_search",
            self.route_next_action,
            {
                "perform_vector_search": "perform_vector_search",
                "apply_personalization": "apply_personalization",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "perform_vector_search",
            self.route_next_action,
            {
                "perform_text_search": "perform_text_search",
                "apply_personalization": "apply_personalization",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "perform_text_search",
            self.route_next_action,
            {
                "perform_perplexity_search": "perform_perplexity_search",
                "apply_personalization": "apply_personalization",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "perform_perplexity_search",
            self.route_next_action,
            {
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "apply_personalization",
            self.route_next_action,
            {
                "generate_final_results": "generate_final_results",
                "perform_perplexity_search": "perform_perplexity_search",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "generate_final_results",
            self.route_next_action,
            {
                END: END
            }
        )
        
        return workflow.compile()

    # ======================================================================================
    # 기존 시스템의 헬퍼 메서드들
    # ======================================================================================
    
    def create_user_profile(self, user_spending_history: List[Dict]) -> Dict:
        """사용자 프로필 생성"""
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
            
            # 최근 브랜드
            if date >= recent_threshold:
                recency_weight = self._calculate_recency_weight(date, current_date)
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
        
        # 선호 카테고리 정렬
        profile['preferred_categories'] = sorted(
            profile['category_counts'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return dict(profile)

    def _calculate_recency_weight(self, spending_date: datetime, current_date: datetime) -> float:
        """최근성 가중치 계산"""
        days_diff = (current_date - spending_date).days
        if days_diff <= 7:
            return 1.0
        elif days_diff <= 30:
            return 0.8
        elif days_diff <= 90:
            return 0.5
        else:
            return 0.2

    def _extract_brands_from_query(self, query: str, debug: bool = False) -> List[str]:
        """쿼리에서 브랜드 추출"""
        found_brands = []
        
        known_brand_patterns = {
            '스타벅스': [r'스타벅스', r'starbucks'],
            '이디야': [r'이디야', r'ediya'],
            '투썸플레이스': [r'투썸', r'투썸플레이스', r'twosome'],
            '맥도날드': [r'맥도날드', r'맥날', r'mcdonald'],
            '버거킹': [r'버거킹', r'burgerking'],
            'KFC': [r'kfc', r'케이에프씨'],
            '이마트': [r'이마트', r'emart'],
            '홈플러스': [r'홈플러스', r'homeplus'],
            '롯데마트': [r'롯데마트', r'lotte'],
            '쿠팡': [r'쿠팡', r'coupang'],
            '지마켓': [r'지마켓', r'gmarket'],
            '11번가': [r'11번가', r'십일번가'],
            'GS25': [r'gs25', r'지에스'],
            'CU': [r'cu', r'씨유'],
            '세븐일레븐': [r'세븐일레븐', r'7-eleven', r'세븐'],
            '이마트24': [r'이마트24', r'이마트이십사'],
            '올리브영': [r'올리브영', r'oliveyoung'],
        }
        
        query_lower = query.lower()
        
        for brand_name, patterns in known_brand_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    found_brands.append(brand_name)
                    if debug:
                        print(f"   ✅ 브랜드 발견: '{brand_name}' (패턴: {pattern})")
                    break
        
        return list(set(found_brands))

    def _extract_categories_from_query(self, query: str, debug: bool = False) -> List[str]:
        """쿼리에서 카테고리 추출"""
        found_categories = []
        
        known_category_patterns = {
            '카페': [r'카페', r'커피', r'coffee', r'cafe', r'커피숍', r'아메리카노', r'라떼'],
            '마트': [r'마트', r'mart', r'슈퍼', r'대형마트', r'할인마트', r'쇼핑몰'],
            '편의점': [r'편의점', r'편의', r'컨비니', r'convenience'],
            '온라인쇼핑': [r'온라인', r'쇼핑', r'인터넷', r'online', r'shopping', r'배송'],
            '식당': [r'식당', r'음식점', r'레스토랑', r'restaurant', r'음식', r'치킨', r'버거'],
            '뷰티': [r'뷰티', r'화장품', r'미용', r'beauty', r'cosmetic', r'스킨케어'],
            '의료': [r'의료', r'약국', r'병원', r'pharmacy', r'medical', r'건강'],
            '교통': [r'교통', r'지하철', r'버스', r'택시', r'전철', r'대중교통']
        }
        
        query_lower = query.lower()
        
        for category_name, patterns in known_category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    found_categories.append(category_name)
                    if debug:
                        print(f"   ✅ 카테고리 발견: '{category_name}' (패턴: {pattern})")
                    break
        
        return list(set(found_categories))

    def _is_personalization_query(self, query: str) -> bool:
        """개인화 요청인지 판단"""
        personalization_patterns = [
            r'내\s*소비.*패턴', r'내.*맞는', r'나.*맞는', r'우리.*맞는',
            r'개인화.*추천', r'맞춤.*추천', r'맞춤형.*혜택',
            r'지난.*소비', r'최근.*소비', r'저번.*소비',
            r'지난주.*썼', r'저번주.*썼', r'최근.*썼',
            r'내가.*자주', r'내가.*많이', r'내가.*주로',
            r'패턴.*기반', r'이력.*기반', r'히스토리.*기반'
        ]
        
        for pattern in personalization_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False

    def _validate_query_improved(self, query: str, analysis: Dict, parsed_info: Dict, 
                            extracted_brands: List[str], is_personalization: bool, debug: bool) -> Dict[str, Any]:
        """개선된 쿼리 검증"""
        if debug:
            print("🔧 개선된 쿼리 검증 시작...")
        
        # 개인화 요청이면 무조건 통과
        if is_personalization:
            if debug:
                print("   ✅ 개인화 요청으로 인식 - 검색 진행")
            return {'valid': True}
        
        # 브랜드가 추출되었는지 확인
        if extracted_brands:
            brand_existence = self._check_brand_existence(extracted_brands, debug)
            missing_brands = [brand for brand, exists in brand_existence.items() if not exists]
            
            if missing_brands and len(missing_brands) == len(extracted_brands):
                if debug:
                    print(f"   ❌ 추출된 모든 브랜드 '{', '.join(missing_brands)}'가 DB에 없음")
                return {
                    'valid': False,
                    'message': f"브랜드 '{', '.join(missing_brands)}'에 대한 정보를 실시간으로 검색합니다."
                }
        else:
            # 브랜드가 추출되지 않았지만 특정 제품명이 포함된 경우 체크
            unknown_product_patterns = [r'애플워치', r'아이폰', r'갤럭시', r'맥북', r'아이패드']
            for pattern in unknown_product_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    if debug:
                        print(f"   ❌ 알려지지 않은 제품 '{pattern}' 감지")
                    return {
                        'valid': False,
                        'message': f"'{pattern}'에 대한 정보를 실시간으로 검색합니다."
                    }
        
        # 기본적으로 통과
        return {'valid': True}

    def _check_brand_existence(self, brands: List[str], debug: bool = False) -> Dict[str, bool]:
        """브랜드 존재 여부 확인"""
        if not self.db_metadata_loaded:
            return {brand: True for brand in brands}
        
        result = {}
        for brand in brands:
            exists = brand in self.available_brands or any(
                brand.lower() in available_brand.lower() or 
                available_brand.lower() in brand.lower()
                for available_brand in self.available_brands
            )
            result[brand] = exists
            
            if debug:
                status = "✅ 존재" if exists else "❌ 없음"
                print(f"   🔍 '{brand}': {status}")
        
        return result

    def _try_direct_brand_search(self, query: str, top_k: int, debug: bool = False) -> List[Dict]:
        """브랜드 기반 직접 검색"""
        try:
            extracted_brands = self._extract_brands_from_query(query, debug)
            
            if not extracted_brands:
                return []
            
            all_results = []
            
            for brand in extracted_brands:
                try:
                    brand_results = self.collection.get(
                        where={"brand": {"$eq": brand}},
                        include=["metadatas", "documents"]
                    )
                    
                    if brand_results and brand_results.get('metadatas'):
                        for i, metadata in enumerate(brand_results['metadatas']):
                            if self._validate_result(metadata, datetime.now()):
                                all_results.append({
                                    "id": f"direct_{brand}_{i}",
                                    "metadata": metadata,
                                    "distance": 0.0,
                                    "document": brand_results['documents'][i] if brand_results.get('documents') else "",
                                    "vector_rank": i + 1
                                })
                except Exception as e:
                    if debug:
                        print(f"   '{brand}' 검색 실패: {e}")
                    continue
            
            return all_results[:top_k]
            
        except Exception as e:
            if debug:
                print(f"❌ 직접 브랜드 검색 오류: {e}")
            return []

    def _try_direct_category_search(self, query: str, categories: List[str], top_k: int, debug: bool = False) -> List[Dict]:
        """카테고리 기반 직접 검색"""
        try:
            all_results = []
            
            for category in categories:
                try:
                    category_results = self.collection.get(
                        where={"category": {"$eq": category}},
                        include=["metadatas", "documents"]
                    )
                    
                    if category_results and category_results.get('metadatas'):
                        for i, metadata in enumerate(category_results['metadatas']):
                            if self._validate_result(metadata, datetime.now()):
                                all_results.append({
                                    "id": f"direct_cat_{category}_{i}",
                                    "metadata": metadata,
                                    "distance": 0.0,
                                    "document": category_results['documents'][i] if category_results.get('documents') else "",
                                    "vector_rank": i + 1
                                })
                except Exception as e:
                    if debug:
                        print(f"   '{category}' 검색 실패: {e}")
                    continue
            
            return all_results[:top_k]
            
        except Exception as e:
            if debug:
                print(f"❌ 직접 카테고리 검색 오류: {e}")
            return []

    def _fallback_text_search(self, query: str, filters: Dict, top_k: int, debug: bool = False) -> List[Dict]:
        """텍스트 기반 폴백 검색"""
        try:
            all_results = self.collection.get(include=["metadatas", "documents"])
            
            if not all_results or not all_results.get('metadatas'):
                return []
            
            scored_results = []
            query_lower = query.lower()
            query_words = query_lower.split()
            
            for i, metadata in enumerate(all_results['metadatas']):
                if not metadata or not self._validate_result(metadata, datetime.now()):
                    continue
                
                score = 0.0
                
                # 브랜드 매칭 (60%)
                brand = metadata.get('brand', '').lower()
                if brand and brand in query_lower:
                    score += 0.6
                elif brand and any(word in brand for word in query_words):
                    score += 0.4
                
                # 카테고리 매칭 (20%)
                category = metadata.get('category', '').lower()
                if category and category in query_lower:
                    score += 0.2
                
                # 제목 매칭 (15%)
                title = metadata.get('title', '').lower()
                if title:
                    matching_words = sum(1 for word in query_words if word in title)
                    score += 0.15 * (matching_words / len(query_words) if query_words else 0)
                
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
                        "distance": 1.0 - score,
                        "document": all_results['documents'][i] if all_results.get('documents') else "",
                        "vector_rank": 0,
                        "text_score": score
                    })
            
            scored_results.sort(key=lambda x: x['text_score'], reverse=True)
            return scored_results[:top_k]
            
        except Exception as e:
            if debug:
                print(f"❌ 텍스트 검색 오류: {e}")
            return []

    def _apply_personalization_scoring_readonly(self, results: List[Dict], user_profile: Dict, 
                                              parsed_info: Dict, debug: bool) -> List[Dict]:
        """개인화 스코어링"""
        if not results:
            return []
        
        scored_results = []
        current_date = datetime.now()
        all_distances = [result.get('distance', 0) for result in results]
        
        for result in results:
            try:
                metadata = result.get('metadata', {})
                
                if not self._validate_result(metadata, current_date):
                    continue
                
                # 기본 벡터 점수
                vector_score = self.calculate_vector_similarity_universal(
                    result.get('distance', 0), all_distances
                )
                
                # 개인화 점수 (간단 버전)
                personalized_score = vector_score * 0.8 + 0.2
                
                result['personalized_score'] = personalized_score
                result['vector_score'] = vector_score
                
                scored_results.append(result)
                
            except Exception as e:
                if debug:
                    print(f"      ❌ 스코어링 오류: {e}")
                continue
        
        return scored_results

    def calculate_vector_similarity_universal(self, distance: float, all_distances: List[float] = None) -> float:
        """만능 벡터 유사도 계산"""
        # 음수 거리값 처리 (IP 방식)
        if distance < 0:
            if all_distances:
                min_dist = min(all_distances)
                max_dist = max(all_distances)
                range_dist = max_dist - min_dist
                
                if range_dist > 0:
                    relative_pos = (distance - min_dist) / range_dist
                    similarity = 1 - relative_pos
                else:
                    similarity = 0.5
            else:
                normalized = max(0, min(1, (distance + 1000) / 200))
                similarity = normalized
        else:
            # 양수 거리값 처리
            similarity = max(0, 1 - distance)
        
        return max(0, min(similarity, 1))

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
        
        try:
            sorted_results = sorted(results, key=lambda x: x.get('personalized_score', 0), reverse=True)
        except Exception as e:
            return results[:top_k]
        
        return sorted_results[:top_k]

    def _generate_results_readonly(self, results: List[Dict], user_profile: Dict, parsed_info: Dict = None) -> str:
        """검색 결과 생성 - JSON 형식으로 이벤트 기간 포함"""
        if not results:
            # 결과가 없을 때 빈 JSON 배열을 반환합니다.
            return json.dumps([], ensure_ascii=False, indent=4)
        
        try:
            # 최종 결과를 담을 리스트를 생성합니다.
            output_results = []
            
            for result in results[:5]:
                metadata = result.get('metadata', {})
                score = result.get('personalized_score', 0)
                
                # 1. 혜택 내용 요약 생성
                benefit_type = metadata.get('benefit_type', 'Unknown')
                discount_rate = metadata.get('discount_rate', 0)
                conditions = metadata.get('conditions', '조건 없음')
                
                try:
                    discount_rate_float = float(discount_rate) if discount_rate else 0
                except ValueError:
                    discount_rate_float = 0

                benefit_summary = f"{benefit_type}"
                if benefit_type == "할인" and discount_rate_float > 0:
                    benefit_summary = f"{discount_rate_float}% 할인"
                elif benefit_type == "적립" and discount_rate_float > 0:
                    benefit_summary = f"{discount_rate_float}배 적립"
                
                if conditions != '조건 없음':
                    benefit_summary += f" ({conditions})"

                # 2. 이벤트 기간 문자열 생성
                valid_from = metadata.get('valid_from', '')
                valid_to = metadata.get('valid_to', '')
                
                if valid_from and valid_to:
                    event_period = f"{valid_from} ~ {valid_to}"
                elif valid_to:
                    event_period = f"~ {valid_to}까지"
                elif valid_from:
                    event_period = f"{valid_from}부터"
                else:
                    event_period = "상시 진행"

                # 3. 고객 타입 문자열 생성
                brand = metadata.get('brand', 'Unknown')
                customer_type_map = {
                    "스타벅스": "카공/업무용 선호 고객",
                    "이디야": "가성비 중시 고객",
                    "맥도날드": "편의성 중시 고객",
                    "이마트": "대용량 구매 선호 고객",
                    "GS25": "접근성 중시 고객",
                    "올리브영": "뷰티/케어 관심 고객"
                }
                customer_type = customer_type_map.get(brand, "일반 고객")

                # 4. JSON 객체로 만들 정보를 딕셔너리에 담습니다.
                item_info = {
                    "brand": brand,
                    "event_name": metadata.get('title', 'Unknown'),
                    "benefit": benefit_summary,
                    "period": event_period,
                    "recommended_for": customer_type,
                    "suitability": f"{score*100:.0f}%"
                }
                
                # 리스트에 딕셔너리를 추가합니다.
                output_results.append(item_info)
                
            # 최종적으로 리스트를 JSON 문자열로 변환하여 반환합니다.
            # ensure_ascii=False는 한글이 깨지지 않게 합니다.
            # indent=4는 가독성을 위해 JSON을 예쁘게 포맷팅합니다.
            return json.dumps(output_results, ensure_ascii=False, indent=4)
            
        except Exception as e:
            # 오류 발생 시 에러 정보를 담은 JSON을 반환합니다.
            error_message = {
                "error": "결과를 생성하는 중 오류가 발생했습니다.",
                "details": str(e)
            }
            return json.dumps(error_message, ensure_ascii=False, indent=4)

    # ======================================================================================
    # 메인 실행 함수
    # ======================================================================================
    
    def run(self, query: str, user_history: List[Dict] = None, debug: bool = False) -> str:
        """RAG 시스템 실행"""
        if user_history is None:
            user_history = create_sample_user_history()
        
        # 초기 상태 설정
        initial_state: RAGState = {
            "query": query,
            "user_history": user_history,
            "debug": debug,
            
            # 초기화할 필드들
            "query_analysis": {},
            "parsed_info": {},
            "filters": {},
            "user_profile_data": {},
            "extracted_brands": [],
            "extracted_categories": [],
            "is_personalization": False,
            "validation_result": {},
            "direct_search_results": [],
            "vector_search_results": [],
            "text_search_results": [],
            "perplexity_results": "",
            "personalized_results": [],
            "final_results": [],
            "response": "",
            "next_action": "",
            "error_message": ""
        }
        
        try:
            # 그래프 실행
            final_state = self.graph.invoke(initial_state)
            return final_state["response"]
            
        except Exception as e:
            return f"❌ 시스템 오류: {e}"


# ======================================================================================
# 사용 예시
# ======================================================================================

def main():
    """메인 실행 함수"""
    print("🎯 LangGraph 기반 개인화 혜택 추천 RAG 시스템")
    print("=" * 80)
    
    # RAG 시스템 초기화
    rag = LangGraphRAGSystem()
    
    # 데이터베이스 연결
    if not rag.connect_database():
        print("❌ 데이터베이스 연결 실패. 더미 데이터로 테스트합니다.")
    
    # 테스트 쿼리들
    test_queries = [
        "스타벅스 할인 혜택 있어?",
        "내 소비 패턴에 맞는 혜택 추천해줘",
        "카페 할인 이벤트 궁금해",
        "애플워치 할인",  # DB에 없음 -> Perplexity
        "편의점 쿠폰 있나?"
    ]
    
    print("\n🧪 자동 테스트 시작...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}] {query}")
        print("-" * 50)
        
        try:
            result = rag.run(query, debug=False)
            print(f"📋 결과:\n{result}")
        except Exception as e:
            print(f"❌ 오류: {e}")
        
        print("-" * 50)
    
    print("\n✅ 자동 테스트 완료")
    
    # 대화형 모드
    print("\n💬 대화형 모드 시작 (종료: 'quit')")
    
    while True:
        try:
            query = input("\n🔧 질문: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 서비스를 종료합니다.")
                break
            
            if not query:
                continue
            
            print("\n⏳ LangGraph RAG 검색 중...")
            result = rag.run(query, debug=True)
            print(f"\n🔗 추천 결과:\n{result}")
            
        except KeyboardInterrupt:
            print("\n\n👋 사용자가 중단했습니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
