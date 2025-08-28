# ======================================================================================
# 구조화된 카페 혜택 RAG 구축 (build_database.py) - 더미 데이터 import 수정
# ======================================================================================

import json
import requests
import chromadb
import os
import datetime
import shutil
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import sys
from pathlib import Path

# 🔧 더미 데이터 import 수정
try:
    from multi_category_dummy_data import MULTI_CATEGORY_DATA
except ImportError:
    print("❌ multi_category_dummy_data.py를 찾을 수 없습니다.")
    print("💡 paste.txt의 더미 데이터를 multi_category_dummy_data.py로 저장해주세요.")
    sys.exit(1)

# API 설정
CLOVA_STUDIO_API_KEY = 'nv-53f7a8c4abe74e20ab90446ed46ba79fvozJ'
CLOVA_EMBEDDING_API_URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/clir-emb-dolphin"

# ======================================================================================
# 임베딩 API
# ======================================================================================

class EmbeddingAPI:
    """CLOVA Studio Embedding API"""
    
    @staticmethod
    def generate_embedding(text: str) -> Optional[List[float]]:
        """텍스트 임베딩 생성"""
        try:
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Bearer {CLOVA_STUDIO_API_KEY}',
                'X-NCP-CLOVASTUDIO-REQUEST-ID': '93ae6593a47d4437b634f2cbc5282896'
            }
            request_data = {"text": text}
            
            response = requests.post(
                CLOVA_EMBEDDING_API_URL,
                headers=headers,
                json=request_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['status']['code'] == '20000':
                    return result['result']['embedding']
            
            return None
            
        except Exception as e:
            print(f"임베딩 오류: {e}")
            return None

# ======================================================================================
# 구조화된 RAG 빌더
# ======================================================================================

class StructuredCafeRAGBuilder:
    """구조화된 카페 RAG 빌더"""
    
    def __init__(self, db_path: str = "./cafe_vector_db", collection_name: str = "cafe_events"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
    
    def initialize_database(self, reset: bool = True):
        """DB 초기화"""
        try:
            if reset and os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
                print("🗑️ 기존 데이터베이스 삭제")
            
            os.makedirs(self.db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "ip"}
            )
            print("🆕 새 컬렉션 생성 완료")
            return True
                
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 실패: {e}")
            return False
    
    def build_structured_database(self):
        """구조화된 데이터베이스 구축"""
        print(f"\n📝 구조화된 혜택 RAG 구축")
        
        total_items = len(MULTI_CATEGORY_DATA)
        print(f"🎯 총 처리할 항목: {total_items}개")
        
        success_count = 0
        error_count = 0
        
        for i, item in enumerate(tqdm(MULTI_CATEGORY_DATA, desc="임베딩 처리중")):
            try:
                # 임베딩 생성 (text 필드 사용)
                embedding = EmbeddingAPI.generate_embedding(item['text'])
                
                if embedding:
                    # ChromaDB에 저장 (구조화된 메타데이터)
                    self.collection.add(
                        ids=[item['id']],
                        embeddings=[embedding],
                        metadatas=[{
                            # 기존 필드들
                            "source": item['source_url'],
                            "title": item['title'],
                            "text": item['text'],
                            "brand": item['brand'],
                            
                            # 새로운 구조화된 필드들
                            "id": item['id'],
                            "brand_aliases": json.dumps(item['brand_aliases']),
                            "category": item['category'],
                            "benefit_type": item['benefit_type'],
                            "discount_rate": item['discount_rate'],
                            "conditions": item['conditions'],
                            "valid_from": item['valid_from'],
                            "valid_to": item['valid_to'],
                            "is_active": item['is_active'],
                            
                            # 호환성을 위한 기존 필드들
                            "event_type": item['benefit_type'],
                            "start_date": f"{item['valid_from']}T00:00:00",
                            "end_date": f"{item['valid_to']}T23:59:59",
                            
                            "processed_at": datetime.datetime.now().isoformat()
                        }],
                        documents=[item['text']]
                    )
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print(f"처리 오류 (항목 {i}): {e}")
                error_count += 1
        
        # 최종 결과
        final_count = self.collection.count()
        print(f"\n🎯 구조화된 RAG 구축 완료:")
        print(f"   ✅ 성공: {success_count}개")
        print(f"   ❌ 실패: {error_count}개") 
        print(f"   💾 DB 총 문서: {final_count}개")
        print(f"   📈 성공률: {(success_count / total_items * 100):.1f}%")
        
        # 🔧 브랜드별 통계 (실제 데이터 기준)
        brand_stats = {}
        category_stats = {}
        for item in MULTI_CATEGORY_DATA:
            brand = item['brand']
            category = item['category']
            brand_stats[brand] = brand_stats.get(brand, 0) + 1
            category_stats[category] = category_stats.get(category, 0) + 1
        
        print(f"\n📊 브랜드별 분포:")
        for brand, count in sorted(brand_stats.items()):
            print(f"   {brand}: {count}개")
        
        print(f"\n🏷️ 카테고리별 분포:")
        for category, count in sorted(category_stats.items()):
            print(f"   {category}: {count}개")
        
        return success_count > 0

# ======================================================================================
# 메인 실행
# ======================================================================================

def main():
    """메인 실행"""
    print("☕ 구조화된 혜택 RAG 구축 도구 (개선됨)")
    print("=" * 60)
    
    print(f"📊 처리할 데이터: {len(MULTI_CATEGORY_DATA)}개")
    print("🏗️ 구조화된 메타데이터 + 임베딩")
    print(f"📁 더미 데이터: multi_category_dummy_data.py에서 로드")
    
    # 🔧 데이터 미리보기
    if MULTI_CATEGORY_DATA:
        sample = MULTI_CATEGORY_DATA[0]
        print(f"\n📋 데이터 샘플:")
        print(f"   브랜드: {sample['brand']}")
        print(f"   카테고리: {sample['category']}")
        print(f"   제목: {sample['title']}")
        print(f"   혜택타입: {sample['benefit_type']}")
    
    confirm = input(f"\n구조화된 RAG 데이터베이스를 구축하시겠습니까? (y/N): ")
    
    if confirm.lower() in ['y', 'yes']:
        builder = StructuredCafeRAGBuilder()
        
        if builder.initialize_database(reset=True):
            success = builder.build_structured_database()
            
            if success:
                print(f"\n✅ 구조화된 혜택 RAG 구축 완료!")
                print(f"📁 저장 위치: {os.path.abspath('./cafe_vector_db')}")
                print(f"\n🔍 이제 다음으로 테스트하세요:")
                print(f"   python3 personalized_rag_system.py")
                print(f"\n💡 검색 예시:")
                print(f"   '스타벅스 10만원 썼어, 혜택 추천해줘'")
                print(f"   '투썸플레이스 할인 이벤트 있어?'")
                print(f"   '카페 혜택 추천해줘'")
                print(f"   '편의점 쿠폰 있나?'")
            else:
                print("\n❌ 구축 실패")
        else:
            print("\n❌ DB 초기화 실패")
    else:
        print("❌ 취소되었습니다.")

if __name__ == "__main__":
    main()
# # ======================================================================================
