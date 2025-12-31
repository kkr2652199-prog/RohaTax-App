# 🔄 Git을 통한 원격 업데이트 가이드

> **목적**: 로컬에서 코드를 수정한 후, 인터넷 서버에 자동으로 업데이트를 전송하는 방법

---

## 📋 개요

**질문**: "서버를 인터넷에 두면 로컬로 추가 업데이트 내용 전송 가능한지?"

**답변**: ✅ **네, 가능합니다!** Git을 사용하면 로컬에서 수정한 코드를 원격 서버에 쉽게 전송할 수 있습니다.

---

## 🎯 전체 프로세스 개요

```
[로컬 PC]                    [GitHub/GitLab]              [프로덕션 서버]
   │                              │                              │
   │ 1. 코드 수정                  │                              │
   ├─────────────────────────────>│                              │
   │                              │                              │
   │ 2. git commit                 │                              │
   ├─────────────────────────────>│                              │
   │                              │                              │
   │ 3. git push                   │                              │
   ├─────────────────────────────>│                              │
   │                              │                              │
   │                              │ 4. git pull                  │
   │                              ├─────────────────────────────>│
   │                              │                              │
   │                              │ 5. 서버 재시작               │
   │                              │                              │
```

---

## 🔧 방법 1: 수동 업데이트 (가장 안전)

### 로컬에서 작업

```bash
# 1. 코드 수정 후 커밋
cd C:\Users\user\Desktop\RohaTax\homepage1
git add .
git commit -m "새로운 기능 추가"

# 2. 원격 저장소에 푸시
git push origin main
```

### 서버에서 업데이트 받기

```bash
# 1. 서버 접속
ssh user@your-server-ip

# 2. 프로젝트 디렉토리로 이동
cd /var/www/rohatax

# 3. 최신 코드 가져오기
git pull origin main

# 4. 의존성 업데이트 (필요시)
source venv/bin/activate
pip install -r requirements.txt

# 5. 서버 재시작
sudo supervisorctl restart rohatax
# 또는
./scripts/deploy.sh --restart-only
```

**장점:**
- ✅ 안전함 (수동으로 확인 가능)
- ✅ 롤백 쉬움
- ✅ 문제 발생 시 즉시 대응 가능

**단점:**
- ❌ 매번 서버 접속 필요

---

## 🚀 방법 2: 자동 배포 (Git Hook 사용)

서버에서 Git Hook을 설정하면, `git push``만으로 자동 배포됩니다.

### 서버에서 설정

```bash
# 1. 서버 접속
ssh user@your-server-ip
cd /var/www/rohatax

# 2. Git Hook 디렉토리 확인
ls -la .git/hooks/

# 3. post-receive Hook 생성
nano .git/hooks/post-receive
```

**post-receive 내용:**

```bash
#!/bin/bash
set -e

# 프로젝트 디렉토리로 이동
cd /var/www/rohatax

# 최신 코드 가져오기
git --git-dir=/var/www/rohatax/.git --work-tree=/var/www/rohatax checkout -f main
git pull origin main

# 가상환경 활성화
source venv/bin/activate

# 의존성 업데이트
pip install -r requirements.txt

# 데이터베이스 마이그레이션 (선택사항)
# flask db upgrade

# 서버 재시작
sudo supervisorctl restart rohatax

# 로그 기록
echo "$(date): 자동 배포 완료" >> /var/www/rohatax/logs/deploy.log
```

```bash
# 4. 실행 권한 부여
chmod +x .git/hooks/post-receive
```

### 로컬에서 사용

```bash
# 로컬에서
cd C:\Users\user\Desktop\RohaTax\homepage1
git add .
git commit -m "새로운 기능"
git push origin main

# 서버에서 자동으로 배포됨! 🎉
```

**장점:**
- ✅ 자동화 (한 번 설정하면 자동)
- ✅ 빠른 배포
- ✅ 실수 방지 (자동화된 절차)

**단점:**
- ❌ 설정 복잡
- ❌ 문제 발생 시 즉시 인지 어려움

---

## 🔐 방법 3: GitHub Actions (CI/CD)

GitHub에 코드를 푸시하면 자동으로 서버에 배포됩니다.

### GitHub Actions 워크플로우 생성

`.github/workflows/deploy.yml` 파일 생성:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/rohatax
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            sudo supervisorctl restart rohatax
```

### GitHub Secrets 설정

1. GitHub 저장소 → Settings → Secrets and variables → Actions
2. 다음 Secrets 추가:
   - `SERVER_HOST`: 서버 IP 주소
   - `SERVER_USER`: 서버 사용자명
   - `SSH_PRIVATE_KEY`: SSH 개인키

### 사용법

```bash
# 로컬에서
git push origin main

# GitHub Actions가 자동으로 서버에 배포! 🚀
```

**장점:**
- ✅ 완전 자동화
- ✅ 배포 히스토리 관리
- ✅ 롤백 쉬움
- ✅ 여러 서버 동시 배포 가능

**단점:**
- ❌ 초기 설정 복잡
- ❌ GitHub Pro 필요 (Private 저장소)

---

## 📦 방법 4: 배포 스크립트 사용 (권장)

이미 작성한 `scripts/deploy.sh` 스크립트를 사용합니다.

### 서버에서 설정

```bash
# 배포 스크립트에 실행 권한 부여
chmod +x /var/www/rohatax/scripts/deploy.sh
```

### 로컬에서 작업 후

```bash
# 1. 로컬에서 커밋 및 푸시
cd C:\Users\user\Desktop\RohaTax\homepage1
git add .
git commit -m "업데이트 내용"
git push origin main
```

### 서버에서 배포 스크립트 실행

```bash
# 서버 접속 후
cd /var/www/rohatax
./scripts/deploy.sh --branch main
```

**배포 스크립트가 자동으로:**
1. ✅ Git에서 최신 코드 가져오기
2. ✅ 의존성 설치
3. ✅ 데이터베이스 백업
4. ✅ 마이그레이션 실행
5. ✅ 서버 재시작
6. ✅ 헬스 체크

---

## 🔄 실전 워크플로우 예시

### 시나리오: 홈페이지 텍스트 수정

```bash
# [로컬 PC]
cd C:\Users\user\Desktop\RohaTax\homepage1

# 1. 템플릿 파일 수정
# templates/home_sections/_hero.html 편집

# 2. 변경사항 확인
git status

# 3. 커밋
git add templates/home_sections/_hero.html
git commit -m "홈페이지 히어로 섹션 텍스트 수정"

# 4. 원격 저장소에 푸시
git push origin main
```

```bash
# [프로덕션 서버]
ssh user@your-server-ip
cd /var/www/rohatax

# 5. 배포 스크립트 실행
./scripts/deploy.sh --restart-only

# 또는 수동으로
git pull origin main
sudo supervisorctl restart rohatax
```

**결과**: 몇 초 내에 변경사항이 프로덕션에 반영됩니다! ✅

---

## 🛡️ 안전한 배포를 위한 팁

### 1. 브랜치 전략

```bash
# 개발 브랜치에서 작업
git checkout -b feature/new-feature
# ... 코드 수정 ...
git commit -m "새 기능"
git push origin feature/new-feature

# 테스트 후 main 브랜치로 병합
git checkout main
git merge feature/new-feature
git push origin main
```

### 2. 배포 전 테스트

```bash
# 로컬에서 테스트
python app.py

# 서버에서 배포 전 확인
./scripts/deploy.sh --dry-run  # (구현 필요)
```

### 3. 롤백 방법

```bash
# 서버에서 이전 커밋으로 되돌리기
cd /var/www/rohatax
git log  # 커밋 히스토리 확인
git checkout <이전-커밋-해시>
sudo supervisorctl restart rohatax
```

### 4. 배포 전 백업

```bash
# 배포 스크립트가 자동으로 백업하지만, 수동 백업도 가능
cd /var/www/rohatax
./scripts/backup_db.sh  # 데이터베이스 백업
```

---

## 📊 비교표

| 방법 | 난이도 | 속도 | 안전성 | 자동화 |
|------|--------|------|--------|--------|
| 수동 업데이트 | ⭐ 쉬움 | ⭐⭐ 보통 | ⭐⭐⭐ 높음 | ❌ |
| Git Hook | ⭐⭐ 보통 | ⭐⭐⭐ 빠름 | ⭐⭐ 보통 | ✅ |
| GitHub Actions | ⭐⭐⭐ 어려움 | ⭐⭐⭐ 빠름 | ⭐⭐⭐ 높음 | ✅ |
| 배포 스크립트 | ⭐⭐ 보통 | ⭐⭐ 보통 | ⭐⭐⭐ 높음 | ⭐ 반자동 |

---

## ✅ 추천 워크플로우

**초보자용 (안전 우선):**
```
로컬 수정 → git commit → git push → 서버에서 git pull → 수동 재시작
```

**중급자용 (효율 우선):**
```
로컬 수정 → git commit → git push → 서버에서 배포 스크립트 실행
```

**고급자용 (완전 자동화):**
```
로컬 수정 → git commit → git push → GitHub Actions 자동 배포
```

---

## 🆘 문제 해결

### "Permission denied" 오류

```bash
# SSH 키 권한 확인
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

### "Connection refused" 오류

```bash
# 서버 방화벽 확인
sudo ufw status
sudo ufw allow 22/tcp  # SSH 포트
```

### Git 충돌 해결

```bash
# 서버에서 충돌 발생 시
cd /var/www/rohatax
git stash  # 현재 변경사항 임시 저장
git pull origin main
git stash pop  # 변경사항 복원
# 충돌 해결 후
git add .
git commit -m "충돌 해결"
```

---

## 📝 요약

**질문에 대한 답변:**

> "서버를 인터넷에 두면 로컬로 추가 업데이트 내용 전송 가능한지?"

**답변: ✅ 네, 완전히 가능합니다!**

**가장 간단한 방법:**
1. 로컬에서 코드 수정
2. `git commit` 및 `git push`
3. 서버에서 `git pull` 및 재시작

**자동화하려면:**
- 배포 스크립트 사용 (`./scripts/deploy.sh`)
- 또는 GitHub Actions 설정

**결론:** Git을 사용하면 로컬에서 수정한 내용을 언제든지 원격 서버에 전송할 수 있습니다! 🚀

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

