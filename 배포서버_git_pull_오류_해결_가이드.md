# 배포 서버 git pull 오류 해결 가이드

**문제**: `git pull` 실행 시 로컬 변경사항 때문에 실패

---

## 🔍 현재 문제

### 오류 메시지
```
error: Your local changes to the following files would be overwritten by merge:
  database/app.db
  scripts/backup_verification.sh
Please commit your changes or stash them before you merge.
```

### 원인
- 배포 서버에 로컬 변경사항이 있어서 `git pull`이 실패
- 새로운 스크립트 파일들이 아직 배포 서버에 없음

---

## ✅ 해결 방법 (단계별)

### 배포 서버 터미널에서 순서대로 실행

#### 1단계: 로컬 변경사항 임시 저장

```bash
cd /home/ubuntu/RohaTax-App
git stash
```

**의미**: 로컬 변경사항을 임시로 저장 (나중에 복원 가능)

#### 2단계: 하늘저장소에서 최신 코드 가져오기

```bash
git pull origin main
```

**의미**: 새로운 스크립트 파일들을 가져옴

#### 3단계: 스크립트 파일 확인

```bash
ls -la scripts/clear_activity_logs_only.py
```

**의미**: 스크립트 파일이 있는지 확인

#### 4단계: 스크립트 실행 권한 부여

```bash
chmod +x scripts/clear_activity_logs_only.py
```

#### 5단계: 스크립트 실행

```bash
python3 scripts/clear_activity_logs_only.py
```

---

## 📋 전체 명령어 (복사해서 실행)

```bash
cd /home/ubuntu/RohaTax-App
git stash
git pull origin main
ls -la scripts/clear_activity_logs_only.py
chmod +x scripts/clear_activity_logs_only.py
python3 scripts/clear_activity_logs_only.py
```

---

## ⚠️ 주의사항

### git stash란?
- 로컬 변경사항을 **임시로 저장**하는 명령어
- 나중에 `git stash pop`으로 복원 가능
- 하지만 `database/app.db`는 데이터베이스 파일이므로 복원할 필요 없음

### database/app.db는?
- 데이터베이스 파일은 Git에 추적되지 않아야 함
- 변경사항을 무시해도 됨

---

## 🆘 문제 해결

### 문제: git stash 후에도 오류 발생
```bash
# 강제로 변경사항 무시하고 pull
git reset --hard origin/main
git pull origin main
```

**주의**: 이 명령어는 로컬 변경사항을 완전히 삭제합니다.

---

## ✅ 완료 확인

```bash
# 스크립트 파일 확인
ls -la scripts/clear_activity_logs_only.py

# 파일이 있으면 성공!
```

---

**위 명령어를 순서대로 실행하세요!**

