#!/bin/bash
# 배포 서버 진단 및 복구 스크립트
# 문제를 자동으로 진단하고 수정합니다.

echo "=========================================="
echo "🔍 배포 서버 진단 시작"
echo "=========================================="

cd /home/ubuntu/RohaTax-App || exit 1

# 1. 현재 상태 확인
echo ""
echo "1️⃣ 현재 프로세스 상태 확인"
echo "----------------------------------------"
echo "포트 5000 사용 중인 프로세스:"
lsof -i :5000 || echo "포트 5000 사용 중인 프로세스 없음"
echo ""
echo "Python 프로세스:"
ps aux | grep "python3.*app.py" | grep -v grep || echo "실행 중인 Flask 프로세스 없음"
echo ""
echo "Screen 세션:"
screen -ls || echo "Screen 세션 없음"

# 2. 로그 파일 확인
echo ""
echo "2️⃣ 최근 로그 확인 (마지막 50줄)"
echo "----------------------------------------"
if [ -f /home/ubuntu/flask_server.log ]; then
    echo "=== flask_server.log ==="
    tail -50 /home/ubuntu/flask_server.log
else
    echo "⚠️ flask_server.log 파일이 없습니다."
fi

# 3. 환경 변수 확인
echo ""
echo "3️⃣ 환경 변수 확인"
echo "----------------------------------------"
echo "FLASK_RUN_HOST: ${FLASK_RUN_HOST:-미설정}"
echo "FLASK_RUN_PORT: ${FLASK_RUN_PORT:-미설정}"
echo "FLASK_ENV: ${FLASK_ENV:-미설정}"

# 4. 가상환경 확인
echo ""
echo "4️⃣ 가상환경 확인"
echo "----------------------------------------"
if [ -d "venv" ]; then
    echo "✅ venv 디렉토리 존재"
    if [ -f "venv/bin/activate" ]; then
        echo "✅ venv/bin/activate 존재"
    else
        echo "❌ venv/bin/activate 없음"
    fi
else
    echo "❌ venv 디렉토리 없음"
fi

# 5. Python 의존성 확인
echo ""
echo "5️⃣ Python 의존성 확인"
echo "----------------------------------------"
source venv/bin/activate 2>/dev/null || echo "⚠️ 가상환경 활성화 실패"
python3 --version
pip list | grep -E "(Flask|Pydantic|Werkzeug)" || echo "⚠️ 주요 패키지 확인 실패"

# 6. 코드 문법 검사
echo ""
echo "6️⃣ 코드 문법 검사"
echo "----------------------------------------"
python3 -m py_compile app.py 2>&1 | head -20 || echo "⚠️ app.py 문법 오류"

# 7. 데이터베이스 확인
echo ""
echo "7️⃣ 데이터베이스 확인"
echo "----------------------------------------"
if [ -f "database/app.db" ]; then
    echo "✅ database/app.db 존재"
    ls -lh database/app.db
else
    echo "⚠️ database/app.db 없음"
fi

# 8. .env 파일 확인
echo ""
echo "8️⃣ .env 파일 확인"
echo "----------------------------------------"
if [ -f ".env" ]; then
    echo "✅ .env 파일 존재"
    echo "주요 환경 변수:"
    grep -E "(SECRET_KEY|DATABASE_URL|FLASK_ENV)" .env | sed 's/=.*/=***/' || echo "환경 변수 없음"
else
    echo "⚠️ .env 파일 없음"
fi

# 9. Pydantic 경고 확인
echo ""
echo "9️⃣ Pydantic 경고 확인"
echo "----------------------------------------"
echo "orm_mode 사용 위치 검색:"
grep -r "orm_mode" --include="*.py" . 2>/dev/null | head -5 || echo "orm_mode 사용 없음"

echo ""
echo "=========================================="
echo "✅ 진단 완료"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. 위의 오류를 확인하세요"
echo "2. 복구 스크립트를 실행하세요: bash 배포서버_복구_실행.sh"

