# 🚨 긴급: API 키 오류 해결 가이드

## 현재 상황

1. ✅ `.env` 파일 생성 완료
2. ❌ React 빌드 파일에 **유출된 API 키가 하드코딩**되어 있음
3. ❌ 서버가 실행 중이지만 새로운 API 키가 설정되지 않음

---

## 즉시 해결 방법 (3단계)

### 1단계: 새로운 API 키 발급 및 설정

1. **Google AI Studio 접속**
   - https://aistudio.google.com/app/apikey

2. **API 키 생성**
   - "Create API Key" 클릭
   - 새 키 복사 (예: `AIzaSy...`)

3. **`.env` 파일 수정**
   - 파일 위치: `homepage1/.env`
   - 다음 줄을 찾아서:
     ```env
     GEMINI_API_KEY=your_new_api_key_here
     ```
   - 실제 API 키로 교체:
     ```env
     GEMINI_API_KEY=AIzaSy발급받은_실제_키_여기
     ```

---

### 2단계: React 앱 재빌드 (필수!)

**현재 빌드된 파일에 유출된 API 키가 포함되어 있어 반드시 재빌드해야 합니다.**

```powershell
# kweon21 디렉토리로 이동
cd kweon21

# React 앱 재빌드 (새로운 API 키로)
npm run build

# 원래 디렉토리로 돌아가기
cd ..
```

**중요**: 빌드가 완료될 때까지 기다리세요 (약 30초~1분 소요)

---

### 3단계: 서버 재시작

```powershell
# 모든 Python 프로세스 종료
taskkill /F /IM python.exe /T

# 서버 재시작
.\start_server_5001.bat
```

---

## 확인 방법

1. 브라우저에서 `http://localhost:5001/studio` 접속
2. 주제 생성 기능 테스트
3. 콘솔에 오류가 없는지 확인

---

## 문제가 계속되면

1. **`.env` 파일 확인**
   - `homepage1/.env` 파일이 존재하는지 확인
   - `GEMINI_API_KEY=실제_키` 형식이 맞는지 확인 (공백 없이)

2. **React 빌드 확인**
   - `homepage1/kweon21/dist/` 폴더가 최신인지 확인
   - 빌드 시간이 방금인지 확인

3. **서버 로그 확인**
   - 서버 콘솔에 환경 변수 로드 메시지가 있는지 확인

---

**작성일**: 2025-12-06  
**상태**: 긴급 수정 필요



