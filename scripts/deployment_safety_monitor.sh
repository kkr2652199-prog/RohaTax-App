#!/bin/bash
# 배포 서버 안전장치 모니터링 스크립트
# 매 5분마다 실행 (cron: */5 * * * *)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/ubuntu/RohaTax-App"
LOG_FILE="$PROJECT_DIR/logs/safety_monitor.log"
ALERT_EMAIL=""  # 필요시 이메일 설정

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 서비스 상태 확인
check_service() {
    if systemctl is-active --quiet rohatax; then
        return 0
    else
        log "❌ CRITICAL: rohatax 서비스가 중지되었습니다!"
        systemctl restart rohatax
        log "🔄 서비스 재시작 시도 완료"
        return 1
    fi
}

# 디스크 공간 확인
check_disk_space() {
    USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$USAGE" -gt 90 ]; then
        log "⚠️ WARNING: 디스크 사용량이 ${USAGE}%입니다!"
        return 1
    fi
    return 0
}

# 메모리 사용량 확인
check_memory() {
    MEMORY=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$MEMORY" -gt 90 ]; then
        log "⚠️ WARNING: 메모리 사용량이 ${MEMORY}%입니다!"
        return 1
    fi
    return 0
}

# 백업 파일 확인
check_backups() {
    BACKUP_DIR="$PROJECT_DIR/database/backups"
    if [ ! -d "$BACKUP_DIR" ]; then
        log "⚠️ WARNING: 백업 디렉토리가 없습니다!"
        return 1
    fi
    
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.db" -mtime -1 | wc -l)
    if [ "$BACKUP_COUNT" -eq 0 ]; then
        log "⚠️ WARNING: 최근 24시간 내 백업 파일이 없습니다!"
        return 1
    fi
    
    return 0
}

# 헬스체크 엔드포인트 확인
check_health() {
    HEALTH=$(curl -s http://localhost/health 2>/dev/null)
    if [ -z "$HEALTH" ] || echo "$HEALTH" | grep -q '"status":"unhealthy"'; then
        log "❌ CRITICAL: 헬스체크 실패!"
        return 1
    fi
    return 0
}

# 로그 파일 크기 확인
check_log_size() {
    LOG_DIR="$PROJECT_DIR/logs"
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            SIZE=$(du -m "$log_file" | cut -f1)
            if [ "$SIZE" -gt 100 ]; then
                log "⚠️ WARNING: 로그 파일이 너무 큽니다: $(basename $log_file) (${SIZE}MB)"
            fi
        fi
    done
}

# 메인 실행
main() {
    log "🔍 안전장치 모니터링 시작"
    
    ERRORS=0
    
    check_service || ((ERRORS++))
    check_disk_space || ((ERRORS++))
    check_memory || ((ERRORS++))
    check_backups || ((ERRORS++))
    check_health || ((ERRORS++))
    check_log_size
    
    if [ $ERRORS -eq 0 ]; then
        log "✅ 모든 안전장치 정상"
    else
        log "⚠️ 총 $ERRORS 개의 문제가 발견되었습니다"
    fi
    
    log "🔍 안전장치 모니터링 완료"
}

main

