#!/bin/bash
# 배포 서버 안전장치 모니터링 설정 스크립트

PROJECT_DIR="/home/ubuntu/RohaTax-App"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

echo "🔧 배포 서버 안전장치 모니터링 설정 시작..."

# 스크립트 실행 권한 부여
chmod +x "$SCRIPTS_DIR/deployment_safety_monitor.sh"
chmod +x "$SCRIPTS_DIR/backup_verification.sh"

# 로그 디렉토리 생성
mkdir -p "$PROJECT_DIR/logs"

# Cron 작업 추가
(crontab -l 2>/dev/null; cat <<EOF
# 배포 서버 안전장치 모니터링 (매 5분마다)
*/5 * * * * $SCRIPTS_DIR/deployment_safety_monitor.sh

# 백업 검증 (매일 새벽 3시)
0 3 * * * $SCRIPTS_DIR/backup_verification.sh
EOF
) | crontab -

echo "✅ 안전장치 모니터링 설정 완료!"
echo ""
echo "설정된 Cron 작업:"
crontab -l | grep -E "(deployment_safety_monitor|backup_verification)"

