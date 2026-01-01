#!/bin/bash
# 백업에서 복원 스크립트
# 사용법: bash scripts/restore_from_backup.sh [백업파일명]

set -e

PROJECT_DIR="/home/ubuntu/RohaTax-App"
BACKUP_DIR="/home/ubuntu/deployment_backups"

if [ -z "$1" ]; then
    echo "사용법: bash scripts/restore_from_backup.sh [백업파일명]"
    echo ""
    echo "사용 가능한 백업 파일:"
    ls -lh ${BACKUP_DIR}/*.tar.gz 2>/dev/null | awk '{print $9}' | xargs -n1 basename
    exit 1
fi

BACKUP_FILE="${BACKUP_DIR}/$1"
RESTORE_DIR="${BACKUP_DIR}/restore_$(date +%Y%m%d_%H%M%S)"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ 오류: 백업 파일을 찾을 수 없습니다: ${BACKUP_FILE}"
    exit 1
fi

echo "=========================================="
echo "백업 복원 시작"
echo "=========================================="
echo "백업 파일: ${BACKUP_FILE}"
echo "복원 대상: ${PROJECT_DIR}"
echo ""

# 확인
read -p "⚠️  서비스를 중지하고 복원을 진행하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "복원이 취소되었습니다."
    exit 1
fi

# 서비스 중지
echo "서비스 중지 중..."
sudo systemctl stop rohatax || true
sleep 2

# 현재 상태 백업 (안전장치)
echo "현재 상태 백업 중..."
CURRENT_BACKUP="${PROJECT_DIR}_before_restore_$(date +%Y%m%d_%H%M%S)"
if [ -d "${PROJECT_DIR}" ]; then
    cp -r ${PROJECT_DIR} ${CURRENT_BACKUP}
    echo "✅ 현재 상태 백업 완료: ${CURRENT_BACKUP}"
fi

# 백업 압축 해제
echo "백업 압축 해제 중..."
mkdir -p ${RESTORE_DIR}
cd ${BACKUP_DIR}
tar -xzf ${BACKUP_FILE} -C ${RESTORE_DIR}

# 프로젝트 디렉토리 복원
echo "프로젝트 디렉토리 복원 중..."
if [ -d "${RESTORE_DIR}/project" ]; then
    rm -rf ${PROJECT_DIR}
    cp -r ${RESTORE_DIR}/project ${PROJECT_DIR}
    echo "✅ 프로젝트 디렉토리 복원 완료"
fi

# 데이터베이스 복원
echo "데이터베이스 복원 중..."
if [ -f "${RESTORE_DIR}/database_backup/app.db" ]; then
    mkdir -p ${PROJECT_DIR}/database
    cp ${RESTORE_DIR}/database_backup/app.db ${PROJECT_DIR}/database/app.db
    chown ubuntu:ubuntu ${PROJECT_DIR}/database/app.db
    chmod 644 ${PROJECT_DIR}/database/app.db
    echo "✅ 데이터베이스 복원 완료"
fi

# 환경 설정 복원
echo "환경 설정 복원 중..."
if [ -f "${RESTORE_DIR}/.env.backup" ]; then
    cp ${RESTORE_DIR}/.env.backup ${PROJECT_DIR}/.env
    chown ubuntu:ubuntu ${PROJECT_DIR}/.env
    chmod 600 ${PROJECT_DIR}/.env
    echo "✅ 환경 설정 복원 완료"
fi

# systemd 서비스 파일 복원 (선택사항)
if [ -f "${RESTORE_DIR}/rohatax.service.backup" ]; then
    read -p "systemd 서비스 파일도 복원하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo cp ${RESTORE_DIR}/rohatax.service.backup /etc/systemd/system/rohatax.service
        sudo systemctl daemon-reload
        echo "✅ systemd 서비스 파일 복원 완료"
    fi
fi

# 권한 설정
echo "권한 설정 중..."
chown -R ubuntu:ubuntu ${PROJECT_DIR}
chmod -R u+w ${PROJECT_DIR}

# 임시 디렉토리 정리
rm -rf ${RESTORE_DIR}

# 서비스 재시작
echo "서비스 재시작 중..."
sudo systemctl start rohatax
sleep 3
sudo systemctl status rohatax

echo ""
echo "=========================================="
echo "복원 완료!"
echo "=========================================="
echo "프로젝트 디렉토리: ${PROJECT_DIR}"
echo "서비스 상태 확인: sudo systemctl status rohatax"
echo "=========================================="

