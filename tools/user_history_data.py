# ======================================================================================
# 사용자 이용내역 데이터 (user_history_data.py)
# ======================================================================================

from datetime import datetime, timedelta
from typing import List, Dict

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