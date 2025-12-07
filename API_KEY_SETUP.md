# 🔑 API 키 설정 가이드

## ⚠️ 중요: API 키 유출 문제 해결

유출된 API 키가 Google에서 차단되었습니다. 새로운 API 키를 발급받아 설정해야 합니다.

---

## 📋 설정 방법

### 1. 새로운 Gemini API 키 발급

1. **Google AI Studio 접속**
   - https://aistudio.google.com/app/apikey

2. **API 키 생성**
   - "Create API Key" 버튼 클릭
   - 새 API 키가 생성됩니다 (예: `AIzaSy...`)

3. **기존 키 삭제 (선택사항)**
   - 유출된 키는 Google에서 이미 차단되었으므로 삭제 권장

---

### 2. `.env` 파일 생성 및 설정

**위치**: `homepage1/.env` (프로젝트 루트)

**파일 내용**:
```env
# Google Gemini API Key (필수)
GEMINI_API_KEY=your_new_api_key_here

# 또는 GOOGLE_API_KEY 사용 가능
# GOOGLE_API_KEY=your_new_api_key_here

# 기본 설정
SECRET_KEY=your-secret-key-here-min-32-chars
PORT=5001
HOST=127.0.0.1
DEBUG=false
ENVIRONMENT=development
```

**주의사항**:
- `.env` 파일은 Git에 커밋하지 마세요 (이미 `.gitignore`에 포함됨)
- `your_new_api_key_here` 부분을 실제 발급받은 API 키로 교체하세요

---

### 3. React 앱용 `.env` 파일 (선택사항)

React 앱은 상위 디렉토리(`homepage1/.env`)의 환경 변수를 자동으로 읽습니다.

**별도 설정이 필요한 경우**: `homepage1/kweon21/.env.local`

```env
GEMINI_API_KEY=your_new_api_key_here
```

---

### 4. 서버 재시작

1. **모든 Python 프로세스 종료**
   ```powershell
   taskkill /F /IM python.exe /T
   ```

2. **서버 재시작**
   ```powershell
   .\start_server_5001.bat
   ```

3. **React 앱 재빌드** (필요시)
   ```powershell
   cd kweon21
   npm run build
   ```

---

## ✅ 확인 방법

서버 시작 후 브라우저에서 `/studio` 페이지에 접속하여:
- 주제 생성 기능이 정상 작동하는지 확인
- 콘솔에 API 키 관련 오류가 없는지 확인

---

## 🔒 보안 주의사항

1. **절대 하드코딩 금지**
   - ❌ 코드 파일에 API 키 직접 작성
   - ❌ 배치 파일(`.bat`)에 API 키 직접 작성
   - ✅ `.env` 파일에만 저장

2. **Git 커밋 금지**
   - `.env` 파일은 절대 Git에 커밋하지 마세요
   - 이미 `.gitignore`에 포함되어 있지만, 확인하세요

3. **API 키 관리**
   - 정기적으로 키를 교체하세요
   - 사용량 모니터링을 통해 이상 징후 확인

---

## 🆘 문제 해결

### "API key not valid" 오류
- `.env` 파일이 올바른 위치에 있는지 확인 (`homepage1/.env`)
- API 키 앞뒤에 공백이 없는지 확인
- 서버를 재시작했는지 확인

### "API key was reported as leaked" 오류
- 새로운 API 키를 발급받아야 합니다
- 기존 키는 더 이상 사용할 수 없습니다

---

**작성일**: 2025-12-06  
**수정일**: 2025-12-06 (하드코딩된 API 키 제거)



