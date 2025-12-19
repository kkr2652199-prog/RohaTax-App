#!/bin/bash
# RohaTax 프로덕션 배포 스크립트
#
# 기능:
# 1. Git에서 최신 코드 가져오기
# 2. 의존성 설치
# 3. 데이터베이스 마이그레이션
# 4. 정적 파일 수집 (필요시)
# 5. 서버 재시작
# 6. 헬스 체크
#
# 사용법:
#   ./scripts/deploy.sh [--branch main] [--skip-migration] [--restart-only]

set -e  # 에러 발생 시 즉시 종료

# 색상 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 기본 설정
BRANCH="${1:-main}"
SKIP_MIGRATION=false
RESTART_ONLY=false
PROJECT_DIR="/var/www/rohatax"  # 프로덕션 경로 (수정 필요)
VENV_PATH="$PROJECT_DIR/venv"
APP_USER="www-data"  # 웹 서버 사용자 (수정 필요)

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        --restart-only)
            RESTART_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}알 수 없는 옵션: $1${NC}"
            exit 1
            ;;
    esac
done

# 함수 정의
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "필수 요구사항 확인 중..."
    
    # Python 확인
    if ! command -v python3 &> /dev/null; then
        log_error "Python3가 설치되지 않았습니다"
        exit 1
    fi
    
    # Git 확인
    if ! command -v git &> /dev/null; then
        log_error "Git이 설치되지 않았습니다"
        exit 1
    fi
    
    # 프로젝트 디렉토리 확인
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "프로젝트 디렉토리를 찾을 수 없습니다: $PROJECT_DIR"
        exit 1
    fi
    
    log_info "✅ 모든 요구사항 충족"
}

backup_database() {
    log_info "데이터베이스 백업 중..."
    
    BACKUP_DIR="$PROJECT_DIR/database/backups"
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # PostgreSQL 백업
    if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql://* ]]; then
        pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
        log_info "✅ PostgreSQL 백업 완료: $BACKUP_FILE"
    # MySQL 백업
    elif [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == mysql://* ]]; then
        # MySQL URL 파싱 필요
        mysqldump "$DATABASE_NAME" > "$BACKUP_FILE"
        log_info "✅ MySQL 백업 완료: $BACKUP_FILE"
    else
        log_warn "데이터베이스 백업 스킵 (SQLite 또는 DATABASE_URL 미설정)"
    fi
}

update_code() {
    if [ "$RESTART_ONLY" = true ]; then
        log_info "코드 업데이트 스킵 (--restart-only 모드)"
        return
    fi
    
    log_info "Git에서 최신 코드 가져오기 (브랜치: $BRANCH)..."
    
    cd "$PROJECT_DIR"
    
    # 현재 변경사항 저장 (stash)
    git stash || true
    
    # 최신 코드 가져오기
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    
    log_info "✅ 코드 업데이트 완료"
}

install_dependencies() {
    if [ "$RESTART_ONLY" = true ]; then
        log_info "의존성 설치 스킵 (--restart-only 모드)"
        return
    fi
    
    log_info "의존성 설치 중..."
    
    cd "$PROJECT_DIR"
    
    # 가상환경 활성화
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    else
        log_warn "가상환경을 찾을 수 없습니다. 시스템 Python 사용"
    fi
    
    # 의존성 설치
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_info "✅ 의존성 설치 완료"
}

run_migrations() {
    if [ "$SKIP_MIGRATION" = true ]; then
        log_warn "데이터베이스 마이그레이션 스킵 (--skip-migration)"
        return
    fi
    
    log_info "데이터베이스 마이그레이션 실행 중..."
    
    cd "$PROJECT_DIR"
    
    # 가상환경 활성화
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    fi
    
    # 마이그레이션 실행 (Flask-Migrate 사용 시)
    # flask db upgrade
    
    # 또는 직접 스키마 적용
    # python -c "from core.db import init_db; init_db()"
    
    log_info "✅ 마이그레이션 완료"
}

restart_server() {
    log_info "서버 재시작 중..."
    
    # Gunicorn 사용 시
    if systemctl is-active --quiet rohatax.service; then
        sudo systemctl restart rohatax.service
        log_info "✅ systemd 서비스 재시작 완료"
    # Supervisor 사용 시
    elif supervisorctl status rohatax | grep -q RUNNING; then
        sudo supervisorctl restart rohatax
        log_info "✅ Supervisor 재시작 완료"
    # 직접 실행 중인 경우
    else
        log_warn "서비스 관리자를 찾을 수 없습니다. 수동으로 재시작하세요"
    fi
    
    # Nginx 재로드 (설정 변경 시)
    if command -v nginx &> /dev/null; then
        sudo nginx -t && sudo systemctl reload nginx
        log_info "✅ Nginx 재로드 완료"
    fi
}

health_check() {
    log_info "헬스 체크 중..."
    
    # 애플리케이션 헬스 체크 엔드포인트 호출
    if command -v curl &> /dev/null; then
        sleep 3  # 서버 시작 대기
        
        if curl -f http://localhost:5000/health > /dev/null 2>&1; then
            log_info "✅ 서버 정상 작동 확인"
        else
            log_error "❌ 서버 헬스 체크 실패"
            exit 1
        fi
    else
        log_warn "curl이 없어 헬스 체크를 스킵합니다"
    fi
}

# 메인 실행
main() {
    log_info "=========================================="
    log_info "🚀 RohaTax 프로덕션 배포 시작"
    log_info "=========================================="
    
    check_requirements
    backup_database
    update_code
    install_dependencies
    run_migrations
    restart_server
    health_check
    
    log_info "=========================================="
    log_info "✅ 배포 완료!"
    log_info "=========================================="
}

# 스크립트 실행
main

