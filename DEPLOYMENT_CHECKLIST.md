# 🚀 서버 배포 전 필수 체크리스트

> **현재 상태**: 개발 환경 (로컬 SQLite)  
> **목표**: 프로덕션 환경 (클라우드 서버 + PostgreSQL/MySQL)

---

## 📋 1. 보안 설정 (Critical - 배포 전 필수)

### ✅ 현재 상태
- [x] `SECRET_KEY` 환경 변수 기반 설정
- [x] 프로덕션에서 `SECRET_KEY` 없으면 서버 종료 로직
- [x] CSRF 보호 활성화
- [x] 세션 쿠키 보안 설정 (HttpOnly, SameSite, Secure)
- [x] 보안 헤더 미들웨어 (`SecurityMiddleware`)

### ⚠️ 배포 전 필수 작업
- [ ] **프로덕션 `SECRET_KEY` 생성 및 설정**
  ```bash
  # Python으로 안전한 키 생성
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  - 최소 32자 이상의 랜덤 문자열
  - `.env` 파일에 저장 (절대 Git에 커밋 금지)

- [ ] **환경 변수 설정 확인**
  ```bash
  ENVIRONMENT=production
  SECRET_KEY=<생성한-프로덕션-키>
  DEBUG=false
  HOST=0.0.0.0
  LOG_LEVEL=WARNING
  ```

- [ ] **`.gitignore`에 `.env` 포함 확인**
  - `.env` 파일이 Git에 커밋되지 않았는지 확인

---

## 🗄️ 2. 데이터베이스 마이그레이션 (Critical)

### ⚠️ 현재 상태
- **SQLite 사용 중** (`sqlite:///database/app.db`)
- 프로덕션에서는 **PostgreSQL 또는 MySQL 필수**

### 📝 배포 전 필수 작업
- [ ] **클라우드 데이터베이스 생성**
  - AWS RDS (PostgreSQL/MySQL)
  - Azure Database
  - GCP Cloud SQL
  - 또는 다른 관리형 DB 서비스

- [ ] **데이터베이스 연결 문자열 설정**
  ```bash
  # PostgreSQL 예시
  DATABASE_URL=postgresql://user:password@host:5432/dbname
  
  # MySQL 예시
  DATABASE_URL=mysql://user:password@host:3306/dbname
  ```

- [ ] **스키마 마이그레이션**
  - `database/schema.sql` 확인
  - 프로덕션 DB에 스키마 적용
  - 기존 데이터 마이그레이션 스크립트 작성 (필요시)

- [ ] **데이터베이스 백업 전략 수립**
  - 자동 백업 설정 (일일/주간)
  - 복구 절차 문서화

---

## 📁 3. 파일 저장소 설정 (Important)

### ⚠️ 현재 상태
- 로컬 폴더 사용 (`uploads/`, `output/`)
- 24시간 자동 삭제 로직 있음

### 📝 배포 전 고려사항
- [ ] **파일 저장소 선택**
  - **옵션 1**: 서버 로컬 디스크 (간단, 비용 저렴)
    - 디스크 용량 모니터링 필요
    - 서버 교체 시 데이터 손실 위험
  - **옵션 2**: 클라우드 스토리지 (권장)
    - AWS S3, Azure Blob Storage, GCP Cloud Storage
    - 확장성 및 안정성 우수
    - 자동 백업 및 버전 관리

- [ ] **파일 자동 삭제 로직 확인**
  - 24시간 후 자동 삭제가 정상 작동하는지 확인
  - 프로덕션에서도 동일하게 작동하는지 테스트

- [ ] **파일 업로드 크기 제한**
  - 현재: `MAX_FILE_SIZE=52428800` (50MB)
  - 프로덕션에서도 적절한지 검토

---

## 🔧 4. 환경 설정 및 의존성 (Important)

### ✅ 현재 상태
- [x] `requirements.txt` 존재
- [x] `env.example` 템플릿 존재
- [x] 환경 변수 기반 설정 구조

### 📝 배포 전 필수 작업
- [ ] **프로덕션 `.env` 파일 생성**
  ```bash
  cp env.example .env
  # 프로덕션 값으로 수정
  ```

- [ ] **의존성 버전 고정 확인**
  - `requirements.txt`의 모든 패키지 버전 명시 확인
  - 보안 취약점 스캔 (`safety check`)

- [ ] **Python 버전 확인**
  - 프로덕션 서버의 Python 버전과 호환성 확인
  - 권장: Python 3.10 이상

---

## 📊 5. 로깅 및 모니터링 (Important)

### ✅ 현재 상태
- [x] `TimedRotatingFileHandler` 로그 회전 (3일 보관)
- [x] 날짜별 로그 파일 생성
- [x] 요청/응답 로깅

### 📝 배포 전 고려사항
- [ ] **로그 저장 위치**
  - 서버 로컬 디스크 vs 클라우드 로깅 서비스
  - AWS CloudWatch, Azure Monitor, GCP Logging

- [ ] **로그 레벨 조정**
  - 프로덕션: `LOG_LEVEL=WARNING` (INFO는 너무 많을 수 있음)
  - 에러만 집중적으로 모니터링

- [ ] **로그 파일 크기 모니터링**
  - 디스크 공간 부족 방지
  - 자동 정리 스크립트 필요 여부 확인

- [ ] **에러 알림 설정** (선택사항)
  - 중요한 에러 발생 시 이메일/Slack 알림
  - Sentry, Rollbar 같은 에러 트래킹 서비스 연동

---

## 🚦 6. 성능 및 확장성 (Recommended)

### 📝 배포 전 검토사항
- [ ] **정적 파일 캐싱**
  - 현재: 1년 캐시 설정 (`_add_cache_headers`)
  - CDN 사용 고려 (CloudFront, Azure CDN 등)

- [ ] **데이터베이스 연결 풀링**
  - SQLite는 단일 연결만 지원
  - PostgreSQL/MySQL로 전환 시 연결 풀 설정 필요

- [ ] **세션 저장소**
  - 현재: Flask 기본 세션 (서버 메모리)
  - 다중 서버 환경: Redis 세션 스토어 고려

- [ ] **파일 업로드 최적화**
  - 대용량 파일 처리 시 타임아웃 설정
  - 비동기 처리 고려 (Celery, RQ)

---

## 🔄 7. 백업 및 복구 전략 (Critical)

### ✅ 현재 상태
- [x] 데이터베이스 백업 기능 (`FileManager.create_backup`)
- [x] DB 무결성 검사 (`_check_db_integrity`)

### 📝 배포 전 필수 작업
- [ ] **데이터베이스 자동 백업 스케줄**
  - 일일 백업 스크립트 작성
  - 백업 파일 저장 위치 (로컬 + 클라우드)

- [ ] **복구 절차 문서화**
  - 데이터베이스 복구 방법
  - 파일 복구 방법
  - 롤백 절차

- [ ] **백업 테스트**
  - 백업 생성 → 복구 테스트 수행
  - 복구 시간 측정

---

## 🧪 8. 테스트 및 검증 (Critical)

### 📝 배포 전 필수 테스트
- [ ] **기능 테스트**
  - 회원가입/로그인
  - 파일 업로드 및 변환
  - 토큰 충전 및 사용
  - 상품 관리

- [ ] **보안 테스트**
  - CSRF 공격 방어 확인
  - SQL Injection 방어 확인
  - XSS 방어 확인
  - 파일 업로드 보안 (확장자, 크기 제한)

- [ ] **성능 테스트**
  - 동시 사용자 부하 테스트
  - 대용량 파일 처리 테스트
  - 데이터베이스 쿼리 성능 확인

- [ ] **에러 핸들링 테스트**
  - 404, 500 에러 페이지 확인
  - 예외 상황 처리 확인

---

## 🌐 9. 서버 인프라 (Critical)

### 📝 배포 전 필수 작업
- [ ] **서버 선택**
  - AWS EC2, Azure VM, GCP Compute Engine
  - 최소 사양: 2GB RAM, 2 CPU 코어

- [ ] **웹 서버 설정**
  - Gunicorn 또는 uWSGI (Flask 프로덕션 서버)
  - Nginx 리버스 프록시 설정
  - SSL/TLS 인증서 설정 (Let's Encrypt)

- [ ] **방화벽 설정**
  - 필요한 포트만 개방 (80, 443)
  - SSH 접근 제한 (특정 IP만)

- [ ] **도메인 및 DNS**
  - 도메인 구매 및 DNS 설정
  - A 레코드 또는 CNAME 설정

---

## 📦 10. 배포 자동화 (Recommended)

### 📝 배포 전 고려사항
- [ ] **배포 스크립트 작성**
  - Git pull
  - 의존성 설치 (`pip install -r requirements.txt`)
  - 데이터베이스 마이그레이션
  - 서버 재시작

- [ ] **CI/CD 파이프라인** (선택사항)
  - GitHub Actions, GitLab CI, Jenkins
  - 자동 테스트 → 배포

- [ ] **롤백 계획**
  - 배포 실패 시 이전 버전으로 복구 방법
  - 데이터베이스 롤백 절차

---

## ✅ 최종 체크리스트 요약

### 🚨 배포 전 반드시 해야 할 것 (Critical)
1. ✅ 프로덕션 `SECRET_KEY` 생성 및 설정
2. ✅ PostgreSQL/MySQL 데이터베이스 생성 및 연결
3. ✅ 프로덕션 `.env` 파일 생성 (`.gitignore` 확인)
4. ✅ 데이터베이스 스키마 마이그레이션
5. ✅ 기본 기능 테스트 (회원가입, 로그인, 파일 변환)
6. ✅ 보안 테스트 (CSRF, SQL Injection, XSS)
7. ✅ 백업 전략 수립 및 테스트

### 💡 배포 전 하면 좋은 것 (Recommended)
1. 클라우드 스토리지 연동 (S3, Blob Storage)
2. 로깅 서비스 연동 (CloudWatch, Monitor)
3. 에러 트래킹 서비스 (Sentry)
4. CDN 설정 (정적 파일)
5. 자동 백업 스크립트
6. 성능 모니터링 도구

### ⏰ 배포 후 즉시 확인할 것
1. 서버 로그 확인 (에러 없음)
2. 데이터베이스 연결 확인
3. 파일 업로드/다운로드 작동 확인
4. 이메일 발송 기능 확인 (필요시)
5. SSL 인증서 정상 작동 확인

---

## 📞 문제 발생 시 대응

### 즉시 확인할 로그
```bash
# 애플리케이션 로그
tail -f logs/app_$(date +%Y-%m-%d).log

# 서버 에러 로그
tail -f /var/log/nginx/error.log  # Nginx 사용 시
```

### 긴급 롤백 절차
1. 이전 버전으로 Git checkout
2. 데이터베이스 백업에서 복구 (필요시)
3. 서버 재시작

---

## 🎯 결론

**현재 상태**: 개발 환경에서 잘 작동하고 있으나, 프로덕션 배포를 위해서는:

1. **데이터베이스 마이그레이션** (SQLite → PostgreSQL/MySQL) - **가장 중요**
2. **보안 설정 강화** (SECRET_KEY, 환경 변수)
3. **파일 저장소 전략** (로컬 vs 클라우드)
4. **백업 전략 수립**

이 4가지만 완료하면 **배포 가능한 상태**입니다.

나머지는 배포 후 점진적으로 개선해도 됩니다.

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

