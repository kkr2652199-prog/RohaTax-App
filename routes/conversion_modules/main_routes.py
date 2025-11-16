"""
메인 변환 라우트 모듈
기본 변환 페이지 및 공통 기능
"""

from flask import Blueprint, render_template, session, redirect, url_for, request
import os
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.utils import row_value

main_bp = Blueprint('main', __name__)


@main_bp.route('/conversion')
def conversion():
    """변환 메인 페이지"""
    # 로그인 확인
    print(f"🔍 변환 페이지 접근 - 세션 user_id: {session.get('user_id')}")
    if not session.get('user_id'):
        print("❌ 세션에 user_id가 없음 - VIP 회원가입 페이지로 리다이렉트")
        return redirect(url_for('registration.register'))
    
    # 토큰 잔액 확인 (지급된 토큰 - 사용한 토큰)
    with get_conn() as conn:
        user = conn.execute(
            "SELECT token_balance, COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?", 
            (session['user_id'],)
        ).fetchone()
        
        if not user:
            print(f"❌ 사용자 ID {session['user_id']}를 찾을 수 없음 - 로그인 페이지로 리다이렉트")
            return redirect(url_for('auth.login'))
        
        # 사용 가능한 토큰 = 지급된 토큰 - 사용한 토큰
        available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
        print(f"✅ 사용자 인증 성공 - 사용 가능한 토큰: {available_tokens}")
        
        return render_template('conversion.html', 
                             available_tokens=available_tokens,
                             total_tokens=user['token_balance'] or 0,
                             used_tokens=user['tokens_used'] or 0)


@main_bp.route('/conversion/admin-token')
def admin_token_dashboard():
    """관리자 토큰 대시보드 (간단 HTML + JS)"""
    # 로그인 + 관리자 확인(리디렉트)
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    if not session.get('is_admin'):
        return redirect(url_for('main.conversion'))

    # 이전 상태로: 게이트 제거 (관리자 로그인만 확인)
    if False:
        gate_html = """
<!DOCTYPE html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\" />
  <title>비밀방 입장</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:40px;background:#f7f9fc}
    .card{max-width:420px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px;box-shadow:0 6px 18px rgba(0,0,0,.06)}
    h1{font-size:18px;margin:0 0 12px}
    label{display:block;font-size:12px;color:#555;margin-bottom:6px}
    input{width:100%;padding:10px;border:1px solid #d1d5db;border-radius:8px;font-size:14px}
    button{margin-top:10px;width:100%;padding:10px;background:#2c7be5;border:0;color:#fff;border-radius:8px;font-weight:700;cursor:pointer}
    .muted{color:#6b7280;font-size:12px;margin-top:8px}
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>관리자 비밀방 입장</h1>
    <form method=\"post\" action=\"/conversion/admin-token/enter\"> 
      <label>접근 코드</label>
      <input name=\"code\" type=\"password\" placeholder=\"코드를 입력하세요\" required />
      <button type=\"submit\">입장</button>
      <div class=\"muted\">관리자만 접근 가능합니다.</div>
    </form>
  </div>
</body>
</html>
        """
        return gate_html

    # 간단한 inline 템플릿 렌더 (JS가 관리자 API 호출)
    html = """
<!DOCTYPE html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\" />
  <title>관리자 토큰 대시보드</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 20px; }
    h1 { font-size: 20px; margin: 0 0 16px; }
    .toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
    .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #ddd; padding: 6px 8px; font-size: 12px; }
    th { background: #f5f5f5; text-align: left; }
    .card { border: 1px solid #ddd; padding: 8px; }
    .muted { color: #666; font-size: 12px; }
  </style>
  <script>
    async function fetchJSON(url) {
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    }

    function renderLogs(logs) {
      const tbody = document.getElementById('logs-body');
      tbody.innerHTML = '';
      for (const r of logs) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${r.created_at || ''}</td>
          <td>${r.user_id || ''}</td>
          <td>${r.username || ''}</td>
          <td>${r.action || ''}</td>
          <td>${r.tokens || 0}</td>
          <td>${r.balance_before ?? ''}</td>
          <td>${r.balance_after ?? ''}</td>
        `;
        tbody.appendChild(tr);
      }
    }

    function renderSummary(byDay, byUser) {
      const dayEl = document.getElementById('summary-day');
      const userEl = document.getElementById('summary-user');
      dayEl.innerHTML = '';
      userEl.innerHTML = '';
      for (const [k, v] of Object.entries(byDay || {})) {
        const li = document.createElement('div');
        li.textContent = `${k} :: tokens=${v.tokens}, success=${v.success}, fail=${v.fail}, events=${v.events}`;
        dayEl.appendChild(li);
      }
      for (const [k, v] of Object.entries(byUser || {})) {
        const li = document.createElement('div');
        li.textContent = `user ${k} :: tokens=${v.tokens}, success=${v.success}, fail=${v.fail}, events=${v.events}`;
        userEl.appendChild(li);
      }
    }

    async function loadAll() {
      const date = document.getElementById('date').value.trim();
      const q = date ? ('?date=' + encodeURIComponent(date)) : '';
      try {
        const logsRes = await fetchJSON('/api/admin/token-logs' + q);
        renderLogs(logsRes.data.logs || []);
      } catch (e) {
        console.error(e);
      }
      try {
        const sumRes = await fetchJSON('/api/admin/token-usage-summary');
        renderSummary(sumRes.data.by_day, sumRes.data.by_user);
      } catch (e) {
        console.error(e);
      }
    }
    function onSearch() { loadAll(); }
    function onAuto() {
      const cb = document.getElementById('auto');
      if (cb.checked) {
        window.__autoTimer = setInterval(loadAll, 5000);
      } else if (window.__autoTimer) {
        clearInterval(window.__autoTimer);
        window.__autoTimer = null;
      }
    }
    window.addEventListener('DOMContentLoaded', loadAll);
  </script>
</head>
<body>
  <h1>관리자 토큰 대시보드</h1>
  <div class="toolbar">
    <input id="date" type="date" />
    <button onclick="onSearch()">조회</button>
    <label class="muted"><input id="auto" type="checkbox" onchange="onAuto()" /> 자동 새로고침(5초)</label>
  </div>
  <div class="grid">
    <div class="card">
      <div class="muted">토큰 로그</div>
      <table>
        <thead>
          <tr>
            <th>시간</th><th>유저ID</th><th>유저명</th><th>액션</th><th>토큰</th><th>잔액 전</th><th>잔액 후</th>
          </tr>
        </thead>
        <tbody id="logs-body"></tbody>
      </table>
    </div>
    <div class="card">
      <div class="muted">요약</div>
      <div id="summary-day"></div>
      <hr />
      <div id="summary-user"></div>
    </div>
  </div>
  <p class="muted">데이터 소스: /api/admin/token-logs, /api/admin/token-usage-summary</p>
</body>
</html>
    """
    return html


@main_bp.route('/conversion/admin-token/enter', methods=['POST'])
def admin_token_enter():
    # 더 이상 사용하지 않음 (호환을 위해 리디렉션)
    return redirect(url_for('main.admin_token_dashboard'))
