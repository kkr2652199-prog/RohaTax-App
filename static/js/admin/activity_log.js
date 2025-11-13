/**
 * Admin Dashboard 활동 로그 모듈
 *
 * 이 파일은 admin.html에서 분리된 통합 관제실(Activity Logs) 관련 함수를 포함합니다.
 * - 활동 로그 데이터 로드 및 렌더링
 * - 필터링 기능 연동
 * - 페이지네이션 지원
 */

/**
 * 통합 관제실(Activity Logs) 데이터 로드 및 렌더링 함수 v5 (필터링 기능 연동)
 * 서버에서 활동 로그 데이터를 가져와 UI에 표시합니다.
 * @param {number} page - 페이지 번호 (기본값: 1)
 * @param {number} limit - 페이지당 항목 수 (기본값: 50)
 * @returns {Promise<void>}
 */
async function loadActivityLogs(page = 1, limit = 50) {
    const contentContainer = document.getElementById('control-deck-content');
    if (!contentContainer) {
        console.error("'control-deck-content' 컨테이너를 찾을 수 없습니다.");
        return;
    }
    contentContainer.innerHTML = '<p class="muted">활동 로그를 불러오는 중...</p>';

    // [신규] 필터 값들을 읽어 API 요청 URL을 동적으로 생성
    const startDate = document.getElementById('filter-start-date').value;
    const endDate = document.getElementById('filter-end-date').value;
    const activityType = document.getElementById('filter-activity-type').value;
    const userSearch = document.getElementById('filter-user-search').value;

    const params = new URLSearchParams({ page, limit });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (activityType) params.append('activity_type', activityType);
    if (userSearch) params.append('user_search', userSearch);

    try {
        const response = await fetch(`/admin/api/activity-logs?${params.toString()}`, {
            headers: { 'X-CSRF-Token': csrfToken() }
        });
        const result = await response.json();

        if (!result.success || !result.data.logs) {
            contentContainer.innerHTML = '<p class="text-danger">데이터를 불러오는 데 실패했습니다: ' + (result.error || '알 수 없는 오류') + '</p>';
            return;
        }

        const { logs, pagination } = result.data;

        if (logs.length === 0) {
            contentContainer.innerHTML = '<p class="muted">기록된 활동 로그가 없습니다.</p>';
            return;
        }

        // [신규] 활동 유형 번역 사전
        const activityTypeKorean = {
            'FILE_CONVERT': '파일 변환',
            'TOKEN_PURCHASE': '토큰 구매',
            'TOKEN_GRANT_BY_ADMIN': '토큰 지급 (관리자)',
            'TOKEN_RESET_BY_ADMIN': '토큰 초기화 (관리자)',
            'GRADE_CHANGE_BY_ADMIN': '등급 변경 (관리자)',
            'USER_SOFT_DELETE_BY_ADMIN': '계정 비활성화 (관리자)',
            'USER_RESTORE_BY_ADMIN': '계정 복구 (관리자)',
            'USER_PURGE_BY_ADMIN': '계정 영구 삭제 (관리자)',
            // 추후 다른 활동 유형이 추가될 수 있음
        };

        const tableRows = logs.map(log => {
            const timestamp = new Date(log.timestamp).toLocaleString('ko-KR', { hour12: false });
            const details = log.details ? JSON.parse(log.details) : {};

            // --- [신규] 데이터 가공 로직 v2 시작 ---
            
            // 1. 관리자 표시 로직
            let adminDisplay = (log.performed_by_type === 'ADMIN') ? log.actor_username : 
                               (log.performed_by_type === 'SYSTEM') ? 'system' : '-';

            // 2. '상세 내용' 요약 로직
            let detailsSummary = '';
            switch (log.activity_type) {
                case 'FILE_CONVERT':
                    detailsSummary = `${details.filename} (${details.extracted_rows}건)`;
                    break;
                case 'GRADE_CHANGE_BY_ADMIN':
                    detailsSummary = `[${details.from_plan}] → [${details.to_plan}]`;
                    break;
                case 'TOKEN_GRANT_BY_ADMIN':
                    detailsSummary = `${details.granted_amount} 토큰 지급`;
                    break;
                case 'TOKEN_RESET_BY_ADMIN':
                    detailsSummary = `잔액 ${details.reset_balance} → 0`;
                    break;
                case 'USER_SOFT_DELETE_BY_ADMIN':
                case 'USER_RESTORE_BY_ADMIN':
                    detailsSummary = details.username || details.reason || '상세 정보 없음';
                    break;
                case 'USER_PURGE_BY_ADMIN':
                    detailsSummary = details.purged_username || details.reason || '상세 정보 없음';
                    break;
                default:
                    detailsSummary = '상세 정보 없음';
            }

            // 3. '복식부기' 로직 (충전량, 사용량 분리)
            let chargeDisplay = '';
            let usageDisplay = '';
            const isUnlimited = ['unlimited', 'gold', 'gold-vip'].includes(log.user_plan_snapshot);

            // [수정] TOKEN_RESET_BY_ADMIN의 경우 사용량/충전량 표시하지 않음 (마이너스는 빼야 하므로)
            if (log.activity_type === 'TOKEN_RESET_BY_ADMIN') {
                chargeDisplay = '-';
                usageDisplay = '-';
            } else if (log.token_change > 0) {
                chargeDisplay = `+${log.token_change}`; // 충전
            } else {
                if (isUnlimited && log.activity_type === 'FILE_CONVERT') {
                    usageDisplay = `무제한사용(${Math.abs(log.potential_cost)})`;
                } else if (log.token_change < 0) {
                    usageDisplay = log.token_change; // 사용
                }
            }
            
            const translatedActivityType = activityTypeKorean[log.activity_type] || log.activity_type;
            // --- 데이터 가공 로직 종료 ---

            return `
                <tr>
                    <td class="small">${timestamp}</td>
                    <td>${adminDisplay}</td>
                    <td>${log.target_username}</td>
                    <td>${translatedActivityType}</td>
                    <td>${detailsSummary}</td>
                    <td><span class="badge ${isUnlimited ? 'bg-warning text-dark' : 'bg-success'}">${log.user_plan_snapshot}</span></td>
                    <td class="text-muted">${log.token_balance_before !== null ? log.token_balance_before : '-'}</td>
                    <td class="text-success fw-bold">${chargeDisplay}</td>
                    <td class="${isUnlimited ? '' : 'text-danger'}">${usageDisplay}</td>
                    <td class="fw-bold">${log.token_balance_after !== null ? log.token_balance_after : '-'}</td>
                </tr>
            `;
        }).join('');

        const tableHtml = `
            <div class="table-container">
                <table class="table table-sm table-hover">
                    <thead>
                        <tr>
                            <th>변환/토큰지급/등급변경</th>
                            <th>관리자</th>
                            <th>유저</th>
                            <th>활동 유형 (Type)</th>
                            <th>상세 내용/파일명</th>
                            <th>유저등급</th>
                            <th>토큰 총수량</th>
                            <th>토큰 충전량</th>
                            <th>사용량</th>
                            <th>토큰 총잔량</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
            </div>
        `;
        
        contentContainer.innerHTML = tableHtml;

    } catch (error) {
        console.error('활동 로그 로드 중 오류 발생:', error);
        contentContainer.innerHTML = '<p class="text-danger">활동 로그를 불러오는 중 오류가 발생했습니다.</p>';
    }
}

// 전역 함수로 노출 (다른 모듈에서 호출 가능하도록)
window.loadActivityLogs = loadActivityLogs;

