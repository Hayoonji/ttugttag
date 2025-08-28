# ======================================================================================
# EC2 서버용 개인화된 혜택 추천 API - app.py
# ======================================================================================

import os
import json
import logging
import datetime
import sys
import traceback
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from tools.main_rag_system import LangGraphRAGSystem as PersonalizedBenefitRAG
# 로컬 모듈 import (tools에서 모든 것을 import)
from config import get_ec2_config
from tools.user_history_data import create_sample_user_history
from rag_system import create_user_profile_from_history

# Clova OCR SDK 분석기 import
from tools.clova_ocr_sdk_analyzer import ClovaOCRSDKAnalyzer

# 모든 필요한 모듈들을 tools 패키지에서 import
# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 앱 생성 (static 폴더 설정)
app = Flask(__name__, static_folder='../static', static_url_path='/static')
CORS(app, resources={r"/api/*": {"origins": "https://ttak.kwarke.com"}})


# 프록시 설정 (nginx 뒤에서 실행시)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# 글로벌 변수 (인스턴스 재사용)
rag_system = None
config = None
database_connected = False

# ======================================================================================
# API 엔드포인트
# ======================================================================================


def initialize_rag_system():
    """RAG 시스템 초기화"""
    global rag_system, config, database_connected
    
    if rag_system is not None and database_connected:
        return rag_system
    
    try:
        logger.info("🚀 EC2 RAG 시스템 초기화 중...")
        
        # 설정 로드
        if config is None:
            config = get_ec2_config()
            logger.info("✅ EC2 설정 로드 완료")
        
        # RAG 시스템 생성
        rag_system = PersonalizedBenefitRAG()
        
        # 데이터베이스 연결
        if rag_system.connect_database():
            database_connected = True
            logger.info("✅ RAG 시스템 초기화 및 DB 연결 완료")
            return rag_system
        else:
            logger.warning("⚠️ 데이터베이스 연결 실패 - 기본 모드로 동작")
            # 데이터베이스 연결 실패해도 기본 RAG 시스템은 사용 가능
            return rag_system
            
    except Exception as e:
        logger.error(f"❌ RAG 시스템 초기화 실패: {e}")
        logger.info("🔄 기본 모드로 전환 시도...")
        try:
            # 기본 설정으로 RAG 시스템 생성
            rag_system = PersonalizedBenefitRAG()
            return rag_system
        except Exception as e2:
            logger.error(f"❌ 기본 모드도 실패: {e2}")
            return None



def initialize_clova_ocr_analyzer():
    """Clova OCR SDK 분석기 초기화"""
    global config
    
    try:
        logger.info("🔍 Clova OCR SDK 분석기 초기화 중...")
        
        # 설정 로드
        if config is None:
            config = get_ec2_config()
            logger.info("✅ EC2 설정 로드 완료")
        
        # Clova OCR SDK 분석기 생성
        ocr_analyzer = ClovaOCRSDKAnalyzer(config)
        logger.info("✅ Clova OCR SDK 분석기 초기화 완료")
        
        return ocr_analyzer
        
    except Exception as e:
        logger.error(f"❌ Clova OCR SDK 분석기 초기화 실패: {e}")
        return None

# ======================================================================================
# API 엔드포인트들
# ======================================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "혜택 추천 RAG API",
        "database_connected": rag_system is not None and rag_system.collection is not None
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """시스템 상태 조회"""
    try:
        if not rag_system:
            return jsonify({"error": "시스템이 초기화되지 않았습니다"}), 500
        
        # 데이터베이스 상태 확인
        db_count = rag_system.collection.count() if rag_system.collection else 0
        
        return jsonify({
            "status": "운영중",
            "database": {
                "connected": rag_system.collection is not None,
                "total_documents": db_count,
                "available_brands": len(rag_system.available_brands),
                "available_categories": len(rag_system.available_categories)
            },
            "perplexity": {
                "available": rag_system.perplexity_api is not None
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": f"상태 확인 실패: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
def get_chat():
    query = request.json.get('query')
    debug_mode = request.json.get('debug', False)
    
    if not query:
        return jsonify({"error": "쿼리가 필요합니다"}), 400
    
    rag = initialize_rag_system()
    
    # RAG 시스템 초기화 확인
    if not rag:
        return jsonify({
            "success": False,
            "error": "RAG 시스템이 초기화되지 않았습니다."
        }), 503
    
    try:
        # 샘플 사용자 프로필 생성
        logger.info("\n👤 샘플 사용자 프로필 생성...")
        sample_history = create_sample_user_history()
        
        # LangGraphRAGSystem의 run 메서드 사용
        answer = rag.run(query, sample_history, debug=debug_mode)
        
        return jsonify({
            "success": True,
            "answer": answer
        })
        
    except Exception as e:
        logger.error(f"❌ RAG 시스템 실행 오류: {e}")
        return jsonify({
            "success": False,
            "error": f"RAG 시스템 실행 중 오류가 발생했습니다: {str(e)}"
        }), 500
    

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """이미지 업로드 및 브랜드 매칭 API"""
    try:
        # 이미지 파일 확인
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "error": "이미지 파일이 필요합니다."
            }), 400
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({
                "success": False,
                "error": "이미지 파일을 선택해주세요."
            }), 400
        
        # 디버그 모드 확인
        debug_mode = request.form.get('debug', 'false').lower() == 'true'
        
        if debug_mode:
            logger.info(f"🔍 이미지 분석 요청: {image_file.filename}")
        
        # 이미지 데이터 읽기
        image_data = image_file.read()
        
        # 통합 Clova OCR + 리워드 시스템 초기화
        analyzer = initialize_clova_ocr_analyzer()
        if not analyzer:
            return jsonify({
                "success": False,
                "error": "Clova OCR 분석기를 초기화할 수 없습니다."
            }), 503
        
        # 사용자 ID (실제 구현에서는 JWT 토큰에서 추출)
        user_id = request.form.get('user_id', 'test_user_001')
        
        # 이미지 분석 및 LLM 처리
        analysis_result = analyzer.analyze_image_with_llm(image_data, debug=debug_mode)
        
        if not analysis_result['success']:
            return jsonify({
                "success": False,
                "error": analysis_result['error']
            }), 500
        
        # 성공 응답 (OCR + LLM 분석 결과)
        return jsonify({
            "success": True,
            "data": {
                "extracted_text": analysis_result['extracted_text'],
                "extracted_date": analysis_result['extracted_date'],
                "matched_brands": analysis_result['matched_brands'],
                "confidence_scores": analysis_result['confidence_scores'],
                "llm_analysis": analysis_result.get('llm_analysis', {}),
                "analysis_summary": analysis_result['analysis_summary']
            },
            "message": f"이미지 분석 완료: {len(analysis_result['matched_brands'])}개 브랜드 매칭, LLM 분석: {analysis_result.get('llm_analysis', {}).get('summary', 'N/A')}"
        })
        
    except Exception as e:
        error_msg = f"이미지 분석 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500


# ======================================================================================
# 에러 핸들러
# ======================================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "엔드포인트를 찾을 수 없습니다.",
        "available_endpoints": {
            "web": ["/", "/health", "/api/info"],
            "api": ["/api/search", "/api/recommend", "/api/chat"]
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "서버 내부 오류가 발생했습니다.",
        "timestamp": datetime.datetime.now().isoformat()
    }), 500

# ======================================================================================
# HTML 템플릿 (임베디드)
# ======================================================================================

CHATBOT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>혜택 추천 챗봇 - EC2 버전</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .chat-container {
            width: 400px;
            height: 600px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8fafc;
        }
        .message {
            margin-bottom: 15px;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.bot { text-align: left; }
        .message.user { text-align: right; }
        .message-bubble {
            display: inline-block;
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            white-space: pre-wrap;
        }
        .message.bot .message-bubble {
            background: #e2e8f0;
            color: #2d3748;
            border-bottom-left-radius: 4px;
        }
        .message.user .message-bubble {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        .suggestion-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .suggestion-btn:hover {
            background: #5a67d8;
            transform: translateY(-1px);
        }
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e2e8f0;
        }
        .input-container {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .chat-input input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 20px;
            font-size: 14px;
            outline: none;
        }
        .send-btn {
            background: #667eea;
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .ec2-badge {
            background: #ff6b6b;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            margin-left: 8px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 혜택 추천 챗봇 <span class="ec2-badge">EC2</span></h1>
            <p>개인화된 할인 혜택을 찾아드려요!</p>
        </div>
        <div class="chat-messages" id="messages"></div>
        <div class="chat-input">
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="메시지를 입력하세요..." maxlength="500">
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">→</button>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;
        let userId = 'ec2_user_' + Date.now();

        window.onload = function() {
            setTimeout(startConversation, 500);
        };

        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        async function startConversation() {
            try {
                const response = await fetch('/api/chat/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, user_name: '고객님' })
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.response) {
                        addBotMessage(data.response.message, data.response.data?.suggestions || []);
                    }
                } else {
                    addBotMessage("API 연결에 실패했습니다. 서버 상태를 확인해주세요.", []);
                }
            } catch (error) {
                console.error('Error:', error);
                addBotMessage("API 연결 오류가 발생했습니다. 네트워크를 확인해주세요.", []);
            }
        }

        async function sendMessage(text = null) {
            if (isLoading) return;

            const message = text || document.getElementById('messageInput').value.trim();
            if (!message) return;

            addUserMessage(message);
            if (!text) document.getElementById('messageInput').value = '';
            showLoading();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        user_id: userId,
                        user_context: { spending_history: [] }
                    })
                });

                hideLoading();

                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.response) {
                        addBotMessage(data.response.message, data.response.data?.suggestions || []);
                    } else {
                        addBotMessage("응답을 처리하는 중 오류가 발생했습니다.", []);
                    }
                } else {
                    const errorData = await response.json();
                    addBotMessage(`오류: ${errorData.error || '알 수 없는 오류가 발생했습니다.'}`, []);
                }
            } catch (error) {
                hideLoading();
                console.error('Error:', error);
                addBotMessage("네트워크 오류가 발생했습니다. 다시 시도해주세요.", []);
            }
        }

        function addUserMessage(message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message user';
            messageDiv.innerHTML = `<div class="message-bubble">${escapeHtml(message)}</div>`;
            messagesDiv.appendChild(messageDiv);
            scrollToBottom();
        }

        function addBotMessage(message, suggestions = []) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            
            let suggestionsHtml = '';
            if (suggestions.length > 0) {
                suggestionsHtml = '<div class="suggestions">' +
                    suggestions.map(suggestion => 
                        `<button class="suggestion-btn" onclick="sendMessage('${escapeHtml(suggestion)}')">${escapeHtml(suggestion)}</button>`
                    ).join('') + '</div>';
            }
            
            messageDiv.innerHTML = `<div class="message-bubble">${escapeHtml(message)}</div>${suggestionsHtml}`;
            messagesDiv.appendChild(messageDiv);
            scrollToBottom();
        }

        function showLoading() {
            isLoading = true;
            document.getElementById('sendBtn').disabled = true;
        }

        function hideLoading() {
            isLoading = false;
            document.getElementById('sendBtn').disabled = false;
        }

        function scrollToBottom() {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML.replace(/\\n/g, '<br>');
        }
    </script>
</body>
</html>
"""



# ======================================================================================
# 메인 실행
# ======================================================================================

if __name__ == '__main__':
    # 환경 설정
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🚀 EC2 혜택 추천 API 서버 시작")
    logger.info(f"   포트: {port}")
    logger.info(f"   디버그: {debug}")
    
    # RAG 시스템 사전 초기화
    initialize_rag_system()
    
    # Flask 서버 실행
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
