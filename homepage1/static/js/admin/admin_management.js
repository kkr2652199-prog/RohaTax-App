/**
 * Admin Dashboard 관리자 관리 모듈
 *
 * 이 파일은 admin.html에서 분리된 관리자 관리 관련 함수를 포함합니다.
 * - 관리자 목록 로드
 * - 관리자 대시보드 통계 로드 및 업데이트
 */

/**
 * 관리자 목록 로드
 * 서버에서 관리자 사용자 목록을 가져와 UI에 표시합니다.
 * @returns {Promise<void>}
 */
async function loadAdminUsers() {
    try {
        const res = await fetch('/admin/api/admin-users', {
            headers: {
                'X-CSRF-Token': csrfToken()
            },
        });
        const body = await res.json();
        const adminUsers = body?.data?.admin_users || [];
        
        if (adminUsers.length === 0) {
            document.getElementById('adminUsersTable').innerHTML = '<p class="muted">등록된 관리자가 없습니다.</p>';
            return;
        }
        
        const adminItems = adminUsers.map(admin => `
            <div class="admin-user-item">
                <div class="admin-user-info">
                    <div class="admin-user-avatar">${admin.username.charAt(0).toUpperCase()}</div>
                    <div class="admin-user-details">
                        <h5>${admin.username}</h5>
                        <p>${admin.email || '이메일 없음'} • 가입일: ${admin.created_at ? new Date(admin.created_at).toLocaleDateString('ko-KR') : '-'}</p>
                    </div>
                </div>
                <div class="admin-user-status">
                    <span class="admin-status-badge ${admin.is_active ? 'admin-status-active' : 'admin-status-inactive'}">
                        ${admin.is_active ? '활성' : '비활성'}
                    </span>
                </div>
            </div>
        `).join('');
        
        document.getElementById('adminUsersTable').innerHTML = adminItems;
    } catch (err) {
        document.getElementById('adminUsersTable').innerHTML = '<p class="muted">관리자 목록 로드 실패</p>';
    }
}

/**
 * 관리자 대시보드 통계 로드
 * 서버에서 관리자 대시보드 통계 데이터를 가져와 UI를 업데이트합니다.
 * @returns {Promise<void>}
 */
async function loadAdminDashboardStats() {
    try {
        const response = await fetch('/admin/api/admin-dashboard-stats', {
            headers: {
                'X-CSRF-Token': csrfToken()
            },
        });
        const data = await response.json();
        
        if (data.success) {
            updateAdminDashboardStats(data.data);
        } else {
            console.error('관리자 대시보드 통계 로드 실패:', data.message);
        }
    } catch (error) {
        console.error('관리자 대시보드 통계 요청 실패:', error);
    }
}

/**
 * 관리자 대시보드 통계 UI 업데이트
 * 제공된 통계 데이터를 기반으로 대시보드의 통계 카드들을 업데이트합니다.
 * @param {object} data - 통계 데이터 객체 (total_issued_tokens, active_users_count, system_error_rate, system_uptime 포함)
 */
function updateAdminDashboardStats(data) {
    // 총 발급 토큰
    document.getElementById('totalIssuedTokens').textContent = data.total_issued_tokens || 0;
    
    // 현재 활성 사용자
    document.getElementById('activeUsersCount').textContent = data.active_users_count || 0;
    
    // 시스템 에러율
    document.getElementById('systemErrorRate').textContent = `${data.system_error_rate || 0}%`;
    
    // 시스템 가동률
    document.getElementById('systemUptime').textContent = `${data.system_uptime || 99.9}%`;
}

// 전역 함수로 노출 (다른 모듈에서 호출 가능하도록)
window.loadAdminUsers = loadAdminUsers;
window.loadAdminDashboardStats = loadAdminDashboardStats;
window.updateAdminDashboardStats = updateAdminDashboardStats;


