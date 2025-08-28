#!/bin/bash

# ======================================================================================
# Tools 폴더 Hot-fix 배포 스크립트
# ======================================================================================

set -e

# 설정
APP_DIR="/opt/benefits-api"
APP_USER="ec2-user"

echo "🔧 Tools 폴더 Hot-fix 배포 시작..."

# 1. 기존 tools 폴더 백업
if [ -d "${APP_DIR}/app/tools" ]; then
    sudo cp -r "${APP_DIR}/app/tools" "${APP_DIR}/app/tools.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 기존 tools 폴더 백업 완료"
fi

# 2. 새 tools 폴더 복사
sudo cp -r tools "${APP_DIR}/app/"
sudo chown -R "$APP_USER:$APP_USER" "${APP_DIR}/app/tools"
echo "✅ 새 tools 폴더 복사 완료"

# 3. 서비스 재시작
sudo systemctl restart benefits-api
echo "✅ 서비스 재시작 완료"

# 4. 상태 확인
sleep 3
if sudo systemctl is-active --quiet benefits-api; then
    echo "🎉 서비스가 성공적으로 실행 중입니다!"
    sudo systemctl status benefits-api --no-pager -l
else
    echo "❌ 서비스 시작 실패. 로그를 확인하세요:"
    sudo journalctl -u benefits-api --no-pager -n 20
fi

echo "📋 배포 완료!"
