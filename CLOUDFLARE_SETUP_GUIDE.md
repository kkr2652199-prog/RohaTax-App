# 🚀 Cloudflare DDoS 방어 설정 가이드

> **목적**: Cloudflare를 통한 DDoS 방어 설정  
> **소요 시간**: 약 1시간  
> **비용**: 무료

---

## 📋 사전 준비사항

### 필요한 것
- ✅ 도메인 (예: your-domain.com)
- ✅ 도메인 등록 업체 계정 (가비아, 후이즈 등)
- ✅ 이메일 주소 (Cloudflare 가입용)
- ✅ 서버 IP 주소

---

## 🔧 단계별 설정 가이드

### 1단계: Cloudflare 가입 (5분)

1. [Cloudflare 웹사이트](https://www.cloudflare.com/) 접속
2. "Sign Up" 클릭
3. 이메일 주소로 가입
4. 이메일 인증 완료

---

### 2단계: 도메인 추가 (10분)

1. Cloudflare 대시보드에서 **"Add a Site"** 클릭
2. 도메인 입력 (예: `your-domain.com`)
3. **Free 플랜 선택** (무료)
4. **Continue** 클릭

---

### 3단계: DNS 레코드 확인 (10분)

Cloudflare가 자동으로 DNS 레코드를 스캔합니다.

#### 확인 사항:
- ✅ **A 레코드**: 서버 IP 주소가 올바른지 확인
  ```
  Type: A
  Name: @ (또는 your-domain.com)
  Content: 123.45.67.89 (서버 IP)
  Proxy: 🟠 Proxied (주황색 구름 아이콘) ← 중요!
  ```

- ✅ **CNAME 레코드** (www 서브도메인)
  ```
  Type: CNAME
  Name: www
  Content: your-domain.com
  Proxy: 🟠 Proxied (주황색 구름 아이콘) ← 중요!
  ```

#### 중요: Proxy 상태 확인
- 🟠 **Proxied (주황색 구름)**: Cloudflare를 통과 → **DDoS 방어 활성화** ✅
- ⚪ **DNS only (회색 구름)**: Cloudflare를 통과하지 않음 → DDoS 방어 비활성화 ❌

**반드시 🟠 Proxied 상태로 설정하세요!**

---

### 4단계: 네임서버 변경 (20분)

#### 4-1. Cloudflare 네임서버 확인
Cloudflare 대시보드에서 네임서버 정보 확인:
```
예시:
ns1.cloudflare.com
ns2.cloudflare.com
```

#### 4-2. 도메인 등록 업체에서 네임서버 변경

**가비아 (Gabia) 예시:**
1. 가비아 로그인
2. "도메인 관리" → 도메인 선택
3. "네임서버 변경" 클릭
4. Cloudflare 네임서버 입력:
   ```
   ns1.cloudflare.com
   ns2.cloudflare.com
   ```
5. 저장

**후이즈 (Whois) 예시:**
1. 후이즈 로그인
2. "도메인 관리" → 도메인 선택
3. "네임서버 설정" 클릭
4. Cloudflare 네임서버 입력
5. 저장

**다른 업체:**
- 도메인 관리 페이지에서 "네임서버" 또는 "DNS" 설정 찾기
- Cloudflare 네임서버로 변경

#### 4-3. 네임서버 전파 대기
- **일반적으로**: 24-48시간 소요
- **실제로는**: 보통 1-2시간 내 완료
- **확인 방법**: [DNS Checker](https://dnschecker.org/)에서 확인

---

### 5단계: SSL/TLS 설정 (10분)

1. Cloudflare 대시보드 → **SSL/TLS** 메뉴
2. **Encryption mode** 선택:
   - ✅ **Full (strict)** 권장 (서버에 SSL 인증서 있는 경우)
   - 또는 **Full** (서버에 SSL 인증서 없는 경우)
3. **Always Use HTTPS** 활성화
4. **Automatic HTTPS Rewrites** 활성화

---

### 6단계: 보안 설정 확인 (5분)

1. Cloudflare 대시보드 → **Security** 메뉴
2. **Security Level**: Medium 또는 High 권장
3. **DDoS Protection**: 자동 활성화됨 ✅
4. **Bot Fight Mode**: Free 플랜에서 자동 활성화됨 ✅

---

### 7단계: 서버 설정 확인 (10분)

#### Nginx 설정 확인

**서버에서 실제 IP 확인:**
```bash
# 서버 접속 후
hostname -I
# 또는
ip addr show
```

**Nginx 설정 파일 확인:**
```bash
sudo nano /etc/nginx/sites-available/rohatax
```

**확인 사항:**
- 서버가 실제 IP로 요청을 받을 수 있는지
- Cloudflare IP 대역 허용 (선택사항, 일반적으로 불필요)

#### Cloudflare IP 대역 허용 (선택사항)

**Nginx 설정에 추가:**
```nginx
# Cloudflare IP 대역 (선택사항)
# 일반적으로 불필요하지만, 추가 보안을 원할 경우
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
set_real_ip_from 141.101.64.0/18;
set_real_ip_from 108.162.192.0/18;
set_real_ip_from 190.93.240.0/20;
set_real_ip_from 188.114.96.0/20;
set_real_ip_from 197.234.240.0/22;
set_real_ip_from 198.41.128.0/17;
set_real_ip_from 162.158.0.0/15;
set_real_ip_from 104.16.0.0/13;
set_real_ip_from 104.24.0.0/14;
set_real_ip_from 172.64.0.0/13;
set_real_ip_from 131.0.72.0/22;
real_ip_header CF-Connecting-IP;
```

**일반적으로는 불필요합니다.** Cloudflare가 자동으로 처리합니다.

---

## ✅ 설정 완료 확인

### 1. DNS 전파 확인

**온라인 도구 사용:**
- [DNS Checker](https://dnschecker.org/)
- 도메인 입력 후 Cloudflare 네임서버 확인

**터미널에서 확인:**
```bash
nslookup your-domain.com
# Cloudflare 네임서버가 반환되는지 확인
```

### 2. 웹사이트 접속 테스트

1. 브라우저에서 `https://your-domain.com` 접속
2. 정상적으로 접속되는지 확인
3. 주소창에 자물쇠 아이콘(🔒) 표시되는지 확인

### 3. Cloudflare 작동 확인

**방법 1: HTTP 헤더 확인**
```bash
curl -I https://your-domain.com
```

**응답에 다음 헤더가 있으면 Cloudflare 작동 중:**
```
cf-ray: xxxxxx-XXX
server: cloudflare
```

**방법 2: 온라인 도구 사용**
- [Cloudflare Test](https://www.cloudflare.com/cdn-cgi/trace)
- 접속하면 Cloudflare 정보 표시

---

## 🔒 DDoS 방어 자동 활성화

### Cloudflare가 자동으로 하는 일

1. **DDoS 공격 자동 차단** ✅
   - Layer 3/4 공격 차단
   - Layer 7 공격 차단
   - 자동으로 악의적인 트래픽 필터링

2. **Rate Limiting** ✅
   - Free 플랜: 기본 Rate Limiting
   - 자동으로 과도한 요청 차단

3. **Bot 관리** ✅
   - 악성 봇 자동 차단
   - 정상 봇은 허용

### 확인 방법

Cloudflare 대시보드 → **Security** → **Events**
- 차단된 공격 내역 확인 가능
- 실시간 보안 이벤트 모니터링

---

## 📊 설정 전후 비교

### 설정 전
```
[사용자] → [서버] (직접 접속)
- DDoS 공격 시 서버 다운 가능 ❌
- SSL 인증서 별도 설정 필요
```

### 설정 후
```
[사용자] → [Cloudflare] → [서버]
- DDoS 공격 자동 차단 ✅
- SSL 인증서 자동 제공 ✅
- CDN 기능 포함 ✅
- 기존 기능 100% 유지 ✅
```

---

## ⚠️ 주의사항

### 1. 네임서버 전파 시간
- **일반적으로**: 1-2시간
- **최대**: 48시간
- 전파 완료 전까지는 기존 DNS 사용

### 2. 기존 DNS 레코드
- Cloudflare로 마이그레이션 시 기존 DNS 레코드 확인 필수
- 누락된 레코드가 있으면 서비스 중단 가능

### 3. 이메일 서버 (선택사항)
- 이메일 서버를 별도로 운영하는 경우
- MX 레코드가 Cloudflare에 추가되어 있는지 확인

---

## 🆘 문제 해결

### 문제 1: 웹사이트 접속 안 됨

**원인:**
- 네임서버 전파 미완료
- DNS 레코드 설정 오류

**해결:**
1. DNS 전파 확인: [DNS Checker](https://dnschecker.org/)
2. Cloudflare DNS 레코드 확인
3. 서버 IP 주소 확인

### 문제 2: SSL 인증서 오류

**원인:**
- SSL/TLS 모드 설정 오류

**해결:**
1. Cloudflare → SSL/TLS → Encryption mode 확인
2. "Full" 또는 "Full (strict)" 선택
3. 서버에 SSL 인증서 있는지 확인

### 문제 3: 특정 기능 작동 안 함

**원인:**
- Cloudflare 캐싱 문제 (거의 없음)

**해결:**
1. Cloudflare → Caching → Purge Everything
2. 또는 해당 페이지를 "Bypass Cache"로 설정

---

## 📋 체크리스트

### Cloudflare 설정
- [ ] Cloudflare 가입 완료
- [ ] 도메인 추가 완료
- [ ] DNS 레코드 확인 완료
- [ ] Proxy 상태 확인 (🟠 Proxied)
- [ ] 네임서버 변경 완료
- [ ] SSL/TLS 설정 완료
- [ ] DNS 전파 확인 완료
- [ ] 웹사이트 접속 테스트 완료
- [ ] Cloudflare 작동 확인 완료

### 기능 테스트
- [ ] 로그인 기능 테스트
- [ ] 회원가입 기능 테스트
- [ ] 파일 업로드 테스트
- [ ] API 엔드포인트 테스트

---

## 🎯 완료!

### 설정 완료 후

1. **DDoS 방어 자동 활성화** ✅
2. **SSL 인증서 자동 제공** ✅
3. **기존 기능 100% 유지** ✅
4. **보안 강화 완료** ✅

### 다음 단계

1순위 작업 완료! 다음 작업으로 진행:
- 2순위: SECRET_KEY 설정 (10분)
- 3순위: 자동 백업 설정 (10분)
- 4순위: SSL 인증서 설정 (이미 Cloudflare에서 자동 제공) ✅

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

