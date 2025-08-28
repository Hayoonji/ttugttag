#!/usr/bin/env python3
# ======================================================================================
# ChromaDB 초기화 스크립트 - RAG 시스템용
# ======================================================================================

import chromadb
import os
import sys
import json
from pathlib import Path

def create_sample_data():
    """샘플 데이터 생성 및 ChromaDB에 삽입"""
    
    # 샘플 카페 혜택 데이터
    sample_data = [
        {
            "text": "스타벅스 신규 고객 20% 할인 혜택입니다. 5000원 이상 구매 시 최대 3000원 할인받을 수 있어요.",
            "metadata": {
                "brand": "스타벅스",
                "category": "카페",
                "benefit_type": "할인",
                "discount_rate": "20%",
                "min_amount": 5000,
                "max_discount": 3000,
                "conditions": "신규 고객만"
            }
        },
        {
            "text": "투썹플레이스 첫 구매 15% 할인 혜택입니다. 3000원 이상 구매 시 최대 2000원 할인받을 수 있어요.",
            "metadata": {
                "brand": "투썹플레이스",
                "category": "카페",
                "benefit_type": "할인",
                "discount_rate": "15%",
                "min_amount": 3000,
                "max_discount": 2000,
                "conditions": "첫 구매 고객만"
            }
        },
        {
            "text": "할리스커피 주말 25% 할인 혜택입니다. 8000원 이상 구매 시 최대 4000원 할인받을 수 있어요.",
            "metadata": {
                "brand": "할리스커피",
                "category": "카페",
                "benefit_type": "할인",
                "discount_rate": "25%",
                "min_amount": 8000,
                "max_discount": 4000,
                "conditions": "주말만"
            }
        },
        {
            "text": "이디야커피 이벤트 기간 10% 할인 혜택입니다. 5000원 이상 구매 시 최대 2000원 할인받을 수 있어요.",
            "metadata": {
                "brand": "이디야커피",
                "category": "카페",
                "benefit_type": "할인",
                "discount_rate": "10%",
                "min_amount": 5000,
                "max_discount": 2000,
                "conditions": "이벤트 기간만"
            }
        },
        {
            "text": "메가MGC커피 새벽 시간 20% 할인 혜택입니다. 3000원 이상 구매 시 최대 1500원 할인받을 수 있어요.",
            "metadata": {
                "brand": "메가MGC커피",
                "category": "카페",
                "benefit_type": "할인",
                "discount_rate": "20%",
                "min_amount": 3000,
                "max_discount": 1500,
                "conditions": "새벽 2-6시"
            }
        },
        {
            "text": "GS25 편의점 쿠폰 혜택입니다. 5000원 구매 시 1000원 할인받을 수 있어요.",
            "metadata": {
                "brand": "GS25",
                "category": "편의점",
                "benefit_type": "쿠폰",
                "discount_amount": 1000,
                "min_amount": 5000,
                "conditions": "모든 고객"
            }
        },
        {
            "text": "CU 편의점 포인트 적립 혜택입니다. 구매 금액의 5% 포인트를 적립받을 수 있어요.",
            "metadata": {
                "brand": "CU",
                "category": "편의점",
                "benefit_type": "포인트",
                "point_rate": "5%",
                "min_amount": 1000,
                "conditions": "회원만"
            }
        },
        {
            "text": "이마트 대형 할인마트 5% 할인 혜택입니다. 10만원 이상 구매 시 최대 1만원 할인받을 수 있어요.",
            "metadata": {
                "brand": "이마트",
                "category": "마트",
                "benefit_type": "할인",
                "discount_rate": "5%",
                "min_amount": 100000,
                "max_discount": 10000,
                "conditions": "모든 고객"
            }
        },
        {
            "text": "홈플러스 대형 할인마트 3% 포인트 적립 혜택입니다. 5만원 이상 구매 시 구매 금액의 3%를 포인트로 적립받을 수 있어요.",
            "metadata": {
                "brand": "홈플러스",
                "category": "마트",
                "benefit_type": "포인트",
                "point_rate": "3%",
                "min_amount": 50000,
                "conditions": "회원만"
            }
        },
        {
            "text": "스타벅스 생일 축하 30% 할인 혜택입니다. 생일 당일 1만원 이상 구매 시 최대 5000원 할인받을 수 있어요.",
            "metadata": {
                "brand": "스타벅스",
                "category": "카페",
                "benefit_type": "할인",
                "discount_rate": "30%",
                "min_amount": 10000,
                "max_discount": 5000,
                "conditions": "생일 당일만"
            }
        }
    ]
    
    return sample_data

def init_chromadb():
    """ChromaDB 초기화 및 샘플 데이터 삽입"""
    
    try:
        # ChromaDB 클라이언트 생성
        client = chromadb.PersistentClient(path="/chroma/chroma")
        
        # 기존 컬렉션 삭제 (깨끗한 상태로 시작)
        try:
            client.delete_collection("cafe_benefits")
            print("✅ 기존 컬렉션 삭제 완료")
        except:
            pass
        
        # 새 컬렉션 생성
        collection = client.create_collection(
            name="cafe_benefits",
            metadata={"description": "카페 및 편의점 혜택 정보"}
        )
        print("✅ ChromaDB 컬렉션 생성 완료")
        
        # 샘플 데이터 준비
        sample_data = create_sample_data()
        
        # 데이터를 ChromaDB에 삽입
        texts = [item["text"] for item in sample_data]
        metadatas = [item["metadata"] for item in sample_data]
        ids = [f"benefit_{i+1}" for i in range(len(sample_data))]
        
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ 샘플 데이터 {len(sample_data)}개 삽입 완료")
        
        # 컬렉션 정보 출력
        count = collection.count()
        print(f"📊 현재 컬렉션 문서 수: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB 초기화 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ChromaDB 초기화 시작...")
    success = init_chromadb()
    
    if success:
        print("✅ ChromaDB 초기화 완료!")
    else:
        print("❌ ChromaDB 초기화 실패!")
        sys.exit(1) 