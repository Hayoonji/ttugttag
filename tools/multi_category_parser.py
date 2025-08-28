
# ======================================================================================
# 다중 카테고리 쿼리 파싱 클래스 (multi_category_parser.py) - 브랜드 매핑 개선
# ======================================================================================

import re
from typing import List, Dict, Any, Optional

class MultiCategoryQueryParser:
    """다중 카테고리 지원 쿼리 파서"""
    
    # 🔧 확장된 브랜드 매핑 (실제 데이터와 일치)
    BRAND_CATEGORY_MAPPING = {
        # 카페
        "스타벅스": {
            "aliases": ["스타벅스", "starbucks", "스타벅스코리아", "스벅"],
            "category": "카페"
        },
        "투썸플레이스": {
            "aliases": ["투썸", "twosome", "투썸플레이스"],
            "category": "카페"
        },
        "메가커피": {
            "aliases": ["메가", "mega", "메가커피", "메가MGC커피", "MEGA MGC"],
            "category": "카페"
        },
        "할리스": {
            "aliases": ["할리스", "hollys", "할리스커피"],
            "category": "카페"
        },
        "파스쿠찌": {
            "aliases": ["파스쿠찌", "pascucci", "파스쿠치"],
            "category": "카페"
        },
        "이디야": {
            "aliases": ["이디야", "ediya", "이디야커피", "EDIYA COFFEE"],
            "category": "카페"
        },
        
        # 편의점
        "GS25": {
            "aliases": ["gs25", "지에스25", "gs편의점", "지에스편의점", "GS 편의점"],
            "category": "편의점"
        },
        "세븐일레븐": {
            "aliases": ["세븐일레븐", "7-eleven", "세븐", "711"],
            "category": "편의점"
        },
        "CU": {
            "aliases": ["cu", "씨유", "cu편의점", "PocketCU"],
            "category": "편의점"
        },
        
        # 마트
        "홈플러스": {
            "aliases": ["홈플러스", "homeplus", "홈플"],
            "category": "마트"
        },
        "이마트": {
            "aliases": ["이마트", "emart", "e마트", "SSG"],
            "category": "마트"
        },
        
        # 패션
        "무신사": {
            "aliases": ["무신사", "musinsa"],
            "category": "패션"
        },
        "지그재그": {
            "aliases": ["지그재그", "zigzag"],
            "category": "패션"
        },
        
        # 온라인쇼핑
        "쿠팡": {
            "aliases": ["쿠팡", "coupang", "쿠팡이츠"],
            "category": "온라인쇼핑"
        },
        "지마켓": {
            "aliases": ["지마켓", "gmarket", "g마켓"],
            "category": "온라인쇼핑"
        },
        "11번가": {
            "aliases": ["11번가", "11st", "십일번가"],
            "category": "온라인쇼핑"
        },
        "네이버쇼핑": {
            "aliases": ["네이버쇼핑", "naver shopping", "네이버"],
            "category": "온라인쇼핑"
        },
        
        # 식당
        "맥도날드": {
            "aliases": ["맥도날드", "mcdonalds", "맥날", "맥도"],
            "category": "식당"
        },
        "KFC": {
            "aliases": ["kfc", "케이에프씨", "치킨"],
            "category": "식당"
        },
        "버거킹": {
            "aliases": ["버거킹", "burger king", "버킹"],
            "category": "식당"
        },
        
        # 뷰티
        "올리브영": {
            "aliases": ["올리브영", "oliveyoung", "올영"],
            "category": "뷰티"
        },
        
        # 의료
        "온누리약국": {
            "aliases": ["온누리약국", "온누리", "약국"],
            "category": "의료"
        },
        
        # 교통
        "지하철": {
            "aliases": ["지하철", "전철", "도시철도", "metro"],
            "category": "교통"
        },
        "버스": {
            "aliases": ["버스", "시내버스", "마을버스"],
            "category": "교통"
        }
    }
    
    # 🔧 카테고리 키워드 매핑 (실제 데이터와 일치)
    CATEGORY_KEYWORDS = {
        "카페": ["카페", "커피", "음료", "cafe", "coffee", "아메리카노", "라떼", "스타벅스", "이디야", "투썸"],
        "편의점": ["편의점", "편스", "convenience store", "gs25", "cu", "세븐일레븐"],
        "마트": ["마트", "대형마트", "슈퍼마켓", "mart", "supermarket", "홈플러스", "이마트"],
        "패션": ["패션", "옷", "의류", "fashion", "무신사", "지그재그"],
        "온라인쇼핑": ["온라인", "인터넷쇼핑", "쇼핑몰", "배송", "online shopping", "쿠팡"],
        "식당": ["식당", "레스토랑", "패스트푸드", "음식점", "restaurant", "맥도날드", "버거킹"],
        "뷰티": ["뷰티", "화장품", "코스메틱", "beauty", "cosmetic", "올리브영"],
        "의료": ["약국", "병원", "의료", "pharmacy", "medical", "온누리약국"],
        "교통": ["교통", "지하철", "버스", "택시", "transport", "전철"]
    }
    
    @classmethod
    def extract_brands_with_categories(cls, query: str) -> Dict[str, Dict]:
        """쿼리에서 브랜드와 카테고리를 함께 추출"""
        query_lower = query.lower()
        found_brands = {}
        
        for main_brand, info in cls.BRAND_CATEGORY_MAPPING.items():
            for alias in info["aliases"]:
                if alias.lower() in query_lower:
                    found_brands[main_brand] = {
                        "category": info["category"],
                        "matched_alias": alias
                    }
                    break
        
        return found_brands
    
    @classmethod
    def extract_categories(cls, query: str) -> List[str]:
        """쿼리에서 카테고리 추출"""
        query_lower = query.lower()
        found_categories = []
        
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            if any(keyword.lower() in query_lower for keyword in keywords):
                found_categories.append(category)
        
        return list(set(found_categories))  # 중복 제거
    
    @classmethod
    def extract_multi_spending_data(cls, query: str) -> Dict[str, Dict]:
        """다중 카테고리 소비 데이터 추출"""
        spending_data = {}
        
        # 패턴: "브랜드에서 금액" 형태
        patterns = [
            r'(\S+)에서\s*(\d+)\s*만원',
            r'(\S+)에서\s*(\d+)\s*천원', 
            r'(\S+)에서\s*(\d+)\s*원',
            r'(\S+)\s*(\d+)\s*만원',
            r'(\S+)\s*(\d+)\s*천원',
            r'(\S+)\s*(\d+)\s*원'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query)
            for brand_text, amount_str in matches:
                # 브랜드명 정규화 및 카테고리 정보 추가
                brand_info = cls._normalize_brand_with_category(brand_text)
                if brand_info:
                    amount = int(amount_str)
                    if '만원' in pattern:
                        amount *= 10000
                    elif '천원' in pattern:
                        amount *= 1000
                    
                    spending_data[brand_info["brand"]] = {
                        "amount": amount,
                        "category": brand_info["category"]
                    }
        
        return spending_data
    
    @classmethod  
    def _normalize_brand_with_category(cls, brand_text: str) -> Optional[Dict]:
        brand_text_lower = brand_text.lower().strip()
        
        # 정확한 매칭 우선
        for main_brand, info in cls.BRAND_CATEGORY_MAPPING.items():
            for alias in info["aliases"]:
                if brand_text_lower == alias.lower():
                    return {"brand": main_brand, "category": info["category"]}
        
        # 부분 매칭 (정확한 매칭이 안 될 때만)  
        for main_brand, info in cls.BRAND_CATEGORY_MAPPING.items():
            for alias in info["aliases"]:
                if alias.lower() in brand_text_lower:
                    return {"brand": main_brand, "category": info["category"]}
        
        return None
    
    @classmethod
    def extract_benefit_type(cls, query: str) -> Optional[str]:
        """혜택 타입 추출"""
        query_lower = query.lower()
        
        type_keywords = {
            "할인": ["할인", "세일", "discount", "특가"],
            "적립": ["적립", "포인트", "point", "보너스", "캐시백"],
            "증정": ["증정", "무료", "free", "gift", "선물"],
            "쿠폰": ["쿠폰", "coupon"],
            "포인트사용": ["포인트사용", "포인트 사용", "m포인트"],
            "복합": ["복합", "종합", "패키지"]
        }
        
        for benefit_type, keywords in type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return benefit_type
        return None
    
    @classmethod
    def build_multi_category_filters(cls, query: str, debug: bool = False) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """다중 카테고리 지원 필터 생성"""
        parsed_info = {}
        
        # 다중 브랜드+카테고리 소비 데이터 추출
        spending_data = cls.extract_multi_spending_data(query)
        
        if spending_data:
            parsed_info["spending_data"] = spending_data
            # 최대 소비 브랜드 및 카테고리 찾기
            max_spending_item = max(spending_data.items(), key=lambda x: x[1]["amount"])
            parsed_info["max_spending_brand"] = max_spending_item[0]
            parsed_info["max_spending_amount"] = max_spending_item[1]["amount"]
            parsed_info["max_spending_category"] = max_spending_item[1]["category"]
            
            # 카테고리별 총 소비액 계산
            category_totals = {}
            for brand, data in spending_data.items():
                category = data["category"]
                category_totals[category] = category_totals.get(category, 0) + data["amount"]
            parsed_info["category_totals"] = category_totals
        
        else:
            # 브랜드+카테고리 정보 추출
            brands_info = cls.extract_brands_with_categories(query)
            if brands_info:
                parsed_info["brands_info"] = brands_info
                parsed_info["primary_brand"] = list(brands_info.keys())[0]
                parsed_info["primary_category"] = brands_info[parsed_info["primary_brand"]]["category"]
            
            # 카테고리만 명시된 경우
            categories = cls.extract_categories(query)
            if categories:
                parsed_info["mentioned_categories"] = categories
        
        # 혜택 타입 추출
        benefit_type = cls.extract_benefit_type(query)
        if benefit_type:
            parsed_info["benefit_type"] = benefit_type
        
        # 필터 생성
        conditions = []
        
        if parsed_info.get("max_spending_brand"):
            conditions.append({"brand": {"$eq": parsed_info["max_spending_brand"]}})
        elif parsed_info.get("primary_brand"):
            conditions.append({"brand": {"$eq": parsed_info["primary_brand"]}})
        elif parsed_info.get("mentioned_categories"):
            if len(parsed_info["mentioned_categories"]) == 1:
                conditions.append({"category": {"$eq": parsed_info["mentioned_categories"][0]}})
            else:
                category_conditions = [{"category": {"$eq": cat}} for cat in parsed_info["mentioned_categories"]]
                conditions.append({"$or": category_conditions})
        
        # 혜택 타입 필터
        if benefit_type:
            conditions.append({"benefit_type": {"$eq": benefit_type}})
        
        # 활성 이벤트만
        conditions.append({"is_active": {"$eq": True}})
        
        # ChromaDB 필터 구성
        if len(conditions) == 1:
            filters = conditions[0]
        elif len(conditions) > 1:
            filters = {"$and": conditions}
        else:
            filters = {"is_active": {"$eq": True}}
        
        if debug:
            print(f"파싱된 정보: {parsed_info}")
            print(f"적용할 필터: {filters}")
        
        return filters, parsed_info
    
    @classmethod
    def analyze_query_intent(cls, query: str) -> Dict[str, Any]:
        """쿼리 의도 종합 분석"""
        analysis = {
            "query": query,
            "brands": cls.extract_brands_with_categories(query),
            "categories": cls.extract_categories(query),
            "spending_data": cls.extract_multi_spending_data(query),
            "benefit_type": cls.extract_benefit_type(query),
            "intent": "unknown"
        }
        
        # 의도 분류
        if analysis["spending_data"]:
            analysis["intent"] = "spending_based_recommendation"
        elif analysis["brands"]:
            analysis["intent"] = "brand_specific_inquiry"
        elif analysis["categories"]:
            analysis["intent"] = "category_specific_inquiry"
        elif analysis["benefit_type"]:
            analysis["intent"] = "benefit_type_inquiry"
        else:
            analysis["intent"] = "general_inquiry"
        
        return analysis
