# 🚀 프로덕션 환경 설정 가이드

> **목적**: 로컬 개발 환경(SQLite)에서 프로덕션 환경(클라우드 서버 + PostgreSQL/MySQL)으로 전환하는 완전한 가이드

---

## 📋 목차

1. [서버 준비](#1-서버-준비)
2. [데이터베이스 설정](#2-데이터베이스-설정)
3. [애플리케이션 설정](#3-애플리케이션-설정)
4. [웹 서버 설정](#4-웹-서버-설정)
5. [SSL 인증서 설정](#5-ssl-인증서-설정)
6. [배포 및 업데이트](#6-배포-및-업데이트)
7. [모니터링 및 백업](#7-모니터링-및-백업)

---

## 1. 서버 준비

### 1.1 클라우드 서버 선택

**추천 옵션:**
- **AWS EC2**: 유연하고 확장 가능
- **DigitalOcean**: 간단하고 저렴
- **Azure VM**: Microsoft 생태계 통합
- **GCP Compute Engine**: Google 클라우드 통합

**최소 사양:**
- CPU: 2 코어
- RAM: 2GB (4GB 권장)
- 디스크: 20GB SSD
- OS: Ubuntu 22.04 LTS (권장)

### 1.2 서버 초기 설정

```bash
# 1. 서버 접속
ssh root@your-server-ip

# 2. 시스템 업데이트
apt update && apt upgrade -y

# 3. 필수 패키지 설치
apt install -y python3 python3-pip python3-venv git nginx supervisor

# 4. 방화벽 설정 (UFW)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable

# 5. 프로젝트 디렉토리 생성
mkdir -p /var/www/rohatax
chown www-data:www-data /var/www/rohatax
```

---

## 2. 데이터베이스 설정

### 2.1 PostgreSQL 설치 및 설정 (권장)

```bash
# PostgreSQL 설치
apt install -y postgresql postgresql-contrib

# PostgreSQL 사용자 및 데이터베이스 생성
sudo -u postgres psql << EOF
CREATE USER rohatax_user WITH PASSWORD 'your-secure-password';
CREATE DATABASE rohatax_db OWNER rohatax_user;
GRANT ALL PRIVILEGES ON DATABASE rohatax_db TO rohatax_user;
\q
EOF
```

### 2.2 MySQL 설치 및 설정 (대안)

```bash
# MySQL 설치
apt install -y mysql-server

# MySQL 설정
mysql_secure_installation

# 데이터베이스 생성
mysql -u root -p << EOF
CREATE DATABASE rohatax_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rohatax_user'@'localhost' IDENTIFIED BY 'your-secure-password';
GRANT ALL PRIVILEGES ON rohatax_db.* TO 'rohatax_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 2.3 데이터 마이그레이션

**로컬에서 실행:**

```bash
# PostgreSQL로 마이그레이션
python scripts/migrate_to_postgresql.py \
    --sqlite-path database/app.db \
    --postgres-url postgresql://rohatax_user:password@your-server-ip:5432/rohatax_db \
    --dry-run  # 먼저 테스트

# 테스트 성공 후 실제 마이그레이션
python scripts/migrate_to_postgresql.py \
    --sqlite-path database/app.db \
    --postgres-url postgresql://rohatax_user:password@your-server-ip:5432/rohatax_db
```

**또는 MySQL로:**

```bash
python scripts/migrate_to_mysql.py \
    --sqlite-path database/app.db \
    --mysql-host your-server-ip \
    --mysql-user rohatax_user \
    --mysql-password password \
    --mysql-database rohatax_db \
    --dry-run
```

---

## 3. 애플리케이션 설정

### 3.1 코드 배포

```bash
# 서버에서
cd /var/www/rohatax

# Git 저장소 클론 (또는 기존 저장소 pull)
git clone https://github.com/your-username/rohatax.git .
# 또는
git pull origin main

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# PostgreSQL 드라이버 설치 (PostgreSQL 사용 시)
pip install psycopg2-binary

# MySQL 드라이버 설치 (MySQL 사용 시)
pip install pymysql
```

### 3.2 환경 변수 설정

```bash
# .env 파일 생성
cd /var/www/rohatax
cp env.example .env
nano .env
```

**.env 파일 내용:**

```bash
# 환경 설정
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-min-32-chars-generate-with-python-secrets-token_hex-32
DEBUG=false
HOST=0.0.0.0
PORT=5000

# 데이터베이스 설정 (PostgreSQL)
DATABASE_URL=postgresql://rohatax_user:password@localhost:5432/rohatax_db

# 또는 MySQL
# DATABASE_URL=mysql://rohatax_user:password@localhost:3306/rohatax_db

# 파일 업로드 설정
MAX_FILE_SIZE=52428800
UPLOAD_FOLDER=/var/www/rohatax/uploads
OUTPUT_FOLDER=/var/www/rohatax/output

# 로깅 설정
LOG_LEVEL=WARNING
LOG_FOLDER=/var/www/rohatax/logs

# 보안 설정
CSRF_ENABLED=true
RATE_LIMIT_ENABLED=true

# 토큰 시스템
DEFAULT_TOKEN_BALANCE=100
TOKEN_COST_PER_CONVERSION=1
```

**SECRET_KEY 생성:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3.3 디렉토리 권한 설정

```bash
# 업로드/출력 디렉토리 생성
mkdir -p /var/www/rohatax/{uploads,output,logs,database/backups}
chown -R www-data:www-data /var/www/rohatax
chmod -R 755 /var/www/rohatax
```

---

## 4. 웹 서버 설정

### 4.1 Gunicorn 설치 및 설정

```bash
# Gunicorn 설치
pip install gunicorn

# Gunicorn 설정 파일 생성
nano /var/www/rohatax/gunicorn_config.py
```

**gunicorn_config.py:**

```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "/var/www/rohatax/logs/gunicorn_access.log"
errorlog = "/var/www/rohatax/logs/gunicorn_error.log"
loglevel = "info"
```

### 4.2 Supervisor 설정 (프로세스 관리)

```bash
# Supervisor 설정 파일 생성
sudo nano /etc/supervisor/conf.d/rohatax.conf
```

**rohatax.conf:**

```ini
[program:rohatax]
command=/var/www/rohatax/venv/bin/gunicorn -c /var/www/rohatax/gunicorn_config.py app:app
directory=/var/www/rohatax
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/rohatax/logs/supervisor.log
environment=PATH="/var/www/rohatax/venv/bin"
```

```bash
# Supervisor 재시작
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start rohatax
```

### 4.3 Nginx 설정 (리버스 프록시)

```bash
# Nginx 설정 파일 생성
sudo nano /etc/nginx/sites-available/rohatax
```

**rohatax (Nginx 설정):**

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # SSL 인증서 설정 후 443 포트로 리다이렉트
    # return 301 https://$server_name$request_uri;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static {
        alias /var/www/rohatax/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        alias /var/www/rohatax/uploads;
        expires 1d;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/rohatax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. SSL 인증서 설정

### 5.1 Let's Encrypt (무료 SSL)

```bash
# Certbot 설치
apt install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

### 5.2 Nginx SSL 설정 업데이트

Certbot이 자동으로 Nginx 설정을 업데이트하지만, 수동 설정 예시:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 보안 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... 나머지 설정 동일
}

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 6. 배포 및 업데이트

### 6.1 배포 스크립트 사용

```bash
# 배포 스크립트에 실행 권한 부여
chmod +x scripts/deploy.sh

# 전체 배포
./scripts/deploy.sh --branch main

# 마이그레이션 스킵하고 배포
./scripts/deploy.sh --skip-migration

# 서버만 재시작
./scripts/deploy.sh --restart-only
```

### 6.2 수동 배포 절차

```bash
# 1. 코드 업데이트
cd /var/www/rohatax
git pull origin main

# 2. 의존성 업데이트
source venv/bin/activate
pip install -r requirements.txt

# 3. 데이터베이스 마이그레이션 (필요시)
# flask db upgrade  # Flask-Migrate 사용 시
# 또는 직접 스키마 적용

# 4. 서버 재시작
sudo supervisorctl restart rohatax

# 5. 헬스 체크
curl http://localhost:5000/health
```

### 6.3 Git을 통한 원격 업데이트 (로컬 → 서버)

**로컬에서 작업 후:**

```bash
# 1. 변경사항 커밋
git add .
git commit -m "업데이트 내용"

# 2. 원격 저장소에 푸시
git push origin main
```

**서버에서 자동 업데이트 (선택사항):**

```bash
# 서버에서 Git Hook 설정 (자동 배포)
cd /var/www/rohatax/.git/hooks
nano post-receive
```

**post-receive (Git Hook):**

```bash
#!/bin/bash
cd /var/www/rohatax
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart rohatax
```

또는 **수동으로 서버에서 pull:**

```bash
# 서버 접속 후
cd /var/www/rohatax
git pull origin main
./scripts/deploy.sh --restart-only
```

---

## 7. 모니터링 및 백업

### 7.1 로그 모니터링

```bash
# 애플리케이션 로그
tail -f /var/www/rohatax/logs/app_$(date +%Y-%m-%d).log

# Gunicorn 로그
tail -f /var/www/rohatax/logs/gunicorn_error.log

# Nginx 로그
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Supervisor 로그
tail -f /var/www/rohatax/logs/supervisor.log
```

### 7.2 데이터베이스 백업

**자동 백업 스크립트:**

```bash
# 백업 스크립트 생성
nano /var/www/rohatax/scripts/backup_db.sh
```

**backup_db.sh:**

```bash
#!/bin/bash
BACKUP_DIR="/var/www/rohatax/database/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# PostgreSQL 백업
pg_dump postgresql://rohatax_user:password@localhost:5432/rohatax_db > "$BACKUP_FILE"

# 오래된 백업 삭제 (7일 이상)
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +7 -delete
```

**Cron으로 자동 실행:**

```bash
# Crontab 편집
crontab -e

# 매일 새벽 2시에 백업
0 2 * * * /var/www/rohatax/scripts/backup_db.sh
```

### 7.3 파일 백업

```bash
# 업로드 파일 백업 (선택사항)
rsync -av /var/www/rohatax/uploads/ /backup/uploads/
```

---

## ✅ 체크리스트

배포 전 확인사항:

- [ ] 서버 접속 및 기본 설정 완료
- [ ] PostgreSQL/MySQL 설치 및 데이터베이스 생성
- [ ] 데이터 마이그레이션 완료 (테스트 포함)
- [ ] `.env` 파일 생성 및 SECRET_KEY 설정
- [ ] Gunicorn 및 Supervisor 설정 완료
- [ ] Nginx 설정 및 SSL 인증서 발급
- [ ] 도메인 DNS 설정 완료
- [ ] 방화벽 설정 확인
- [ ] 백업 스크립트 설정
- [ ] 로그 모니터링 설정

---

## 🆘 문제 해결

### 서버가 시작되지 않을 때

```bash
# Supervisor 상태 확인
sudo supervisorctl status rohatax

# 로그 확인
sudo supervisorctl tail -f rohatax

# 수동 실행 테스트
cd /var/www/rohatax
source venv/bin/activate
python app.py
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 연결 테스트
psql -U rohatax_user -d rohatax_db -h localhost

# MySQL 연결 테스트
mysql -u rohatax_user -p rohatax_db

# 방화벽 확인
sudo ufw status
```

### Nginx 502 Bad Gateway

```bash
# Gunicorn이 실행 중인지 확인
ps aux | grep gunicorn

# 포트 확인
netstat -tlnp | grep 5000

# Gunicorn 재시작
sudo supervisorctl restart rohatax
```

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

