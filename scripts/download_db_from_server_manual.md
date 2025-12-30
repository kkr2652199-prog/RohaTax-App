# 배포 서버에서 데이터베이스 다운로드 가이드

## 방법 1: PowerShell에서 SCP 사용 (SSH 키 필요)

```powershell
# 배포 서버에서 데이터베이스 다운로드
scp ubuntu@52.78.116.159:/home/ubuntu/RohaTax-App/database/app.db database/app.db.from_server
```

**SSH 키가 설정되어 있지 않은 경우:**
- SSH 키를 먼저 설정하거나
- 아래 방법 2를 사용하세요

## 방법 2: AWS Lightsail 웹 콘솔 사용 (권장)

1. **AWS Lightsail 콘솔 접속**
   - https://lightsail.aws.amazon.com 접속
   - `roha-tax-server` 인스턴스 선택

2. **터미널 열기**
   - "Connect using SSH" 버튼 클릭
   - 웹 기반 터미널이 열립니다

3. **서버에서 데이터베이스 확인**
   ```bash
   cd /home/ubuntu/RohaTax-App
   ls -lh database/app.db
   
   # 상품 정보 확인
   sqlite3 database/app.db "SELECT COUNT(*) FROM products;"
   sqlite3 database/app.db "SELECT COUNT(*) FROM product_packages;"
   sqlite3 database/app.db "SELECT COUNT(*) FROM subscription_plans;"
   ```

4. **데이터베이스 파일 다운로드**
   - Lightsail 콘솔에서 "Download" 버튼 사용
   - 또는 아래 명령어로 파일 내용 확인 후 복사

## 방법 3: 서버에서 직접 SQL 덤프 (가장 안전)

서버 터미널에서 실행:

```bash
cd /home/ubuntu/RohaTax-App

# 데이터베이스 백업 생성
sqlite3 database/app.db ".backup database/app_backup_$(date +%Y%m%d_%H%M%S).db"

# 상품 정보만 SQL로 추출
sqlite3 database/app.db <<EOF
.output products_restore.sql
.mode insert products
SELECT * FROM products;
.mode insert product_packages
SELECT * FROM product_packages;
.mode insert subscription_plans
SELECT * FROM subscription_plans;
.quit
EOF

# 생성된 SQL 파일 확인
cat products_restore.sql
```

그 다음 로컬에서:
1. `products_restore.sql` 파일 내용을 복사
2. 로컬 데이터베이스에 적용

## 방법 4: 스크립트로 자동화 (SSH 키 설정 후)

SSH 키를 설정한 후:

```bash
# SSH 키 생성 (처음 한 번만)
ssh-keygen -t rsa -b 4096

# 공개 키를 서버에 복사
ssh-copy-id ubuntu@52.78.116.159

# 그 다음 스크립트 실행
python scripts/download_db_from_server.py
```


