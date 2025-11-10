import os
import json
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(__file__))
E2E_JSON = os.path.join(BASE, 'tests', 'e2e_result.json')
REPORT_HTML = os.path.join(BASE, 'tests', 'report.html')


def render_html(data: dict) -> str:
    files = data.get('files', [])
    preview = data.get('recipients_preview', [])
    log = data.get('conversion_log', [])
    summary = data.get('extraction_summary', {})
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def esc(s: str) -> str:
        return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    preview_rows = ''
    for i, rec in enumerate(preview, 1):
        biz = esc(str(rec.get('사업자등록번호', rec.get('business_number', ''))))
        name = esc(str(rec.get('상호', rec.get('buyer_name', ''))))
        rep = esc(str(rec.get('대표명', rec.get('representative', ''))))
        addr = esc(str(rec.get('사업장주소', rec.get('address', ''))))
        email = esc(str(rec.get('사업자이메일', rec.get('email', ''))))
        supply = esc(str(rec.get('공급가액', '')))
        vat = esc(str(rec.get('부가세', '')))
        total = esc(str(rec.get('요금합계', '')))
        preview_rows += f'<tr><td>{i}</td><td>{biz}</td><td>{name}</td><td>{rep}</td><td>{addr}</td><td>{email}</td><td>{supply}</td><td>{vat}</td><td>{total}</td></tr>'

    file_list = ''.join(f'<li>{esc(p)}</li>' for p in files)
    log_list = ''.join(f'<li>{esc(line)}</li>' for line in log)

    html = f"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>변환 단계 리포트</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Noto Sans KR, Arial; margin: 24px; }}
    h1 {{ margin-bottom: 8px; }}
    h2 {{ margin-top: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 13px; }}
    th {{ background: #f3f4f6; text-align: left; }}
    code {{ background: #f6f8fa; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>변환 단계 리포트</h1>
  <div>생성 시각: {ts}</div>

  <h2>요약</h2>
  <ul>
    <li>총 추출 건수: <b>{summary.get('total_count', 0)}</b></li>
    <li>추출률: <b>{summary.get('extraction_rate', 0)}</b></li>
    <li>산출 파일 수: <b>{len(files)}</b></li>
  </ul>

  <h2>산출 파일</h2>
  <ul>
    {file_list}
  </ul>

  <h2>변환 로그</h2>
  <ol>
    {log_list}
  </ol>

  <h2>공급받는자 미리보기(상위 5건)</h2>
  <table>
    <thead>
      <tr>
        <th>#</th><th>사업자등록번호</th><th>상호</th><th>대표명</th><th>주소</th><th>이메일</th><th>공급가액</th><th>부가세</th><th>요금합계</th>
      </tr>
    </thead>
    <tbody>
      {preview_rows}
    </tbody>
  </table>
</body>
</html>
"""
    return html


def main():
    if not os.path.exists(E2E_JSON):
        raise SystemExit(f"not found: {E2E_JSON}")
    # Handle potential UTF-8 BOM from Windows redirection
    with open(E2E_JSON, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    html = render_html(data)
    with open(REPORT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(REPORT_HTML)


if __name__ == '__main__':
    main()
