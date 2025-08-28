# 🔧 데이터베이스 초기화 문제 해결 가이드

## 🔍 문제 상황

```
데이터베이스가 비어있습니다. 데이터를 추가해주세요.
검색 완료: 0개 결과 반환
```

## 📊 문제 원인

1. **매번 새로운 컬렉션 생성**: 서비스 재시작 시 빈 데이터베이스에서 시작
2. **혜택 데이터 미구축**: deploy.sh가 디렉토리만 생성하고 데이터는 구축하지 않음
3. **데이터 영구 저장 안됨**: 구축된 데이터가 서비스 재시작 시 유지되지 않음

## 🛠️ 해결 방법

### 1단계: 데이터베이스 상태 확인

```bash
# EC2 서버에서 실행
cd /path/to/your/project/ec2/
sudo bash check_database.sh
```

### 2단계: 자동 데이터베이스 구축

```bash
# EC2 서버에서 실행
cd /path/to/your/project/ec2/
sudo chmod +x setup_database.sh
sudo bash setup_database.sh
```

### 3단계: 수동 해결 (자동 구축 실패 시)

#### A. 소스 데이터 확인

```bash
# benefits_db 디렉토리에 JSON 파일들이 있는지 확인
ls -la ../benefits_db/*.json

# 없다면 다른 경로에서 찾기
find / -name "*_consolidated.json" 2>/dev/null
```

#### B. 데이터베이스 수동 구축

```bash
# 1. 기존 빈 데이터베이스 삭제
sudo rm -rf /opt/benefits-api/data/cafe_vector_db/*

# 2. tools/build_database.py 복사
sudo cp ../tools/build_database.py /opt/benefits-api/app/

# 3. 가상환경에서 구축
cd /opt/benefits-api/app
sudo -u benefits /opt/benefits-api/venv/bin/python build_database.py

# 4. 서비스 재시작
sudo systemctl restart benefits-api
```

### 4단계: 검증

```bash
# 1. 데이터베이스 파일 확인
ls -la /opt/benefits-api/data/cafe_vector_db/

# 2. API 테스트
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "스타벅스 혜택 알려주세요", "user_id": "test_user", "user_context": {"spending_history": []}}'

# 3. 로그 확인
sudo journalctl -u benefits-api -f
```

## 🔄 지속적 해결을 위한 deploy.sh 수정

기존 deploy.sh를 업데이트했습니다:

### 새로운 기능

- ✅ 기존 데이터베이스 자동 감지
- ✅ 비어있는 경우 자동 구축 시도
- ✅ setup_database.sh 스크립트 통합

### 사용 방법

```bash
# 전체 배포 (데이터베이스 포함)
sudo bash deploy.sh

# 데이터베이스 설정 건너뛰기
sudo bash deploy.sh --skip-db

# 앱 업데이트만
sudo bash deploy.sh --update-only
```

## 🚨 긴급 복구 방법

### 방법 1: 서비스 재시작

```bash
sudo systemctl stop benefits-api
sudo bash setup_database.sh
sudo systemctl start benefits-api
```

### 방법 2: 기존 데이터베이스 복사 (있는 경우)

```bash
# 다른 서버나 백업에서 복사
sudo rsync -av /backup/cafe_vector_db/ /opt/benefits-api/data/cafe_vector_db/
sudo chown -R benefits:benefits /opt/benefits-api/data/cafe_vector_db/
sudo systemctl restart benefits-api
```

### 방법 3: 컨테이너 방식으로 전환

```bash
# Docker 방식으로 전환 (권장)
cd ec2/
sudo docker-compose down
sudo docker-compose up -d --build
```

## 📋 예방 방법

### 1. 정기 백업 설정

```bash
# 크론탭에 추가
sudo crontab -e

# 매일 새벽 2시에 백업
0 2 * * * tar -czf /opt/benefits-api/backups/db_backup_$(date +\%Y\%m\%d).tar.gz /opt/benefits-api/data/cafe_vector_db/
```

### 2. 헬스체크 모니터링

```bash
# 5분마다 헬스체크
*/5 * * * * curl -f http://localhost/health || systemctl restart benefits-api
```

### 3. 로그 모니터링

```bash
# 특정 에러 발생 시 알림
sudo journalctl -u benefits-api -f | grep -i "empty\|error" | mail -s "API Error" admin@example.com
```

## 🔧 고급 진단

### 데이터베이스 상세 확인

```bash
# Python으로 직접 확인
cd /opt/benefits-api/app
sudo -u benefits /opt/benefits-api/venv/bin/python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/opt/benefits-api/data/cafe_vector_db')
collections = client.list_collections()
print(f'Collections: {len(collections)}')
for c in collections:
    print(f'  {c.name}: {c.count()} documents')
"
```

### 권한 문제 해결

```bash
# 전체 권한 재설정
sudo chown -R benefits:benefits /opt/benefits-api/
sudo chmod -R 755 /opt/benefits-api/
sudo chmod -R 644 /opt/benefits-api/data/
```

## 📞 문제 지속 시 체크리스트

- [ ] 디스크 용량 충분한가? (`df -h`)
- [ ] 메모리 충분한가? (`free -h`)
- [ ] 권한 올바른가? (`ls -la /opt/benefits-api/`)
- [ ] 환경 변수 설정됐나? (`cat /opt/benefits-api/app/.env`)
- [ ] 네트워크 연결 정상인가? (`curl http://localhost/health`)
- [ ] Python 가상환경 정상인가? (`/opt/benefits-api/venv/bin/python --version`)

## ✅ 성공 확인 방법

1. **로그에서 확인**:

   ```
   ✅ 데이터베이스 연결 성공
   ✅ 검색 완료: 5개 결과 반환
   ```

2. **API 응답 확인**:

   ```json
   {
     "success": true,
     "response": {
       "message": "스타벅스 관련 혜택을 찾았습니다..."
     }
   }
   ```

3. **웹 인터페이스**:
   - `http://서버IP/`에서 챗봇 테스트
   - 질문에 대한 정상적인 AI 응답 확인
