#!/bin/bash
# 배포 서버 백업 스크립트
# 사용법: bash scripts/create_deployment_backup.sh

set -e

PROJECT_DIR="/home/ubuntu/RohaTax-App"
BACKUP_DIR="/home/ubuntu/deployment_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="rohatax_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "=========================================="
echo "배포 서버 백업 시작"
echo "=========================================="

# 백업 디렉토리 생성
mkdir -p ${BACKUP_DIR}
mkdir -p ${BACKUP_PATH}

# 프로젝트 디렉토리 전체 복사
echo "프로젝트 디렉토리 백업 중..."
cp -r ${PROJECT_DIR} ${BACKUP_PATH}/project

# 데이터베이스 별도 백업
echo "데이터베이스 백업 중..."
mkdir -p ${BACKUP_PATH}/database_backup
if [ -f "${PROJECT_DIR}/database/app.db" ]; then
    cp ${PROJECT_DIR}/database/app.db ${BACKUP_PATH}/database_backup/app.db
    echo "✅ 데이터베이스 백업 완료"
else
    echo "⚠️  데이터베이스 파일 없음"
fi

# 환경 설정 파일 백업
echo "환경 설정 파일 백업 중..."
if [ -f "${PROJECT_DIR}/.env" ]; then
    cp ${PROJECT_DIR}/.env ${BACKUP_PATH}/.env.backup
    echo "✅ 환경 설정 파일 백업 완료"
else
    echo "⚠️  .env 파일 없음"
fi

# systemd 서비스 파일 백업
echo "systemd 서비스 파일 백업 중..."
if [ -f "/etc/systemd/system/rohatax.service" ]; then
    sudo cp /etc/systemd/system/rohatax.service ${BACKUP_PATH}/rohatax.service.backup
    echo "✅ systemd 서비스 파일 백업 완료"
else
    echo "⚠️  systemd 서비스 파일 없음"
fi

# Git 상태 백업
echo "Git 상태 백업 중..."
cd ${PROJECT_DIR}
git log --oneline -10 > ${BACKUP_PATH}/git_log.txt
git tag -l > ${BACKUP_PATH}/git_tags.txt
echo "✅ Git 상태 백업 완료"

# 압축
echo "백업 압축 중..."
cd ${BACKUP_DIR}
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}
rm -rf ${BACKUP_NAME}

BACKUP_SIZE=$(du -h ${BACKUP_NAME}.tar.gz | cut -f1)

echo ""
echo "=========================================="
echo "백업 완료!"
echo "=========================================="
echo "백업 파일: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "백업 크기: ${BACKUP_SIZE}"
echo "=========================================="

