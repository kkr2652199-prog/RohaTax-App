export async function initVipNotice({ mountSelector, forceParam = 'vip' } = {}){
  try{
    const mount = document.querySelector(mountSelector || '.panel .bd');
    if (!mount) return;
    const forceVip = new URLSearchParams(location.search).get(forceParam) === '1';
    if (!forceVip && sessionStorage.getItem('vipNoticeSeen') === '1') return;

    const res = await fetch('/api/user-info', { method:'GET', credentials:'same-origin', headers:{ 'Content-Type':'application/json' } });
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;
    const user = data.data && data.data.user;
    if (!forceVip && (!user || (user.plan_type||'').toLowerCase() !== 'vip')) return;

    // 이미 삽입되어 있으면 재사용
    const backdrop = document.getElementById('vip-backdrop');
    let el = document.getElementById('vip-notice');
    if (!el){
      // 서버 템플릿에 partial이 포함되어 있다고 가정 (templates/partials/vip_notice.html)
      // 만약 포함이 안되었다면, 최소 구조를 동적으로 생성
      el = document.createElement('div');
      el.id = 'vip-notice';
      el.className = 'vip-notice';
      el.style.display = 'none';
      el.innerHTML = `
        <div class="vip-head">✨ 파일 검증 및 자동 정제 완료!</div>
        <div class="vip-body">쉼표(,), 하이픈(-) 등 모든 불필요한 기호는 시스템이 자동으로 제거되고 변환을 준비합니다.</div>
        <div class="vip-guide">이 파일은 VIP 사용자님의 고객님 정보입니다. 아래 7가지 ‘제목(열 이름)’을 확인해 주세요.</div>
        <ol class="vip-list">
          <li>상호</li>
          <li>사업자등록번호(10자리, 하이픈 허용)</li>
          <li>대표자명</li>
          <li>사업장주소</li>
          <li>이메일</li>
          <li>공급가액(숫자)</li>
          <li>부가세(숫자)</li>
        </ol>
        <button id="vipNoticeConfirm" type="button" class="vip-btn">VIP 고객님, 변환 전 꼭 확인!</button>
      `;
      mount.appendChild(el);
    }
    function show(){
      try{ console.log('[vip] show'); }catch(_){}
      if (backdrop) backdrop.style.display = 'block';
      el.style.display = 'block';
      document.addEventListener('keydown', onEsc, { once: true });
    }
    function hide(){
      try{ console.log('[vip] hide'); }catch(_){}
      try{ el.style.display = 'none'; }catch(_){}
      try{ backdrop && (backdrop.style.display = 'none'); }catch(_){}
      if (!forceVip) sessionStorage.setItem('vipNoticeSeen','1');
    }
    function onEsc(e){ if (e.key === 'Escape') hide(); }
    show();
    // 팝업 자체 클릭으로는 닫히지 않도록 하고, 배경(백드롭) 클릭으로만 닫힘
    if (backdrop){ backdrop.onclick = hide; }
    const btn = el.querySelector('#vipNoticeConfirm');
    const xbtn = el.querySelector('#vipNoticeClose');
    if (btn){ btn.addEventListener('click', function(){ hide(); }); }
    if (xbtn){ xbtn.addEventListener('click', hide); }

    // 외부에서 토글할 수 있도록 전역 API 노출
    try{
      window.vipNotice = {
        show,
        hide,
        toggle: ()=> (el.style.display === 'none' ? show() : hide()),
        isOpen: ()=> {
          const n = document.getElementById('vip-notice');
          return !!(n && n.style.display !== 'none');
        }
      };
    }catch(_){ }
  }catch(e){
    console.warn('VIP Notice init failed', e);
  }
}



// 업로드된 헤더 배열을 받아 템플릿 7컬럼 비교(✓/?/✗)를 갱신한다
// headers: string[]
export function updateVipHeaderComparison(headers){
  if (!Array.isArray(headers)) return;

  const strong = [
    { key:'reg_no', patterns:[/사업자등록번호|사업자번호|등록번호/i] },
    { key:'store_name', patterns:[/가맹점명|상호|회사명/i] },
    { key:'ceo', patterns:[/대표자명|대표자|성명/i] },
    { key:'address', patterns:[/사업장주소|주소/i] },
    { key:'email', patterns:[/이메일1|이메일\s*1|email/i] },
    { key:'supply_total', patterns:[/공급가액\s*합계|총합계|공급가액/i] },
    { key:'tax_total', patterns:[/세액\s*합계|부가세|세액/i] }
  ];

  const weak = [
    { key:'reg_no', patterns:[/번호|등록/i] },
    { key:'store_name', patterns:[/상호|가맹점|점명/i] },
    { key:'ceo', patterns:[/대표|성명|이름/i] },
    { key:'address', patterns:[/주소/i] },
    { key:'email', patterns:[/이메일|mail/i] },
    { key:'supply_total', patterns:[/공급가액|합계|총합/i] },
    { key:'tax_total', patterns:[/세액|부가세|vat/i] }
  ];

  const getStatus = (key)=>{
    const values = headers.map(h => (typeof h === 'string' ? h.trim() : '')).filter(Boolean);
    const s = strong.find(x=>x.key===key);
    const w = weak.find(x=>x.key===key);
    if (s && values.some(v => s.patterns.some(p=>p.test(v)))) return '✓';
    if (w && values.some(v => w.patterns.some(p=>p.test(v)))) return '?';
    return '✗';
  };

  ['reg_no','store_name','ceo','address','email','supply_total','tax_total'].forEach(key => {
    const cell = document.querySelector('.vip-compare-cell[data-col="' + key + '"]');
    if (!cell) return;
    const status = getStatus(key);
    cell.textContent = status;
    cell.style.fontWeight = '700';
    cell.style.color = (status==='✓') ? '#059669' : (status==='?') ? '#d97706' : '#dc2626';
    // 애니메이션 트리거
    cell.classList.remove('is-updated');
    void cell.offsetWidth;
    cell.classList.add('is-updated');
  });
}

// 예시 금액 정제 데모 (한 번만)
export function runOnceAmountCleanDemo(){
  const targets = document.querySelectorAll('.vip-example-cell.clean-demo');
  if (!targets.length) return;
  setTimeout(()=>{
    targets.forEach(el=>{
      const raw = String(el.textContent||'');
      const numeric = raw.replace(/[₩원,\s]/g,'');
      el.textContent = numeric;
    });
  }, 1200);
}
try{ runOnceAmountCleanDemo(); }catch(_){}


// =============================
// 컬럼 헤더 드롭다운 제어 함수
// (HTML onclick에서 직접 호출)
// =============================

function toggleHeaderDropdown(columnKey) {
  console.log("Dropdown Toggled:", columnKey);
  // 모든 드롭다운 닫기
  const allDropdowns = document.querySelectorAll('.header-dropdown');
  allDropdowns.forEach(dropdown => {
    dropdown.style.display = 'none';
  });

  // 클릭한 컬럼의 드롭다운 토글
  const targetDropdown = document.getElementById(`dropdown-${columnKey}`);
  if (targetDropdown) {
    const isVisible = targetDropdown.style.display === 'block';
    targetDropdown.style.display = isVisible ? 'none' : 'block';
  }
}

function selectHeaderItem(columnKey, headerText) {
  const titleElement = document.querySelector(`[data-col="${columnKey}"]`);
  if (titleElement) {
    titleElement.textContent = headerText;
  }

  // 드롭다운 닫기
  const dropdown = document.getElementById(`dropdown-${columnKey}`);
  if (dropdown) {
    dropdown.style.display = 'none';
  }
}

function closeDropdown(columnKey, event) {
  if (event) {
    event.stopPropagation();
  }
  const dropdown = document.getElementById(`dropdown-${columnKey}`);
  if (dropdown) {
    dropdown.style.display = 'none';
  }
}

// 드롭다운 외부 클릭 시 닫기
document.addEventListener('click', function(e) {
  if (!e.target.closest('.vip-excel-col')) {
    const allDropdowns = document.querySelectorAll('.header-dropdown');
    allDropdowns.forEach(dropdown => {
      dropdown.style.display = 'none';
    });
  }
});

// [Emergency Export] HTML onclick이 찾을 수 있도록 전역 노출
if (typeof window !== 'undefined') {
  window.toggleHeaderDropdown = toggleHeaderDropdown;
  window.selectHeaderItem = selectHeaderItem;
  window.closeDropdown = closeDropdown;
}

