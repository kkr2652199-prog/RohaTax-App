# 📚 배포 스크립트 및 가이드 상세 설명

> 각 스크립트와 가이드의 기능, 사용법, 작동 원리를 자세히 설명합니다.

---

## 📋 목차

1. [데이터베이스 마이그레이션 스크립트](#1-데이터베이스-마이그레이션-스크립트)
2. [배포 스크립트](#2-배포-스크립트)
3. [프로덕션 설정 가이드](#3-프로덕션-설정-가이드)
4. [Git 원격 업데이트 가이드](#4-git-원격-업데이트-가이드)

---

## 1. 데이터베이스 마이그레이션 스크립트

### 📄 파일: `scripts/migrate_to_postgresql.py`

#### 🎯 기능

**SQLite 데이터베이스를 PostgreSQL로 변환하는 스크립트**

1. **SQLite에서 데이터 읽기**
   - 모든 테이블 목록 가져오기
   - 각 테이블의 스키마(컬럼, 타입, 제약조건) 분석
   - 모든 데이터 추출

2. **PostgreSQL 스키마 생성**
   - SQLite 타입을 PostgreSQL 타입으로 변환
     - `INTEGER` → `INTEGER`
     - `TEXT` → `TEXT`
     - `AUTOINCREMENT` → `SERIAL`
     - `datetime('now')` → `CURRENT_TIMESTAMP`
   - 외래키 제약조건 재생성
   - 인덱스 재생성

3. **데이터 마이그레이션**
   - 배치 삽입으로 성능 최적화
   - 트랜잭션으로 데이터 무결성 보장
   - 에러 발생 시 롤백

4. **안전장치**
   - `--dry-run` 모드: 실제 마이그레이션 없이 테스트
   - 상세한 로그 기록
   - 각 단계별 검증

#### 💻 사용법

```bash
# 1. 필수 패키지 설치
pip install psycopg2-binary

# 2. 테스트 모드 (실제 마이그레이션 안 함)
python scripts/migrate_to_postgresql.py \
    --sqlite-path database/app.db \
    --postgres-url postgresql://user:pass@host:5432/dbname \
    --dry-run

# 3. 실제 마이그레이션
python scripts/migrate_to_postgresql.py \
    --sqlite-path database/app.db \
    --postgres-url postgresql://user:pass@host:5432/dbname
```

#### 🔍 작동 원리

```
1. SQLite 연결
   ↓
2. 테이블 목록 가져오기
   ↓
3. 각 테이블마다:
   ├─ 스키마 분석 (컬럼, 타입, 제약조건)
   ├─ PostgreSQL CREATE TABLE SQL 생성
   ├─ 테이블 생성
   ├─ 데이터 읽기 (SQLite)
   ├─ 데이터 삽입 (PostgreSQL, 배치)
   └─ 인덱스 생성
   ↓
4. 마이그레이션 완료
```

#### ⚠️ 주의사항

- **백업 필수**: 마이그레이션 전 SQLite 파일 백업
- **테스트 먼저**: `--dry-run`으로 먼저 테스트
- **데이터 검증**: 마이그레이션 후 데이터 개수 확인

---

### 📄 파일: `scripts/migrate_to_mysql.py`

#### 🎯 기능

**SQLite 데이터베이스를 MySQL로 변환하는 스크립트**

PostgreSQL 버전과 동일하지만, MySQL 특화 변환:
- `INTEGER` → `INT`
- `TEXT` → `TEXT`
- `AUTOINCREMENT` → `AUTO_INCREMENT`
- `ENGINE=InnoDB`, `CHARSET=utf8mb4` 추가

#### 💻 사용법

```bash
# 필수 패키지 설치
pip install pymysql

# 마이그레이션 실행
python scripts/migrate_to_mysql.py \
    --sqlite-path database/app.db \
    --mysql-host localhost \
    --mysql-user root \
    --mysql-password password \
    --mysql-database rohatax \
    --dry-run
```

---

## 2. 배포 스크립트

### 📄 파일: `scripts/deploy.sh`

#### 🎯 기능

**프로덕션 서버에 코드를 배포하는 자동화 스크립트**

1. **요구사항 확인**
   - Python3, Git 설치 확인
   - 프로젝트 디렉토리 존재 확인

2. **데이터베이스 백업**
   - PostgreSQL/MySQL 자동 백업
   - 백업 파일에 타임스탬프 추가
   - 오래된 백업 자동 삭제

3. **코드 업데이트**
   - Git에서 최신 코드 가져오기
   - 현재 변경사항 자동 저장 (stash)

4. **의존성 설치**
   - 가상환경 활성화
   - `requirements.txt` 의존성 설치

5. **데이터베이스 마이그레이션**
   - 스키마 변경사항 적용
   - `--skip-migration` 옵션으로 스킵 가능

6. **서버 재시작**
   - systemd 또는 Supervisor로 재시작
   - Nginx 설정 재로드

7. **헬스 체크**
   - 서버 정상 작동 확인
   - 실패 시 자동 롤백 (선택사항)

#### 💻 사용법

```bash
# 1. 실행 권한 부여
chmod +x scripts/deploy.sh

# 2. 전체 배포 (기본: main 브랜치)
./scripts/deploy.sh

# 3. 특정 브랜치 배포
./scripts/deploy.sh --branch develop

# 4. 마이그레이션 스킵하고 배포
./scripts/deploy.sh --skip-migration

# 5. 서버만 재시작 (코드 업데이트 없음)
./scripts/deploy.sh --restart-only
```

#### 🔍 작동 원리

```
1. 요구사항 확인
   ↓
2. 데이터베이스 백업
   ↓
3. Git에서 코드 가져오기
   ↓
4. 의존성 설치
   ↓
5. 마이그레이션 실행
   ↓
6. 서버 재시작
   ↓
7. 헬스 체크
   ↓
8. 완료!
```

#### ⚙️ 설정 수정

스크립트 상단의 변수 수정:

```bash
PROJECT_DIR="/var/www/rohatax"  # 프로덕션 경로
VENV_PATH="$PROJECT_DIR/venv"   # 가상환경 경로
APP_USER="www-data"             # 웹 서버 사용자
```

#### ⚠️ 주의사항

- **서버 경로 확인**: `PROJECT_DIR` 변수 수정 필수
- **권한 확인**: 스크립트 실행 권한 및 sudo 권한 필요
- **백업 확인**: 마이그레이션 전 자동 백업 확인

---

## 3. 프로덕션 설정 가이드

### 📄 파일: `PRODUCTION_SETUP_GUIDE.md`

#### 🎯 기능

**로컬 개발 환경을 프로덕션 환경으로 전환하는 완전한 가이드**

#### 📚 포함 내용

1. **서버 준비**
   - 클라우드 서버 선택 가이드
   - 초기 시스템 설정
   - 필수 패키지 설치

2. **데이터베이스 설정**
   - PostgreSQL/MySQL 설치
   - 데이터베이스 및 사용자 생성
   - 마이그레이션 실행

3. **애플리케이션 설정**
   - 코드 배포
   - 환경 변수 설정 (`.env`)
   - 디렉토리 권한 설정

4. **웹 서버 설정**
   - Gunicorn 설치 및 설정
   - Supervisor 프로세스 관리
   - Nginx 리버스 프록시

5. **SSL 인증서 설정**
   - Let's Encrypt 무료 SSL
   - HTTPS 강제 리다이렉트

6. **배포 및 업데이트**
   - 배포 스크립트 사용법
   - 수동 배포 절차

7. **모니터링 및 백업**
   - 로그 모니터링
   - 자동 백업 설정

#### 💡 사용 시나리오

**처음 프로덕션 배포할 때:**
1. 가이드를 순서대로 따라하기
2. 각 단계별 체크리스트 확인
3. 문제 발생 시 "문제 해결" 섹션 참고

**기존 서버 업데이트할 때:**
- "배포 및 업데이트" 섹션만 참고

---

## 4. Git 원격 업데이트 가이드

### 📄 파일: `GIT_REMOTE_UPDATE_GUIDE.md`

#### 🎯 기능

**로컬에서 수정한 코드를 원격 서버에 전송하는 방법 가이드**

#### 📚 포함 내용

1. **전체 프로세스 개요**
   - 로컬 → GitHub → 서버 흐름도
   - 각 단계별 설명

2. **4가지 업데이트 방법**
   - **방법 1**: 수동 업데이트 (가장 안전)
   - **방법 2**: Git Hook 자동 배포
   - **방법 3**: GitHub Actions CI/CD
   - **방법 4**: 배포 스크립트 사용 (권장)

3. **실전 워크플로우**
   - 실제 사용 예시
   - 단계별 명령어

4. **안전한 배포 팁**
   - 브랜치 전략
   - 배포 전 테스트
   - 롤백 방법

#### 💡 핵심 질문에 대한 답변

**Q: "서버를 인터넷에 두면 로컬로 추가 업데이트 내용 전송 가능한지?"**

**A: ✅ 네, 완전히 가능합니다!**

**가장 간단한 방법:**
```bash
# 로컬에서
git add .
git commit -m "업데이트"
git push origin main

# 서버에서
git pull origin main
sudo supervisorctl restart rohatax
```

**자동화 방법:**
- 배포 스크립트 사용: `./scripts/deploy.sh`
- GitHub Actions 설정 (완전 자동)

#### 🔄 업데이트 프로세스 비교

| 방법 | 난이도 | 속도 | 안전성 | 추천도 |
|------|--------|------|--------|--------|
| 수동 업데이트 | ⭐ 쉬움 | ⭐⭐ | ⭐⭐⭐ | 초보자 |
| 배포 스크립트 | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | **권장** |
| Git Hook | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 중급자 |
| GitHub Actions | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 고급자 |

---

## 🎯 전체 워크플로우 요약

### 처음 배포할 때

```
1. 서버 준비
   └─ PRODUCTION_SETUP_GUIDE.md 참고

2. 데이터베이스 마이그레이션
   └─ scripts/migrate_to_postgresql.py 실행

3. 애플리케이션 배포
   └─ scripts/deploy.sh 실행

4. 완료! ✅
```

### 이후 업데이트할 때

```
1. 로컬에서 코드 수정
   └─ git commit & git push

2. 서버에서 업데이트
   └─ scripts/deploy.sh 실행
   또는
   └─ GIT_REMOTE_UPDATE_GUIDE.md 참고
```

---

## 📊 파일 구조

```
homepage1/
├── scripts/
│   ├── migrate_to_postgresql.py  # SQLite → PostgreSQL
│   ├── migrate_to_mysql.py       # SQLite → MySQL
│   └── deploy.sh                 # 배포 자동화
├── PRODUCTION_SETUP_GUIDE.md     # 프로덕션 설정 가이드
├── GIT_REMOTE_UPDATE_GUIDE.md    # Git 업데이트 가이드
└── DEPLOYMENT_CHECKLIST.md       # 배포 전 체크리스트
```

---

## ✅ 사용 시나리오별 가이드

### 시나리오 1: 처음 프로덕션 배포

1. `DEPLOYMENT_CHECKLIST.md` 확인
2. `PRODUCTION_SETUP_GUIDE.md` 따라하기
3. `scripts/migrate_to_postgresql.py` 실행
4. `scripts/deploy.sh` 실행

### 시나리오 2: 코드 업데이트

1. 로컬에서 코드 수정
2. `git commit` & `git push`
3. `GIT_REMOTE_UPDATE_GUIDE.md` 참고
4. 서버에서 `scripts/deploy.sh` 실행

### 시나리오 3: 데이터베이스 마이그레이션

1. `scripts/migrate_to_postgresql.py --dry-run` 테스트
2. 실제 마이그레이션 실행
3. 데이터 검증

---

## 🆘 문제 해결

각 가이드 파일에 "문제 해결" 섹션이 포함되어 있습니다:
- 서버 시작 실패
- 데이터베이스 연결 실패
- Nginx 502 오류
- Git 충돌 해결

---

## 📝 요약

### 각 스크립트/가이드의 역할

1. **마이그레이션 스크립트**: SQLite → PostgreSQL/MySQL 변환
2. **배포 스크립트**: 코드 업데이트 및 서버 재시작 자동화
3. **프로덕션 가이드**: 처음 배포할 때 전체 설정 방법
4. **Git 업데이트 가이드**: 로컬 → 서버 업데이트 방법

### 핵심 답변

**Q: 로컬에서 서버로 업데이트 전송 가능한가?**
**A: ✅ 네, Git을 사용하면 완전히 가능합니다!**

**가장 간단한 방법:**
```bash
# 로컬: git push
# 서버: git pull + 재시작
```

**자동화 방법:**
```bash
# 서버: ./scripts/deploy.sh
```

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

