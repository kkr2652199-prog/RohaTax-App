#!/bin/bash
# 서버 초기 설정 및 배포 자동화 스크립트
# 사용법: bash scripts/server_setup.sh

set -e  # 오류 발생 시 중단

echo "=========================================="
echo "🚀 RohaTax 서버 배포 자동화"
echo "=========================================="

# 프로젝트 디렉토리로 이동
cd /home/ubuntu/RohaTax-App || exit 1

# 1. 가상환경 활성화
echo ""
echo "📦 가상환경 활성화 중..."
source venv/bin/activate

# 2. 데이터베이스 권한 수정
echo ""
echo "🔧 데이터베이스 권한 수정 중..."
sudo chown -R ubuntu:ubuntu database/ 2>/dev/null || true
chmod 644 database/*.db* 2>/dev/null || true

# 3. 배포 스크립트 실행
echo ""
echo "📋 데이터베이스 배포 스크립트 실행 중..."
python3 scripts/deploy_server.py

# 4. .env 파일 확인
echo ""
echo "🔐 환경 변수 확인 중..."
if [ ! -f .env ]; then
    echo "⚠️ .env 파일이 없습니다. SECRET_KEY를 생성합니다..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
ENVIRONMENT=production
DEBUG=False
FLASK_APP=app.py
EOF
    echo "✅ .env 파일 생성 완료"
else
    echo "✅ .env 파일 존재 확인"
fi

# 5. 서버 재시작
echo ""
echo "🔄 서버 재시작 중..."
pkill -f "python3 app.py" 2>/dev/null || true
sleep 2

# 포트 80으로 서버 시작
echo "서버 시작 중 (포트 80)..."
sudo -E env "PATH=$PATH" "FLASK_RUN_HOST=0.0.0.0" "FLASK_RUN_PORT=80" \
    /home/ubuntu/RohaTax-App/venv/bin/python3 app.py > app.log 2>&1 &

sleep 5

# 6. 서버 상태 확인
echo ""
echo "📊 서버 상태 확인 중..."
if lsof -i :80 > /dev/null 2>&1; then
    echo "✅ 서버가 포트 80에서 실행 중입니다"
    echo ""
    echo "최근 로그:"
    tail -10 app.log
else
    echo "❌ 서버 시작 실패. 로그 확인:"
    tail -20 app.log
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 배포 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. 브라우저에서 https://rohatax.com 접속"
echo "2. 로그인 테스트"
echo "3. 기능 테스트"

