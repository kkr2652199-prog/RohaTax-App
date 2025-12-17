## Cursor Rules Summary (RohaTax / 로하택스)

### Priority
- Always apply Cursor rules first before any task.
- Complex changes must be rolled out via stepwise testing (1-step test per change).

### Extension-Based Module Management
- Do NOT split existing main files; extend via linked modules only.
- Keep existing structure stable; add functionality in extension modules.
- Directory patterns:
  - `core/file_parser.py` + `core/file_parser_utils/` (e.g., `data_processor.py`, `header_analyzer.py`)
  - `routes/conversion.py` + `routes/conversion_modules/`
  - `core/conversion_engine.py` + `core/engine_processor.py`
- Naming: `[feature]_processor.py`, `[feature]_analyzer.py` in dedicated utils dirs.

### Extension Workflow (Phases)
1) Requirement analysis → target file, functionality, dependencies, interface.
2) Module design → structure, interface spec, implementation/test plan.
3) Implementation → small, independent module; typed; minimal deps.
4) Integration → import and use from the main file (no refactor/split).
5) Tests → unit + integration; measure performance.
6) Docs & quality checks → complexity < 10, coverage ≥ 90% (where feasible).

### Database/Backend Guides
- Use `core/db.py:get_conn()`; enable foreign keys; transactions for critical ops.
- Schema in `database/schema.sql`; add indices for perf hotspots.
- Logging: `core/logging_setup.py`; reduce noise for third-party loggers.
- Error handling: return user-friendly messages; centralize patterns.

### Security
- CSRF token generation/validation patterns in `core/security.py`.
- Session hardening (HTTPOnly, SameSite, conditional Secure) via `app.py`.
- Admin checks gated via session flags; prefer decorators when feasible.

### Token System (Business Rules)
- Track `token_balance` and `tokens_used` in `users`.
- Available tokens = `token_balance - tokens_used`.
- Validate before conversion; log usage to `usage_logs`.

### File Size & Structure Rules
- Preferred: keep Python files ≤ 500 lines (guideline; main files may exceed but extend via modules).
- Avoid deep nesting; use guard clauses; add only non-obvious comments.

### Frontend/UX Guidelines
- Consistent design tokens; responsive layouts; accessible components.

#### VIP/Premium 마이홈 안정성 규칙 (2025-10-31)
- 아코디언/모달 토글은 다른 스크립트 오류와 무관하게 동작해야 한다.
  - 필요 시 try/catch 래핑으로 격리.
- 외부 CSS 우선순위로 인한 숨김 유지 방지:
  - 열 때 `element.style.setProperty('display','block','important')`, 닫을 때 `'none','important'` 허용.
- 토큰 내역 표:
  - 기본 페이지 크기 50, 헤더 클릭 정렬(날짜/구분/파일명/충전/사용/잔액) 제공.

### Operational
- Backups under `database/backups/`; logs under `logs/` with retention.
- No destructive actions without dry-run/confirmation.

#### Git Hooks / Lint
- ESLint v9(flat) + Prettier, Husky/lint-staged 필수. 커밋 전 자동 포맷/린트.

---
This summary is a working, high-signal reference. For full details, see `.cursor/rules/*`.




