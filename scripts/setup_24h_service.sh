#!/bin/bash
# 서버 24시간 자동 실행 설정 스크립트
# 사용법: bash scripts/setup_24h_service.sh

set -e

echo "=========================================="
echo "🔧 서버 24시간 자동 실행 설정"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/RohaTax-App"
SERVICE_FILE="/etc/systemd/system/rohatax.service"
VENV_PATH="$PROJECT_DIR/venv"
APP_PATH="$PROJECT_DIR/app.py"
ENV_FILE="$PROJECT_DIR/.env"
LOG_DIR="$PROJECT_DIR/logs"

# 1. 기존 프로세스 종료
echo ""
echo "🛑 기존 프로세스 종료 중..."
pkill -f "python3 app.py" 2>/dev/null || true
lsof -ti:80 | xargs kill -9 2>/dev/null || true
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
sleep 2

# 2. 로그 디렉토리 생성
echo ""
echo "📁 로그 디렉토리 생성 중..."
mkdir -p "$LOG_DIR"

# 3. .env 파일 확인
echo ""
echo "🔐 .env 파일 확인 중..."
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️ .env 파일이 없습니다. 생성 중..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > "$ENV_FILE" << EOF
SECRET_KEY=${SECRET_KEY}
ENVIRONMENT=production
DEBUG=False
FLASK_APP=app.py
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=80
EOF
    echo "✅ .env 파일 생성 완료"
else
    echo "✅ .env 파일 존재 확인"
fi

# 4. Systemd 서비스 파일 생성
echo ""
echo "📝 Systemd 서비스 파일 생성 중..."
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

# 5. 서비스 파일 복사
echo ""
echo "📋 서비스 파일 복사 중..."
sudo cp /tmp/rohatax.service "$SERVICE_FILE"
sudo chmod 644 "$SERVICE_FILE"

# 6. Systemd 리로드
echo ""
echo "🔄 Systemd 리로드 중..."
sudo systemctl daemon-reload

# 7. 기존 서비스 중지 (있다면)
echo ""
echo "🛑 기존 서비스 중지 중..."
sudo systemctl stop rohatax.service 2>/dev/null || true

# 8. 서비스 활성화
echo ""
echo "✅ 서비스 활성화 중..."
sudo systemctl enable rohatax.service

# 9. 서비스 시작
echo ""
echo "🚀 서비스 시작 중..."
sudo systemctl start rohatax.service

# 10. 잠시 대기
sleep 5

# 11. 서비스 상태 확인
echo ""
echo "📊 서비스 상태 확인 중..."
if sudo systemctl is-active --quiet rohatax.service; then
    echo "✅ 서비스가 정상적으로 실행 중입니다!"
    echo ""
    sudo systemctl status rohatax.service --no-pager -l
else
    echo "❌ 서비스 시작 실패!"
    echo ""
    sudo systemctl status rohatax.service --no-pager -l
    echo ""
    echo "로그 확인:"
    sudo journalctl -u rohatax -n 50 --no-pager
    exit 1
fi

# 12. 포트 확인
echo ""
echo "🔍 포트 80 확인 중..."
if lsof -i :80 > /dev/null 2>&1; then
    echo "✅ 포트 80에서 실행 중"
    lsof -i :80
else
    echo "⚠️ 포트 80에서 실행되지 않음"
fi

# 13. HTTP 응답 확인
echo ""
echo "🌐 HTTP 응답 확인 중..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80 | grep -q "200"; then
    echo "✅ HTTP 응답 정상 (200 OK)"
else
    echo "⚠️ HTTP 응답 확인 필요"
fi

echo ""
echo "=========================================="
echo "✅ 24시간 자동 실행 설정 완료!"
echo "=========================================="
echo ""
echo "서비스 관리 명령어:"
echo "  시작: sudo systemctl start rohatax"
echo "  중지: sudo systemctl stop rohatax"
echo "  재시작: sudo systemctl restart rohatax"
echo "  상태: sudo systemctl status rohatax"
echo "  로그: sudo journalctl -u rohatax -f"
echo ""
echo "이제 로컬 PC를 꺼도 서버는 계속 실행됩니다! 🚀"
echo ""

