import streamlit as st
import sys
import os
import json
from datetime import datetime
import time

# 상위 디렉토리의 tools 폴더를 Python 경로에 추가
sys.path.append('../../tools')

# RAG 시스템 import
from main_rag_system import LangGraphRAGSystem
from user_history_data import create_sample_user_history

# 페이지 설정
st.set_page_config(
    page_title="TTUGTTAG - 개인화 혜택 추천 시스템",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .status-box {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success-status {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    .error-status {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    .info-status {
        background-color: #d1ecf1;
        border-color: #bee5eb;
        color: #0c5460;
    }
    .metric-card {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'user_history' not in st.session_state:
    st.session_state.user_history = None
if 'system_status' not in st.session_state:
    st.session_state.system_status = "초기화 필요"
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = True

def initialize_rag_system():
    """RAG 시스템 초기화"""
    try:
        with st.spinner("RAG 시스템을 초기화하는 중..."):
            # 환경 변수 설정 (테스트용)
            import os
            os.environ['CLOVA_STUDIO_API_KEY'] = 'test_key'
            os.environ['NAVER_CLIENT_ID'] = 'test_id'
            os.environ['NAVER_CLIENT_SECRET'] = 'test_secret'
            os.environ['CLOVA_OCR_API_KEY'] = 'test_key'
            os.environ['CLOVA_OCR_SECRET_KEY'] = 'test_secret'
            
            # 올바른 데이터베이스 경로 설정
            db_path = '../../cafe_vector_db'
            
            # RAG 시스템 생성
            rag = LangGraphRAGSystem(db_path=db_path)
            
            # 데이터베이스 연결 시도
            try:
                if rag.connect_database():
                    st.session_state.system_status = "데이터베이스 연결 성공"
                else:
                    st.session_state.system_status = "데이터베이스 연결 실패 - 기본 모드로 동작"
            except Exception as db_error:
                st.session_state.system_status = f"데이터베이스 오류 - 기본 모드로 동작: {str(db_error)}"
            
            # RAG 시스템은 기본 모드로라도 사용 가능
            st.session_state.rag_system = rag
            st.session_state.user_history = create_sample_user_history()
            return True
            
    except Exception as e:
        st.session_state.system_status = f"초기화 오류: {str(e)}"
        st.error(f"RAG 시스템 초기화 실패: {str(e)}")
        return False

def add_message(role, content, status_info=None):
    """채팅 메시지 추가"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": timestamp,
        "status_info": status_info
    })

def display_chat_message(message):
    """채팅 메시지 표시"""
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 사용자 ({message['timestamp']}):</strong><br>
            {message['content']}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message bot-message">
            <strong>🤖 TTUGTTAG ({message['timestamp']}):</strong><br>
            {message['content']}
        </div>
        """, unsafe_allow_html=True)
        
        # 상태 정보가 있으면 표시
        if message.get("status_info"):
            st.markdown(f"""
            <div class="status-box info-status">
                <strong>🔍 검색 과정:</strong><br>
                {message['status_info']}
            </div>
            """, unsafe_allow_html=True)

def run_rag_query(query, debug_mode=True):
    """RAG 쿼리 실행"""
    if not st.session_state.rag_system:
        return "❌ RAG 시스템이 초기화되지 않았습니다. 먼저 시스템을 초기화해주세요.", "시스템 미초기화"
    
    try:
        # 상태 정보를 수집하기 위한 콜백
        status_messages = []
        
        def status_callback(status):
            status_messages.append(status)
        
        # 쿼리 실행
        with st.spinner("검색 중..."):
            result = st.session_state.rag_system.run(
                query, 
                st.session_state.user_history, 
                debug=debug_mode
            )
        
        # 상태 정보 생성
        status_info = "\n".join(status_messages) if status_messages else "검색 완료"
        
        return result, status_info
        
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}", f"오류: {str(e)}"

# 메인 앱
def main():
    # 헤더
    st.markdown('<h1 class="main-header">🎯 TTUGTTAG</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">The Ultimate Guide To The Best Offers & Deals</p>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        
        # 시스템 초기화
        if st.button("🔄 RAG 시스템 초기화", type="primary"):
            if initialize_rag_system():
                st.success("✅ 시스템 초기화 완료!")
                add_message("assistant", "✅ RAG 시스템이 성공적으로 초기화되었습니다!")
            else:
                st.error("❌ 시스템 초기화 실패")
                add_message("assistant", "❌ RAG 시스템 초기화에 실패했습니다.")
        
        # 시스템 상태 표시
        st.subheader("📊 시스템 상태")
        if st.session_state.system_status == "데이터베이스 연결 성공":
            st.success("🟢 시스템 준비 완료")
        else:
            st.error("🔴 시스템 초기화 필요")
        
        # 디버그 모드 토글
        st.session_state.debug_mode = st.checkbox("🐛 디버그 모드", value=st.session_state.debug_mode)
        
        # 사용자 이력 정보
        if st.session_state.user_history:
            st.subheader("👤 사용자 이력")
            total_spending = sum(item['amount'] for item in st.session_state.user_history)
            st.metric("총 소비액", f"{total_spending:,}원")
            st.metric("거래 횟수", len(st.session_state.user_history))
            
            # 브랜드별 소비 통계
            brand_counts = {}
            for item in st.session_state.user_history:
                brand = item['brand']
                brand_counts[brand] = brand_counts.get(brand, 0) + item['amount']
            
            if brand_counts:
                st.subheader("🏷️ 브랜드별 소비")
                for brand, amount in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    st.write(f"• {brand}: {amount:,}원")
        
        # 예시 쿼리
        st.subheader("💡 예시 쿼리")
        example_queries = [
            "스타벅스 할인 혜택 있어?",
            "내 소비 패턴에 맞는 혜택 추천해줘",
            "카페 할인 이벤트 궁금해",
            "편의점 쿠폰 있나?",
            "이마트에서 10만원 썼어, 혜택 추천해줘"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{query}"):
                st.session_state.example_query = query
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 개인화 혜택 추천 채팅")
        
        # 채팅 히스토리 표시
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(message)
        
        # 입력 폼
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "질문을 입력하세요:",
                placeholder="예: 스타벅스 할인 혜택 있어?",
                height=100
            )
            
            submit_col1, submit_col2 = st.columns([1, 1])
            with submit_col1:
                submit_button = st.form_submit_button("🚀 검색 시작", type="primary")
            with submit_col2:
                clear_button = st.form_submit_button("🗑️ 대화 초기화")
        
        # 예시 쿼리 처리
        if hasattr(st.session_state, 'example_query'):
            user_input = st.session_state.example_query
            del st.session_state.example_query
            submit_button = True
        
        # 폼 제출 처리
        if submit_button and user_input.strip():
            # 사용자 메시지 추가
            add_message("user", user_input.strip())
            
            # RAG 쿼리 실행
            result, status_info = run_rag_query(user_input.strip(), st.session_state.debug_mode)
            
            # 봇 응답 추가
            add_message("assistant", result, status_info)
            
            # 페이지 새로고침
            st.rerun()
        
        # 대화 초기화
        if clear_button:
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        st.header("📈 실시간 통계")
        
        # 검색 통계
        if st.session_state.messages:
            user_messages = [m for m in st.session_state.messages if m["role"] == "user"]
            bot_messages = [m for m in st.session_state.messages if m["role"] == "assistant"]
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("총 대화 수", len(st.session_state.messages))
            with metric_col2:
                st.metric("검색 횟수", len(user_messages))
        
        # 시스템 정보
        st.subheader("🔧 시스템 정보")
        if st.session_state.rag_system:
            st.info("✅ RAG 시스템 활성화")
            st.info("✅ ChromaDB 연결됨")
            st.info("✅ 개인화 엔진 준비")
        else:
            st.warning("⚠️ RAG 시스템 미초기화")
        
        # 최근 검색 결과 미리보기
        if st.session_state.messages:
            st.subheader("🔍 최근 검색 결과")
            recent_results = [m for m in st.session_state.messages if m["role"] == "assistant"][-3:]
            
            for i, result in enumerate(reversed(recent_results)):
                with st.expander(f"검색 결과 {len(recent_results) - i}"):
                    st.write(result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"])
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        🎯 TTUGTTAG - The Ultimate Guide To The Best Offers & Deals<br>
        LangGraph 기반 개인화 혜택 추천 시스템
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 