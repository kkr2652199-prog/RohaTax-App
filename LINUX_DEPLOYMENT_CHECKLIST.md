# 🐧 Linux 상용 서버 배포 체크리스트

> **작성일**: 2025-12-19  
> **목적**: Windows 개발 환경에서 Linux 상용 서버로 이주 시 호환성 검증

---

## ✅ 완료된 작업

### 1. 의존성 파일 현행화
- ✅ `requirements.txt` 정리 완료
- ✅ 필수 라이브러리만 포함
- ✅ `gunicorn==21.2.0` 추가 (프로덕션 WSGI 서버)
- ✅ 개발용 라이브러리 제외 (pytest, flake8, black 등)

### 2. 경로 하드코딩 검사
- ✅ 프로덕션 코드에서 Windows 경로 하드코딩 없음
- ✅ `os.path.join()` 사용 확인
- ⚠️ 테스트 파일에 Windows 경로 존재 (프로덕션 영향 없음)

### 3. 실행 엔진 준비
- ✅ `app.py` 최상단에 프로덕션 실행 명령어 주석 추가
- ✅ `Procfile` 생성 (Heroku/플랫폼 배포용)

---

## 📋 배포 전 확인 사항

### 필수 확인

1. **환경 변수 설정**:
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export PORT=5000
   export ENVIRONMENT=production
   export DEBUG=false
   ```

2. **데이터베이스 경로**:
   - SQLite: `database/app.db` (상대 경로 사용 중 ✅)
   - PostgreSQL/MySQL: `DATABASE_URL` 환경 변수 설정

3. **파일 업로드 경로**:
   - `uploads/`, `output/` 디렉토리 생성 필요
   - 권한 설정: `chmod 755 uploads output`

4. **로그 디렉토리**:
   - `logs/` 디렉토리 생성 필요
   - 권한 설정: `chmod 755 logs`

---

## 🚀 Linux 서버 배포 명령어

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
export SECRET_KEY="your-production-secret-key"
export PORT=5000
export ENVIRONMENT=production
export DEBUG=false
```

### 3. 프로덕션 실행
```bash
# Gunicorn 사용 (권장)
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - app:app

# 또는 Supervisor/Nginx와 함께 사용
```

---

## ⚠️ 주의사항

### Windows 전용 파일 (배포 시 제외)
- `start_server_5000.bat`
- `start_server_5001.bat`
- `tests/master_conversion_test.py` (Windows 경로 하드코딩)

### 경로 호환성
- ✅ 프로덕션 코드: `os.path.join()` 사용으로 크로스 플랫폼 호환
- ✅ 데이터베이스 경로: 상대 경로 사용
- ✅ 로그 경로: 상대 경로 사용

---

## 📝 배포 후 확인

1. **서버 실행 확인**:
   ```bash
   curl http://localhost:5000/health
   ```

2. **메타 태그 확인**:
   ```bash
   curl http://localhost:5000 | grep "og:title"
   ```

3. **Favicon 확인**:
   - 브라우저에서 접속하여 탭 아이콘 확인

---

**작성일**: 2025-12-19  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

