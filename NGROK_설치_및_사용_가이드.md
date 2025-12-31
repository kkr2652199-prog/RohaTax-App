# 🌐 Ngrok 완전 가이드 - 인터넷에서 로컬 서버 접속하기

## 📖 목차
1. [Ngrok이란?](#ngrok이란)
2. [설치 방법 (3가지)](#설치-방법)
3. [사용 방법 (단계별)](#사용-방법)
4. [실제 사용 예시](#실제-사용-예시)
5. [문제 해결](#문제-해결)

---

## 🎯 Ngrok이란?

**Ngrok**은 로컬에서 실행 중인 웹 서버를 인터넷에서 접속할 수 있게 해주는 터널링 도구입니다.

### 왜 필요한가요?
- 로컬에서 개발 중인 웹사이트를 모바일에서 테스트하고 싶을 때
- 다른 사람에게 데모를 보여주고 싶을 때
- 웹훅(Webhook) 테스트가 필요할 때
- 집 밖에서 내 서버에 접속하고 싶을 때

### 작동 원리
```
인터넷 → Ngrok 서버 → 로컬 서버(localhost:5001)
```

---

## 📥 설치 방법

### 방법 1: 직접 다운로드 (가장 간단) ⭐ 추천

#### 1단계: 다운로드
1. 브라우저에서 https://ngrok.com/download 접속
2. "Windows" 버전 클릭하여 다운로드
3. 다운로드한 `ngrok.zip` 파일 압축 해제

#### 2단계: 파일 복사
1. 압축 해제한 폴더에서 `ngrok.exe` 파일 찾기
2. `ngrok.exe` 파일을 다음 위치로 복사:
   ```
   C:\Users\user\Desktop\RohaTax\homepage1\ngrok.exe
   ```

#### 3단계: 확인
- `homepage1` 폴더에 `ngrok.exe` 파일이 있는지 확인

---

### 방법 2: Chocolatey 사용 (관리자 권한 필요)

#### 1단계: Chocolatey 설치 확인
```powershell
choco --version
```

#### 2단계: Ngrok 설치
```powershell
choco install ngrok
```

#### 3단계: 확인
```powershell
ngrok version
```

---

### 방법 3: Scoop 사용

```powershell
scoop install ngrok
```

---

## 🚀 사용 방법 (단계별)

### 전체 프로세스 요약
```
1. Flask 서버 실행 (포트 5001)
2. Ngrok 터널 시작
3. 공개 URL 확인
4. 인터넷에서 접속!
```

---

### 상세 단계

#### ✅ 1단계: Flask 서버 실행

**터미널 1 (서버 실행용)**
```batch
cd C:\Users\user\Desktop\RohaTax\homepage1
start_server_5001.bat
```

또는 더블클릭:
- `start_server_5001.bat` 파일 더블클릭

**확인 방법:**
- 브라우저에서 `http://localhost:5001` 접속
- 정상적으로 페이지가 보이면 성공!

---

#### ✅ 2단계: Ngrok 터널 시작

**방법 A: 배치 파일 사용 (추천)** ⭐

**터미널 2 (Ngrok 실행용)**
```batch
cd C:\Users\user\Desktop\RohaTax\homepage1
start_ngrok_tunnel.bat
```

또는 더블클릭:
- `start_ngrok_tunnel.bat` 파일 더블클릭

**방법 B: 직접 명령어**
```batch
cd C:\Users\user\Desktop\RohaTax\homepage1
ngrok http 5001
```

---

#### ✅ 3단계: 공개 URL 확인

Ngrok이 실행되면 다음과 같은 화면이 나타납니다:

```
ngrok

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        Asia Pacific (ap)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5001

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**중요한 정보:**
- **Forwarding URL**: `https://abc123.ngrok-free.app`
  - 이 URL이 공개 URL입니다!
  - 이 URL을 인터넷 어디서나 접속할 수 있습니다.

---

#### ✅ 4단계: 인터넷에서 접속 테스트

**테스트 방법:**

1. **같은 컴퓨터에서 테스트:**
   - 브라우저에서 `https://abc123.ngrok-free.app` 접속
   - 로컬 서버와 동일한 페이지가 보여야 합니다.

2. **모바일에서 테스트:**
   - 모바일 브라우저에서 `https://abc123.ngrok-free.app` 접속
   - 같은 Wi-Fi 또는 데이터를 사용하여 접속

3. **다른 사람에게 공유:**
   - `https://abc123.ngrok-free.app` URL을 상대방에게 전달
   - 상대방이 브라우저에서 접속하면 내 서버가 보입니다!

---

## 💡 실제 사용 예시

### 예시 1: 모바일에서 테스트하기

**상황:** 로컬에서 개발 중인 웹사이트를 스마트폰에서 확인하고 싶음

**절차:**
1. 컴퓨터에서 `start_server_5001.bat` 실행
2. 새 터미널에서 `start_ngrok_tunnel.bat` 실행
3. 생성된 URL 확인 (예: `https://abc123.ngrok-free.app`)
4. 스마트폰 브라우저에서 해당 URL 접속
5. ✅ 모바일에서 내 웹사이트 확인 가능!

---

### 예시 2: 친구에게 데모 보여주기

**상황:** 개발 중인 기능을 친구에게 보여주고 싶음

**절차:**
1. 서버 실행 (`start_server_5001.bat`)
2. Ngrok 실행 (`start_ngrok_tunnel.bat`)
3. 생성된 URL을 카카오톡/이메일로 전송
4. 친구가 URL 클릭하면 내 서버 접속!

---

### 예시 3: 웹훅(Webhook) 테스트

**상황:** 외부 서비스(예: 결제 API)에서 내 서버로 데이터를 보내야 함

**절차:**
1. 서버 실행
2. Ngrok 실행
3. 생성된 URL을 웹훅 설정에 입력
4. 외부 서비스가 내 로컬 서버로 데이터 전송 가능!

---

## 🔧 문제 해결

### 문제 1: "Ngrok이 설치되어 있지 않습니다" 오류

**해결 방법:**
1. `ngrok.exe` 파일이 `homepage1` 폴더에 있는지 확인
2. 없다면 https://ngrok.com/download 에서 다운로드
3. 다운로드한 `ngrok.exe`를 `homepage1` 폴더에 복사

---

### 문제 2: "서버가 실행 중이지 않습니다" 경고

**해결 방법:**
1. 먼저 `start_server_5001.bat`를 실행하여 서버 시작
2. 브라우저에서 `http://localhost:5001` 접속하여 서버 확인
3. 서버가 정상 작동하면 Ngrok 실행

---

### 문제 3: Ngrok 연결이 안 됨

**확인 사항:**
1. 인터넷 연결 확인
2. 방화벽 설정 확인
3. 서버가 정상 실행 중인지 확인 (`http://localhost:5001`)

**해결 방법:**
```batch
# 서버 재시작
start_server_5001.bat

# Ngrok 재시작
start_ngrok_tunnel.bat
```

---

### 문제 4: "This site can't be reached" 오류

**원인:** Ngrok 세션이 만료되었거나 서버가 종료됨

**해결 방법:**
1. 서버가 실행 중인지 확인
2. Ngrok을 다시 실행 (새 URL 생성됨)
3. 새 URL로 접속

---

### 문제 5: Ngrok 무료 버전 제한

**제한 사항:**
- 세션이 일정 시간 후 자동 종료
- URL이 매번 변경됨
- 트래픽 제한

**해결 방법:**
- Ngrok 유료 플랜 구독 (고정 URL, 더 긴 세션)
- 또는 다른 터널링 서비스 사용 (Localtunnel, Cloudflare Tunnel)

---

## 📊 Ngrok 웹 인터페이스

Ngrok이 실행되면 자동으로 웹 인터페이스가 열립니다:
- **URL**: `http://127.0.0.1:4040`
- **기능**: 요청 로그 확인, 재전송, 통계 등

브라우저에서 `http://127.0.0.1:4040` 접속하면 Ngrok 관리 화면을 볼 수 있습니다.

---

## ⚠️ 보안 주의사항

### ⚠️ 중요: 보안 경고

1. **임시 테스트용으로만 사용**
   - 프로덕션 환경에서는 사용하지 마세요
   - 민감한 데이터가 있는 경우 주의하세요

2. **URL 공유 주의**
   - Ngrok 무료 버전은 URL이 공개되어 누구나 접속 가능
   - URL을 신뢰할 수 있는 사람에게만 공유

3. **세션 종료**
   - 사용 후 반드시 Ngrok 세션 종료 (Ctrl+C)
   - 서버도 종료하는 것을 권장

---

## 🎓 추가 팁

### 팁 1: 고정 URL 사용 (유료 플랜)

Ngrok 유료 플랜을 사용하면 고정 URL을 사용할 수 있습니다:
```batch
ngrok http 5001 --domain=my-fixed-url.ngrok-free.app
```

### 팁 2: 인증 추가

Ngrok에 기본 인증을 추가할 수 있습니다:
```batch
ngrok http 5001 --basic-auth="username:password"
```

### 팁 3: 커스텀 도메인 (유료 플랜)

자신의 도메인을 사용할 수 있습니다:
```batch
ngrok http 5001 --hostname=my-domain.com
```

---

## 📚 참고 자료

- [Ngrok 공식 문서](https://ngrok.com/docs)
- [Ngrok 다운로드](https://ngrok.com/download)
- [Ngrok 가격 플랜](https://ngrok.com/pricing)

---

## ✅ 체크리스트

사용 전 확인 사항:
- [ ] Ngrok 설치 완료 (`ngrok.exe` 파일 확인)
- [ ] Flask 서버 실행 중 (`http://localhost:5001` 접속 가능)
- [ ] 인터넷 연결 정상
- [ ] 방화벽 설정 확인

사용 후 정리:
- [ ] Ngrok 세션 종료 (Ctrl+C)
- [ ] 서버 종료 (필요시)
- [ ] 공유한 URL 무효화 확인

---

**이제 준비 완료! 위 단계를 따라하면 인터넷에서 로컬 서버에 접속할 수 있습니다! 🚀**



