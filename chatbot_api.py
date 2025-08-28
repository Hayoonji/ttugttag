# ======================================================================================
# EC2 서버용 챗봇 API - chatbot_api.py
# ======================================================================================

import json
import logging
import datetime
import re
from typing import Dict, Any, List, Optional
from flask import jsonify

from config import EC2Config
from rag_system import create_user_profile_from_history

# 로깅 설정
logger = logging.getLogger(__name__)

# ======================================================================================
# 챗봇 대화 처리 클래스 (EC2 최적화)
# ======================================================================================
import requests
import json
import os
from datetime import datetime

class PerplexityAPI:
    def __init__(self, api_key=None):
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.api_key = api_key or self.get_api_key()
        
    def get_api_key(self):
        """API 키 입력받기"""
        api_key = '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'
        
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

def main():
    """메인 실행 함수"""
    print("🚀 Perplexity API 실시간 검색봇")
    print("=" * 50)
    
    # API 초기화
    pplx = PerplexityAPI()
    
    if not pplx.api_key:
        print("❌ API 키가 필요합니다.")
        return
    
    print("✅ API 설정 완료!")
    print("\n💬 질문을 입력하세요 (종료: quit)")
    print("-" * 50)
    
    while True:
        try:
            # 사용자 입력
            query = input("\n❓ 질문: ").strip()
            
            if query.lower() in ['quit', 'exit', '종료', 'q']:
                print("👋 프로그램을 종료합니다!")
                break
            
            if not query:
                print("💭 질문을 입력해주세요.")
                continue
            
            # 실시간 검색
            print("🔍 검색 중...")
            result = pplx.search(query, model="sonar-pro")
            
            if result['success']:
                print(f"\n📱 [{result['model']}] 검색 결과:")
                print("=" * 60)
                print(result['content'])
                print("=" * 60)
                
                # 사용량 정보
                usage = result.get('usage', {})
                if usage:
                    print(f"📊 토큰 사용량: {usage.get('total_tokens', 'N/A')}")
            else:
                print(f"\n❌ 검색 실패: {result['error']}")
                
        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")

# 간단한 사용 예제
def example_usage():
    """사용 예제"""
    pplx = PerplexityAPI()
    
    # 스타벅스 이벤트 검색
    query = "2025년 8월 현재 진행 중인 스타벅스 이벤트와 프로모션"
    result = pplx.search(query)
    
    if result['success']:
        print("검색 결과:")
        print(result['content'])
    else:
        print("검색 실패:", result['error'])

if __name__ == "__main__":
    # 실행 방법 선택
    print("실행 방법을 선택하세요:")
    print("1. 대화형 모드")
    print("2. 예제 실행")
    
    choice = input("선택 (1 또는 2): ").strip()
    
    if choice == "2":
        example_usage()
    else:
        main()
class EC2ChatbotHandler:
    """EC2 서버용 챗봇 대화 처리 핸들러"""
    
    def __init__(self, rag_system):
        self.rag = rag_system
        self.conversation_context = {}  # 대화 맥락 저장
        
        # 인사말 패턴
        self.greeting_patterns = [
            r'안녕', r'hello', r'hi', r'헬로', r'반가워', r'처음', r'시작', r'하이'
        ]
        
        # 도움 요청 패턴
        self.help_patterns = [
            r'도움', r'help', r'사용법', r'명령어', r'기능', r'뭐할수있어', r'뭐 할 수 있어', r'사용방법'
        ]
        
        # 감사 인사 패턴
        self.thanks_patterns = [
            r'고마워', r'감사', r'thank', r'thx', r'ㄱㅅ', r'고맙'
        ]
        
        # 카테고리 관련 패턴
        self.category_question_patterns = [
            r'카테고리', r'분류', r'종류', r'어떤.*있어', r'뭐뭐.*있어', r'뭐가.*있어'
        ]
        
        # 정보 요청 패턴
        self.info_patterns = [
            r'정보', r'소개', r'뭐야', r'무엇', r'설명'
        ]
    
    def process_message(self, message: str, user_id: str = None, user_context: Dict = None) -> Dict[str, Any]:
        """챗봇 메시지 처리"""
        try:
            # 메시지 전처리
            message = message.strip()
            if not message:
                return self._create_response("메시지를 입력해주세요! 🙂", "error")
            
            # 대화 맥락 로드
            context = self.conversation_context.get(user_id, {}) if user_id else {}
            
            # 메시지 타입 분석
            message_type = self._analyze_message_type(message)
            
            logger.debug(f"메시지 타입 분석: '{message}' -> {message_type}")
            
            # 타입별 처리
            if message_type == "greeting":
                response = self._handle_greeting(message)
            elif message_type == "help":
                response = self._handle_help_request()
            elif message_type == "thanks":
                response = self._handle_thanks()
            elif message_type == "category_inquiry":
                response = self._handle_category_inquiry()
            elif message_type == "info_request":
                response = self._handle_info_request()
            elif message_type == "benefit_search":
                response = PersonalizedBenefitRAG.search_personalized_benefits(message, user_context, context)
            else:
                # 기본적으로 혜택 검색으로 처리
                response = PersonalizedBenefitRAG.search_personalized_benefits(message, user_context, context)
            
            # 대화 맥락 업데이트
            if user_id:
                self._update_conversation_context(user_id, message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"챗봇 메시지 처리 오류: {e}")
            return self._create_response(
                "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해주세요. 😅",
                "error"
            )
    
    def _analyze_message_type(self, message: str) -> str:
        """메시지 타입 분석"""
        message_lower = message.lower()
        
        # 인사말 체크
        if any(re.search(pattern, message_lower) for pattern in self.greeting_patterns):
            return "greeting"
        
        # 도움 요청 체크
        if any(re.search(pattern, message_lower) for pattern in self.help_patterns):
            return "help"
        
        # 감사 인사 체크
        if any(re.search(pattern, message_lower) for pattern in self.thanks_patterns):
            return "thanks"
        
        # 카테고리 문의 체크
        if any(re.search(pattern, message_lower) for pattern in self.category_question_patterns):
            return "category_inquiry"
        
        # 정보 요청 체크
        if any(re.search(pattern, message_lower) for pattern in self.info_patterns):
            return "info_request"
        
        return "benefit_search"
    
    def _handle_greeting(self, message: str) -> Dict[str, Any]:
        """인사말 처리"""
        responses = [
            "안녕하세요! 🎉 EC2에서 실행되는 개인화된 혜택 추천 봇입니다!",
            "무엇을 도와드릴까요? 😊",
            "",
            "💡 이런 것들을 물어보실 수 있어요:",
            "• '스타벅스 할인 혜택 있어?' - 특정 브랜드 혜택 검색",
            "• '카페에서 쓸 수 있는 쿠폰 있어?' - 카테고리별 혜택 검색", 
            "• '내 소비패턴에 맞는 혜택 추천해줘' - 개인화 추천",
            "• '도움말' - 자세한 사용법 보기",
            "",
            "🖥️ EC2 서버에서 안정적으로 서비스 중입니다!"
        ]
        
        return self._create_response("\n".join(responses), "greeting", {
            "suggestions": [
                "스타벅스 할인 혜택 있어?",
                "카페 쿠폰 있나?",
                "개인화 추천해줘",
                "도움말"
            ]
        })
    
    def _handle_help_request(self) -> Dict[str, Any]:
        """도움 요청 처리"""
        help_text = [
            "🤖 EC2 혜택 추천 봇 사용법",
            "",
            "📍 브랜드별 검색:",
            "• '스타벅스 할인 있어?'",
            "• '이디야 이벤트 뭐 있나?'",
            "• '맥도날드 쿠폰 알려줘'",
            "",
            "🏷️ 카테고리별 검색:",
            "• '카페 쿠폰 있어?'",
            "• '편의점 혜택 알려줘'",
            "• '마트 할인 정보 줘'",
            "• '배달음식 쿠폰 찾아줘'",
            "",
            "🎯 개인화 추천:",
            "• '내 소비패턴에 맞는 혜택 추천해줘'",
            "• '자주 가는 곳 혜택 있어?'",
            "",
            "📊 지원 카테고리:",
            f"{', '.join(list(EC2Config.CATEGORIES.keys()))}",
            "",
            "💬 자연스럽게 말씀해주시면 알아서 찾아드려요!",
            "🖥️ 빠르고 안정적인 EC2 서버에서 실행 중입니다."
        ]
        
        return self._create_response("\n".join(help_text), "help", {
            "suggestions": [
                "스타벅스 할인 있어?",
                "카페 쿠폰 추천해줘", 
                "개인화 혜택 추천",
                "카테고리 목록 보여줘"
            ]
        })
    
    def _handle_thanks(self) -> Dict[str, Any]:
        """감사 인사 처리"""
        responses = [
            "천만에요! 😊 도움이 되었다니 기뻐요!",
            "",
            "또 다른 혜택이 궁금하시면 언제든 물어보세요!",
            "EC2 서버에서 24시간 대기 중이에요! 🖥️✨"
        ]
        
        return self._create_response("\n".join(responses), "thanks", {
            "suggestions": [
                "다른 혜택도 찾아줘",
                "카테고리별로 보여줘",
                "개인화 추천해줘"
            ]
        })
    
    def _handle_category_inquiry(self) -> Dict[str, Any]:
        """카테고리 문의 처리"""
        categories = list(EC2Config.CATEGORIES.keys())
        
        response_text = [
            "🏷️ 현재 지원하는 카테고리들이에요:",
            ""
        ]
        
        for i, category in enumerate(categories, 1):
            examples = EC2Config.CATEGORIES[category][:3]  # 예시 3개만
            response_text.append(f"{i}. **{category}** - {', '.join(examples)} 등")
        
        response_text.extend([
            "",
            "어떤 카테고리의 혜택을 찾고 계신가요? 😊",
            "",
            "🖥️ EC2 서버에서 모든 카테고리를 빠르게 검색해드려요!"
        ])
        
        return self._create_response("\n".join(response_text), "category_info", {
            "categories": categories,
            "suggestions": [f"{cat} 혜택 찾아줘" for cat in categories[:4]]
        })
    
    def _handle_info_request(self) -> Dict[str, Any]:
        """정보 요청 처리"""
        info_text = [
            "🤖 EC2 개인화된 혜택 추천 봇 소개",
            "",
            "🎯 **주요 기능:**",
            "• AI 기반 혜택 검색 및 추천",
            "• 개인 소비 패턴 분석",
            "• 실시간 혜택 정보 제공",
            "• 자연어 대화 인터페이스",
            "",
            "🖥️ **기술 스택:**",
            "• AWS EC2 서버 기반",
            "• CLOVA Studio AI 엔진",
            "• ChromaDB 벡터 데이터베이스",
            "• Flask 웹 프레임워크",
            "",
            "📊 **데이터 범위:**",
            f"• {len(EC2Config.CATEGORIES)}개 주요 카테고리",
            "• 실시간 업데이트 혜택 정보",
            "• 개인화된 추천 알고리즘",
            "",
            "무엇을 도와드릴까요? 😊"
        ]
        
        return self._create_response("\n".join(info_text), "info", {
            "suggestions": [
                "혜택 검색해줘",
                "카테고리 보여줘",
                "사용법 알려줘"
            ]
        })
    
    def _handle_benefit_search(self, message: str, user_context: Dict = None, conversation_context: Dict = None) -> Dict[str, Any]:
        """혜택 검색 처리"""
        try:
            # 사용자 프로필 준비
            user_profile = None
            if user_context and user_context.get('spending_history'):
                user_profile = create_user_profile_from_history(user_context['spending_history'])
            
            # RAG 검색 수행
            search_result = self.rag.search_benefits(
                query=message,
                user_history=user_profile,
                top_k=5,
                debug=False
            )
            
            if not search_result.get('success'):
                return self._create_response(
                    "죄송합니다. 혜택을 찾는 중 문제가 발생했어요. 다시 시도해주세요. 😅",
                    "error"
                )
            
            results = search_result.get('results', [])
            
            if not results:
                return self._handle_no_results(message)
            
            # 챗봇 친화적 응답 생성
            response_text = self._format_search_results_for_chat(message, results, user_profile)
            
            # 추가 제안 생성
            suggestions = self._generate_suggestions(results, message)
            
            return self._create_response(response_text, "search_results", {
                "results": results,
                "suggestions": suggestions,
                "result_count": len(results),
                "search_info": search_result.get('search_strategy', {})
            })
            
        except Exception as e:
            logger.error(f"혜택 검색 오류: {e}")
            return self._create_response(
                "혜택을 찾는 중 오류가 발생했어요. 조금 다른 방식으로 질문해주시겠어요? 🤔",
                "error"
            )
    
    def _handle_no_results(self, query: str) -> Dict[str, Any]:
        """검색 결과 없음 처리"""
        # 쿼리에서 키워드 추출하여 대안 제시
        extracted_categories = EC2Config.detect_category_from_text(query)
        
        response_lines = [
            f"'{query}'에 대한 혜택을 찾지 못했어요. 😅",
            ""
        ]
        
        if extracted_categories:
            response_lines.extend([
                f"하지만 {extracted_categories} 카테고리에는 다른 혜택들이 있어요!",
                f"'{extracted_categories} 혜택 보여줘'라고 물어보시면 찾아드릴게요! 😊"
            ])
            suggestions = [f"{extracted_categories} 혜택 보여줘"]
        else:
            response_lines.extend([
                "이런 방식으로 질문해보시는 건 어떨까요?",
                "• '스타벅스 할인 혜택' - 특정 브랜드로 검색",
                "• '카페 쿠폰' - 카테고리로 검색",
                "• '편의점 혜택' - 다른 카테고리로 검색",
                "",
                "🖥️ EC2 서버에서 더 정확한 검색을 위해 계속 개선 중이에요!"
            ])
            suggestions = ["스타벅스 할인 있어?", "카페 쿠폰 보여줘", "편의점 혜택 알려줘"]
        
        return self._create_response("\n".join(response_lines), "no_results", {
            "suggestions": suggestions
        })
    
    def _format_search_results_for_chat(self, query: str, results: List[Dict], user_profile: Dict = None) -> str:
        """검색 결과를 챗봇 친화적으로 포맷팅"""
        response_lines = []
        
        # 인트로 메시지
        if len(results) == 1:
            response_lines.append(f"'{query}'에 대한 혜택을 찾았어요! 🎉")
        else:
            response_lines.append(f"'{query}'에 대한 {len(results)}개의 혜택을 찾았어요! 🎉")
        
        response_lines.append("")
        
        # 결과 포맷팅 (상위 3개만)
        top_results = results[:3]
        
        for i, result in enumerate(top_results, 1):
            response_lines.append(f"**{i}. {result['brand']} - {result['title']}**")
            response_lines.append(f"   🎁 혜택: {result['benefit_type']}")
            
            if result['discount_rate'] != 'N/A':
                response_lines.append(f"   💰 할인율: {result['discount_rate']}")
            
            if result['conditions'] != 'N/A':
                # 조건이 너무 길면 축약
                conditions = result['conditions']
                if len(conditions) > 50:
                    conditions = conditions[:47] + "..."
                response_lines.append(f"   📋 조건: {conditions}")
            
            # 유효기간 표시 (간단히)
            if result['valid_to'] != 'N/A':
                try:
                    end_date = datetime.datetime.fromisoformat(result['valid_to'].replace('Z', '+00:00'))
                    days_left = (end_date - datetime.datetime.now()).days
                    if days_left > 0:
                        if days_left <= 7:
                            response_lines.append(f"   ⚠️ {days_left}일 후 종료 (서둘러요!)")
                        else:
                            response_lines.append(f"   ⏰ {days_left}일 후 종료")
                    else:
                        response_lines.append(f"   ⚠️ 종료된 혜택일 수 있어요")
                except:
                    response_lines.append(f"   📅 ~{result['valid_to']}")
            
            # 개인화 점수가 높으면 표시
            if 'personalized_score' in result and result['personalized_score'] > 0.7:
                response_lines.append(f"   ⭐ 당신에게 추천! (점수: {result['personalized_score']:.1f}/1.0)")
            
            response_lines.append("")
        
        # 더 많은 결과가 있는 경우
        if len(results) > 3:
            response_lines.append(f"💡 총 {len(results)}개의 혜택이 더 있어요!")
            response_lines.append("더 자세히 보시려면 '자세히 보여줘'라고 말씀해주세요!")
            response_lines.append("")
        
        # 개인화 팁
        if user_profile and user_profile.get('preferred_brands'):
            matching_brands = [r['brand'] for r in top_results if r['brand'] in user_profile['preferred_brands']]
            if matching_brands:
                response_lines.append(f"🎯 **개인화 팁**: {', '.join(matching_brands)} 브랜드를 자주 이용하시니 이 혜택이 특히 유용할 거예요!")
                response_lines.append("")
        
        # EC2 서버 브랜딩
        response_lines.append("🖥️ EC2 서버에서 빠르게 검색해드렸어요!")
        
        return "\n".join(response_lines)
    
    def _generate_suggestions(self, results: List[Dict], original_query: str) -> List[str]:
        """다음 대화를 위한 제안 생성"""
        suggestions = []
        
        if results:
            # 결과에서 브랜드/카테고리 추출
            brands = list(set([r['brand'] for r in results[:3] if r['brand'] != 'N/A']))
            categories = list(set([r['category'] for r in results[:3] if r['category'] != 'N/A']))
            
            # 관련 브랜드 제안
            if brands:
                for brand in brands[:2]:
                    suggestions.append(f"{brand} 다른 혜택도 보여줘")
            
            # 관련 카테고리 제안
            if categories:
                for category in categories[:1]:
                    suggestions.append(f"{category} 다른 혜택 알려줘")
        
        # 기본 제안들
        suggestions.extend([
            "개인화 추천해줘",
            "다른 카테고리도 보여줘"
        ])
        
        return suggestions[:4]  # 최대 4개
    
    def _update_conversation_context(self, user_id: str, message: str, response: Dict[str, Any]):
        """대화 맥락 업데이트"""
        if user_id not in self.conversation_context:
            self.conversation_context[user_id] = {
                'messages': [],
                'last_search_results': [],
                'preferred_categories': [],
                'conversation_count': 0,
                'created_at': datetime.datetime.now().isoformat()
            }
        
        context = self.conversation_context[user_id]
        context['messages'].append({
            'user_message': message,
            'bot_response': response.get('message', ''),
            'timestamp': datetime.datetime.now().isoformat(),
            'response_type': response.get('type', 'unknown')
        })
        
        # 최근 검색 결과 저장
        if response.get('data', {}).get('results'):
            context['last_search_results'] = response['data']['results']
        
        # 최근 10개 대화만 유지 (메모리 절약)
        context['messages'] = context['messages'][-10:]
        context['conversation_count'] += 1
        
        # 컨텍스트가 너무 많아지면 오래된 것 정리
        if len(self.conversation_context) > 100:
            # 가장 오래된 대화 10개 제거
            oldest_users = sorted(
                self.conversation_context.keys(), 
                key=lambda x: self.conversation_context[x].get('created_at', '')
            )[:10]
            
            for user in oldest_users:
                del self.conversation_context[user]
            
            logger.info(f"대화 컨텍스트 정리: {len(oldest_users)}개 세션 제거")
    
    def _create_response(self, message: str, response_type: str, data: Dict = None) -> Dict[str, Any]:
        """응답 객체 생성"""
        return {
            "message": message,
            "type": response_type,
            "data": data or {},
            "timestamp": datetime.datetime.now().isoformat()
        }

# ======================================================================================
# EC2 챗봇 API 엔드포인트 처리 함수들
# ======================================================================================

def handle_chatbot_message(data: Dict[str, Any], rag_system):
    """챗봇 메시지 처리 엔드포인트 (EC2용)"""
    try:
        if not data:
            return jsonify({
                "success": False,
                "error": "요청 데이터가 없습니다."
            }), 400
        
        message = data.get('message', '').strip()
        user_id = data.get('user_id')  # 선택적
        user_context = data.get('user_context', {})  # 사용자 소비 이력 등
        
        if not message:
            return jsonify({
                "success": False,
                "error": "message 파라미터가 필요합니다."
            }), 400
        
        # 챗봇 핸들러 초기화
        chatbot = EC2ChatbotHandler(rag_system)
        
        # 메시지 처리
        response = chatbot.process_message(message, user_id, user_context)
        
        logger.info(f"챗봇 응답 생성: {response['type']} 타입")
        
        return jsonify({
            "success": True,
            "response": response,
            "user_id": user_id,
            "server": "EC2",
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"챗봇 메시지 처리 오류: {e}")
        return jsonify({
            "success": False,
            "error": "메시지 처리 중 오류가 발생했습니다.",
            "response": {
                "message": "죄송합니다. 잠시 후 다시 시도해주세요. 😅",
                "type": "error"
            }
        }), 500

def handle_chatbot_conversation(data: Dict[str, Any], rag_system):
    """챗봇 대화 시작 엔드포인트 (EC2용)"""
    try:
        data = data or {}
        user_id = data.get('user_id')
        user_name = data.get('user_name', '고객님')
        
        # 환영 메시지 생성
        welcome_message = [
            f"안녕하세요, {user_name}! 🎉",
            "",
            "저는 EC2 서버에서 실행되는 개인화된 혜택 추천 봇이에요!",
            "어떤 혜택을 찾고 계신가요? 😊",
            "",
            "💡 이런 식으로 물어보세요:",
            "• '스타벅스 할인 있어?'",
            "• '카페 쿠폰 추천해줘'",
            "• '내 소비패턴에 맞는 혜택 알려줘'",
            "",
            "🖥️ 안정적이고 빠른 EC2 서버에서 24시간 서비스 중입니다!"
        ]
        
        response = {
            "message": "\n".join(welcome_message),
            "type": "welcome",
            "data": {
                "suggestions": [
                    "스타벅스 할인 있어?",
                    "카페 쿠폰 추천해줘",
                    "개인화 혜택 찾아줘",
                    "도움말"
                ],
                "server_info": {
                    "platform": "AWS EC2",
                    "status": "active",
                    "features": ["24/7 가용성", "빠른 응답", "안정적 서비스"]
                }
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"새 대화 시작: user_id={user_id}, user_name={user_name}")
        
        return jsonify({
            "success": True,
            "response": response,
            "user_id": user_id,
            "session_started": True,
            "server": "EC2"
        }), 200
        
    except Exception as e:
        logger.error(f"챗봇 대화 시작 오류: {e}")
        return jsonify({
            "success": False,
            "error": "대화 시작 중 오류가 발생했습니다."
        }), 500

def handle_chatbot_quick_reply(data: Dict[str, Any], rag_system):
    """챗봇 퀵 리플라이 처리 (EC2용)"""
    try:
        if not data:
            return jsonify({
                "success": False,
                "error": "요청 데이터가 없습니다."
            }), 400
        
        action = data.get('action', '')
        user_id = data.get('user_id')
        
        if not action:
            return jsonify({
                "success": False,
                "error": "action 파라미터가 필요합니다."
            }), 400
        
        # 미리 정의된 액션들
        quick_actions = {
            'show_categories': {
                "message": "🏷️ EC2 서버에서 지원하는 카테고리들이에요:\n\n" + 
                          "\n".join([f"• {cat}" for cat in EC2Config.CATEGORIES.keys()]) +
                          "\n\n어떤 카테고리를 선택하시겠어요?",
                "suggestions": list(EC2Config.CATEGORIES.keys())[:4]
            },
            'popular_benefits': {
                "message": "🔥 EC2에서 인기 혜택 카테고리예요:\n\n• 카페 - 스타벅스, 이디야 등\n• 편의점 - GS25, CU 등\n• 마트 - 이마트, 홈플러스 등\n• 배달음식 - 배달의민족, 요기요 등\n\n🖥️ 빠른 EC2 서버로 어떤 걸 찾아드릴까요?",
                "suggestions": ["카페 혜택", "편의점 쿠폰", "마트 할인", "배달 혜택"]
            },
            'help': {
                "message": "🤖 EC2 혜택 봇 도움말\n\n자연스럽게 말씀해주세요!\n• '스타벅스 할인 있어?'\n• '카페에서 쓸 수 있는 쿠폰 있나?'\n• '개인화 추천해줘'\n\n🖥️ EC2 서버에서 빠르게 처리해드려요!\n\n무엇을 도와드릴까요?",
                "suggestions": ["스타벅스 혜택", "카페 쿠폰", "개인화 추천", "카테고리 보기"]
            },
            'server_info': {
                "message": "🖥️ EC2 서버 정보\n\n• **플랫폼**: Amazon Web Services EC2\n• **가용성**: 24시간 연중무휴\n• **성능**: 빠른 응답 속도\n• **안정성**: 높은 업타임 보장\n• **확장성**: 트래픽에 따른 자동 스케일링\n\n무엇을 도와드릴까요? 😊",
                "suggestions": ["혜택 검색", "카테고리 보기", "사용법 알려줘"]
            }
        }
        
        if action not in quick_actions:
            return jsonify({
                "success": False,
                "error": f"지원되지 않는 액션: {action}",
                "available_actions": list(quick_actions.keys())
            }), 400
        
        action_data = quick_actions[action]
        
        response = {
            "message": action_data["message"],
            "type": "quick_reply",
            "data": {
                "suggestions": action_data["suggestions"],
                "action": action,
                "server": "EC2"
            },
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"퀵 리플라이 처리: action={action}, user_id={user_id}")
        
        return jsonify({
            "success": True,
            "response": response,
            "user_id": user_id,
            "server": "EC2"
        }), 200
        
    except Exception as e:
        logger.error(f"퀵 리플라이 처리 오류: {e}")
        return jsonify({
            "success": False,
            "error": "퀵 리플라이 처리 중 오류가 발생했습니다."
        }), 500




# ======================================================================================
# 개인화된 혜택 추천 RAG 시스템 (브랜드 인식 및 개인화 요청 처리 개선)
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
        """개인화된 혜택 검색 및 추천 (브랜드 매칭 실패 문제 해결)"""
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
        if not validation_result['valid']:
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
            final_results = PerplexityAPI.search(query)
            return self._generate_results_readonly(final_results, user_profile, parsed_info)
            
        
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
            
            # 🔧 모든 브랜드가 없을 때만 차단
            if missing_brands and len(missing_brands) == len(extracted_brands):
                if debug:
                    print(f"   ❌ 추출된 모든 브랜드 '{', '.join(missing_brands)}'가 DB에 없음")
                return {
                    'valid': False,
                    'message': self._generate_missing_brands_message(missing_brands, 'query')
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
    print("🎯 개선된 개인화 혜택 추천 RAG 시스템")
    print("=" * 80)
    print("🔧 주요 개선사항:")
    print("   ✅ 브랜드 인식 정확도 향상")
    print("   ✅ 개인화 요청 자동 감지")
    print("   ✅ 사용자 이력 모듈 분리")
    print("🚀 이제 브랜드와 개인화 모두 완벽 지원!")
    print("=" * 80)
    
    # RAG 시스템 초기화
    rag = PersonalizedBenefitRAG()
    
    # 데이터베이스 연결
    if not rag.connect_database():
        print("❌ 데이터베이스 연결 실패. 프로그램을 종료합니다.")
        return
    
    # 샘플 사용자 프로필 생성
    print("\n👤 샘플 사용자 프로필 생성...")
    sample_history = create_sample_user_history()
    user_profile = rag.create_user_profile(sample_history)
    
    # 사용자 프로필 요약 출력
    print(f"   📊 총 소비: {user_profile['total_spending']:,.0f}원 ({user_profile['total_transactions']}건)")
    print(f"   ⭐ 선호 브랜드: {dict(list(sorted(user_profile['brand_counts'].items(), key=lambda x: x[1], reverse=True))[:3])}")
    print(f"   🏷️ 선호 카테고리: {dict(user_profile['preferred_categories'][:3])}")
    print(f"   📅 최근 1주일 소비: {len(user_profile.get('recent_brands', []))}건")
    
    print("\n💬 RAG 혜택 추천 테스트!")
    print("💡 명령어: debug on/off, brands, categories, test")
    print("💡 종료: 'quit', 'exit', 'q'")
    print("-" * 80)
    
    debug_mode = False
    
    while True:
        try:
            query = input("\n🔧 질문: ").strip()
            
            # 종료 명령
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 서비스를 종료합니다.")
                break
            
            # 명령어 처리
            if query.lower() == 'debug on':
                debug_mode = True
                print("🐛 디버그 모드 활성화")
                continue
            elif query.lower() == 'debug off':
                debug_mode = False
                print("🔇 디버그 모드 비활성화")
                continue
            elif query.lower() == 'test':
                print("\n🧪 자동 테스트 시작...")
                test_queries = [
                    "스타벅스 할인 혜택 알려줘",
                    "내 소비 패턴에 맞는 혜택 추천해줘",
                    "카페 할인 이벤트 있어?",
                    "편의점 쿠폰 있나?",
                    "최근에 자주 간 곳 혜택 있어?"
                ]
                
                for test_query in test_queries:
                    print(f"\n🔍 테스트: {test_query}")
                    answer = rag.search_personalized_benefits(test_query, user_profile, debug=False)
                    print(f"📋 결과: {answer}")
                    print("-" * 50)
                
                print("✅ 자동 테스트 완료")
                continue
            elif query.lower() == 'brands':
                print(f"\n📦 현재 DB에 등록된 브랜드 ({len(rag.available_brands)}개):")
                if rag.available_brands:
                    sorted_brands = sorted(list(rag.available_brands))
                    for i, brand in enumerate(sorted_brands, 1):
                        print(f"   {i:2d}. {brand}")
                        if i % 20 == 0 and i < len(sorted_brands):
                            more = input("   ... 더 보시겠습니까? (y/n): ")
                            if more.lower() != 'y':
                                break
                else:
                    print("   브랜드 정보가 없습니다.")
                continue
            elif query.lower() == 'categories':
                print(f"\n🏷️ 현재 DB에 등록된 카테고리 ({len(rag.available_categories)}개):")
                if rag.available_categories:
                    sorted_categories = sorted(list(rag.available_categories))
                    for i, category in enumerate(sorted_categories, 1):
                        print(f"   {i:2d}. {category}")
                else:
                    print("   카테고리 정보가 없습니다.")
                continue
            
            # 빈 입력 무시
            if not query:
                continue
            
            print("\n⏳ RAG 검색 중...")
            
            # 개인화 혜택 검색 및 추천
            answer = rag.search_personalized_benefits(query, user_profile, debug=debug_mode)
            
            print(f"\n🔧 추천 결과:\n{answer}")
            print("-" * 80)
            
        except KeyboardInterrupt:
            print("\n\n👋 사용자가 중단했습니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            if debug_mode:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
# # ======================================================================================
# # 개인화된 혜택 추천 RAG 시스템 (user data 분리 전)
# # ======================================================================================

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
        """개인화된 혜택 검색 및 추천 (브랜드 매칭 실패 문제 해결)"""
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
        if not validation_result['valid']:
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
            final_re = search(query)
            return self._generate_no_results_message_enhanced(parsed_info, user_profile, analysis)
        
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
            
            # 🔧 모든 브랜드가 없을 때만 차단
            if missing_brands and len(missing_brands) == len(extracted_brands):
                if debug:
                    print(f"   ❌ 추출된 모든 브랜드 '{', '.join(missing_brands)}'가 DB에 없음")
                return {
                    'valid': False,
                    'message': self._generate_missing_brands_message(missing_brands, 'query')
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
            
            # 🔧 4단계: 벡터 검색 (브랜드 우선, 카테고리 차순위)
            try:
                # 브랜드가 있으면 해당 브랜드만 벡터 검색
                if extracted_brands:
                    brand_filtered_results = []
                    for brand in extracted_brands:
                        try:
                            brand_results = self.collection.query(
                                query_embeddings=[normalized_query_vector],
                                where={"brand": {"$eq": brand}},
                                n_results=top_k,
                                include=["metadatas", "distances", "documents"]
                            )
                            
                            if brand_results and brand_results.get('ids') and brand_results['ids'][0]:
                                for i in range(len(brand_results['ids'][0])):
                                    brand_filtered_results.append({
                                        "id": brand_results['ids'][0][i],
                                        "metadata": brand_results['metadatas'][0][i],
                                        "distance": brand_results['distances'][0][i],
                                        "document": brand_results['documents'][0][i],
                                        "vector_rank": i + 1
                                    })
                            
                            if debug:
                                result_count = len(brand_results['ids'][0]) if brand_results and brand_results.get('ids') else 0
                                print(f"🔍 '{brand}' 브랜드 벡터 검색: {result_count}개")
                                
                        except Exception as e:
                            if debug:
                                print(f"⚠️ '{brand}' 브랜드 벡터 검색 실패: {e}")
                            continue
                    
                    if brand_filtered_results:
                        limited_results = brand_filtered_results[:top_k]
                        print(f"✅ 브랜드 필터링 벡터 검색 성공: {len(limited_results)}개 (브랜드: {extracted_brands})")
                        return limited_results
                
                # 카테고리가 있으면 해당 카테고리만 벡터 검색
                elif extracted_categories:
                    category_filtered_results = []
                    for category in extracted_categories:
                        try:
                            cat_results = self.collection.query(
                                query_embeddings=[normalized_query_vector],
                                where={"category": {"$eq": category}},
                                n_results=top_k,
                                include=["metadatas", "distances", "documents"]
                            )
                            
                            if cat_results and cat_results.get('ids') and cat_results['ids'][0]:
                                for i in range(len(cat_results['ids'][0])):
                                    category_filtered_results.append({
                                        "id": cat_results['ids'][0][i],
                                        "metadata": cat_results['metadatas'][0][i],
                                        "distance": cat_results['distances'][0][i],
                                        "document": cat_results['documents'][0][i],
                                        "vector_rank": i + 1
                                    })
                            
                            if debug:
                                result_count = len(cat_results['ids'][0]) if cat_results and cat_results.get('ids') else 0
                                print(f"🔍 '{category}' 카테고리 벡터 검색: {result_count}개")
                                
                        except Exception as e:
                            if debug:
                                print(f"⚠️ '{category}' 카테고리 벡터 검색 실패: {e}")
                            continue
                    
                    if category_filtered_results:
                        limited_results = category_filtered_results[:top_k]
                        print(f"✅ 카테고리 필터링 벡터 검색 성공: {len(limited_results)}개 (카테고리: {extracted_categories})")
                        return limited_results
                
                # 브랜드/카테고리 모두 없으면 일반 벡터 검색
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
        
        print(f"🔄 개인화 스코어링: {len(results)}개 결과 (만능 벡터 유사도)")
        
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
                
                if debug:
                    print(f"   [{i+1}] 처리중: {brand} - {metadata.get('title')}")
                
                # 기본 검증
                if not self._validate_result(metadata, current_date):
                    if debug:
                        print(f"      ❌ 검증 실패: {brand}")
                    continue
                
                # 1순위: 최근 소비 가중치 (40%)
                recent_weight = self._calculate_recent_spending_weight(
                    brand, category, user_profile, parsed_info
                )
                recent_weight = min(max(recent_weight, 0), 1)
                
                # 2순위: 개인 선호도 점수 (30%)
                preference_score = self.score_calculator.calculate_preference_score(
                    brand, category, user_profile
                )
                preference_score = min(max(preference_score, 0), 1)
                
                # 3순위: 예상 절감액 점수 (25%)
                avg_spending = user_profile.get('avg_spending_per_brand', {}).get(brand, 
                              user_profile.get('total_spending', 0) / max(user_profile.get('total_transactions', 1), 1))
                
                raw_savings = self.score_calculator.calculate_potential_savings(
                    benefit_type, discount_rate, avg_spending
                )
                
                normalization_base = max(avg_spending, 50000)
                savings_score = min(raw_savings / normalization_base, 1.0) if normalization_base > 0 else 0
                savings_score = min(max(savings_score, 0), 1)
                
                # 🔧 4순위: 만능 벡터 유사도 (5%)
                distance = result.get('distance', 0)
                vector_score = self.calculate_vector_similarity_universal(distance, all_distances)
                
                if debug:
                    print(f"      🔧 거리: {distance:.6f} → 유사도: {vector_score:.3f}")
                    print(f"      📊 점수: recent={recent_weight:.3f}, prefer={preference_score:.3f}, savings={savings_score:.3f}, vector={vector_score:.3f}")
                
                # 최종 개인화 점수 계산
                personalized_score = (
                    vector_score * 0.40 +        # 쿼리 관련성 최우선
                    recent_weight * 0.25 +       # 개인화 1순위
                    preference_score * 0.20 +    # 개인화 2순위
                    savings_score * 0.15         # 실용성
                )
                
                personalized_score = min(max(personalized_score, 0), 1)
                
                if debug:
                    print(f"      🎯 최종 점수: {personalized_score:.3f}")
                
                # 결과에 점수 저장
                result['personalized_score'] = personalized_score
                result['recent_weight'] = recent_weight
                result['preference_score'] = preference_score
                result['savings_score'] = savings_score
                result['vector_score'] = vector_score
                result['expected_savings'] = raw_savings
                
                scored_results.append(result)
                
            except Exception as e:
                if debug:
                    print(f"      ❌ 오류: {e}")
                continue
        
        print(f"✅ 개인화 스코어링 완료: {len(scored_results)}/{len(results)}개 처리")
        return scored_results
    
    def _calculate_recent_spending_weight(self, brand: str, category: str, 
                                        user_profile: Dict, parsed_info: Dict) -> float:
        """최근 소비 기반 가중치 계산 (0-1 범위)"""
        # 1) 쿼리에서 명시된 소비 데이터 우선
        if parsed_info.get('spending_data'):
            spending_data = parsed_info['spending_data']
            if brand in spending_data:
                return 1.0  # 최고 가중치
            # 같은 카테고리면 중간 가중치
            for b, data in spending_data.items():
                if data.get('category') == category:
                    return 0.6
        
        # 2) 최근 1주일 소비 이력
        recent_brands = user_profile.get('recent_brands', [])
        recent_weight = 0.0
        
        for recent in recent_brands:
            if recent['brand'] == brand:
                recent_weight = max(recent_weight, recent.get('weight', 0))
            elif recent['category'] == category:
                recent_weight = max(recent_weight, recent.get('weight', 0) * 0.5)
        
        return min(recent_weight, 1.0)  # 1.0 초과 방지
    
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
            print("❌ 순위 결정: 입력 결과 없음")
            return []
        
        print(f"🔄 순위 결정 시작: {len(results)}개 결과")
        
        # 개인화 점수로 정렬
        try:
            sorted_results = sorted(results, key=lambda x: x.get('personalized_score', 0), reverse=True)
            print(f"✅ 정렬 완료: 최고점수 {sorted_results[0].get('personalized_score', 0):.3f}")
        except Exception as e:
            print(f"❌ 정렬 실패: {e}")
            return results[:top_k]
        
        # 다양성 보장
        final_results = []
        brand_count = defaultdict(int)
        max_per_brand = max(1, top_k // 3)
        
        for result in sorted_results:
            brand = result['metadata']['brand']
            
            if len(final_results) >= top_k:
                break
            
            if brand_count[brand] < max_per_brand:
                final_results.append(result)
                brand_count[brand] += 1
        
        # 부족하면 점수 순으로 추가
        if len(final_results) < top_k:
            remaining = top_k - len(final_results)
            for result in sorted_results:
                if result not in final_results and remaining > 0:
                    final_results.append(result)
                    remaining -= 1
        
        print(f"✅ 최종 선택: {len(final_results)}개 결과")
        
        # 벡터 유사도 구분력 확인
        vector_scores = [r.get('vector_score', 0) for r in final_results]
        if len(set(vector_scores)) > 1:
            print(f"✅ 벡터 유사도 구분력 있음: {min(vector_scores):.3f} ~ {max(vector_scores):.3f}")
        else:
            print(f"⚠️ 벡터 유사도 구분력 없음: 모두 {vector_scores[0]:.3f}")
        
        return final_results
    
    def _generate_results_readonly(self, results: List[Dict], user_profile: Dict, parsed_info: Dict = None) -> str:
        """🔒 검색 결과 생성 (읽기 전용)"""
        if not results:
            return self._generate_no_results_message_enhanced(parsed_info or {}, user_profile, {})
        
        try:
            message = f"🎯 개선된 개인화 혜택 추천 결과 (🔧 브랜드 인식 개선):\n\n"
            
            for i, result in enumerate(results[:5], 1):
                metadata = result.get('metadata', {})
                score = result.get('personalized_score', 0)
                expected_savings = result.get('expected_savings', 0)
                vector_score = result.get('vector_score', 0)
                distance = result.get('distance', 0)
                
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
                
                # 🔧 개선된 벡터 정보
                message += f"📊 개인화점수: {score:.3f} (예상절감: {expected_savings:,.0f}원)\n"
                if distance < 0:
                    message += f"   └ 벡터유사도: {vector_score:.3f} (거리: {distance:.3f}, IP 추정) 🔧\n\n"
                else:
                    message += f"   └ 벡터유사도: {vector_score:.3f} (거리: {distance:.3f}, {self.vector_space_type.upper()}) ✅\n\n"
            
            # 시스템 정보
            distances = [r.get('distance', 0) for r in results[:5]]
            vector_scores = [r.get('vector_score', 0) for r in results[:5]]
            
            message += f"🔧 브랜드 인식 개선 시스템 정보:\n"
            message += f"   • 벡터 공간: {self.vector_space_type.upper()}\n"
            message += f"   • 거리 범위: {min(distances):.3f} ~ {max(distances):.3f}\n"
            message += f"   • 유사도 범위: {min(vector_scores):.3f} ~ {max(vector_scores):.3f}\n"
            message += f"   • 등록 브랜드: {len(self.available_brands)}개\n"
            message += f"   • 등록 카테고리: {len(self.available_categories)}개\n"
            message += f"   • 브랜드 인식: ✅ 개선됨\n"
            message += f"   • 개인화 요청: ✅ 지원됨\n"
            
            return message.strip()
            
        except Exception as e:
            print(f"❌ 결과 생성 오류: {e}")
            return f"📋 검색 결과: {len(results)}개의 혜택을 찾았지만 출력 중 오류가 발생했습니다."
    
    def _generate_no_results_message_enhanced(self, parsed_info: Dict, user_profile: Dict, analysis: Dict) -> str:
        """🔍 향상된 결과 없음 메시지 (브랜드/카테고리 제안 포함)"""
        
        # 기본 메시지
        if parsed_info.get("spending_data"):
            brands = list(parsed_info["spending_data"].keys())
            brand_list = ", ".join(brands[:3])
            message = f"❌ {brand_list}에 대한 현재 진행중인 혜택 정보가 데이터베이스에 없습니다."
        elif parsed_info.get("max_spending_brand"):
            brand = parsed_info["max_spending_brand"]
            category = parsed_info.get("max_spending_category", "")
            message = f"❌ {brand}({category})에 대한 현재 진행중인 혜택 정보가 데이터베이스에 없습니다."
        else:
            message = "❌ 해당 조건에 맞는 혜택 정보가 데이터베이스에 없습니다."
        
        # 🔍 사용 가능한 브랜드/카테고리 제안 추가
        if self.available_brands and len(self.available_brands) > 0:
            # 사용자 소비 이력과 유사한 브랜드 우선 제안
            user_brands = set(user_profile.get('brand_counts', {}).keys())
            similar_brands = []
            
            # 1) 사용자가 이용한 브랜드 중 DB에 있는 것
            for user_brand in user_brands:
                if user_brand in self.available_brands:
                    similar_brands.append(user_brand)
            
            # 2) 부족하면 인기 브랜드로 채우기
            if len(similar_brands) < 6:
                popular_brands = list(self.available_brands)[:10]
                for brand in popular_brands:
                    if brand not in similar_brands and len(similar_brands) < 6:
                        similar_brands.append(brand)
            
            if similar_brands:
                message += f"\n\n💡 현재 혜택이 있는 추천 브랜드: {', '.join(similar_brands[:6])}"
                if len(self.available_brands) > 6:
                    message += f" 등 총 {len(self.available_brands)}개"
        
        if self.available_categories and len(self.available_categories) > 0:
            # 사용자 선호 카테고리 우선 제안
            user_categories = [cat for cat, _ in user_profile.get('preferred_categories', [])[:3]]
            similar_categories = []
            
            for user_cat in user_categories:
                if user_cat in self.available_categories:
                    similar_categories.append(user_cat)
            
            # 부족하면 인기 카테고리로 채우기
            if len(similar_categories) < 5:
                popular_categories = list(self.available_categories)[:8]
                for category in popular_categories:
                    if category not in similar_categories and len(similar_categories) < 5:
                        similar_categories.append(category)
            
            if similar_categories:
                message += f"\n💡 현재 혜택이 있는 추천 카테고리: {', '.join(similar_categories[:5])}"
        
        return message

    def _generate_missing_brands_message(self, missing_brands: List[str], context: str) -> str:
        """존재하지 않는 브랜드에 대한 메시지 생성"""
        if len(missing_brands) == 1:
            brand = missing_brands[0]
            message = f"❌ '{brand}' 브랜드는 현재 혜택 데이터베이스에 등록되어 있지 않습니다."
        else:
            brand_list = "', '".join(missing_brands)
            message = f"❌ '{brand_list}' 브랜드들은 현재 혜택 데이터베이스에 등록되어 있지 않습니다."
        
        # 사용 가능한 브랜드 제안
        if self.available_brands and len(self.available_brands) > 0:
            sample_brands = list(self.available_brands)[:8]
            message += f"\n\n💡 현재 지원하는 브랜드 예시: {', '.join(sample_brands)}"
            if len(self.available_brands) > 8:
                message += f" 등 총 {len(self.available_brands)}개 브랜드"
        
        return message


# API 클래스들 (기존과 동일)
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


# 테스트용 더미 사용자 데이터 (기존과 동일)
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


# 메인 실행 함수
def main():
    """메인 실행 함수"""
    print("🎯 개선된 개인화 혜택 추천 RAG 시스템")
    print("=" * 80)
    print("🔧 주요 개선사항:")
    print("   ✅ 브랜드 인식 정확도 향상 ('애플' 제대로 인식)")
    print("   ✅ 개인화 요청 자동 감지 ('내 소비 패턴에 맞는 혜택')")
    print("   ✅ 일반 단어 필터링 강화 ('알려줘', '패턴에' 등 제외)")
    print("   ✅ 확실한 브랜드만 DB 검증, 개인화 요청은 무조건 통과")
    print("   ✅ 사용자 선호 브랜드 기반 쿼리 확장")
    print("🚀 이제 브랜드와 개인화 모두 완벽 지원!")
    print("=" * 80)
    
    # RAG 시스템 초기화
    rag = PersonalizedBenefitRAG()
    
    # 데이터베이스 연결 (브랜드 목록 자동 로드)
    if not rag.connect_database():
        print("❌ 데이터베이스 연결 실패. 프로그램을 종료합니다.")
        return
    
    # 샘플 사용자 프로필 생성
    print("\n👤 샘플 사용자 프로필 생성...")
    sample_history = create_sample_user_history()
    user_profile = rag.create_user_profile(sample_history)
    
    # 사용자 프로필 요약 출력
    print(f"   📊 총 소비: {user_profile['total_spending']:,.0f}원 ({user_profile['total_transactions']}건)")
    print(f"   ⭐ 선호 브랜드: {dict(list(sorted(user_profile['brand_counts'].items(), key=lambda x: x[1], reverse=True))[:3])}")
    print(f"   🏷️ 선호 카테고리: {dict(user_profile['preferred_categories'][:3])}")
    print(f"   📅 최근 1주일 소비: {len(user_profile.get('recent_brands', []))}건")
    
    print("\n💬 개선된 RAG 혜택 추천 테스트!")
    print("📋 개선된 예시:")
    print("   ✅ '애플 할인 혜택 알려줘' (브랜드 인식 개선)")
    print("   ✅ '버거킹 이벤트 있어?' (없으면 명확히 안내)")
    print("   ✅ '내 소비 패턴에 맞는 혜택 추천해줘' (개인화 자동 감지)")
    print("   ✅ '지난주에 스타벅스 많이 썼어. 혜택 있어?' (개인화)")
    print("   ✅ '카페 할인 이벤트 있어?' (일반 검색)")
    print("\n💡 명령어: profile, debug on/off, newuser, brands, categories, test")
    print("💡 종료: 'quit', 'exit', 'q'")
    print("-" * 80)
    
    debug_mode = False
    
    while True:
        try:
            query = input("\n🔧 질문: ").strip()
            
            # 종료 명령
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 서비스를 종료합니다.")
                break
            
            # 명령어 처리
            if query.lower() == 'debug on':
                debug_mode = True
                print("🐛 디버그 모드 활성화")
                continue
            elif query.lower() == 'debug off':
                debug_mode = False
                print("🔇 디버그 모드 비활성화")
                continue
            elif query.lower() == 'test':
                print("\n🧪 자동 테스트 시작...")
                test_queries = [
                    "애플 할인 혜택 알려줘",
                    "버거킹 이벤트 있어?",
                    "내 소비 패턴에 맞는 혜택 추천해줘",
                    "지난주에 스타벅스 많이 썼어. 혜택 있어?",
                    "카페 할인 이벤트 있어?"
                ]
                
                for test_query in test_queries:
                    print(f"\n🔍 테스트: {test_query}")
                    print("⏳ 검색 중...")
                    answer = rag.search_personalized_benefits(test_query, user_profile, debug=False)
                    print(f"📋 결과: {answer[:200]}...")
                    print("-" * 50)
                
                print("✅ 자동 테스트 완료")
                continue
            elif query.lower() == 'brands':
                print(f"\n📦 현재 DB에 등록된 브랜드 ({len(rag.available_brands)}개):")
                if rag.available_brands:
                    sorted_brands = sorted(list(rag.available_brands))
                    for i, brand in enumerate(sorted_brands, 1):
                        print(f"   {i:2d}. {brand}")
                        if i % 20 == 0 and i < len(sorted_brands):
                            more = input("   ... 더 보시겠습니까? (y/n): ")
                            if more.lower() != 'y':
                                break
                else:
                    print("   브랜드 정보가 없습니다.")
                continue
            elif query.lower() == 'categories':
                print(f"\n🏷️ 현재 DB에 등록된 카테고리 ({len(rag.available_categories)}개):")
                if rag.available_categories:
                    sorted_categories = sorted(list(rag.available_categories))
                    for i, category in enumerate(sorted_categories, 1):
                        print(f"   {i:2d}. {category}")
                else:
                    print("   카테고리 정보가 없습니다.")
                continue
            elif query.lower() == 'profile':
                print("\n👤 현재 사용자 프로필:")
                print(f"   📊 총 소비: {user_profile['total_spending']:,.0f}원 ({user_profile['total_transactions']}건)")
                print(f"   💳 평균 거래액: {user_profile['total_spending']/max(user_profile['total_transactions'], 1):,.0f}원")
                
                print(f"\n   🏪 브랜드별 이용 횟수:")
                for brand, count in sorted(user_profile['brand_counts'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    avg_amount = user_profile['avg_spending_per_brand'].get(brand, 0)
                    db_status = "✅" if brand in rag.available_brands else "❌"
                    print(f"      {brand}: {count}회 (평균 {avg_amount:,.0f}원) {db_status}")
                
                print(f"\n   🏷️ 카테고리별 이용 횟수:")
                for category, count in user_profile['preferred_categories'][:5]:
                    db_status = "✅" if category in rag.available_categories else "❌"
                    print(f"      {category}: {count}회 {db_status}")
                
                print(f"\n   📅 최근 1주일 소비:")
                for recent in sorted(user_profile.get('recent_brands', []), key=lambda x: x['date'], reverse=True)[:5]:
                    db_status = "✅" if recent['brand'] in rag.available_brands else "❌"
                    print(f"      {recent['brand']}: {recent['amount']:,.0f}원 ({recent['date'].strftime('%m-%d')}) {db_status}")
                continue
            elif query.lower() == 'newuser':
                print("👤 새로운 사용자 프로필 생성...")
                sample_history = create_sample_user_history()
                user_profile = rag.create_user_profile(sample_history)
                print("✅ 새 프로필 생성 완료")
                continue
            
            # 빈 입력 무시
            if not query:
                continue
            
            print("\n⏳ 개선된 RAG 검색 중...")
            
            # 🔧 개선된 개인화 혜택 검색 및 추천
            answer = rag.search_personalized_benefits(query, user_profile, debug=debug_mode)
            
            print(f"\n🔧 개선된 추천 결과:\n{answer}")
            print("-" * 80)
            
        except KeyboardInterrupt:
            print("\n\n👋 사용자가 중단했습니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            if debug_mode:
                import traceback
                traceback.print_exc()


# if __name__ == "__main__":
#     main()