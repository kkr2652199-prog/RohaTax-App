#!/bin/bash
# Systemd 서비스 파일 생성 스크립트
# 사용법: bash scripts/create_systemd_service.sh

set -e

echo "=========================================="
echo "🔧 Systemd 서비스 파일 생성"
echo "=========================================="

SERVICE_FILE="/etc/systemd/system/rohatax.service"
PROJECT_DIR="/home/ubuntu/RohaTax-App"
VENV_PATH="$PROJECT_DIR/venv"
APP_PATH="$PROJECT_DIR/app.py"
ENV_FILE="$PROJECT_DIR/.env"
LOG_DIR="$PROJECT_DIR/logs"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 서비스 파일 내용
cat > /tmp/rohatax.service << EOF
[Unit]
Description=RohaTax Flask Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
Environment="FLASK_RUN_HOST=0.0.0.0"
Environment="FLASK_RUN_PORT=80"
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_PATH/bin/python3 $APP_PATH
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/app_service.log
StandardError=append:$LOG_DIR/app_service_error.log

[Install]
WantedBy=multi-user.target
EOF

# 서비스 파일 복사 (sudo 필요)
echo ""
echo "서비스 파일 생성 중..."
sudo cp /tmp/rohatax.service "$SERVICE_FILE"
sudo chmod 644 "$SERVICE_FILE"

# Systemd 리로드
echo "Systemd 리로드 중..."
sudo systemctl daemon-reload

# 서비스 활성화
echo "서비스 활성화 중..."
sudo systemctl enable rohatax.service

echo ""
echo "=========================================="
echo "✅ 서비스 파일 생성 완료!"
echo "=========================================="
echo ""
echo "다음 명령어로 서비스 관리:"
echo "  시작: sudo systemctl start rohatax"
echo "  중지: sudo systemctl stop rohatax"
echo "  재시작: sudo systemctl restart rohatax"
echo "  상태: sudo systemctl status rohatax"
echo "  로그: sudo journalctl -u rohatax -f"
echo ""

