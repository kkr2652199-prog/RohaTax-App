/**
 * Admin Dashboard 코어 모듈
 *
 * 이 파일은 admin.html에서 분리된 대시보드 초기화 및 새로고침 관련 함수들을 포함합니다.
 * - 관리자 세션 확인
 * - 대시보드 표시/숨김 제어
 * - 대시보드 전체 새로고침
 * - 자동 새로고침 토글
 */

/**
 * 관리자 세션 확인
 * 초기 데이터가 있으면 먼저 렌더링하고, 이후 API를 통해 세션 상태를 확인합니다.
 * 세션이 유효하지 않으면 로그인 페이지로 리다이렉트합니다.
 */
async function checkAdminSession() {
    try{
        if(adminInitialData?.general_users){
            renderUsers(adminInitialData.general_users);
            showDashboard();
        }
        // 세션 상태 확인
        const res = await fetch('/admin/api/users', {
            headers: {
                'X-CSRF-Token': csrfToken(),
            },
        });
        if (res.status === 403) {
            // 관리자 권한 없음 - 로그인 페이지로 리다이렉트
            window.location.href = '/login';
            return;
        }
        if (res.ok) {
            // 관리자 권한 있음 - 대시보드 표시
            showDashboard();
            loadUsers();
            loadTokenHistory();
            loadStats();
            updateLastRefreshTime();
        }
    } catch (error) {
        console.error('세션 체크 실패:', error);
        window.location.href = '/login';
    }
}

/**
 * 대시보드 표시
 * 관리자 대시보드의 hidden 클래스를 제거하여 화면에 표시합니다.
 */
function showDashboard(){ 
    dashboard.classList.remove('hidden'); 
}

/**
 * 대시보드 새로고침
 * 대시보드의 모든 주요 데이터를 다시 로드합니다.
 * - 사용자 목록
 * - 토큰 히스토리
 * - 통계 데이터
 * - 마지막 새로고침 시간 업데이트
 */
function refreshDashboard() {
    loadUsers();
    loadTokenHistory();
    loadStats();
    updateLastRefreshTime();
}

/**
 * 자동 새로고침 토글
 * 자동 새로고침을 시작하거나 중지합니다.
 * 버튼 텍스트도 함께 업데이트합니다.
 */
function toggleAutoRefresh() {
    if (autoRefreshInterval) {
        stopAutoRefresh();
        updateRefreshButtonText('자동 새로고침 시작');
    } else {
        startAutoRefresh();
        updateRefreshButtonText('자동 새로고침 중지');
    }
}

// 전역 스코프에 함수들을 노출 (다른 모듈에서 호출하기 위해)
window.checkAdminSession = checkAdminSession;
window.showDashboard = showDashboard;
window.refreshDashboard = refreshDashboard;
window.toggleAutoRefresh = toggleAutoRefresh;

