#!/bin/bash

# ======================================================================================
# ChromaDB 초기화 스크립트
# ======================================================================================

set -e

echo "🚀 ChromaDB 초기화 시작..."

# ChromaDB 서버 시작
echo "📦 ChromaDB 서버 시작 중..."
chroma run --host 0.0.0.0 --port 8000 &

# 서버 준비 대기
echo "⏳ ChromaDB 서버 준비 대기 중..."
sleep 15

# Python 초기화 스크립트 실행
echo "🐍 ChromaDB 초기화 스크립트 실행 중..."
python3 /chroma/init-chroma.py

echo "🎉 ChromaDB 초기화 완료!"
echo "🌐 ChromaDB 서버: http://localhost:8000"

# 백그라운드 프로세스 유지
wait 