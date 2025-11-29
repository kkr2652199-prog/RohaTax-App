/**
 * Admin Dashboard 사용자 관리 모듈
 *
 * 이 파일은 admin.html에서 분리된 사용자 관리 관련 함수들을 포함합니다.
 * - 사용자 목록 로드 및 렌더링
 * - 사용자별 변환 이력 조회
 * - 토큰 지급/초기화
 * - 사용자 승인/삭제/복구/완전삭제
 * - 사용자 플랜 변경
 */

// 전역 csrfToken 함수가 없다면 안전하게 정의
if (typeof csrfToken !== 'function') {
    window.csrfToken = function() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    };
}

/**
 * 사용자 목록 로드
 * API를 통해 사용자 목록을 가져와 renderUsers() 함수로 렌더링합니다.
 */
async function loadUsers(){
    try{
        const res = await fetch('/admin/api/users', {
            headers: {
                'X-CSRF-Token': csrfToken()
            },
        });
        const body = await res.json();
        renderUsers(body?.data?.users || []);
    }catch(err){
        console.error('사용자 목록 로드 실패:', err);
        document.getElementById('usersTable').innerHTML = '<p class="muted">사용자 목록 로드 실패</p>';
    }
}

/**
 * 사용자 목록 렌더링
 * 사용자 데이터를 받아 아코디언 형태의 UI로 렌더링하고, 각 사용자별 변환 이력을 로드합니다.
 *
 * @param {Array} users - 사용자 객체 배열
 */
function renderUsers(users){
    if (!Array.isArray(users) || users.length === 0) {
        document.getElementById('usersTable').innerHTML = '<p class="muted">등록된 사용자가 없습니다.</p>';
        return;
    }

    const accordionItems = users.map((u, index) => `
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading-${u.id}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#collapse-${u.id}" aria-expanded="false" aria-controls="collapse-${u.id}">
                        <div class="user-summary">
                            <div class="user-summary-item">
                                <span class="user-summary-label">순번:</span>
                                <span class="user-summary-value">${index + 1}</span>
                            </div>
                            <div class="user-summary-item">
                                <span class="user-summary-label">사용자:</span>
                                <span class="user-summary-value">${u.username}</span>
                            </div>
                            <div class="user-summary-item">
                                <span class="user-summary-label">상호:</span>
                                <span class="user-summary-value">${u.company_name || '회사명 없음'}</span>
                            </div>
                            <div class="user-summary-item">
                                <span class="user-summary-label">상태:</span>
                                <span class="badge ${u.approval_status === 'approved' ? 'bg-success' : u.approval_status === 'pending' ? 'bg-warning' : 'bg-secondary'}">${u.approval_status || 'approved'}</span>
                            </div>
                        </div>
                    </button>
                </h2>
                <div id="collapse-${u.id}" class="accordion-collapse collapse" aria-labelledby="heading-${u.id}" data-bs-parent="#usersAccordion">
                    <div class="accordion-body">
                        <div class="user-details">
                            <div class="detail-section">
                                <h6><i class="bi bi-person"></i> 기본 정보</h6>
                                <div class="detail-row">
                                    <span class="detail-label">순번:</span>
                                    <span class="detail-value">${index + 1}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">사용자 ID:</span>
                                    <span class="detail-value">${u.id}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">사용자명:</span>
                                    <span class="detail-value">${u.username}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">이메일:</span>
                                    <span class="detail-value">${u.email || '이메일 없음'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">대표자명:</span>
                                    <span class="detail-value">${u.representative_name || '대표자명 없음'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">전화번호:</span>
                                    <span class="detail-value">${u.phone || '전화번호 없음'}</span>
                                </div>
                            </div>
                            <div class="detail-section">
                                <h6><i class="bi bi-building"></i> 사업자 정보</h6>
                                <div class="detail-row">
                                    <span class="detail-label">회사명:</span>
                                    <span class="detail-value">${u.company_name || '회사명 없음'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">사업자번호:</span>
                                    <span class="detail-value">${u.business_number || '사업자번호 없음'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">업태:</span>
                                    <span class="detail-value">${u.business_type || '업태 없음'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">종목:</span>
                                    <span class="detail-value">${u.business_category || '종목 없음'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">주소:</span>
                                    <span class="detail-value">${u.address || '주소 없음'}</span>
                                </div>
                            </div>
                            <div class="detail-section">
                                <h6><i class="bi bi-credit-card"></i> 플랜 및 토큰</h6>
                                <div class="detail-row">
                                    <span class="detail-label">플랜:</span>
                                    <span class="badge ${u.plan_type === 'free' ? 'bg-danger' : u.plan_type === 'vip' ? 'bg-success' : u.plan_type === 'premium-vip' ? 'bg-info' : u.plan_type === 'gold-vip' ? 'bg-warning' : 'bg-secondary'}">${u.plan_type || 'free'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">VIP 등급:</span>
                                    <select class="form-control form-control-sm vip-plan-select" data-user-id="${u.id}" onchange="changeUserPlan(${u.id}, this.value)">
                                        <option value="free" ${u.plan_type === 'free' ? 'selected' : ''}>무료</option>
                                        <option value="vip" ${u.plan_type === 'vip' ? 'selected' : ''}>VIP</option>
                                        <option value="premium-vip" ${u.plan_type === 'premium-vip' ? 'selected' : ''}>Premium VIP</option>
                                        <option value="gold-vip" ${u.plan_type === 'gold-vip' ? 'selected' : ''}>Gold VIP</option>
                                    </select>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">구독 만료일:</span>
                                    <span class="detail-value">
                                        ${u.subscription_end_date 
                                            ? new Date(u.subscription_end_date).toLocaleDateString('ko-KR') + ' ' + new Date(u.subscription_end_date).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'})
                                            : '-'}
                                    </span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">보유 토큰:</span>
                                    <span class="detail-value text-success">${u.token_balance || 0}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">사용 토큰:</span>
                                    <span class="detail-value text-danger">${u.tokens_used || 0}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">사용량:</span>
                                    <div class="usage-info">
                                        ${(u.plan_type === 'gold-vip' || u.plan_type === 'gold') ? `
                                        <div class="text-muted small">
                                            <span class="fw-bold text-primary">누적 사용량: ${u.tokens_used || 0} 토큰</span>
                                        </div>
                                        ` : `
                                        <div class="text-muted small">
                                            <span class="fw-bold text-success">잔여 토큰: ${(u.token_balance || 0) - (u.tokens_used || 0)}</span> / 
                                            <span class="fw-bold text-info">누적 사용: ${u.tokens_used || 0}</span>
                                        </div>
                                        `}
                                    </div>
                                </div>
                            </div>
                            <div class="detail-section">
                                <h6><i class="bi bi-calendar"></i> 계정 정보</h6>
                                <div class="detail-row">
                                    <span class="detail-label">가입일:</span>
                                    <span class="detail-value">${u.created_at ? new Date(u.created_at).toLocaleDateString('ko-KR') : '-'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">계정 상태:</span>
                                    <span class="badge ${u.approval_status === 'approved' ? 'bg-success' : u.approval_status === 'pending' ? 'bg-warning' : 'bg-secondary'}">${u.approval_status === 'approved' ? '승인됨' : u.approval_status === 'pending' ? '대기중' : '미승인'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">계정 활성화:</span>
                                    <span class="badge ${u.is_active ? 'bg-success' : 'bg-danger'}">${u.is_active ? '활성' : '비활성'}</span>
                                </div>
                            </div>

                            ${(u.plan_type === 'gold-vip' || u.plan_type === 'gold') && u.subscription_end_date ? `
                            <div class="detail-section">
                                <h6><i class="bi bi-clock-history"></i> 👑 유료 Gold 구독</h6>
                                <div class="detail-row">
                                    <span class="detail-label">이용 기간:</span>
                                    <span class="detail-value">
                                        ${u.gold_payment_start_date
                                            ? new Date(u.gold_payment_start_date).toLocaleDateString('ko-KR')
                                              + ' ~ ' +
                                              new Date(u.subscription_end_date).toLocaleDateString('ko-KR')
                                            : '기록 없음'}
                                    </span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">만료일:</span>
                                    <span class="detail-value d-flex align-items-center gap-2">
                                        <span id="subscription-end-date-${u.id}" data-original-date="${u.subscription_end_date || ''}">
                                            ${u.subscription_end_date
                                                ? new Date(u.subscription_end_date).toLocaleDateString('ko-KR') + ' ' +
                                                  new Date(u.subscription_end_date).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'})
                                                : '미설정'}
                                        </span>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="editSubscriptionEndDate(${u.id}, '${u.username}', '${u.subscription_end_date || ''}')" title="종료일 수정">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                    </span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">남은 기간:</span>
                                    <div class="subscription-progress mt-2">
                                        ${renderSubscriptionProgress(u.subscription_end_date, u.gold_payment_start_date)}
                                    </div>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">D-Day:</span>
                                    <span class="detail-value">
                                        ${calculateDDay(u.subscription_end_date)}
                                    </span>
                                </div>
                            </div>
                            ` : ''}

                            ${u.free_trial_expired_at ? `
                            <div class="detail-section">
                                <h6><i class="bi bi-gift"></i> 🎁 무료 체험</h6>
                                <div class="detail-row">
                                    <span class="detail-label">이용 기간:</span>
                                    <span class="detail-value">
                                        ${u.trial_start_date
                                            ? new Date(u.trial_start_date).toLocaleDateString('ko-KR')
                                              + ' ~ ' +
                                              new Date(u.free_trial_expired_at).toLocaleDateString('ko-KR')
                                            : '무료 체험 사용 이력 있음'}
                                    </span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">체험 만료일:</span>
                                    <span class="detail-value">
                                        ${new Date(u.free_trial_expired_at).toLocaleDateString('ko-KR') + ' ' +
                                          new Date(u.free_trial_expired_at).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'})}
                                    </span>
                                </div>
                            </div>
                            ` : ''}
                            <div class="detail-section">
                                <h6><i class="bi bi-gear"></i> 관리 액션</h6>
                                <div class="d-flex gap-2 flex-wrap">
                                    <button class="btn btn-success btn-sm" onclick="grantTokens(${u.id}, '${u.username}')">
                                        <i class="bi bi-plus-circle"></i> 토큰 지급
                                    </button>
                                    <button class="btn btn-primary btn-sm" onclick="resetTokens(${u.id}, '${u.username}')">
                                        <i class="bi bi-arrow-clockwise"></i> 초기화
                                    </button>
                                    ${u.approval_status === 'pending' ? `
                                        <button class="btn btn-warning btn-sm" onclick="approveUser(${u.id}, '${u.username}')">
                                            <i class="bi bi-check-circle"></i> 승인
                                        </button>
                                    ` : ''}
                                    <button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id}, '${u.username}')">
                                        <i class="bi bi-trash"></i> 삭제
                                    </button>
                                    <button class="btn btn-secondary btn-sm" onclick="restoreUser(${u.id}, '${u.username}')">
                                        <i class="bi bi-arrow-counterclockwise"></i> 복구
                                    </button>
                                    <button class="btn danger btn-sm" onclick="purgeUser(${u.id}, '${u.username}')">
                                        <i class="bi bi-skull"></i> 완전삭제
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

    document.getElementById('usersTable').innerHTML = `
        <div class="accordion" id="usersAccordion">
            ${accordionItems}
        </div>
    `;
}

/**
 * 사용자별 변환 이력 로드
 * 특정 사용자의 변환 이력을 API를 통해 가져와 테이블로 렌더링합니다.
 *
 * @param {number} userId - 사용자 ID
 */
async function loadUserConversionHistory(userId) {
    try {
        const res = await fetch(`/admin/api/user-conversions/${userId}`);
        const data = await res.json();
        const conversions = data?.data?.conversions || [];
        
        const tableBody = document.getElementById(`conversion-table-${userId}`);
        if (!tableBody) return;
        
        if (conversions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">변환 이력이 없습니다.</td></tr>';
            return;
        }
        
        const tableRows = conversions.map(conv => `
            <tr>
                <td>${new Date(conv.created_at).toLocaleString('ko-KR')}</td>
                <td>
                    <span class="badge bg-primary">${conv.tokens_used || 0}</span>
                </td>
                <td>
                    <a href="#" class="text-primary text-decoration-none" onclick="downloadFile('${conv.original_filename}')">
                        ${conv.original_filename || '파일명 없음'}
                    </a>
                </td>
            </tr>
        `).join('');
        
        tableBody.innerHTML = tableRows;
    } catch (err) {
        const tableBody = document.getElementById(`conversion-table-${userId}`);
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">이력 로드 실패</td></tr>';
        }
    }
}

/**
 * 토큰 지급
 * 사용자에게 토큰을 지급하는 기능입니다.
 *
 * @param {number} userId - 사용자 ID
 * @param {string} username - 사용자명
 */
async function grantTokens(userId, username) {
    const amount = prompt(`${username}에게 지급할 토큰 수량을 입력하세요:`, '100');
    if (!amount || isNaN(amount) || amount <= 0) return;
    
    try {
        const response = await fetch('/admin/api/grant-tokens', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken()
            },
            body: JSON.stringify({ user_id: userId, amount: parseInt(amount) })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('토큰이 성공적으로 지급되었습니다.');
            loadUsers();
        } else {
            alert('토큰 지급 실패: ' + result.error);
        }
    } catch (error) {
        alert('토큰 지급 중 오류가 발생했습니다.');
    }
}

/**
 * 토큰 초기화
 * 사용자의 토큰 사용량을 초기화하는 기능입니다.
 *
 * @param {number} userId - 사용자 ID
 * @param {string} username - 사용자명
 */
async function resetTokens(userId, username) {
    if (!confirm(`${username}의 토큰 사용량을 초기화하시겠습니까?`)) return;
    
    try {
        const response = await fetch('/admin/api/reset-tokens', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken()
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        const result = await response.json();
        if (result.success) {
            // 완전 초기화로 인해 등급이 변경되었을 수 있으므로 페이지 새로고침
            alert('토큰, 등급, 구독 기간이 모두 초기화되었습니다.');
            window.location.reload();
        } else {
            alert('초기화 실패: ' + result.error);
        }
    } catch (error) {
        alert('토큰 초기화 중 오류가 발생했습니다.');
    }
}

/**
 * 사용자 승인
 * 대기 중인 사용자를 승인하는 기능입니다.
 *
 * @param {number} userId - 사용자 ID
 * @param {string} username - 사용자명
 */
async function approveUser(userId, username) {
    if (!confirm(`${username}을(를) 승인하시겠습니까?`)) return;
    
    try {
        const response = await fetch('/admin/api/approve-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken()
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('사용자가 승인되었습니다.');
            loadUsers();
        } else {
            alert('사용자 승인 실패: ' + result.error);
        }
    } catch (error) {
        alert('사용자 승인 중 오류가 발생했습니다.');
    }
}

/**
 * 사용자 삭제 (소프트 삭제)
 * 사용자 계정을 비활성화하는 기능입니다.
 *
 * @param {number} userId - 사용자 ID
 * @param {string} username - 사용자명
 */
async function deleteUser(userId, username) {
    if (!confirm(`${username}을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) return;
    
    try {
        const response = await fetch('/admin/api/delete-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken()
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('사용자가 삭제되었습니다.');
            loadUsers();
        } else {
            alert('사용자 삭제 실패: ' + result.error);
        }
    } catch (error) {
        alert('사용자 삭제 중 오류가 발생했습니다.');
    }
}

/**
 * 사용자 복구
 * 비활성화된 사용자 계정을 복구하는 기능입니다.
 *
 * @param {number} userId - 사용자 ID
 * @param {string} username - 사용자명
 */
async function restoreUser(userId, username){
    if(!confirm(`${username} 계정을 복구하시겠습니까?`)) return;
    try{
        const res = await fetch(`/admin/api/users/${userId}/restore`,{
            method:'POST',
            headers:{
                'Content-Type':'application/json',
                'X-CSRF-Token': csrfToken()
            }
        });
        const result = await res.json();
        if(result.success){
            alert('복구되었습니다.');
            loadUsers();
        }else{
            alert('복구 실패: ' + (result.error || '알 수 없는 오류'));
        }
    }catch(err){
        alert('복구 처리 중 오류가 발생했습니다');
    }
}

/**
 * 사용자 완전 삭제
 * 사용자 계정을 데이터베이스와 파일 시스템에서 완전히 제거하는 기능입니다.
 *
 * @param {number} userId - 사용자 ID
 * @param {string} username - 사용자명
 */
async function purgeUser(userId, username){
    if(!confirm(`${username}을(를) 완전삭제 하시겠습니까? 이 작업은 DB와 파일에서 모두 제거되며 되돌릴 수 없습니다.`)) return;
    try{
        // CSRF 토큰 안전하게 가져오기 (중복 선언 방지)
        const getCSRFToken = () => {
            if (typeof csrfToken === 'function') {
                return csrfToken();
            }
            const meta = document.querySelector('meta[name="csrf-token"]');
            return meta ? meta.getAttribute('content') || '' : '';
        };
        
        const res = await fetch(`/admin/api/users/${userId}/purge`,{
            method:'POST',
            headers:{
                'Content-Type':'application/json',
                'X-CSRF-Token': getCSRFToken()
            }
        });
        const result = await res.json();
        if(result.success){
            alert('완전삭제가 완료되었습니다.');
            loadUsers();
        }else{
            alert('완전삭제 실패: ' + (result.error || '알 수 없는 오류'));
        }
    }catch(err){
        console.error('완전삭제 처리 중 오류:', err);
        alert('완전삭제 처리 중 오류가 발생했습니다: ' + (err.message || '알 수 없는 오류'));
    }
}

/**
 * 사용자 플랜 변경
 * 사용자의 VIP 등급을 변경하는 기능입니다.
 *
 * @param {number} userId - 사용자 ID
 * @param {string} newPlanType - 새로운 플랜 타입 ('free', 'vip', 'premium-vip', 'gold-vip')
 */
async function changeUserPlan(userId, newPlanType){
    const planNames = {
        'free': '무료',
        'vip': 'VIP',
        'premium-vip': 'Premium VIP',
        'gold-vip': 'Gold VIP'
    };
    
    if(!confirm(`사용자의 VIP 등급을 "${planNames[newPlanType]}"로 변경하시겠습니까?`)) {
        // 취소 시 select 박스를 원래 상태로 되돌림
        loadUsers();
        return;
    }
    
    try{
        const res = await fetch(`/admin/api/users/${userId}/change-plan`, {
            method:'POST',
            headers:{
                'Content-Type':'application/json',
                'X-CSRF-Token': csrfToken()
            },
            body: JSON.stringify({ plan_type: newPlanType })
        });
        
        const result = await res.json();
        if(result.success){
            alert(`VIP 등급이 "${planNames[newPlanType]}"로 변경되었습니다.`);
            loadUsers();
        }else{
            alert('VIP 등급 변경 실패: ' + (result.error || '알 수 없는 오류'));
            loadUsers(); // 실패 시 select 박스를 원래 상태로 되돌림
        }
    }catch(err){
        alert('VIP 등급 변경 중 오류가 발생했습니다');
        loadUsers(); // 오류 시 select 박스를 원래 상태로 되돌림
    }
}

// 전역 스코프에 함수들을 노출 (onclick 속성에서 호출하기 위해)
window.loadUsers = loadUsers;
window.renderUsers = renderUsers;
window.loadUserConversionHistory = loadUserConversionHistory;
window.grantTokens = grantTokens;
window.resetTokens = resetTokens;
window.approveUser = approveUser;
window.deleteUser = deleteUser;
window.restoreUser = restoreUser;
window.purgeUser = purgeUser;
window.changeUserPlan = changeUserPlan;

/**
 * 구독 기간 프로그레스 바 렌더링
 * @param {string|null} endDate - 종료일 (ISO 문자열)
 * @param {string|null} startDate - 시작일 (ISO 문자열)
 * @returns {string} 프로그레스 바 HTML
 */
function renderSubscriptionProgress(endDate, startDate) {
    if (!endDate) {
        return '<div class="progress" style="height: 20px;"><div class="progress-bar bg-secondary" style="width: 0%">미설정</div></div>';
    }
    
    try {
        const end = new Date(endDate);
        const start = startDate ? new Date(startDate) : new Date();
        const now = new Date();
        
        if (Number.isNaN(end.getTime()) || Number.isNaN(start.getTime())) {
            return '<div class="progress" style="height: 20px;"><div class="progress-bar bg-secondary" style="width: 0%">계산 오류</div></div>';
        }
        
        const totalMs = end.getTime() - start.getTime();
        const elapsedMs = now.getTime() - start.getTime();
        const remainingMs = end.getTime() - now.getTime();
        
        if (totalMs <= 0) {
            return '<div class="progress" style="height: 20px;"><div class="progress-bar bg-danger" style="width: 100%">만료됨</div></div>';
        }
        
        const progressPercent = Math.min(Math.max((elapsedMs / totalMs) * 100, 0), 100);
        
        // 일 단위 차이 계산 (시간을 0시 0분 0초로 맞춰서 정확한 일 수 계산)
        const endDateOnly = new Date(end);
        endDateOnly.setHours(0, 0, 0, 0);
        const nowDateOnly = new Date(now);
        nowDateOnly.setHours(0, 0, 0, 0);
        const remainingDays = Math.round((endDateOnly.getTime() - nowDateOnly.getTime()) / (1000 * 60 * 60 * 24));
        
        let progressColor = 'bg-success';
        let progressText = '';
        
        if (remainingDays < 0) {
            progressColor = 'bg-danger';
            progressText = '만료됨';
        } else if (remainingDays <= 7) {
            progressColor = 'bg-warning';
            progressText = `D-${remainingDays} (${Math.round(progressPercent)}% 경과)`;
        } else {
            progressText = `D-${remainingDays} (${Math.round(progressPercent)}% 경과)`;
        }
        
        return `
            <div class="progress" style="height: 24px;">
                <div class="progress-bar ${progressColor} progress-bar-striped progress-bar-animated" 
                     role="progressbar" 
                     style="width: ${progressPercent}%"
                     aria-valuenow="${Math.round(progressPercent)}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                    <small class="fw-bold">${progressText}</small>
                </div>
            </div>
        `;
    } catch (e) {
        return '<div class="progress" style="height: 20px;"><div class="progress-bar bg-secondary" style="width: 0%">계산 오류</div></div>';
    }
}

/**
 * D-Day 계산 함수
 * @param {string|null} endDate - 종료일 (ISO 문자열 또는 null)
 * @returns {string} D-Day 문자열
 */
function calculateDDay(endDate) {
    if (!endDate) {
        return '<span class="badge bg-secondary">미설정</span>';
    }
    
    try {
        // 종료일을 날짜만 비교하도록 시간을 0시 0분 0초로 설정
        const end = new Date(endDate);
        end.setHours(0, 0, 0, 0);
        
        // 오늘 날짜를 시간을 0시 0분 0초로 설정
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        
        // 일 단위 차이 계산 (밀리초 → 일)
        const diffTime = end.getTime() - now.getTime();
        const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays < 0) {
            return '<span class="badge bg-danger">만료됨</span>';
        } else if (diffDays === 0) {
            return '<span class="badge bg-warning text-dark">D-Day</span>';
        } else if (diffDays <= 7) {
            return `<span class="badge bg-warning text-dark">D-${diffDays}</span>`;
        } else {
            return `<span class="badge bg-success">D-${diffDays}</span>`;
        }
    } catch (e) {
        return '<span class="badge bg-secondary">계산 오류</span>';
    }
}

/**
 * 구독 종료일 수정
 * @param {number} userId - 사용자 ID
 * @param {string} username - 사용자명
 * @param {string} currentEndDateISO - 현재 종료일 (ISO 형식 문자열 또는 빈 문자열)
 */
async function editSubscriptionEndDate(userId, username, currentEndDateISO) {
    // 현재 종료일을 표시용으로 포맷팅
    let currentEndDateDisplay = '미설정';
    let defaultDateInput = '';
    
    if (currentEndDateISO && currentEndDateISO.trim()) {
        try {
            const currentDate = new Date(currentEndDateISO);
            if (!isNaN(currentDate.getTime())) {
                currentEndDateDisplay = currentDate.toLocaleDateString('ko-KR') + ' ' + 
                                       currentDate.toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'});
                // YYYY-MM-DD HH:MM 형식으로 변환 (prompt 기본값용)
                const year = currentDate.getFullYear();
                const month = String(currentDate.getMonth() + 1).padStart(2, '0');
                const day = String(currentDate.getDate()).padStart(2, '0');
                const hour = String(currentDate.getHours()).padStart(2, '0');
                const minute = String(currentDate.getMinutes()).padStart(2, '0');
                defaultDateInput = `${year}-${month}-${day} ${hour}:${minute}`;
            }
        } catch (e) {
            console.warn('현재 종료일 파싱 실패:', e);
        }
    }
    
    // 날짜 입력 받기 (YYYY-MM-DD HH:MM 형식)
    let dateInput = prompt(
        `${username}의 Gold 구독 종료일을 입력하세요.\n\n형식: YYYY-MM-DD HH:MM\n예: 2025-12-31 23:59\n\n현재 종료일: ${currentEndDateDisplay}`,
        defaultDateInput
    );
    
    if (!dateInput || !dateInput.trim()) {
        return;
    }
    
    // 날짜 형식 검증 및 변환
    let formattedDate;
    try {
        // YYYY-MM-DD HH:MM 형식을 datetime으로 변환
        const dateTimeStr = dateInput.trim();
        const [datePart, timePart] = dateTimeStr.split(' ');
        
        if (!datePart || !timePart) {
            throw new Error('날짜 형식이 올바르지 않습니다.');
        }
        
        const [year, month, day] = datePart.split('-');
        const [hour, minute] = timePart.split(':');
        
        if (!year || !month || !day || !hour || !minute) {
            throw new Error('날짜 형식이 올바르지 않습니다.');
        }
        
        // 숫자 검증
        if (isNaN(year) || isNaN(month) || isNaN(day) || isNaN(hour) || isNaN(minute)) {
            throw new Error('날짜는 숫자로만 입력해주세요.');
        }
        
        // YYYY-MM-DD HH:MM:SS 형식으로 변환
        formattedDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')} ${hour.padStart(2, '0')}:${minute.padStart(2, '0')}:00`;
        
        // 유효한 날짜인지 확인
        const testDate = new Date(formattedDate);
        if (isNaN(testDate.getTime())) {
            throw new Error('유효하지 않은 날짜입니다.');
        }
    } catch (e) {
        alert('날짜 형식이 올바르지 않습니다. YYYY-MM-DD HH:MM 형식으로 입력해주세요.\n예: 2025-12-31 23:59\n\n오류: ' + e.message);
        return;
    }
    
    if (!confirm(`종료일을 "${formattedDate}"로 변경하시겠습니까?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/users/${userId}/subscription`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken()
            },
            body: JSON.stringify({
                subscription_end_date: formattedDate
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: '서버 오류가 발생했습니다.' }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        if (result.success) {
            const gradeChanged = result.data && result.data.grade_changed;
            const newPlanType = result.data && result.data.new_plan_type;
            
            if (gradeChanged) {
                // 등급이 변경된 경우 페이지 새로고침 (가장 확실한 방법)
                alert(`구독 종료일이 변경되었습니다.\n등급이 ${result.data.old_plan_type}에서 ${newPlanType}로 변경되었습니다.`);
                window.location.reload();
            } else {
                // 등급 변경이 없는 경우 목록만 새로고침
                alert('구독 종료일이 성공적으로 변경되었습니다.');
                loadUsers(); // 목록 새로고침
            }
        } else {
            alert('구독 종료일 변경 실패: ' + (result.error || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('구독 종료일 변경 오류:', error);
        alert('구독 종료일 변경 중 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'));
    }
}

// CSRF 토큰 함수 (admin.html에 정의되어 있지만 안전을 위해 여기서도 정의)
if (typeof csrfToken === 'undefined') {
    function csrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') || '' : '';
    }
    window.csrfToken = csrfToken;
}

// 전역 스코프에 함수 노출
window.editSubscriptionEndDate = editSubscriptionEndDate;
window.calculateDDay = calculateDDay;



