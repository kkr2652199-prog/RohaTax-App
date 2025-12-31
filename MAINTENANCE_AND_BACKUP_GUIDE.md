# 🔧 점검 모드 & 자동 백업 사용 가이드

> **구현 완료일**: 2025-01-18  
> **기능**: 점검 모드 및 자동 백업 스케줄러

---

## ✅ 구현 완료 사항

### 1. APScheduler 라이브러리 추가
- ✅ `requirements.txt`에 `APScheduler==3.10.4` 추가

### 2. 점검 모드 (Maintenance Mode)
- ✅ 미들웨어 구현 (`app.py`의 `_check_maintenance_mode()`)
- ✅ `maintenance.flag` 파일 기반 점검 모드
- ✅ `/static/` 경로 제외
- ✅ 백도어 기능 (로컬호스트, 특정 헤더)
- ✅ 점검 페이지 템플릿 (`templates/maintenance.html`)

### 3. 자동 백업 스케줄러
- ✅ `BackgroundScheduler` 구현
- ✅ 매일 새벽 04:00 자동 백업
- ✅ 30일 이상 된 백업 파일 자동 삭제
- ✅ 백업 로그 기록

---

## 🎯 사용 방법

### 점검 모드 활성화

**서버에서 실행:**
```bash
# 점검 모드 켜기
touch maintenance.flag

# 또는 Windows에서
echo. > maintenance.flag
```

**결과:**
- 모든 페이지 요청이 점검 페이지로 리다이렉트
- `/static/` 경로는 정상 작동 (이미지, CSS 등)
- HTTP 상태 코드: 503 (Service Unavailable)

### 점검 모드 비활성화

**서버에서 실행:**
```bash
# 점검 모드 끄기
rm maintenance.flag

# 또는 Windows에서
del maintenance.flag
```

**결과:**
- 즉시 정상 서비스 재개

---

## 🔓 백도어 (관리자 우회)

### 방법 1: 로컬호스트 접속
```
http://127.0.0.1:5001
http://localhost:5001
```
→ 점검 모드 무시하고 정상 접속

### 방법 2: 특정 헤더 사용
```bash
# curl 예시
curl -H "X-Bypass-Maintenance: admin-bypass-2025" http://your-domain.com/

# 브라우저 확장 프로그램 사용 (ModHeader 등)
# 헤더 추가: X-Bypass-Maintenance = admin-bypass-2025
```

**환경 변수 설정 (선택사항):**
```bash
# .env 파일에 추가
MAINTENANCE_BYPASS_KEY=your-custom-key-here
```

---

## 💾 자동 백업

### 백업 스케줄
- **실행 시간**: 매일 새벽 04:00
- **백업 위치**: `database/backups/app_YYYYMMDD_HHMMSS.db`
- **보관 기간**: 30일 (자동 삭제)

### 백업 파일 예시
```
database/backups/
├── app_20250118_040000.db
├── app_20250119_040000.db
├── app_20250120_040000.db
└── ...
```

### 수동 백업 실행 (테스트용)

**Python에서:**
```python
from app import backup_database
backup_database()
```

**또는 스케줄러에서 즉시 실행:**
```python
from app import scheduler
scheduler.add_job(
    func=backup_database,
    trigger='date',  # 즉시 실행
    id='manual_backup'
)
```

---

## 📋 점검 모드 동작 확인

### 1. 점검 모드 활성화 테스트

```bash
# 서버에서
cd C:\Users\user\Desktop\RohaTax\homepage1
echo. > maintenance.flag

# 브라우저에서 접속
http://localhost:5001
```

**예상 결과:**
- 점검 페이지 표시
- "시스템 점검 중입니다" 메시지
- 점검 시작 시간 표시

### 2. 정적 파일 접근 테스트

```bash
# 브라우저에서
http://localhost:5001/static/css/core/reset.css
```

**예상 결과:**
- 정상적으로 CSS 파일 로드 (점검 모드 무시)

### 3. 백도어 테스트

```bash
# 로컬호스트로 접속
http://127.0.0.1:5001
```

**예상 결과:**
- 정상 페이지 표시 (점검 모드 무시)

---

## 🔍 로그 확인

### 백업 로그 확인

**로그 파일 위치:**
```
logs/app_YYYY-MM-DD.log
```

**로그 내용 예시:**
```
2025-01-18 04:00:00 INFO - 🔄 자동 백업 시작...
2025-01-18 04:00:01 INFO - ✅ 백업 완료: app_20250118_040001.db (크기: 1234567 bytes)
2025-01-18 04:00:02 INFO - 🗑️ 오래된 백업 파일 삭제: app_20241218_040000.db
```

---

## ⚙️ 설정 커스터마이징

### 백업 시간 변경

**`app.py`에서 수정:**
```python
scheduler.add_job(
    func=backup_database,
    trigger=CronTrigger(hour=2, minute=30),  # 새벽 02:30으로 변경
    id='daily_backup',
    name='일일 데이터베이스 백업',
    replace_existing=True
)
```

### 백업 보관 기간 변경

**`app.py`의 `backup_database()` 함수에서 수정:**
```python
# 30일 → 60일로 변경
cutoff_date = datetime.now() - timedelta(days=60)
```

---

## 🆘 문제 해결

### 문제 1: 점검 모드가 작동하지 않음

**확인 사항:**
1. `maintenance.flag` 파일이 프로젝트 루트에 있는지 확인
2. 파일 이름이 정확한지 확인 (대소문자 구분)
3. 서버 재시작 필요할 수 있음

### 문제 2: 백업이 실행되지 않음

**확인 사항:**
1. APScheduler가 설치되었는지 확인: `pip install APScheduler`
2. 서버 로그에서 스케줄러 시작 메시지 확인
3. 시간대 설정 확인 (서버 시간대)

### 문제 3: 백업 파일이 너무 많음

**해결:**
- 30일 자동 삭제 기능이 작동하는지 확인
- 수동으로 오래된 파일 삭제 가능

---

## 📊 구현 상세

### 점검 모드 미들웨어 위치

```223:252:homepage1/app.py
# 점검 모드 미들웨어 (가장 먼저 체크)
@app.before_request
def _check_maintenance_mode():
    """
    점검 모드 체크
    - maintenance.flag 파일이 존재하면 점검 모드 활성화
    - /static/ 경로는 제외
    - 백도어: 로컬호스트 또는 특정 헤더로 우회 가능
    """
    # 정적 파일은 항상 통과
    if request.path.startswith("/static"):
        return None
    
    # 백도어: 로컬호스트는 점검 모드 무시
    if request.remote_addr in ['127.0.0.1', 'localhost', '::1']:
        return None
    
    # 백도어: 특정 헤더로 우회 (관리자 테스트용)
    bypass_header = request.headers.get('X-Bypass-Maintenance', '')
    if bypass_header == os.getenv('MAINTENANCE_BYPASS_KEY', 'admin-bypass-2025'):
        return None
    
    # 점검 모드 플래그 파일 확인
    maintenance_flag_path = os.path.join(app_dir, 'maintenance.flag')
    if os.path.exists(maintenance_flag_path):
        # 점검 페이지 렌더링
        maintenance_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = render_template('maintenance.html', maintenance_time=maintenance_time)
        return response, 503  # Service Unavailable
```

### 자동 백업 스케줄러 위치

```129:200:homepage1/app.py
# 자동 백업 스케줄러 초기화
def backup_database():
    """
    데이터베이스 자동 백업 함수
    - 매일 새벽 04:00에 실행
    - database/app.db → database/backups/app_YYYYMMDD_HHMMSS.db
    - 30일 이상 된 백업 파일 자동 삭제
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info("🔄 자동 백업 시작...")
        
        # 백업 디렉토리 확인
        backup_dir = os.path.join(app_dir, 'database', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # 원본 DB 파일 경로
        source_db = os.path.join(app_dir, 'database', 'app.db')
        
        if not os.path.exists(source_db):
            logger.warning("⚠️ 백업할 데이터베이스 파일이 없습니다: %s", source_db)
            return
        
        # 백업 파일명 생성 (YYYYMMDD_HHMMSS 형식)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'app_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 백업 실행
        shutil.copy2(source_db, backup_path)
        backup_size = os.path.getsize(backup_path)
        logger.info("✅ 백업 완료: %s (크기: %s bytes)", backup_filename, backup_size)
        
        # 오래된 백업 파일 삭제 (30일 이상)
        cutoff_date = datetime.now() - timedelta(days=30)
        deleted_count = 0
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('app_') and filename.endswith('.db'):
                file_path = os.path.join(backup_dir, filename)
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info("🗑️ 오래된 백업 파일 삭제: %s", filename)
                except Exception as e:
                    logger.warning("⚠️ 백업 파일 삭제 실패 (%s): %s", filename, e)
        
        if deleted_count > 0:
            logger.info("🗑️ 총 %d개의 오래된 백업 파일 삭제 완료", deleted_count)
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("❌ 자동 백업 실패: %s", e, exc_info=True)


# 백업 스케줄러 설정
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
    func=backup_database,
    trigger=CronTrigger(hour=4, minute=0),  # 매일 새벽 04:00
    id='daily_backup',
    name='일일 데이터베이스 백업',
    replace_existing=True
)

# 스케줄러 시작
try:
    scheduler.start()
    logging.getLogger(__name__).info("✅ 자동 백업 스케줄러 시작 (매일 04:00)")
except Exception as e:
    logging.getLogger(__name__).error("❌ 백업 스케줄러 시작 실패: %s", e)
```

---

## ✅ 완료 체크리스트

- [x] APScheduler 라이브러리 추가
- [x] 점검 모드 미들웨어 구현
- [x] maintenance.flag 파일 기반 점검 모드
- [x] /static/ 경로 제외
- [x] 백도어 기능 (로컬호스트, 헤더)
- [x] maintenance.html 템플릿 생성
- [x] 자동 백업 함수 구현
- [x] BackgroundScheduler 설정
- [x] 매일 04:00 자동 백업
- [x] 30일 이상 백업 파일 자동 삭제

---

## 🎯 사용 시나리오

### 시나리오 1: 긴급 점검

```bash
# 1. 점검 모드 활성화
touch maintenance.flag

# 2. 서버 작업 수행
# (데이터베이스 마이그레이션, 코드 업데이트 등)

# 3. 점검 모드 비활성화
rm maintenance.flag
```

### 시나리오 2: 정기 점검

```bash
# 매주 일요일 새벽 2시 점검
touch maintenance.flag
# ... 점검 작업 ...
rm maintenance.flag
```

### 시나리오 3: 백업 확인

```bash
# 백업 디렉토리 확인
ls -lh database/backups/

# 최신 백업 확인
ls -lt database/backups/ | head -5
```

---

## 📝 요약

### 구현 완료
- ✅ 점검 모드: `maintenance.flag` 파일로 간단히 제어
- ✅ 자동 백업: 매일 새벽 04:00 자동 실행
- ✅ 백업 정리: 30일 이상 된 파일 자동 삭제

### 사용 방법
- **점검 모드 켜기**: `touch maintenance.flag`
- **점검 모드 끄기**: `rm maintenance.flag`
- **백업**: 자동 실행 (매일 04:00)

### 백도어
- 로컬호스트: 자동 우회
- 헤더: `X-Bypass-Maintenance: admin-bypass-2025`

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

