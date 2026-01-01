#!/bin/bash
# 데이터베이스 백업 스크립트
# 사용법: bash scripts/backup_database.sh

set -e

PROJECT_DIR="/home/ubuntu/RohaTax-App"
BACKUP_DIR="${PROJECT_DIR}/database/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/app_db_${TIMESTAMP}.db"
DB_FILE="${PROJECT_DIR}/database/app.db"

echo "=========================================="
echo "데이터베이스 백업 시작"
echo "=========================================="

# 백업 디렉토리 생성
mkdir -p ${BACKUP_DIR}

# 데이터베이스 파일 확인
if [ ! -f "${DB_FILE}" ]; then
    echo "❌ 오류: 데이터베이스 파일을 찾을 수 없습니다: ${DB_FILE}"
    exit 1
fi

# SQLite 데이터베이스 백업
echo "데이터베이스 백업 중..."
sqlite3 ${DB_FILE} ".backup ${BACKUP_FILE}"

if [ -f "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    echo "✅ 데이터베이스 백업 완료"
    echo "백업 파일: ${BACKUP_FILE}"
    echo "백업 크기: ${BACKUP_SIZE}"
else
    echo "❌ 오류: 백업 파일 생성 실패"
    exit 1
fi

# 오래된 백업 삭제 (30일 이상)
echo "오래된 백업 정리 중..."
DELETED=$(find ${BACKUP_DIR} -name "app_db_*.db" -mtime +30 -delete -print | wc -l)
if [ ${DELETED} -gt 0 ]; then
    echo "✅ ${DELETED}개의 오래된 백업 삭제됨"
else
    echo "✅ 삭제할 오래된 백업 없음"
fi

echo "=========================================="

