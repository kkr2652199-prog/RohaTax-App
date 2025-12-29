#!/bin/bash
# 백업 파일 검증 스크립트
# 매일 새벽 3시 실행 (cron: 0 3 * * *)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/ubuntu/RohaTax-App"
BACKUP_DIR="$PROJECT_DIR/database/backups"
LOG_FILE="$PROJECT_DIR/logs/backup_verification.log"
MAX_BACKUP_AGE=7  # 7일 이상 된 백업 삭제

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 최신 백업 파일 검증
verify_latest_backup() {
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "*.db" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -z "$LATEST_BACKUP" ]; then
        log "❌ ERROR: 백업 파일을 찾을 수 없습니다!"
        return 1
    fi
    
    log "🔍 최신 백업 파일 검증: $(basename $LATEST_BACKUP)"
    
    # SQLite 데이터베이스 무결성 검사
    if sqlite3 "$LATEST_BACKUP" "PRAGMA integrity_check;" | grep -q "ok"; then
        log "✅ 백업 파일 무결성 검증 성공"
        return 0
    else
        log "❌ ERROR: 백업 파일 무결성 검증 실패!"
        return 1
    fi
}

# 오래된 백업 파일 삭제
cleanup_old_backups() {
    log "🧹 오래된 백업 파일 정리 시작 (${MAX_BACKUP_AGE}일 이상)"
    
    DELETED=$(find "$BACKUP_DIR" -name "*.db" -type f -mtime +${MAX_BACKUP_AGE} -delete -print | wc -l)
    
    if [ "$DELETED" -gt 0 ]; then
        log "✅ ${DELETED}개의 오래된 백업 파일 삭제 완료"
    else
        log "ℹ️ 삭제할 오래된 백업 파일 없음"
    fi
}

# 백업 디렉토리 크기 확인
check_backup_size() {
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    log "📊 백업 디렉토리 총 크기: $TOTAL_SIZE"
}

main() {
    log "🔍 백업 검증 시작"
    
    verify_latest_backup
    cleanup_old_backups
    check_backup_size
    
    log "🔍 백업 검증 완료"
}

main

