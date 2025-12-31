#!/bin/bash
# 배포 서버 자동 복구 스크립트
# 문제를 자동으로 수정하고 서버를 재시작합니다.

echo "=========================================="
echo "🔧 배포 서버 자동 복구 시작"
echo "=========================================="

cd /home/ubuntu/RohaTax-App || exit 1

# 1. 기존 프로세스 완전 종료
echo ""
echo "1️⃣ 기존 프로세스 종료"
echo "----------------------------------------"
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
pkill -9 -f "python3.*app.py" 2>/dev/null || true
screen -S rohatax -X quit 2>/dev/null || true
sleep 2
echo "✅ 기존 프로세스 종료 완료"

# 2. 가상환경 확인 및 활성화
echo ""
echo "2️⃣ 가상환경 확인"
echo "----------------------------------------"
if [ ! -d "venv" ]; then
    echo "❌ venv 디렉토리가 없습니다. 가상환경을 생성합니다."
    python3 -m venv venv
fi

source venv/bin/activate || exit 1
echo "✅ 가상환경 활성화 완료"

# 3. 의존성 업데이트 (Pydantic V2 호환성)
echo ""
echo "3️⃣ 의존성 확인 및 업데이트"
echo "----------------------------------------"
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt --quiet
    echo "✅ 의존성 설치 완료"
else
    echo "⚠️ requirements.txt 없음"
fi

# 4. 환경 변수 설정
echo ""
echo "4️⃣ 환경 변수 설정"
echo "----------------------------------------"
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
export FLASK_ENV=production
echo "✅ 환경 변수 설정 완료"

# 5. 로그 디렉토리 생성
echo ""
echo "5️⃣ 로그 디렉토리 준비"
echo "----------------------------------------"
mkdir -p logs
chmod -R 777 logs/ 2>/dev/null || true
echo "✅ 로그 디렉토리 준비 완료"

# 6. 코드 문법 검사
echo ""
echo "6️⃣ 코드 문법 검사"
echo "----------------------------------------"
if python3 -m py_compile app.py 2>&1 | grep -q "SyntaxError"; then
    echo "❌ app.py에 문법 오류가 있습니다."
    python3 -m py_compile app.py
    exit 1
else
    echo "✅ 코드 문법 검사 통과"
fi

# 7. 데이터베이스 초기화 확인
echo ""
echo "7️⃣ 데이터베이스 확인"
echo "----------------------------------------"
mkdir -p database
if [ ! -f "database/app.db" ]; then
    echo "⚠️ 데이터베이스 파일이 없습니다. 초기화가 필요할 수 있습니다."
fi

# 8. 서버 실행 (screen 세션 사용)
echo ""
echo "8️⃣ Flask 서버 시작"
echo "----------------------------------------"
# 기존 screen 세션 제거
screen -S rohatax -X quit 2>/dev/null || true
sleep 1

# screen 세션으로 실행
screen -dmS rohatax bash -c "
    cd /home/ubuntu/RohaTax-App
    source venv/bin/activate
    export FLASK_RUN_HOST=0.0.0.0
    export FLASK_RUN_PORT=5000
    export FLASK_ENV=production
    python3 app.py 2>&1 | tee /home/ubuntu/flask_server.log
"

# 5초 대기
sleep 5

# 9. 실행 확인
echo ""
echo "9️⃣ 서버 실행 확인"
echo "----------------------------------------"
if lsof -i :5000 > /dev/null 2>&1; then
    echo "✅ Flask 서버가 성공적으로 시작되었습니다!"
    echo "포트 5000에서 실행 중입니다."
    echo ""
    echo "📋 유용한 명령어:"
    echo "  - 로그 확인: tail -f /home/ubuntu/flask_server.log"
    echo "  - Screen 세션 확인: screen -r rohatax"
    echo "  - 서버 종료: screen -S rohatax -X quit"
    echo ""
    echo "최근 로그 (마지막 20줄):"
    tail -20 /home/ubuntu/flask_server.log
else
    echo "❌ Flask 서버 시작 실패"
    echo ""
    echo "오류 로그:"
    tail -50 /home/ubuntu/flask_server.log
    echo ""
    echo "수동 확인:"
    echo "  screen -r rohatax"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 복구 완료"
echo "=========================================="

