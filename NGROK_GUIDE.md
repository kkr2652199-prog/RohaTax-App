# 🌐 인터넷에서 로컬 서버 접속하기 (Ngrok 가이드)

## 📋 개요
로컬에서 실행 중인 Flask 서버(포트 5001)를 인터넷에서 접속 가능하게 만드는 방법입니다.

## 🚀 빠른 시작

### 방법 1: Ngrok 사용 (가장 간단)

#### 1단계: Ngrok 설치

**옵션 A: 직접 다운로드**
1. https://ngrok.com/download 접속
2. Windows 버전 다운로드
3. `ngrok.exe` 파일을 `homepage1` 폴더에 복사

**옵션 B: Chocolatey 사용 (관리자 권한 필요)**
```powershell
choco install ngrok
```

#### 2단계: 서버 실행
```batch
start_server_5001.bat
```

#### 3단계: Ngrok 터널 시작
```batch
start_ngrok_tunnel.bat
```

또는 직접 명령어:
```bash
ngrok http 5001
```

#### 4단계: 공개 URL 확인
Ngrok이 다음과 같은 URL을 생성합니다:
```
Forwarding    https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:5001
```

이 `https://xxxx-xxx-xxx-xxx.ngrok-free.app` URL을 인터넷 어디서나 접속할 수 있습니다!

---

## 🔧 다른 방법들

### 방법 2: Localtunnel (무료, 설치 불필요)

**Node.js가 설치되어 있어야 합니다.**

```bash
# 설치
npm install -g localtunnel

# 실행
lt --port 5001
```

### 방법 3: Cloudflare Tunnel (무료, 안정적)

1. https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/ 접속
2. Cloudflare Tunnel 설치
3. 설정 후 실행

### 방법 4: VS Code 포트 포워딩 (VS Code 사용 시)

1. VS Code에서 포트 5001을 열기
2. 포트 옆 "포트 전달" 아이콘 클릭
3. "포트 전달" 선택

---

## ⚠️ 주의사항

### 보안
- **임시 테스트용으로만 사용하세요**
- Ngrok 무료 버전은 URL이 공개되므로 누구나 접속 가능합니다
- 프로덕션 환경에서는 사용하지 마세요
- 민감한 데이터가 있는 경우 주의하세요

### 제한사항
- **Ngrok 무료 버전:**
  - 세션이 일정 시간 후 종료될 수 있음
  - URL이 매번 변경됨
  - 트래픽 제한 있음

- **Ngrok 유료 버전:**
  - 고정 URL 사용 가능
  - 더 긴 세션 시간
  - 더 많은 트래픽 허용

---

## 🎯 사용 예시

### 시나리오 1: 모바일에서 테스트
1. 서버 실행 (`start_server_5001.bat`)
2. Ngrok 실행 (`start_ngrok_tunnel.bat`)
3. 생성된 URL을 모바일 브라우저에서 열기

### 시나리오 2: 다른 사람에게 데모 보여주기
1. 서버 실행
2. Ngrok 실행
3. 생성된 URL을 상대방에게 공유

### 시나리오 3: 웹훅 테스트
1. 서버 실행
2. Ngrok 실행
3. 생성된 URL을 웹훅 설정에 입력

---

## 🔍 문제 해결

### "Ngrok이 설치되어 있지 않습니다" 오류
- `ngrok.exe` 파일이 `homepage1` 폴더에 있는지 확인
- 또는 시스템 PATH에 ngrok이 추가되어 있는지 확인

### "서버가 실행 중이지 않습니다" 경고
- 먼저 `start_server_5001.bat`를 실행하여 서버를 시작하세요

### 연결이 안 됨
- 방화벽 설정 확인
- 서버가 정상적으로 실행 중인지 확인 (`http://localhost:5001` 접속 테스트)

---

## 📚 추가 자료

- [Ngrok 공식 문서](https://ngrok.com/docs)
- [Localtunnel GitHub](https://github.com/localtunnel/localtunnel)
- [Cloudflare Tunnel 문서](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)



