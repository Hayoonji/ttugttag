# ======================================================================================
# RAG 시스템 상태 및 타입 정의
# ======================================================================================

from typing import List, Dict, Any, TypedDict


class RAGState(TypedDict):
    """RAG 시스템의 상태 정의"""
    # 입력
    query: str
    user_history: List[Dict]
    debug: bool
    
    # 분석 결과
    query_analysis: Dict[str, Any]
    parsed_info: Dict[str, Any]
    filters: Dict[str, Any]
    user_profile_data: Dict[str, Any]
    
    # 검색 관련
    extracted_brands: List[str]
    extracted_categories: List[str]
    is_personalization: bool
    validation_result: Dict[str, Any]
    
    # 검색 결과
    direct_search_results: List[Dict]
    vector_search_results: List[Dict]
    text_search_results: List[Dict]
    perplexity_results: str
    
    # 최종 결과
    personalized_results: List[Dict]
    final_results: List[Dict]
    response: str
    
    # 플로우 제어
    next_action: str
    error_message: str