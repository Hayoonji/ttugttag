# ======================================================================================
# API 및 유틸리티 클래스들
# ======================================================================================

import json
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict


class PerplexityAPI:
    """Perplexity API 클래스"""
    def __init__(self, api_key=None):
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.api_key = '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'
        
    def search(self, query, model="sonar", max_tokens=2000):
        """실시간 검색 수행"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Perplexity API 키가 설정되지 않았습니다.'
            }
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "sonar",
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
                    'model': "sonar"
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