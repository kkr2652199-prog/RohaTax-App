"""
스튜디오 페이지 접속 불가 원인 진단 스크립트
"""
import requests
import re

BASE_URL = "http://localhost:5001/studio"
print(f"1. 메인 페이지 접속 시도: {BASE_URL}")

try:
    # 1. HTML 요청
    res = requests.get(BASE_URL)
    print(f"   -> 상태 코드: {res.status_code}")
    
    if res.status_code != 200:
        print(f"   -> [CRITICAL] 페이지 로드 실패! 내용: {res.text[:200]}")
        exit()
        
    print("   -> [SUCCESS] HTML 수신 완료.")
    html_content = res.text
    
    # 2. HTML 내부의 JS 파일 경로 추출 (React 빌드 파일 찾기)
    # 보통 <script type="module" crossorigin src="/assets/index-....js"> 형태임
    # 외부 CDN 링크는 제외하고 로컬 assets 파일만 찾기
    # 여러 패턴 시도: /assets/..., /studio/assets/..., 상대 경로 등
    match = re.search(r'src="(/studio/assets/[^"]+\.js)"', html_content)
    if not match:
        match = re.search(r'src="(/assets/[^"]+\.js)"', html_content)
    if not match:
        match = re.search(r'src="(assets/[^"]+\.js)"', html_content)
    
    if match:
        js_path = match.group(1)
        print(f"2. 연결된 JS 파일 발견: {js_path}")
        
        # 만약 경로가 /assets/... 로 시작하면, 실제 요청은 /studio/assets/... 로 가야 함
        # Flask가 이걸 처리하는지 확인
        
        # 경로 보정 (절대 경로면 도메인 붙이고, 상대 경로면 /studio 붙임)
        if js_path.startswith("/"):
            # 주의: React가 /assets/... 라고 요청하면 Flask는 /studio/assets/... 로 받아야 할 수도 있음
            # 일단 있는 그대로 요청해봄
            js_url = f"http://localhost:5001{js_path}"
        else:
            js_url = f"http://localhost:5001/studio/{js_path}"
            
        print(f"3. JS 파일 다운로드 시도: {js_url}")
        js_res = requests.get(js_url)
        
        if js_res.status_code == 200:
            print("   -> [SUCCESS] JS 파일 로드 성공! (React 앱 구동 가능)")
        else:
            print(f"   -> [FAIL] JS 파일 로드 실패 ({js_res.status_code}). 이것 때문에 흰 화면이 뜨는 것임.")
            # 만약 실패했다면, /studio를 붙여서 재시도 해보라
            retry_url = f"http://localhost:5001/studio{js_path}" if js_path.startswith("/") else js_url
            print(f"   -> 재시도 경로: {retry_url}")
            retry_res = requests.get(retry_url)
            if retry_res.status_code == 200:
                print("   -> [INSIGHT] 아하! 경로 앞에 '/studio'가 빠져서 못 찾는 거였군요.")
            else:
                print("   -> [CRITICAL] 파일이 아예 없습니다.")
    else:
        print("   -> [WARNING] HTML 안에 JS 파일 링크를 못 찾겠습니다. 빈 껍데기일 수 있습니다.")
        print(f"   -> HTML 내용 일부: {html_content[:500]}")
    
    # 추가: CSS 파일도 확인
    css_match = re.search(r'href="([^"]+\.css)"', html_content)
    if css_match:
        css_path = css_match.group(1)
        print(f"\n4. CSS 파일 발견: {css_path}")
        if css_path.startswith("/"):
            css_url = f"http://localhost:5001{css_path}"
        else:
            css_url = f"http://localhost:5001/studio/{css_path}"
        css_res = requests.get(css_url)
        if css_res.status_code == 200:
            print("   -> [SUCCESS] CSS 파일 로드 성공!")
        else:
            print(f"   -> [FAIL] CSS 파일 로드 실패 ({css_res.status_code})")
            retry_css_url = f"http://localhost:5001/studio{css_path}" if css_path.startswith("/") else css_url
            retry_css_res = requests.get(retry_css_url)
            if retry_css_res.status_code == 200:
                print("   -> [INSIGHT] CSS 경로도 '/studio'가 필요합니다.")

except requests.exceptions.ConnectionError:
    print(f"   -> [ERROR] 서버 접속 불가: 서버가 실행 중이지 않거나 포트 5001이 닫혀있습니다.")
except Exception as e:
    print(f"   -> [ERROR] 예상치 못한 오류: {e}")

