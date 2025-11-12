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
                                    <span class="detail-label">보유 토큰:</span>
                                    <span class="detail-value text-success">${u.token_balance || 0}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">사용 토큰:</span>
                                    <span class="detail-value text-danger">${u.tokens_used || 0}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">사용량:</span>
                                    <div class="usage-progress">
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <small class="text-muted">${u.used_count || 0}/${u.monthly_limit || 50}</small>
                                            <small class="text-muted">${Math.round(((u.used_count || 0) / (u.monthly_limit || 50)) * 100)}%</small>
                                        </div>
                                        <div class="progress" style="height: 8px;">
                                            <div class="progress-bar ${(u.used_count || 0) >= (u.monthly_limit || 50) ? 'bg-danger' : (u.used_count || 0) >= (u.monthly_limit || 50) * 0.8 ? 'bg-warning' : 'bg-success'}" 
                                                 role="progressbar" 
                                                 style="width: ${Math.min(((u.used_count || 0) / (u.monthly_limit || 50)) * 100, 100)}%"
                                                 aria-valuenow="${u.used_count || 0}" 
                                                 aria-valuemin="0" 
                                                 aria-valuemax="${u.monthly_limit || 50}">
                                            </div>
                                        </div>
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
                            <div class="detail-section">
                                <h6><i class="bi bi-clock-history"></i> 토큰 사용 및 변환 상세 내역</h6>
                                <div class="conversion-history" id="conversion-history-${u.id}">
                                    <div class="table-responsive">
                                        <table class="table table-hover table-sm">
                                            <thead>
                                                <tr>
                                                    <th>변환 시간</th>
                                                    <th>사용 토큰</th>
                                                    <th>변환 파일명</th>
                                                </tr>
                                            </thead>
                                            <tbody id="conversion-table-${u.id}">
                                                <tr>
                                                    <td colspan="3" class="text-center text-muted">변환 이력을 불러오는 중...</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
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

    users.forEach(user => {
        loadUserConversionHistory(user.id);
    });
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
            alert('토큰 사용량이 초기화되었습니다.');
            loadUsers();
        } else {
            alert('토큰 초기화 실패: ' + result.error);
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
        const res = await fetch(`/admin/api/users/${userId}/purge`,{
            method:'POST',
            headers:{
                'Content-Type':'application/json',
                'X-CSRF-Token': csrfToken()
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
        alert('완전삭제 처리 중 오류가 발생했습니다');
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

