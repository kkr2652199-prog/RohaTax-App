#!/bin/bash
# 배포 서버 Flask 앱 실행 스크립트

cd /home/ubuntu/RohaTax-App || exit 1

# 기존 프로세스 종료
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
pkill -9 -f "python3.*app.py" 2>/dev/null || true
sleep 2

# 가상환경 활성화
source venv/bin/activate || exit 1

# 환경 변수 설정
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
export FLASK_ENV=production

# screen 세션으로 실행 (세션 유지)
screen -dmS rohatax bash -c "cd /home/ubuntu/RohaTax-App && source venv/bin/activate && export FLASK_RUN_HOST=0.0.0.0 && export FLASK_RUN_PORT=5000 && python3 app.py 2>&1 | tee /home/ubuntu/flask_server.log"

# 3초 대기
sleep 3

# 실행 확인
if lsof -i :5000 > /dev/null 2>&1; then
    echo "✅ Flask 서버가 성공적으로 시작되었습니다!"
    echo "포트 5000에서 실행 중입니다."
    echo ""
    echo "서버 로그 확인: tail -f /home/ubuntu/flask_server.log"
    echo "screen 세션 확인: screen -r rohatax"
    echo "서버 종료: screen -S rohatax -X quit"
else
    echo "❌ Flask 서버 시작 실패"
    echo "로그 확인: tail -30 /home/ubuntu/flask_server.log"
    exit 1
fi

