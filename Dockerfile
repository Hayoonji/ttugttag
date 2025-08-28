# ======================================================================================
# Docker 배포용 Dockerfile - 개인화된 혜택 추천 API
# ======================================================================================

# 베이스 이미지 - Python 3.11 slim 버전 사용
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="Benefits API Team"
LABEL version="2.1.0"
LABEL description="EC2 Personal Benefits Recommendation API with Chatbot"

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY *.py ./
COPY tools/ ./tools/
COPY env.example .env
COPY database_schema.sql ./
COPY setup_database_enhanced.sh ./
COPY enhanced_db/ ./enhanced_db/

# 데이터 및 로그 디렉토리 생성
RUN mkdir -p /app/data/cafe_vector_db \
    /app/logs \
    /app/static

# 포트 노출
EXPOSE 5001

# 기본 명령어 (Flask 개발 서버로 시작)
CMD ["python3", "app.py"]
