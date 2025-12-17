import logging
from logging.handlers import TimedRotatingFileHandler
import os
import time
import threading
from datetime import datetime, timedelta
import glob


def init_logging(log_dir: str = "logs") -> None:
    os.makedirs(log_dir, exist_ok=True)
    
    # 날짜 기반 로그 파일명 사용
    today = time.strftime("%Y-%m-%d")
    
    # 메인 앱 로그 (날짜별)
    log_path = os.path.join(log_dir, f"app_{today}.log")

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))

    # Timed rotating file handler (Windows 안전) - 매일 회전, 최근 3개만 보관
    # delay=True로 파일 생성 지연하여 권한 문제 방지
    fh = TimedRotatingFileHandler(
        log_path, 
        when='midnight', 
        interval=1, 
        backupCount=3,  # 모든 로그 파일을 3일로 통일
        encoding="utf-8",
        delay=True  # 파일 생성 지연으로 권한 문제 방지
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))

    # 변환 통계 전용 로그 파일 (상세 로깅)
    conversion_log_path = os.path.join(log_dir, f"conversion_stats_{today}.log")
    conversion_fh = TimedRotatingFileHandler(
        conversion_log_path,
        when='midnight',
        interval=1,
        backupCount=3,  # 3일로 통일
        encoding="utf-8",
        delay=True
    )
    conversion_fh.setLevel(logging.DEBUG)  # DEBUG 레벨로 상세 로깅
    conversion_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))

    # 변환 과정 전체 로그 파일 (단계별 상세 기록)
    conversion_process_log_path = os.path.join(log_dir, f"conversion_process_{today}.log")
    conversion_process_fh = TimedRotatingFileHandler(
        conversion_process_log_path,
        when='midnight',
        interval=1,
        backupCount=3,  # 3일로 통일
        encoding="utf-8",
        delay=True
    )
    conversion_process_fh.setLevel(logging.INFO)  # INFO 레벨로 변환 과정 기록
    conversion_process_fh.setFormatter(logging.Formatter("%(asctime)s [CONVERSION] %(levelname)s %(name)s - %(message)s"))

    # Avoid duplicate handlers on reload
    for h in list(root.handlers):
        root.removeHandler(h)

    root.addHandler(ch)
    root.addHandler(fh)
    root.addHandler(conversion_fh)
    root.addHandler(conversion_process_fh)

    # 변환 관련 모듈들의 로깅 레벨을 DEBUG로 설정
    conversion_logger = logging.getLogger('core.recipient_extractor')
    conversion_logger.setLevel(logging.DEBUG)
    
    conversion_engine_logger = logging.getLogger('core.conversion_engine')
    conversion_engine_logger.setLevel(logging.DEBUG)
    
    # 열려 있는 로그 파일 목록 (삭제 제외)
    open_files = set()
    try:
        for h in (fh, conversion_fh, conversion_process_fh):
            try:
                open_files.add(getattr(h, 'baseFilename', ''))
            except Exception:
                pass
    except Exception:
        pass

    # 리로더(child)에서의 중복 정리 방지 및 오늘자/열린 파일 제외 정리
    try:
        is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    except Exception:
        is_reloader_child = False

    if not is_reloader_child:
        cleanup_old_logs(log_dir, today=today, open_files=open_files)


def cleanup_old_logs(log_dir: str = "logs", *, today: str | None = None, open_files: set[str] | None = None) -> None:
    """
    30일 이상 된 로그 파일들을 자동으로 삭제합니다.
    """
    try:
        logger = logging.getLogger(__name__)
        cutoff_date = datetime.now() - timedelta(days=30)
        today = today or time.strftime("%Y-%m-%d")
        open_files = open_files or set()
        
        # 로그 디렉토리의 모든 파일 검사
        for file_path in glob.glob(os.path.join(log_dir, "*.log*")):
            try:
                # 오늘자 또는 현재 열려있는 파일은 건너뜀
                filename = os.path.basename(file_path)
                if f"_{today}.log" in filename or file_path in open_files:
                    continue
                # 파일 수정 시간 확인
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    os.remove(file_path)
                    logger.info(f"오래된 로그 파일 삭제: {os.path.basename(file_path)}")
                    
            except (OSError, IOError) as e:
                # 사용 중인 파일(WinError 32 등)은 정보 로그로만 표시하여 노이즈 감소
                level = logging.INFO
                try:
                    if getattr(e, 'winerror', None) not in (32,):
                        level = logging.WARNING
                except Exception:
                    level = logging.WARNING
                logger.log(level, f"로그 파일 삭제 실패(보류): {file_path}, 오류: {e}")
                
        # 프로세스 ID 기반 로그 파일들도 정리 (기존 방식 호환)
        cleanup_process_logs(log_dir, today=today, open_files=open_files)
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"로그 정리 중 오류 발생: {e}")


def cleanup_process_logs(log_dir: str = "logs", *, today: str | None = None, open_files: set[str] | None = None) -> None:
    """
    프로세스 ID 기반으로 생성된 기존 로그 파일들을 정리합니다.
    """
    try:
        logger = logging.getLogger(__name__)
        today = today or time.strftime("%Y-%m-%d")
        open_files = open_files or set()
        
        # 프로세스 ID 기반 로그 파일 패턴들
        patterns = [
            "app_*.log",
            "conversion_stats_*.log", 
            "conversion_process_*.log"
        ]
        
        for pattern in patterns:
            for file_path in glob.glob(os.path.join(log_dir, pattern)):
                try:
                    filename = os.path.basename(file_path)
                    if f"_{today}.log" in filename or file_path in open_files:
                        continue
                    # 현재 실행 중인 프로세스의 파일이 아닌 경우에만 삭제
                    if not is_current_process_log(file_path):
                        os.remove(file_path)
                        logger.info(f"기존 프로세스 로그 파일 삭제: {os.path.basename(file_path)}")
                        
                except (OSError, IOError) as e:
                    level = logging.INFO
                    try:
                        if getattr(e, 'winerror', None) not in (32,):
                            level = logging.WARNING
                    except Exception:
                        level = logging.WARNING
                    logger.log(level, f"프로세스 로그 파일 삭제 실패(보류): {file_path}, 오류: {e}")
                    
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"프로세스 로그 정리 중 오류 발생: {e}")


def is_current_process_log(file_path: str) -> bool:
    """
    현재 실행 중인 프로세스의 로그 파일인지 확인합니다.
    """
    try:
        current_pid = os.getpid()
        filename = os.path.basename(file_path)
        
        # 프로세스 ID가 파일명에 포함되어 있는지 확인
        if f"_{current_pid}." in filename:
            return True
            
        return False
        
    except Exception:
        return False


















