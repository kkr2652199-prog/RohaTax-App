#!/bin/bash
# 백업 파일 검증 스크립트
# 매일 새벽 3시 실행 (cron: 0 3 * * *)

# UTF-8 인코딩 설정
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/ubuntu/RohaTax-App"
BACKUP_DIR="$PROJECT_DIR/database/backups"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/backup_verification.log"
MAX_BACKUP_AGE=7  # 7일 이상 된 백업 삭제

# 로그 디렉토리 및 파일 권한 확인 및 생성
mkdir -p "$LOG_DIR"
touch "$LOG_FILE" 2>/dev/null || true
chmod 666 "$LOG_FILE" 2>/dev/null || true
chown ubuntu:ubuntu "$LOG_DIR" 2>/dev/null || true
chmod 755 "$LOG_DIR" 2>/dev/null || true

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 최신 백업 파일 검증
verify_latest_backup() {
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "*.db" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -z "$LATEST_BACKUP" ]; then
        log "ERROR: Backup file not found!"
        return 1
    fi
    
    log "Verifying latest backup file: $(basename $LATEST_BACKUP)"
    
    # SQLite 데이터베이스 무결성 검사
    if sqlite3 "$LATEST_BACKUP" "PRAGMA integrity_check;" | grep -q "ok"; then
        log "Backup file integrity check passed"
        return 0
    else
        log "ERROR: Backup file integrity check failed!"
        return 1
    fi
}

# 오래된 백업 파일 삭제
cleanup_old_backups() {
    log "Cleaning up old backup files (older than ${MAX_BACKUP_AGE} days)"
    
    DELETED=$(find "$BACKUP_DIR" -name "*.db" -type f -mtime +${MAX_BACKUP_AGE} -delete -print | wc -l)
    
    if [ "$DELETED" -gt 0 ]; then
        log "${DELETED} old backup files deleted"
    else
        log "No old backup files to delete"
    fi
}

# 백업 디렉토리 크기 확인
check_backup_size() {
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    log "Backup directory total size: $TOTAL_SIZE"
}

main() {
    log "Backup verification started"
    
    verify_latest_backup
    cleanup_old_backups
    check_backup_size
    
    log "Backup verification completed"
}

main

