# Python 패키지 업데이트 확인 가이드

## 📋 개요
이 가이드는 homepage1 워크트리에서 사용 중인 Python 패키지들의 버전을 확인하고 업데이트하는 방법을 안내합니다.

## 🛠️ 확인 방법

### 방법 1: 배치 파일 실행 (가장 간단)
```bash
check_package_updates.bat
```
이 배치 파일을 실행하면:
- Python 버전 확인
- pip 버전 확인
- 주요 패키지 버전 확인
- 업데이트 가능한 패키지 목록 표시

### 방법 2: Python 스크립트 실행
```bash
python check_updates_simple.py
```
또는
```bash
C:\ProgramData\anaconda3\envs\python314\python.exe check_updates_simple.py
```

### 방법 3: 직접 명령어 실행

#### 현재 설치된 패키지 목록 확인
```bash
python -m pip list
```

#### 업데이트 가능한 패키지 확인
```bash
python -m pip list --outdated
```

#### 특정 패키지 버전 확인
```bash
python -m pip show <패키지명>
```

## 📦 현재 requirements.txt 패키지 목록

### Flask Core
- Flask==3.1.2
- Werkzeug==3.1.3
- Jinja2==3.1.6
- MarkupSafe==3.0.3
- itsdangerous==2.2.0
- click==8.3.0
- blinker==1.9.0

### Database
- sqlalchemy==2.0.23

### Excel Processing
- pandas==2.3.3
- openpyxl==3.1.5
- xlrd==2.0.1

### HTTP & Network
- requests==2.32.5

### System & Utilities
- psutil==7.1.1
- python-dotenv==1.0.0
- APScheduler==3.10.4
- bcrypt==4.3.0
- Flask-Limiter==3.5.0
- gunicorn==21.2.0

## 🔄 업데이트 방법

### 개별 패키지 업데이트
```bash
python -m pip install --upgrade <패키지명>
```

### requirements.txt 기반 업데이트
```bash
python -m pip install --upgrade -r requirements.txt
```

### pip 자체 업데이트
```bash
python -m pip install --upgrade pip
```

## ⚠️ 주의사항

1. **프로덕션 환경**: 업데이트 전에 반드시 테스트 환경에서 먼저 확인하세요.
2. **버전 호환성**: 일부 패키지는 특정 버전에 의존할 수 있으므로, 업데이트 후 호환성을 확인하세요.
3. **백업**: 중요한 프로젝트의 경우 업데이트 전에 가상 환경을 백업하세요.
4. **Python 3.14**: 현재 프로젝트는 Python 3.14 전용입니다.

## 🔍 최신 버전 확인 사이트

- **PyPI (Python Package Index)**: https://pypi.org/
- **Python 공식 사이트**: https://www.python.org/downloads/
- **패키지별 문서**: 각 패키지의 공식 GitHub 또는 문서 사이트

## 📝 업데이트 체크리스트

- [ ] 현재 버전 확인 (`pip list`)
- [ ] 업데이트 가능한 패키지 확인 (`pip list --outdated`)
- [ ] 테스트 환경에서 업데이트 테스트
- [ ] requirements.txt 업데이트 (필요시)
- [ ] 프로덕션 배포 전 최종 테스트

## 🚀 빠른 업데이트 명령어

모든 패키지를 최신 버전으로 업데이트하려면:
```bash
python -m pip install --upgrade Flask Werkzeug Jinja2 MarkupSafe itsdangerous click blinker sqlalchemy pandas openpyxl xlrd requests psutil python-dotenv APScheduler bcrypt Flask-Limiter gunicorn
```

---

**마지막 업데이트 확인**: `check_package_updates.bat` 실행 시 자동으로 확인됩니다.

