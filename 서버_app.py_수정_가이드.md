# 서버에서 app.py 수정하기

## 방법 1: nano 에디터로 직접 수정 (가장 간단)

서버 터미널에서 다음 명령어를 실행하세요:

### 1단계: app.py 파일 열기
```bash
nano app.py
```

### 2단계: 파일 끝부분 찾기
- `Ctrl + W` (검색)
- `if __name__ == "__main__":` 입력하고 Enter
- 파일 끝부분으로 이동

### 3단계: 수정할 부분 찾기
아래 두 줄을 찾으세요 (838-839줄 근처):
```python
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", settings.PORT))
```

### 4단계: 수정하기
다음과 같이 변경하세요:
```python
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
```

**변경 사항:**
- `"127.0.0.1"` → `"0.0.0.0"` (외부 접근 허용)
- `settings.PORT` → `5000` (포트 5000으로 고정)

### 5단계: 저장하고 나가기
- `Ctrl + O` (저장)
- Enter (확인)
- `Ctrl + X` (나가기)

---

## 방법 2: sed 명령어로 자동 수정 (빠른 방법)

서버 터미널에서 다음 명령어를 복사해서 실행하세요:

```bash
sed -i 's/host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")/host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")/g' app.py
sed -i 's/port = int(os.environ.get("FLASK_RUN_PORT", settings.PORT))/port = int(os.environ.get("FLASK_RUN_PORT", 5000))/g' app.py
```

---

## 방법 3: Python 스크립트로 수정

서버에서 다음 명령어를 실행하세요:

```bash
python3 << 'EOF'
import re

# 파일 읽기
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 수정
content = content.replace(
    'host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")',
    'host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")'
)
content = content.replace(
    'port = int(os.environ.get("FLASK_RUN_PORT", settings.PORT))',
    'port = int(os.environ.get("FLASK_RUN_PORT", 5000))'
)

# 파일 저장
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ app.py 수정 완료!")
EOF
```

---

## 수정 확인

수정이 제대로 되었는지 확인하세요:

```bash
tail -5 app.py
```

다음과 같이 나와야 합니다:
```python
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    app.run(host=host, port=port, debug=settings.DEBUG)
```

---

## 서버 재시작

수정 후 서버를 재시작하세요:

```bash
# 기존 프로세스 종료
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# 서버 시작
FLASK_RUN_HOST=0.0.0.0 FLASK_RUN_PORT=5000 nohup python3 app.py > app.log 2>&1 &

# 로그 확인
sleep 3 && tail -10 app.log
```

