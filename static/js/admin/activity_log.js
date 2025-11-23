/**
 * Admin Dashboard 활동 로그 모듈
 *
 * 이 파일은 admin.html에서 분리된 통합 관제실(Activity Logs) 관련 함수를 포함합니다.
 * - 활동 로그 데이터 로드 및 렌더링
 * - 필터링 기능 연동
 * - 페이지네이션 지원
 */

// 현재 페이지 상태
let currentActivityLogPage = 1;
let currentActivityLogLimit = 50;

/**
 * 통합 관제실(Activity Logs) 데이터 로드 및 렌더링 함수 v6 (페이지네이션 및 삭제 기능)
 * 서버에서 활동 로그 데이터를 가져와 UI에 표시합니다.
 * @param {number} page - 페이지 번호 (기본값: 1)
 * @param {number} limit - 페이지당 항목 수 (기본값: 50)
 * @returns {Promise<void>}
 */
async function loadActivityLogs(page = 1, limit = 50) {
    currentActivityLogPage = page;
    currentActivityLogLimit = limit;
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

        /**
         * 활동 유형 한글 번역 및 아이콘 매핑
         * @param {string} activityType - 활동 유형 코드
         * @returns {string} 한글 번역 및 아이콘
         */
        function getActivityTypeLabel(activityType) {
            const typeMap = {
                'TOKEN_CHARGE': '💰 결제/충전',
                'PAYMENT_CANCEL': '↩️ 결제 취소',
                'GRADE_CHANGE': '👑 등급 변경',
                'GRADE_CHANGE_BY_ADMIN': '👑 등급 변경',
                'TOKEN_GRANT_BY_ADMIN': '🎁 관리자 지급',
                'FILE_CONVERT': '📂 파일 변환',
                'TOKEN_PURCHASE': '💰 토큰 구매',
                'TOKEN_RESET_BY_ADMIN': '🔄 토큰 초기화',
                'USER_SOFT_DELETE_BY_ADMIN': '🚫 계정 비활성화',
                'USER_RESTORE_BY_ADMIN': '✅ 계정 복구',
                'USER_PURGE_BY_ADMIN': '🗑️ 계정 영구 삭제',
            };
            return typeMap[activityType] || activityType;
        }

        /**
         * 활동 유형별 배지 스타일 반환
         * @param {string} activityType - 활동 유형 코드
         * @returns {string} Bootstrap 배지 클래스
         */
        function renderActivityTypeBadge(activityType) {
            const badgeMap = {
                'TOKEN_CHARGE': 'bg-success',           // 결제/충전: 녹색
                'PAYMENT_CANCEL': 'bg-secondary',       // 취소: 회색
                'GRADE_CHANGE': 'bg-warning text-dark', // 등급 변경: 노란색
                'GRADE_CHANGE_BY_ADMIN': 'bg-warning text-dark',
                'TOKEN_GRANT_BY_ADMIN': 'bg-info',      // 관리자 지급: 파란색
                'FILE_CONVERT': 'bg-primary',           // 파일 변환: 기본 파랑
                'TOKEN_PURCHASE': 'bg-success',
                'TOKEN_RESET_BY_ADMIN': 'bg-danger',
                'USER_SOFT_DELETE_BY_ADMIN': 'bg-secondary',
                'USER_RESTORE_BY_ADMIN': 'bg-success',
                'USER_PURGE_BY_ADMIN': 'bg-danger',
            };
            return badgeMap[activityType] || 'bg-secondary';
        }

        /**
         * 상세 내용에서 태그 강조 처리
         * @param {string} detailsSummary - 상세 내용 요약
         * @returns {string} 태그가 강조된 HTML
         */
        function highlightTags(detailsSummary) {
            if (!detailsSummary) return detailsSummary;
            
            // "(결제 자동)" 또는 "(결제 연동)" 태그 강조
            let highlighted = detailsSummary.replace(
                /\(결제\s*(자동|연동)\)/g,
                '<span class="badge bg-success text-white fw-bold">(결제 자동)</span>'
            );
            
            // "(결제 취소/환불)" 태그 강조
            highlighted = highlighted.replace(
                /\(결제\s*취소\/환불\)/g,
                '<span class="badge bg-secondary text-white fw-bold">(결제 취소/환불)</span>'
            );
            
            // "(관리자 수동)" 태그 강조
            highlighted = highlighted.replace(
                /\(관리자\s*수동\)/g,
                '<span class="badge bg-info text-white fw-bold">(관리자 수동)</span>'
            );
            
            return highlighted;
        }

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
                case 'TOKEN_CHARGE':
                    // 결제 관련 상세 정보
                    if (details.message) {
                        detailsSummary = details.message;
                    } else if (details.product_name) {
                        detailsSummary = `${details.product_name} 결제 완료 (주문번호: ${details.order_id || 'N/A'})`;
                    } else {
                        detailsSummary = `토큰 ${details.token_amount || log.token_change}개 충전`;
                    }
                    break;
                case 'PAYMENT_CANCEL':
                    detailsSummary = details.message || `결제 취소 (환불: ${details.refund_amount || 0}토큰)`;
                    break;
                case 'GRADE_CHANGE':
                case 'GRADE_CHANGE_BY_ADMIN':
                    detailsSummary = `[${details.from_plan || 'N/A'}] → [${details.to_plan || 'N/A'}]`;
                    if (details.reason) {
                        detailsSummary += ` ${details.reason}`;
                    }
                    break;
                case 'TOKEN_GRANT_BY_ADMIN':
                    detailsSummary = `${details.granted_amount} 토큰 지급`;
                    if (details.reason) {
                        detailsSummary += ` ${details.reason}`;
                    }
                    break;
                case 'TOKEN_RESET_BY_ADMIN':
                    detailsSummary = `잔액 ${details.reset_balance} → 0`;
                    if (details.reason) {
                        detailsSummary += ` ${details.reason}`;
                    }
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
            
            // 태그 강조 적용
            detailsSummary = highlightTags(detailsSummary);

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
            
            const translatedActivityType = getActivityTypeLabel(log.activity_type);
            const badgeClass = renderActivityTypeBadge(log.activity_type);
            // --- 데이터 가공 로직 종료 ---

            return `
                <tr>
                    <td class="small">${timestamp}</td>
                    <td>${adminDisplay}</td>
                    <td>${log.target_username}</td>
                    <td><span class="badge ${badgeClass}">${translatedActivityType}</span></td>
                    <td>${detailsSummary}</td>
                    <td><span class="badge ${isUnlimited ? 'bg-warning text-dark' : 'bg-success'}">${log.user_plan_snapshot}</span></td>
                    <td class="text-muted">${log.token_balance_before !== null ? log.token_balance_before : '-'}</td>
                    <td class="text-success fw-bold">${chargeDisplay}</td>
                    <td class="${isUnlimited ? '' : 'text-danger'}">${usageDisplay}</td>
                    <td class="fw-bold">${log.token_balance_after !== null ? log.token_balance_after : '-'}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteActivityLog(${log.id})" title="기록 삭제">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        // 페이지네이션 HTML 생성
        const paginationHtml = renderActivityLogPagination(pagination);
        
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
                            <th>관리</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
            </div>
            ${paginationHtml}
        `;
        
        contentContainer.innerHTML = tableHtml;

    } catch (error) {
        console.error('활동 로그 로드 중 오류 발생:', error);
        contentContainer.innerHTML = '<p class="text-danger">활동 로그를 불러오는 중 오류가 발생했습니다.</p>';
    }
}

/**
 * 페이지네이션 렌더링 함수
 * @param {Object} pagination - 페이지네이션 정보
 * @returns {string} 페이지네이션 HTML
 */
function renderActivityLogPagination(pagination) {
    const { total_items, current_page, items_per_page, total_pages } = pagination;
    
    if (total_pages <= 1) {
        return `
            <div class="d-flex justify-content-between align-items-center mt-3">
                <div class="text-muted small">전체 ${total_items}건</div>
            </div>
        `;
    }
    
    let paginationHTML = '<nav aria-label="활동 로그 페이지네이션"><ul class="pagination justify-content-center mt-3">';
    
    // 이전 버튼
    if (current_page > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadActivityLogs(${current_page - 1}, ${items_per_page}); return false;">이전</a></li>`;
    } else {
        paginationHTML += `<li class="page-item disabled"><span class="page-link">이전</span></li>`;
    }
    
    // 페이지 번호 버튼
    const startPage = Math.max(1, current_page - 2);
    const endPage = Math.min(total_pages, current_page + 2);
    
    if (startPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadActivityLogs(1, ${items_per_page}); return false;">1</a></li>`;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === current_page ? 'active' : '';
        paginationHTML += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="loadActivityLogs(${i}, ${items_per_page}); return false;">${i}</a></li>`;
    }
    
    if (endPage < total_pages) {
        if (endPage < total_pages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadActivityLogs(${total_pages}, ${items_per_page}); return false;">${total_pages}</a></li>`;
    }
    
    // 다음 버튼
    if (current_page < total_pages) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadActivityLogs(${current_page + 1}, ${items_per_page}); return false;">다음</a></li>`;
    } else {
        paginationHTML += `<li class="page-item disabled"><span class="page-link">다음</span></li>`;
    }
    
    paginationHTML += '</ul></nav>';
    
    // 정보 표시
    paginationHTML += `
        <div class="d-flex justify-content-between align-items-center mt-2">
            <div class="text-muted small">전체 ${total_items}건 (페이지 ${current_page}/${total_pages})</div>
        </div>
    `;
    
    return paginationHTML;
}

/**
 * 활동 로그 삭제 함수
 * @param {number} logId - 삭제할 로그 ID
 */
async function deleteActivityLog(logId) {
    // 확인 창
    if (!confirm('정말 이 활동 로그를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.')) {
        return;
    }
    
    try {
        console.log('[deleteActivityLog] 활동 로그 삭제 시작:', logId);
        
        // CSRF 토큰 가져오기 (payment.js와 동일한 방식)
        const csrfTokenValue = typeof window.getCSRFToken === 'function' 
            ? window.getCSRFToken() 
            : (typeof csrfToken === 'function' ? csrfToken() : 
               (document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''));
        
        const response = await fetch(`/admin/api/activity-logs/${logId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfTokenValue
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `활동 로그 삭제 실패: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[deleteActivityLog] API 응답:', result);
        
        if (result.success) {
            alert('활동 로그가 성공적으로 삭제되었습니다.');
            
            // 현재 페이지 다시 로드
            loadActivityLogs(currentActivityLogPage, currentActivityLogLimit);
        } else {
            throw new Error(result.message || '활동 로그 삭제에 실패했습니다.');
        }
        
    } catch (error) {
        console.error('[deleteActivityLog] 오류:', error);
        alert(`활동 로그 삭제 중 오류가 발생했습니다: ${error.message}`);
    }
}

// 전역 함수로 노출 (다른 모듈에서 호출 가능하도록)
window.loadActivityLogs = loadActivityLogs;
window.deleteActivityLog = deleteActivityLog;

