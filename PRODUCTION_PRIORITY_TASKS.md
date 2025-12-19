# 🎯 상용화 전 필수 작업 우선순위

> **목적**: 상용화 전에 반드시 해야 할 작업을 우선순위별로 정리  
> **작성일**: 2025-01-18

---

## 📋 전체 우선순위 요약

### 🔴 Critical (즉시 해결 - 배포 전 필수)
1. **DDoS 방어 설정** (1시간)
2. **프로덕션 SECRET_KEY 설정** (10분)
3. **자동 백업 설정** (10분)
4. **HTTPS/SSL 인증서 설정** (30분)

### 🟡 Important (배포 전 권장)
5. **데이터베이스 마이그레이션** (SQLite → PostgreSQL/MySQL) (3-5일)
6. **SQL Injection 점검** (30분)
7. **환경 변수 설정** (.env 파일) (10분)
8. **성능 테스트** (2-3시간)

### 🟢 Optional (배포 후 개선)
9. **모니터링 시스템 강화** (Sentry 등)
10. **로드 밸런서 설정**
11. **CDN 설정**

---

## 🔴 1순위: DDoS 방어 설정 (가장 중요!)

### ⏱️ 소요 시간: 1시간

### 🎯 목적
대규모 DDoS 공격으로부터 서버 보호

### 📝 작업 내용

#### 방법 1: Cloudflare 사용 (가장 빠르고 쉬움) ⭐ 권장

**단계:**
1. [Cloudflare](https://www.cloudflare.com/) 가입 (무료)
2. 도메인 추가
3. DNS 설정 변경 (네임서버를 Cloudflare로)
4. DDoS 보호 자동 활성화

**장점:**
- ✅ 무료
- ✅ 자동 DDoS 방어
- ✅ CDN 기능 포함
- ✅ SSL 인증서 자동 제공

**비용:** 무료

#### 방법 2: Nginx Rate Limiting 설정

**Nginx 설정 파일에 추가:**
```nginx
# /etc/nginx/sites-available/rohatax
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=5r/s;

server {
    # 일반 요청 제한
    limit_req zone=general burst=20 nodelay;
    
    # API 요청 제한
    location /api/ {
        limit_req zone=api burst=10 nodelay;
    }
}
```

**재시작:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### ✅ 완료 체크
- [ ] Cloudflare 설정 완료 또는 Nginx Rate Limiting 설정 완료
- [ ] DDoS 방어 테스트 (선택사항)

---

## 🔴 2순위: 프로덕션 SECRET_KEY 설정

### ⏱️ 소요 시간: 10분

### 🎯 목적
세션 보안 및 CSRF 보호를 위한 안전한 키 설정

### 📝 작업 내용

#### 1. SECRET_KEY 생성
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### 2. .env 파일에 설정
```bash
# 프로덕션 서버의 .env 파일
SECRET_KEY=생성한-64자-랜덤-문자열
ENVIRONMENT=production
DEBUG=false
```

#### 3. .gitignore 확인
```bash
# .gitignore에 .env가 포함되어 있는지 확인
echo ".env" >> .gitignore
```

### ✅ 완료 체크
- [ ] SECRET_KEY 생성 완료
- [ ] .env 파일에 설정 완료
- [ ] .gitignore에 .env 포함 확인
- [ ] Git에 .env 파일이 커밋되지 않았는지 확인

---

## 🔴 3순위: 자동 백업 설정

### ⏱️ 소요 시간: 10분

### 🎯 목적
데이터 손실 방지 및 빠른 복구

### 📝 작업 내용

#### 1. 백업 스크립트 생성
```bash
# scripts/backup_db.sh 생성
#!/bin/bash
BACKUP_DIR="/var/www/rohatax/database/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

mkdir -p "$BACKUP_DIR"

# PostgreSQL 백업
pg_dump postgresql://user:pass@localhost:5432/dbname > "$BACKUP_FILE"

# 오래된 백업 삭제 (7일 이상)
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +7 -delete

echo "백업 완료: $BACKUP_FILE"
```

#### 2. 실행 권한 부여
```bash
chmod +x scripts/backup_db.sh
```

#### 3. Cron 설정 (매일 새벽 2시)
```bash
crontab -e

# 추가
0 2 * * * /var/www/rohatax/scripts/backup_db.sh >> /var/www/rohatax/logs/backup.log 2>&1
```

### ✅ 완료 체크
- [ ] 백업 스크립트 생성 완료
- [ ] Cron 설정 완료
- [ ] 백업 테스트 완료
- [ ] 복구 테스트 완료 (선택사항)

---

## 🔴 4순위: HTTPS/SSL 인증서 설정

### ⏱️ 소요 시간: 30분

### 🎯 목적
데이터 암호화 및 보안 통신

### 📝 작업 내용

#### Let's Encrypt 사용 (무료)

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

#### Nginx 설정 자동 업데이트
Certbot이 자동으로 Nginx 설정을 업데이트합니다.

### ✅ 완료 체크
- [ ] SSL 인증서 발급 완료
- [ ] HTTPS 접속 확인
- [ ] HTTP → HTTPS 리다이렉트 확인
- [ ] 자동 갱신 설정 확인

---

## 🟡 5순위: 데이터베이스 마이그레이션

### ⏱️ 소요 시간: 3-5일 (계획 및 실행)

### 🎯 목적
SQLite → PostgreSQL/MySQL 전환 (프로덕션 안정성)

### 📝 작업 내용

#### 1. 클라우드 데이터베이스 생성
- AWS RDS (PostgreSQL/MySQL)
- Azure Database
- GCP Cloud SQL

#### 2. 마이그레이션 실행
```bash
python scripts/migrate_to_postgresql.py \
    --sqlite-path database/app.db \
    --postgres-url postgresql://user:pass@host:5432/dbname \
    --dry-run  # 먼저 테스트

# 실제 마이그레이션
python scripts/migrate_to_postgresql.py \
    --sqlite-path database/app.db \
    --postgres-url postgresql://user:pass@host:5432/dbname
```

#### 3. 환경 변수 업데이트
```bash
# .env 파일
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### ⚠️ 중요
- **백업 필수**: 마이그레이션 전 데이터베이스 백업
- **테스트 먼저**: `--dry-run`으로 먼저 테스트
- **점진적 전환**: 스테이징 환경에서 먼저 테스트

### ✅ 완료 체크
- [ ] 클라우드 데이터베이스 생성 완료
- [ ] 마이그레이션 스크립트 테스트 완료
- [ ] 실제 마이그레이션 완료
- [ ] 데이터 검증 완료
- [ ] 애플리케이션 연결 테스트 완료

---

## 🟡 6순위: SQL Injection 점검

### ⏱️ 소요 시간: 30분

### 🎯 목적
SQL Injection 공격 방어 확인

### 📝 작업 내용

#### 1. Bandit 스캔 실행
```bash
pip install bandit
bandit -r . -f json -o bandit-report.json
```

#### 2. 수동 코드 검토
- 모든 SQL 쿼리에서 파라미터 바인딩 사용 확인
- Raw SQL 사용 부분 점검

#### 3. 수정 (필요시)
```python
# ❌ 위험한 방법
conn.execute(f"SELECT * FROM users WHERE username = '{username}'")

# ✅ 안전한 방법
conn.execute("SELECT * FROM users WHERE username = ?", (username,))
```

### ✅ 완료 체크
- [ ] Bandit 스캔 완료
- [ ] 취약점 수정 완료
- [ ] 재스캔으로 확인 완료

---

## 🟡 7순위: 환경 변수 설정

### ⏱️ 소요 시간: 10분

### 🎯 목적
프로덕션 환경 설정 완료

### 📝 작업 내용

#### .env 파일 생성
```bash
# 프로덕션 서버에서
cd /var/www/rohatax
cp env.example .env
nano .env
```

#### 필수 설정
```bash
ENVIRONMENT=production
SECRET_KEY=<생성한-키>
DEBUG=false
HOST=0.0.0.0
PORT=5000
DATABASE_URL=postgresql://user:pass@host:5432/dbname
LOG_LEVEL=WARNING
```

### ✅ 완료 체크
- [ ] .env 파일 생성 완료
- [ ] 모든 필수 변수 설정 완료
- [ ] .gitignore 확인 완료

---

## 🟡 8순위: 성능 테스트

### ⏱️ 소요 시간: 2-3시간

### 🎯 목적
동시 접속자 처리 능력 확인

### 📝 작업 내용

#### Apache Bench 사용
```bash
# 설치
sudo apt install -y apache2-utils

# 테스트 (100명 동시 접속, 총 1000회 요청)
ab -n 1000 -c 100 http://your-domain.com/
```

#### 목표
- 최소 50명 동시 접속 가능
- 평균 응답 시간 2초 이하
- 에러율 1% 이하

### ✅ 완료 체크
- [ ] 성능 테스트 완료
- [ ] 목표 성능 달성 확인
- [ ] 병목 지점 파악 및 개선 (필요시)

---

## 📊 우선순위별 시간 투자

| 순위 | 작업 | 소요 시간 | 중요도 |
|------|------|----------|--------|
| 1 | DDoS 방어 | 1시간 | 🔴 Critical |
| 2 | SECRET_KEY 설정 | 10분 | 🔴 Critical |
| 3 | 자동 백업 | 10분 | 🔴 Critical |
| 4 | SSL 인증서 | 30분 | 🔴 Critical |
| 5 | DB 마이그레이션 | 3-5일 | 🟡 Important |
| 6 | SQL Injection 점검 | 30분 | 🟡 Important |
| 7 | 환경 변수 설정 | 10분 | 🟡 Important |
| 8 | 성능 테스트 | 2-3시간 | 🟡 Important |

**Critical 작업 총 시간: 약 2시간**  
**Important 작업 총 시간: 약 3-5일**

---

## 🎯 최소 배포 가능 기준

### Critical 작업만 완료하면:
- ✅ 소규모 사용자 (10-50명) 배포 가능
- ✅ 기본 보안 보장
- ✅ 데이터 백업 보장

### Important 작업까지 완료하면:
- ✅ 중규모 사용자 (50-200명) 배포 가능
- ✅ 안정적인 데이터베이스
- ✅ 성능 검증 완료

---

## 📋 체크리스트

### Critical (배포 전 필수)
- [ ] DDoS 방어 설정 (Cloudflare 또는 Nginx)
- [ ] SECRET_KEY 프로덕션 값 설정
- [ ] 자동 백업 스케줄 설정
- [ ] HTTPS/SSL 인증서 설정

### Important (배포 전 권장)
- [ ] 데이터베이스 마이그레이션 (SQLite → PostgreSQL/MySQL)
- [ ] SQL Injection 점검 및 수정
- [ ] 환경 변수 설정 완료
- [ ] 성능 테스트 완료

---

## 🚀 빠른 시작 가이드

### 오늘 바로 할 수 있는 것 (약 2시간)

```bash
# 1. Cloudflare 설정 (1시간)
# - Cloudflare 가입 및 도메인 추가

# 2. SECRET_KEY 생성 및 설정 (10분)
python3 -c "import secrets; print(secrets.token_hex(32))"
# .env 파일에 추가

# 3. 자동 백업 설정 (10분)
# - 백업 스크립트 생성
# - Cron 설정

# 4. SSL 인증서 발급 (30분)
sudo certbot --nginx -d your-domain.com
```

**이 4가지만 완료하면 최소한의 상용화 준비 완료!**

---

## 🎯 결론

### 1순위 작업: **DDoS 방어 설정**

**이유:**
- 가장 큰 보안 위험
- 구현이 가장 빠름 (1시간)
- 무료로 해결 가능 (Cloudflare)
- 다른 작업보다 우선순위 높음

**다음 순서:**
1. DDoS 방어 (1시간)
2. SECRET_KEY 설정 (10분)
3. 자동 백업 (10분)
4. SSL 인증서 (30분)

**총 시간: 약 2시간** → 오늘 바로 완료 가능!

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

