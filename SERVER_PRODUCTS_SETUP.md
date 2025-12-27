# 🚀 서버에서 상품 데이터 삽입 가이드

> **문제**: Python 코드를 bash 쉘에 직접 붙여넣어서 실행하려다 오류 발생  
> **해결**: Python 스크립트 파일로 만들어서 실행

---

## ⚠️ 중요: 복사 방법

- **`<--- 복사하세요`** 표시가 있는 부분만 복사해서 붙여넣으세요
- **`<--- 복사하지 마세요`** 표시가 있는 부분은 설명이므로 복사하지 마세요

---

## 방법 1: 기존 스크립트 사용 (가장 간단함) ⭐

### <--- 복사하지 마세요 (설명)
이 방법은 이미 만들어진 스크립트를 실행하는 방법입니다.
### <--- 복사하지 마세요 (설명 끝)

### 1단계: 프로젝트 디렉토리로 이동
<--- 복사하세요
cd ~/RohaTax-App
<--- 복사 끝

### <--- 복사하지 마세요 (설명)
만약 프로젝트가 다른 경로에 있다면 그 경로로 이동하세요.
예: cd /var/www/rohatax
### <--- 복사하지 마세요 (설명 끝)

### 2단계: 가상환경 활성화 (있는 경우만)
<--- 복사하세요
source venv/bin/activate
<--- 복사 끝

### <--- 복사하지 마세요 (설명)
가상환경이 없다면 이 단계는 건너뛰세요.
### <--- 복사하지 마세요 (설명 끝)

### 3단계: 스크립트 실행
<--- 복사하세요
python3 scripts/seed_products_server.py
<--- 복사 끝

---

## 방법 2: 간단한 Python 파일 직접 만들기

### <--- 복사하지 마세요 (설명)
이 방법은 서버에서 직접 Python 파일을 만들어서 실행하는 방법입니다.
### <--- 복사하지 마세요 (설명 끝)

### 1단계: 프로젝트 디렉토리로 이동
<--- 복사하세요
cd ~/RohaTax-App
<--- 복사 끝

### 2단계: Python 파일 생성 (nano 에디터 열기)
<--- 복사하세요
nano seed_products_simple.py
<--- 복사 끝

### <--- 복사하지 마세요 (설명)
nano 에디터가 열리면 아래 Python 코드를 복사해서 붙여넣으세요.
### <--- 복사하지 마세요 (설명 끝)

### 3단계: Python 코드 복사해서 붙여넣기
<--- 복사하세요
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('database/app.db')
c = conn.cursor()

products = [
    ('Welcome Event', '신규 가입 혜택 (50토큰)', 0, 50, 0, 'event', 1),
    ('Welcome Period Event', '신규 가입 혜택 (3일 무료)', 0, 0, 3, 'event_period', 1),
    ('Standard', '필요할 때만 사용하는 유연한 플랜', 300, 1, 0, 'package', 1),
    ('Premium', '100건 패키지로 한 번에 해결', 15000, 100, 0, 'package', 1),
    ('Gold', '세무사/대리 발급 전문', 100000, 999999, 30, 'subscription', 1),
]

for p in products:
    name, desc, price, token, duration, ptype, active = p
    c.execute('SELECT id FROM products WHERE name = ?', (name,))
    if not c.fetchone():
        c.execute(
            """INSERT INTO products 
               (name, description, price, token_amount, duration_days, type, is_active, vat_included, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime('now', 'localtime'), datetime('now', 'localtime'))""",
            (name, desc, price, token, duration, ptype, active)
        )
        print(f'✅ 삽입 완료: {name}')
    else:
        print(f'⚠️  건너뜀: {name} (이미 존재)')

conn.commit()
conn.close()
print('>>> 상품 데이터 삽입 완료!')
<--- 복사 끝

### <--- 복사하지 마세요 (설명)
nano 에디터에서:
1. 위 코드를 복사해서 붙여넣기 (마우스 우클릭 또는 Ctrl+Shift+V)
2. Ctrl+O (저장)
3. Enter (파일명 확인)
4. Ctrl+X (종료)
### <--- 복사하지 마세요 (설명 끝)

### 4단계: 파일 실행
<--- 복사하세요
python3 seed_products_simple.py
<--- 복사 끝

---

## 방법 3: Python 인터랙티브 모드 사용

### <--- 복사하지 마세요 (설명)
이 방법은 Python 인터랙티브 모드에서 직접 코드를 실행하는 방법입니다.
### <--- 복사하지 마세요 (설명 끝)

### 1단계: 프로젝트 디렉토리로 이동
<--- 복사하세요
cd ~/RohaTax-App
<--- 복사 끝

### 2단계: Python 인터랙티브 모드 시작
<--- 복사하세요
python3
<--- 복사 끝

### <--- 복사하지 마세요 (설명)
Python 프롬프트 `>>>`가 나타나면 아래 코드를 한 줄씩 복사해서 붙여넣으세요.
### <--- 복사하지 마세요 (설명 끝)

### 3단계: Python 코드 복사해서 붙여넣기 (한 줄씩)
<--- 복사하세요
import sqlite3
<--- 복사 끝

<--- 복사하세요
conn = sqlite3.connect('database/app.db')
<--- 복사 끝

<--- 복사하세요
c = conn.cursor()
<--- 복사 끝

<--- 복사하세요
products = [
    ('Welcome Event', '신규 가입 혜택 (50토큰)', 0, 50, 0, 'event', 1),
    ('Welcome Period Event', '신규 가입 혜택 (3일 무료)', 0, 0, 3, 'event_period', 1),
    ('Standard', '필요할 때만 사용하는 유연한 플랜', 300, 1, 0, 'package', 1),
    ('Premium', '100건 패키지로 한 번에 해결', 15000, 100, 0, 'package', 1),
    ('Gold', '세무사/대리 발급 전문', 100000, 999999, 30, 'subscription', 1),
]
<--- 복사 끝

<--- 복사하세요
for p in products:
    name, desc, price, token, duration, ptype, active = p
    c.execute('SELECT id FROM products WHERE name = ?', (name,))
    if not c.fetchone():
        c.execute(
            """INSERT INTO products 
               (name, description, price, token_amount, duration_days, type, is_active, vat_included, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime('now', 'localtime'), datetime('now', 'localtime'))""",
            (name, desc, price, token, duration, ptype, active)
        )
        print(f'✅ 삽입 완료: {name}')
<--- 복사 끝

<--- 복사하세요
conn.commit()
<--- 복사 끝

<--- 복사하세요
conn.close()
<--- 복사 끝

<--- 복사하세요
print('>>> 완료!')
<--- 복사 끝

<--- 복사하세요
exit()
<--- 복사 끝

---

## ✅ 실행 결과 확인

### <--- 복사하지 마세요 (설명)
데이터가 제대로 들어갔는지 확인하는 명령어입니다.
### <--- 복사하지 마세요 (설명 끝)

<--- 복사하세요
python3 -c "import sqlite3; conn = sqlite3.connect('database/app.db'); rows = conn.execute('SELECT name, price FROM products').fetchall(); [print(f'{r[0]}: {r[1]}원') for r in rows]"
<--- 복사 끝

---

## 🆘 문제 해결

### 문제 1: "database/app.db를 찾을 수 없음"

#### 현재 위치 확인
<--- 복사하세요
pwd
<--- 복사 끝

#### 데이터베이스 파일 찾기
<--- 복사하세요
find ~ -name "app.db"
<--- 복사 끝

#### 올바른 경로로 이동 (찾은 경로로 변경)
<--- 복사하세요
cd /var/www/rohatax
<--- 복사 끝

### <--- 복사하지 마세요 (설명)
위 경로는 예시입니다. find 명령어로 찾은 실제 경로로 변경하세요.
### <--- 복사하지 마세요 (설명 끝)

---

### 문제 2: "Permission denied" (권한 오류)

#### 파일 권한 확인
<--- 복사하세요
ls -la database/app.db
<--- 복사 끝

#### 권한 수정
<--- 복사하세요
chmod 644 database/app.db
<--- 복사 끝

---

### 문제 3: "No module named 'core'" (모듈 오류)

#### 프로젝트 루트에서 실행
<--- 복사하세요
cd ~/RohaTax-App
<--- 복사 끝

#### 또는 절대 경로로 실행
<--- 복사하세요
python3 /var/www/rohatax/scripts/seed_products_server.py
<--- 복사 끝

### <--- 복사하지 마세요 (설명)
위 경로는 예시입니다. 실제 프로젝트 경로로 변경하세요.
### <--- 복사하지 마세요 (설명 끝)

---

## 📋 체크리스트

- [ ] 서버에 접속 완료
- [ ] 프로젝트 디렉토리로 이동 완료
- [ ] 데이터베이스 파일 존재 확인 완료
- [ ] Python 스크립트 실행 완료
- [ ] 실행 결과 확인 완료

---

**작성일**: 2025-12-27  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1
