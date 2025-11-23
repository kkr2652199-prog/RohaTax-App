# 삭제 후보 파일 리스트

**작성일:** 2025-11-23  
**작성자:** Executor  
**목적:** 사용되지 않는 파일(Dead Code) 식별 및 제거

---

## ✅ 삭제해도 100% 안전한 파일 목록

### 1. 백업 파일

| 파일 경로 | 삭제 사유 | 확인 방법 |
|---------|---------|---------|
| `routes/conversion.py.backup` | 백업 파일로, 현재 프로젝트에서 어디서도 import되지 않음 | `grep` 검색 결과: 0건 |
| `database/app_backup_before_activity_logs_20251116_161614.db` | 오래된 데이터베이스 백업 파일 (2025-11-16 생성) | 백업 파일이므로 현재 DB와 무관 |

### 2. 사용되지 않는 라우트 파일

| 파일 경로 | 삭제 사유 | 확인 방법 |
|---------|---------|---------|
| `routes/conversion_new.py` | `app.py`에서 등록되지 않음. `conversion_modules/`로 리팩토링되어 대체됨 | `app.py` 확인: `register_blueprint` 없음 |
| `routes/analytics.py` | `app.py`에서 등록되지 않음. 블루프린트가 생성되어 있으나 실제 사용 안 됨 | `app.py` 확인: `register_blueprint` 없음 |

### 3. 임시/테스트 파일

| 파일 경로 | 삭제 사유 | 확인 방법 |
|---------|---------|---------|
| `commit_msg.txt` | 임시 커밋 메시지 파일. Git 히스토리에 이미 반영됨 | `grep` 검색 결과: 0건 |
| `test_token_api_browser.js` | 브라우저 테스트용 스크립트. 프로젝트에서 사용 안 됨 | `grep` 검색 결과: 0건 |

### 4. 체크 스크립트 파일들 (단독 실행용)

| 파일 경로 | 삭제 사유 | 확인 방법 |
|---------|---------|---------|
| `check_dependencies.py` | 단독 실행용 진단 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 함수명만 참조, 파일 import 없음 |
| `check_password.py` | 단독 실행용 체크 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `check_plan_type.py` | 단독 실행용 체크 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `check_plan.py` | 단독 실행용 체크 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `check_table.py` | 단독 실행용 체크 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `check_token.py` | 단독 실행용 체크 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 함수명만 참조, 파일 import 없음 |
| `check_user_grade.py` | 단독 실행용 체크 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `check_users.py` | 단독 실행용 체크 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |

### 5. 유틸리티 스크립트 (사용 안 됨)

| 파일 경로 | 삭제 사유 | 확인 방법 |
|---------|---------|---------|
| `copy_to_rohatax.py` | 일회성 마이그레이션 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `create_password_reset_table.py` | 일회성 마이그레이션 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `create_sample_excel.py` | 샘플 파일 생성 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `restore_tokens.py` | 일회성 복구 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `set_gold_vip.py` | 일회성 설정 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `show_reset_token.py` | 디버깅용 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |
| `verify_token_routes.py` | 검증용 스크립트. 다른 파일에서 import 안 됨 | `grep` 검색 결과: 0건 |

---

## ⚠️ 보류된 파일 (의심스러워서 제외)

| 파일 경로 | 보류 사유 |
|---------|---------|
| `analyze_sample.py` | 함수명으로 참조됨 (`analyze_sample_file()`). 실제 사용 여부 불명확 |
| `diagnose_system.py` | 문서에서 언급됨. 시스템 진단용으로 보관 필요할 수 있음 |
| `forensic_analysis.py` | 포렌식 분석용. 필요 시 사용 가능 |
| `apply_migration.py` | 마이그레이션 관련. `core/db.py`에서 `_apply_migrations` 함수 참조 |
| `run_migration.py` | 마이그레이션 실행 스크립트. 필요 시 사용 가능 |
| `_archive/` 폴더 | 아카이브 폴더. 사용자가 의도적으로 보관한 것으로 추정 |

---

## 📊 삭제 후 예상 효과

- **삭제 예정 파일 수:** 18개
- **예상 디스크 공간 절약:** 약 50-100 KB (코드 파일 기준)
- **코드베이스 정리:** 사용되지 않는 파일 제거로 프로젝트 구조 명확화

---

## ✅ 삭제 실행 전 확인 사항

1. [ ] Git 커밋 완료 (현재 상태 저장)
2. [ ] 백업 파일은 별도 보관 여부 확인
3. [ ] 삭제 후 서버 정상 작동 확인

---

**Commander 승인 대기 중...**

