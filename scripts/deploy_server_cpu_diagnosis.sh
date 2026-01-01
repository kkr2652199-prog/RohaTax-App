#!/bin/bash
# 배포 서버 CPU 급상승 진단 스크립트
# 실행: bash scripts/deploy_server_cpu_diagnosis.sh

echo "=========================================="
echo "배포 서버 CPU 급상승 진단 시작"
echo "=========================================="
echo ""

# 1. 현재 시간 및 시스템 정보
echo "[1단계] 시스템 기본 정보"
echo "----------------------------------------"
echo "현재 시간: $(date)"
echo "호스트명: $(hostname)"
echo "Uptime: $(uptime)"
echo ""

# 2. CPU 사용량 확인 (상위 10개 프로세스)
echo "[2단계] CPU 사용량 상위 프로세스 (상위 10개)"
echo "----------------------------------------"
ps aux --sort=-%cpu | head -11
echo ""

# 3. 메모리 사용량 확인
echo "[3단계] 메모리 사용량"
echo "----------------------------------------"
free -h
echo ""

# 4. 디스크 사용량 확인
echo "[4단계] 디스크 사용량"
echo "----------------------------------------"
df -h
echo ""

# 5. Flask 서비스 상태 확인
echo "[5단계] Flask 서비스 상태"
echo "----------------------------------------"
systemctl status rohatax --no-pager -l | head -20
echo ""

# 6. 최근 서비스 로그 (에러 위주)
echo "[6단계] 최근 서비스 로그 (최근 50줄, 에러 위주)"
echo "----------------------------------------"
journalctl -u rohatax -n 50 --no-pager | grep -i -E "error|exception|traceback|failed|critical" || echo "최근 에러 로그 없음"
echo ""

# 7. Python 프로세스 확인
echo "[7단계] Python 프로세스 상세 정보"
echo "----------------------------------------"
ps aux | grep -E "python|gunicorn|flask" | grep -v grep
echo ""

# 8. 네트워크 연결 확인 (많은 연결이 있으면 문제)
echo "[8단계] 활성 네트워크 연결 수"
echo "----------------------------------------"
# netstat 대신 ss 명령어 사용 (더 현대적이고 대부분의 리눅스에 기본 설치됨)
if command -v ss &> /dev/null; then
    echo "ESTABLISHED 연결 수: $(ss -an | grep ESTABLISHED | wc -l)"
    echo "TIME_WAIT 연결 수: $(ss -an | grep TIME_WAIT | wc -l)"
elif command -v netstat &> /dev/null; then
    echo "ESTABLISHED 연결 수: $(netstat -an | grep ESTABLISHED | wc -l)"
    echo "TIME_WAIT 연결 수: $(netstat -an | grep TIME_WAIT | wc -l)"
else
    echo "⚠️  netstat 또는 ss 명령어를 찾을 수 없습니다"
    echo "   네트워크 연결 확인을 건너뜁니다"
fi
echo ""

# 9. 데이터베이스 파일 크기 및 잠금 확인
echo "[9단계] 데이터베이스 상태"
echo "----------------------------------------"
if [ -f "/home/ubuntu/RohaTax-App/database/app.db" ]; then
    echo "데이터베이스 파일 크기: $(ls -lh /home/ubuntu/RohaTax-App/database/app.db | awk '{print $5}')"
    echo "데이터베이스 파일 수정 시간: $(ls -l /home/ubuntu/RohaTax-App/database/app.db | awk '{print $6, $7, $8}')"
    # SQLite 잠금 확인 (간접적으로)
    if lsof /home/ubuntu/RohaTax-App/database/app.db 2>/dev/null; then
        echo "⚠️  데이터베이스 파일이 다른 프로세스에 의해 사용 중입니다"
    else
        echo "✅ 데이터베이스 파일 잠금 없음"
    fi
else
    echo "⚠️  데이터베이스 파일을 찾을 수 없습니다"
fi
echo ""

# 10. 최근 접근 로그 확인 (Nginx/Apache가 있다면)
echo "[10단계] 웹 서버 접근 로그 (최근 20줄)"
echo "----------------------------------------"
if [ -f "/var/log/nginx/access.log" ]; then
    tail -20 /var/log/nginx/access.log
elif [ -f "/var/log/apache2/access.log" ]; then
    tail -20 /var/log/apache2/access.log
else
    echo "웹 서버 로그 파일을 찾을 수 없습니다"
fi
echo ""

# 11. 시스템 부하 평균
echo "[11단계] 시스템 부하 평균 (1분, 5분, 15분)"
echo "----------------------------------------"
uptime | awk -F'load average:' '{print $2}'
echo ""

# 12. I/O 대기 확인
echo "[12단계] I/O 대기 프로세스"
echo "----------------------------------------"
ps aux | awk '$8 ~ /D/ {print $0}' | head -10 || echo "I/O 대기 프로세스 없음"
echo ""

echo "=========================================="
echo "진단 완료"
echo "=========================================="
echo ""
echo "💡 다음 단계:"
echo "1. CPU 사용량이 높은 프로세스 확인"
echo "2. Flask 서비스 로그에서 에러 패턴 확인"
echo "3. 데이터베이스 잠금 확인"
echo "4. 네트워크 연결 수 확인 (DDoS 가능성)"
echo ""

