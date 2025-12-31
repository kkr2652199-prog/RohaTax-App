# 📊 homepage1 데이터베이스 동기화 가이드

> **목적**: homepage1의 DB를 본진과 똑같이 복사하고, 활동 내역만 초기화

---

## 🎯 작업 목표

1. ✅ **본진 DB → homepage1 복사**: 본진의 DB를 homepage1에 복사
2. ✅ **활동 내역 초기화**: 유저들의 활동 내역만 삭제
3. ✅ **데이터 보존**: 유저 정보, 결제 내역, 상품 정보는 보존

---

## 📋 보존되는 데이터

- ✅ **users** - 유저 정보 (임시 유저 포함)
- ✅ **payment_history** - 결제 내역
- ✅ **orders** - 주문 내역
- ✅ **product_packages** - 상품 패키지
- ✅ **subscription_plans** - 구독 플랜
- ✅ **user_subscriptions** - 사용자 구독
- ✅ **settings** - 설정
- ✅ **gold_customers** - 골드 고객 리스트
- ✅ **policies** - 비즈니스 라운지 정책

---

## 🗑️ 삭제되는 데이터 (활동 내역)

- ❌ **usage_logs** - 사용 로그
- ❌ **validation_logs** - 검증 로그
- ❌ **conversion_logs** - 변환 로그
- ❌ **activity_logs** - 활동 로그
- ❌ **token_history (use 타입만)** - 토큰 사용 내역

---

## 🚀 실행 방법

### 방법 1: 자동 실행 (권장)

homepage1 폴더에서 실행:

```bash
cd homepage1
python scripts/sync_db_from_main.py
python scripts/reset_activity_logs_only.py
```

### 방법 2: 단계별 실행

#### 1단계: 본진 DB 복사

```bash
cd homepage1
python scripts/sync_db_from_main.py
```

이 스크립트는:
- homepage1 DB 백업 생성
- 본진 DB를 homepage1로 복사
- 동기화 확인

#### 2단계: 활동 내역 초기화

```bash
cd homepage1
python scripts/reset_activity_logs_only.py
```

이 스크립트는:
- 활동 내역 테이블만 삭제
- 유저 정보, 결제 내역 등은 보존
- 삭제 요약 출력

---

## ⚠️ 주의사항

1. **백업 자동 생성**: 실행 전 자동으로 백업이 생성됩니다
2. **유저 정보 보존**: 모든 유저 정보는 보존됩니다
3. **결제 내역 보존**: 결제 내역은 보존됩니다
4. **활동 내역만 삭제**: 로그/이력만 삭제됩니다

---

## 🔍 확인 사항

실행 후 확인:

```bash
cd homepage1
python -c "import sqlite3; conn = sqlite3.connect('database/app.db'); cursor = conn.cursor(); print('유저 수:', cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]); print('결제 내역:', cursor.execute('SELECT COUNT(*) FROM payment_history').fetchone()[0]); print('활동 로그:', cursor.execute('SELECT COUNT(*) FROM activity_logs').fetchone()[0] if cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='activity_logs'\").fetchone() else 0)"
```

---

## 📝 작업 순서

1. ✅ 본진 DB 확인 (유저, 결제 내역 등)
2. ✅ homepage1 DB 백업
3. ✅ 본진 DB → homepage1 복사
4. ✅ 활동 내역 초기화
5. ✅ 동기화 확인

---

## 🆘 문제 해결

### 오류: "본진 DB 파일이 없습니다"
- 본진의 `database/app.db` 파일이 있는지 확인
- 경로가 올바른지 확인

### 오류: "권한 오류"
```bash
chmod 644 database/app.db
```

### 오류: "테이블이 없습니다"
- 본진 DB에 해당 테이블이 있는지 확인
- 마이그레이션이 적용되었는지 확인

---

## ✅ 완료 체크리스트

- [ ] 본진 DB 확인 완료
- [ ] homepage1 DB 백업 완료
- [ ] 본진 DB 복사 완료
- [ ] 활동 내역 초기화 완료
- [ ] 동기화 확인 완료
- [ ] 유저 정보 보존 확인
- [ ] 결제 내역 보존 확인

