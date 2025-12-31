# 🔧 도메인 및 DNS 설정 문제 해결 가이드

> **도메인**: rohatax.com  
> **서버**: AWS Lightsail  
> **DNS**: Cloudflare  
> **도메인 등록**: Gabia

---

## 🔍 문제 진단 체크리스트

### 1단계: AWS Lightsail 확인

#### ✅ 확인 사항
- [ ] **고정 IP (Static IP) 할당 여부**
  - Lightsail 인스턴스에 고정 IP가 할당되어 있는지 확인
  - 고정 IP 없으면 인스턴스 재시작 시 IP 변경됨

#### 🔧 해결 방법

**1. 고정 IP 할당 (필수)**
```
1. AWS Lightsail 콘솔 접속
2. 인스턴스 선택
3. "Networking" 탭 클릭
4. "Create static IP" 클릭
5. 이름 입력 후 생성
6. "Attach" 클릭하여 인스턴스에 연결
```

**2. 고정 IP 확인**
- Lightsail 대시보드에서 인스턴스 선택
- "Networking" 탭에서 고정 IP 주소 확인
- 예: `54.123.45.67` (이 IP를 Cloudflare에 등록)

---

### 2단계: Cloudflare DNS 설정 확인

#### ✅ 확인 사항
- [ ] **A 레코드 존재 여부**
- [ ] **Proxy 상태 확인** (🟠 Proxied 여부)
- [ ] **IP 주소가 올바른지 확인**

#### 🔧 Cloudflare DNS 설정 방법

**1. Cloudflare 대시보드 접속**
- https://dash.cloudflare.com 접속
- rohatax.com 도메인 선택

**2. DNS 레코드 확인/추가**

**필수 A 레코드:**
```
Type: A
Name: @ (또는 rohatax.com)
Content: [AWS Lightsail 고정 IP 주소]
Proxy: 🟠 Proxied (주황색 구름) ← 반드시!
TTL: Auto
```

**www 서브도메인 (선택사항):**
```
Type: CNAME
Name: www
Content: rohatax.com
Proxy: 🟠 Proxied (주황색 구름)
TTL: Auto
```

**⚠️ 중요: Proxy 상태 확인**
- 🟠 **Proxied (주황색 구름)**: Cloudflare를 통과 → DDoS 방어 활성화 ✅
- ⚪ **DNS only (회색 구름)**: Cloudflare를 통과하지 않음 → 방어 비활성화 ❌

**3. DNS 레코드 저장**
- "Save" 클릭
- 변경사항 저장 확인

---

### 3단계: Gabia 네임서버 변경 확인

#### ✅ 확인 사항
- [ ] **네임서버가 Cloudflare로 변경되었는지**

#### 🔧 Gabia 네임서버 변경 방법

**1. Gabia 로그인**
- https://domain.gabia.com 접속
- 로그인

**2. 도메인 관리 페이지 접속**
- "도메인 관리" → "내 도메인" 클릭
- rohatax.com 선택

**3. 네임서버 변경**
- "네임서버 설정" 또는 "DNS 관리" 메뉴 찾기
- "네임서버 변경" 클릭

**4. Cloudflare 네임서버 입력**

Cloudflare 대시보드에서 네임서버 확인:
```
ns1.cloudflare.com
ns2.cloudflare.com
```

또는 Cloudflare가 제공하는 고유 네임서버:
```
[계정별로 다를 수 있음]
예시:
alex.ns.cloudflare.com
lola.ns.cloudflare.com
```

**5. 저장 및 확인**
- 네임서버 입력 후 저장
- 변경 완료 확인

---

### 4단계: DNS 전파 확인

#### 🔍 전파 상태 확인 방법

**1. 온라인 도구 사용 (권장)**
- [DNS Checker](https://dnschecker.org/)
- 도메인 입력: `rohatax.com`
- "A" 레코드 선택
- 전 세계 DNS 서버에서 확인

**2. 터미널에서 확인**
```bash
# Windows PowerShell
nslookup rohatax.com

# 또는
nslookup rohatax.com 8.8.8.8
```

**3. Cloudflare 네임서버 확인**
```bash
nslookup -type=NS rohatax.com
```

**예상 결과:**
```
rohatax.com nameserver = ns1.cloudflare.com
rohatax.com nameserver = ns2.cloudflare.com
```

**⚠️ 전파 시간**
- **일반적으로**: 1-2시간
- **최대**: 24-48시간
- 전파 완료 전까지는 기존 DNS 사용

---

## 🚨 일반적인 문제 및 해결 방법

### 문제 1: 웹사이트 접속 안 됨 (404 또는 연결 오류)

**원인:**
1. DNS 전파 미완료
2. A 레코드 IP 주소 오류
3. 서버가 실행 중이 아님

**해결:**
1. **DNS 전파 확인**
   - [DNS Checker](https://dnschecker.org/)에서 확인
   - 전파 완료 대기 (1-2시간)

2. **A 레코드 IP 확인**
   - Cloudflare DNS에서 A 레코드의 IP가 Lightsail 고정 IP와 일치하는지 확인
   - 불일치 시 수정

3. **서버 상태 확인**
   - AWS Lightsail에서 인스턴스가 "Running" 상태인지 확인
   - 애플리케이션이 실행 중인지 확인

---

### 문제 2: "이 사이트에 연결할 수 없음" 오류

**원인:**
1. 서버 방화벽 설정 문제
2. Lightsail 네트워크 설정 문제
3. 애플리케이션이 포트 80/443에서 리스닝하지 않음

**해결:**

**1. Lightsail 방화벽 확인**
```
1. Lightsail 인스턴스 선택
2. "Networking" 탭
3. "Firewall" 섹션 확인
4. 다음 포트 허용 확인:
   - HTTP (80)
   - HTTPS (443)
   - SSH (22) - 관리용
```

**2. 서버 방화벽 확인 (Ubuntu 예시)**
```bash
# UFW 상태 확인
sudo ufw status

# 포트 허용 (필요시)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
```

**3. 애플리케이션 실행 확인**
```bash
# 서버 접속 후
ps aux | grep python
# 또는
ps aux | grep gunicorn

# 포트 리스닝 확인
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

---

### 문제 3: SSL 인증서 오류

**원인:**
1. Cloudflare SSL/TLS 모드 설정 오류
2. 서버에 SSL 인증서 없음

**해결:**

**1. Cloudflare SSL/TLS 설정**
```
1. Cloudflare 대시보드 → SSL/TLS
2. Encryption mode 선택:
   - "Full" (서버에 SSL 없을 때)
   - "Full (strict)" (서버에 SSL 있을 때)
3. "Always Use HTTPS" 활성화
```

**2. 서버 SSL 설정 (선택사항)**
- Cloudflare를 사용하면 서버 SSL 불필요
- "Full" 모드 사용 시 자동 처리

---

### 문제 4: DNS 레코드가 보이지 않음

**원인:**
1. Cloudflare에 도메인이 제대로 추가되지 않음
2. 네임서버가 Cloudflare로 변경되지 않음

**해결:**

**1. Cloudflare 도메인 추가 확인**
```
1. Cloudflare 대시보드 접속
2. "Add a Site" 클릭
3. rohatax.com 입력
4. Free 플랜 선택
5. DNS 레코드 스캔 확인
```

**2. 네임서버 변경 확인**
- Gabia에서 네임서버가 Cloudflare로 변경되었는지 확인
- 변경되지 않았다면 위의 "3단계" 참고

---

## 📋 단계별 설정 체크리스트

### AWS Lightsail
- [ ] 인스턴스 생성 완료
- [ ] 고정 IP (Static IP) 할당 완료
- [ ] 고정 IP 주소 확인 (예: 54.123.45.67)
- [ ] 방화벽 설정 완료 (80, 443 포트 허용)
- [ ] 애플리케이션 실행 중

### Cloudflare
- [ ] Cloudflare 가입 완료
- [ ] rohatax.com 도메인 추가 완료
- [ ] A 레코드 추가 완료 (Lightsail 고정 IP)
- [ ] Proxy 상태 확인 (🟠 Proxied)
- [ ] SSL/TLS 설정 완료 (Full 또는 Full strict)
- [ ] 네임서버 정보 확인

### Gabia
- [ ] Gabia 로그인 완료
- [ ] rohatax.com 도메인 선택
- [ ] 네임서버 변경 완료 (Cloudflare 네임서버로)
- [ ] 변경 사항 저장 완료

### 확인
- [ ] DNS 전파 확인 (DNS Checker 사용)
- [ ] 웹사이트 접속 테스트 (https://rohatax.com)
- [ ] SSL 인증서 정상 작동 확인
- [ ] Cloudflare 작동 확인 (HTTP 헤더 확인)

---

## 🔍 문제 진단 명령어

### 서버에서 확인

**1. 서버 IP 확인**
```bash
hostname -I
# 또는
ip addr show
```

**2. 포트 리스닝 확인**
```bash
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

**3. 애플리케이션 실행 확인**
```bash
ps aux | grep python
ps aux | grep gunicorn
```

**4. 로그 확인**
```bash
# 애플리케이션 로그
tail -f /var/www/rohatax/logs/app_$(date +%Y-%m-%d).log

# Nginx 로그 (사용 시)
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### 로컬에서 확인

**1. DNS 확인**
```powershell
# Windows PowerShell
nslookup rohatax.com
nslookup rohatax.com 8.8.8.8
```

**2. HTTP 헤더 확인**
```powershell
# Cloudflare 작동 확인
curl -I https://rohatax.com

# 응답에 다음이 있으면 Cloudflare 작동 중:
# cf-ray: xxxxxx-XXX
# server: cloudflare
```

**3. 온라인 도구 사용**
- [DNS Checker](https://dnschecker.org/) - DNS 전파 확인
- [SSL Labs](https://www.ssllabs.com/ssltest/) - SSL 인증서 확인
- [Cloudflare Test](https://www.cloudflare.com/cdn-cgi/trace) - Cloudflare 작동 확인

---

## 🎯 빠른 해결 가이드

### 즉시 확인할 3가지

1. **AWS Lightsail 고정 IP 할당 여부**
   - 고정 IP 없으면 할당 (필수!)

2. **Cloudflare A 레코드 IP 주소**
   - Lightsail 고정 IP와 일치하는지 확인

3. **Gabia 네임서버 변경**
   - Cloudflare 네임서버로 변경되었는지 확인

---

## 📞 추가 도움말

### AWS Lightsail 문서
- [Lightsail 고정 IP 설정](https://lightsail.aws.amazon.com/ls/docs/en_us/articles/understanding-static-ip-addresses-in-amazon-lightsail)

### Cloudflare 문서
- [Cloudflare DNS 설정](https://developers.cloudflare.com/dns/manage-dns-records/)
- [Cloudflare 네임서버 변경](https://developers.cloudflare.com/dns/zone-setups/full-setup/)

### Gabia 도메인 관리
- [Gabia 도메인 관리 가이드](https://help.gabia.com/domain)

---

**작성일**: 2025-12-26  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1




