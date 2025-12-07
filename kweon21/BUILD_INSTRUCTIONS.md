# kweon21 빌드 가이드

## 독립 놀이터 설정 완료

kweon21은 이제 Flask 앱과 완전히 독립된 놀이터로 설정되었습니다.

## 빌드 방법

### 1. 의존성 설치
```bash
cd homepage1/kweon21
npm install
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일에 GEMINI_API_KEY 설정
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 3. 빌드 실행
```bash
npm run build
```

빌드가 완료되면 `homepage1/kweon21/dist/` 폴더에 정적 파일이 생성됩니다.

### 4. Flask 서버 재시작
```bash
# Flask 서버를 재시작하면 /studio 경로에서 kweon21 앱에 접근할 수 있습니다.
```

## 접근 경로

- **로컬 개발**: `http://localhost:50001/studio`
- **프로덕션**: `https://your-domain.com/studio`

## 특징

- ✅ 기존 변환 앱과 100% 격리
- ✅ React Router 지원 (클라이언트 사이드 라우팅)
- ✅ 정적 파일 자동 서빙
- ✅ 독립된 Blueprint로 관리

## 문제 해결

### 빌드 오류 발생 시
1. `node_modules` 삭제 후 재설치: `rm -rf node_modules && npm install`
2. Vite 캐시 삭제: `rm -rf node_modules/.vite`
3. TypeScript 오류 확인: `npm run build` 출력 확인

### Flask에서 404 오류 발생 시
1. `homepage1/kweon21/dist/` 폴더가 존재하는지 확인
2. `dist/index.html` 파일이 있는지 확인
3. Flask 서버 로그에서 Blueprint 등록 확인




