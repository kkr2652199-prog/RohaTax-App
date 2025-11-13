/**
 * Admin Dashboard 토큰 히스토리 모듈
 *
 * 이 파일은 admin.html에서 분리된 비활성 사용자 관리 관련 함수를 포함합니다.
 * - 비활성 사용자 목록 로드
 * - 비활성 사용자 테이블 렌더링
 */

/**
 * 비활성 사용자 목록 로드
 * 이 함수는 '비활성 사용자'를 로드하고 관리합니다.
 * @returns {Promise<void>}
 */
async function loadTokenHistory(){
    // [최종 수정] 이 함수는 이제 '비활성 사용자'를 로드하고 관리합니다.
    const contentContainer = document.getElementById('tokenHistoryTable');
    contentContainer.innerHTML = '<p class="muted">비활성 사용자 목록을 불러오는 중...</p>';

    try{
        const csrf = document.querySelector('meta[name=\'csrf-token\']')?.getAttribute('content') || '';
        const res = await fetch('/admin/api/token-history', {
            headers: { 'X-CSRF-Token': csrf }
        });
        const body = await res.json();
        const inactive_users = body?.data?.history || []; // API 응답 필드명은 호환성을 위해 'history' 유지
        
        if(inactive_users.length === 0){
            contentContainer.innerHTML = '<p class="muted">비활성화된 사용자가 없습니다.</p>';
            return;
        }
        
        const rows = inactive_users.map(u => {
            const deletedTime = u.timestamp_utc ? new Date(u.timestamp_utc).toLocaleString('ko-KR', { hour12: false }) : '-';
            return `
            <tr>
                <td>${u.target_username}</td>
                <td>${u.email || '-'}</td>
                <td>${deletedTime}</td>
                <td>
                    <div class="action-group">
                        <button class="btn btn-success btn-sm" onclick="restoreUser(${u.id}, '${u.target_username}')">복구</button>
                        <button class="btn btn-danger btn-sm" onclick="purgeUser(${u.id}, '${u.target_username}')">완전삭제</button>
                    </div>
                </td>
            </tr>
        `;}).join('');
        
        const table = `
            <div class="table-container">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>사용자명</th>
                        <th>이메일</th>
                        <th>비활성화된 시간</th>
                        <th>관리 액션</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
            </div>
        `;
        
        contentContainer.innerHTML = table;

    }catch(err){
        contentContainer.innerHTML = '<p class="muted">비활성 사용자 목록 로드에 실패했습니다.</p>';
    }
}

// 전역 함수로 노출 (다른 모듈에서 호출 가능하도록)
window.loadTokenHistory = loadTokenHistory;


