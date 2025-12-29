#!/bin/bash
# 배포 서버 안전장치 모니터링 스크립트
# 매 5분마다 실행 (cron: */5 * * * *)

# UTF-8 인코딩 설정
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/ubuntu/RohaTax-App"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/safety_monitor.log"
ALERT_EMAIL=""  # 필요시 이메일 설정

# 로그 디렉토리 및 파일 권한 확인 및 생성
mkdir -p "$LOG_DIR"
touch "$LOG_FILE" 2>/dev/null || true
chmod 666 "$LOG_FILE" 2>/dev/null || true
chown ubuntu:ubuntu "$LOG_DIR" 2>/dev/null || true
chmod 755 "$LOG_DIR" 2>/dev/null || true

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 서비스 상태 확인
check_service() {
    if systemctl is-active --quiet rohatax; then
        return 0
    else
        log "CRITICAL: rohatax service is stopped!"
        systemctl restart rohatax
        log "Service restart attempted"
        return 1
    fi
}

# 디스크 공간 확인
check_disk_space() {
    USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$USAGE" -gt 90 ]; then
        log "WARNING: Disk usage is ${USAGE}%!"
        return 1
    fi
    return 0
}

# 메모리 사용량 확인
check_memory() {
    MEMORY=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$MEMORY" -gt 90 ]; then
        log "WARNING: Memory usage is ${MEMORY}%!"
        return 1
    fi
    return 0
}

# 백업 파일 확인
check_backups() {
    BACKUP_DIR="$PROJECT_DIR/database/backups"
    if [ ! -d "$BACKUP_DIR" ]; then
        log "WARNING: Backup directory does not exist!"
        return 1
    fi
    
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.db" -mtime -1 | wc -l)
    if [ "$BACKUP_COUNT" -eq 0 ]; then
        log "WARNING: No backup files found in the last 24 hours!"
        return 1
    fi
    
    return 0
}

# 헬스체크 엔드포인트 확인
check_health() {
    HEALTH=$(curl -s http://localhost/health 2>/dev/null)
    if [ -z "$HEALTH" ] || echo "$HEALTH" | grep -q '"status":"unhealthy"'; then
        log "CRITICAL: Health check failed!"
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
                log "WARNING: Log file is too large: $(basename $log_file) (${SIZE}MB)"
            fi
        fi
    done
}

# 메인 실행
main() {
    log "Safety monitoring started"
    
    ERRORS=0
    
    check_service || ((ERRORS++))
    check_disk_space || ((ERRORS++))
    check_memory || ((ERRORS++))
    check_backups || ((ERRORS++))
    check_health || ((ERRORS++))
    check_log_size
    
    if [ $ERRORS -eq 0 ]; then
        log "All safety checks passed"
    else
        log "Total $ERRORS issues found"
    fi
    
    log "Safety monitoring completed"
}

main

