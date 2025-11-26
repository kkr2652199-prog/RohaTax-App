/**
 * Admin Dashboard 활동 로그 모듈 (클래스 기반 리팩토링)
 *
 * ActivityLogManager 클래스를 사용하여 각 탭별로 독립적인 로그 관리
 * - 활동 로그 데이터 로드 및 렌더링
 * - 필터링 기능 연동
 * - 페이지네이션 지원
 * - 카테고리별 필터링 (FINANCIAL, ACTIVITY, SECURITY)
 */

/**
 * 카테고리별 활동 유형 매핑
 */
const CATEGORY_TYPES = {
    'FINANCIAL': ['TOKEN_CHARGE', 'TOKEN_USE', 'TOKEN_GRANT_BY_ADMIN', 'TOKEN_RESET_BY_ADMIN', 'TOKEN_PURCHASE', 'PAYMENT_CANCEL', 'GRADE_CHANGE', 'GRADE_CHANGE_BY_ADMIN', 'SUBSCRIPTION_UPDATE'],
    'ACTIVITY': ['USER_LOGIN', 'USER_LOGOUT', 'FILE_CONVERT', 'PROFILE_UPDATE'],
    'SECURITY': ['USER_SOFT_DELETE_BY_ADMIN', 'USER_RESTORE_BY_ADMIN', 'USER_PURGE_BY_ADMIN']
};

/**
 * 활동 로그 관리자 클래스
 */
class ActivityLogManager {
    /**
     * @param {string} tabId - 탭 패널 전체를 감싸는 div의 ID (예: 'panel-all', 'panel-financial')
     * @param {string} category - 카테고리 ('ALL', 'FINANCIAL', 'ACTIVITY', 'SECURITY')
     */
    constructor(tabId, category = 'ALL') {
        this.tabId = tabId;
        this.category = category;
        this.currentPage = 1;
        this.currentLimit = 50;
        this.container = null;  // 탭 패널 전체 컨테이너
        this.tableContainer = null;  // 테이블이 들어갈 컨테이너
        
        // 필터 요소 참조 (init에서 초기화)
        this.startDateInput = null;
        this.endDateInput = null;
        this.activityTypeSelect = null;
        this.userSearchInput = null;
        this.searchButton = null;
    }

    /**
     * 컨테이너 초기화
     */
    init() {
        console.log('=== [ActivityLogManager.init] 디버깅 시작 ===');
        console.log('1. this.tabId:', this.tabId);
        console.log('2. this.category:', this.category);
        
        // 탭 패널 전체 컨테이너 찾기
        const tabPanelElement = document.getElementById(this.tabId);
        console.log('3. document.getElementById(this.tabId) 결과:', tabPanelElement);
        console.log('   - null 여부:', tabPanelElement === null);
        console.log('   - 요소 타입:', tabPanelElement ? tabPanelElement.tagName : 'N/A');
        console.log('   - 요소 ID:', tabPanelElement ? tabPanelElement.id : 'N/A');
        
        this.container = tabPanelElement;
        if (!this.container) {
            console.error(`[ActivityLogManager] 탭 패널을 찾을 수 없습니다: ${this.tabId}`);
            console.log('=== [ActivityLogManager.init] 디버깅 종료 (실패) ===');
            return false;
        }
        
        // 테이블 컨테이너 찾기 (데이터가 렌더링될 곳)
        const tableContainerId = `activity-log-container-${this.category.toLowerCase()}`;
        console.log('4. tableContainerId:', tableContainerId);
        
        const tableContainerElement = document.getElementById(tableContainerId);
        console.log('5. document.getElementById(tableContainerId) 결과:', tableContainerElement);
        console.log('   - null 여부:', tableContainerElement === null);
        console.log('   - 요소 타입:', tableContainerElement ? tableContainerElement.tagName : 'N/A');
        console.log('   - 요소 ID:', tableContainerElement ? tableContainerElement.id : 'N/A');
        
        this.tableContainer = tableContainerElement;
        if (!this.tableContainer) {
            console.error(`[ActivityLogManager] 테이블 컨테이너를 찾을 수 없습니다: ${tableContainerId}`);
            console.log('=== [ActivityLogManager.init] 디버깅 종료 (실패) ===');
            return false;
        }
        
        // 필터 요소 찾기 (탭 패널 내부에서 직접 검색)
        console.log('6. 필터 요소 찾기 시작 (this.container 내부에서 검색)');
        console.log('   - this.container:', this.container);
        console.log('   - this.container.querySelector 사용');
        
        this.startDateInput = this.container.querySelector('.filter-start-date');
        console.log('   - .filter-start-date:', this.startDateInput);
        
        this.endDateInput = this.container.querySelector('.filter-end-date');
        console.log('   - .filter-end-date:', this.endDateInput);
        
        this.activityTypeSelect = this.container.querySelector('.filter-activity-type');
        console.log('   - .filter-activity-type:', this.activityTypeSelect);
        
        this.userSearchInput = this.container.querySelector('.filter-user-search');
        console.log('   - .filter-user-search:', this.userSearchInput);
        
        this.searchButton = this.container.querySelector('.btn-apply-filters');
        console.log('   - .btn-apply-filters:', this.searchButton);
        
        // 필터 요소 찾기 실패 시 경고
        if (!this.startDateInput || !this.endDateInput || !this.activityTypeSelect || !this.userSearchInput || !this.searchButton) {
            console.warn(`[ActivityLogManager] 일부 필터 요소를 찾을 수 없습니다 (탭: ${this.tabId})`, {
                startDate: !!this.startDateInput,
                endDate: !!this.endDateInput,
                activityType: !!this.activityTypeSelect,
                userSearch: !!this.userSearchInput,
                searchButton: !!this.searchButton
            });
        }
        
        // 드롭다운 옵션 동적 생성
        if (this.activityTypeSelect) {
            console.log('7. 드롭다운 옵션 생성 시작');
            this.renderActivityTypeOptions();
            console.log('   - 드롭다운 옵션 생성 완료');
        } else {
            console.warn('7. activityTypeSelect가 null이므로 드롭다운 옵션 생성 건너뜀');
        }
        
        // 검색 버튼 이벤트 리스너 등록
        if (this.searchButton) {
            console.log('8. 검색 버튼 이벤트 리스너 등록 시작');
            // 기존 이벤트 리스너 제거 후 새로 등록 (중복 방지)
            this.searchButton.replaceWith(this.searchButton.cloneNode(true));
            this.searchButton = this.container.querySelector('.btn-apply-filters');
            this.searchButton.addEventListener('click', () => {
                console.log('[검색 버튼 클릭] 디버깅 시작');
                console.log('  - this.activityTypeSelect:', this.activityTypeSelect);
                console.log('  - this.activityTypeSelect?.value:', this.activityTypeSelect?.value);
                console.log('  - this.activityTypeSelect?.selectedIndex:', this.activityTypeSelect?.selectedIndex);
                if (this.activityTypeSelect) {
                    const selectedOption = this.activityTypeSelect.options[this.activityTypeSelect.selectedIndex];
                    console.log('  - selectedOption:', selectedOption);
                    console.log('  - selectedOption?.value:', selectedOption?.value);
                    console.log('  - selectedOption?.text:', selectedOption?.text);
                }
                console.log('[검색 버튼 클릭] load() 호출');
                this.load(1, this.currentLimit);
            });
            console.log('   - 검색 버튼 이벤트 리스너 등록 완료');
        } else {
            console.warn('8. searchButton이 null이므로 이벤트 리스너 등록 건너뜀');
        }
        
        console.log('=== [ActivityLogManager.init] 디버깅 종료 (성공) ===');
        return true;
    }

    /**
     * 활동 유형 드롭다운 옵션 동적 생성
     */
    renderActivityTypeOptions() {
        if (!this.activityTypeSelect) return;
        
        // 기존 옵션 제거 (-- 전체 -- 제외)
        this.activityTypeSelect.innerHTML = '<option value="">-- 전체 --</option>';
        
        // 카테고리에 맞는 활동 유형 목록 가져오기
        let activityTypes = [];
        if (this.category === 'ALL') {
            // 전체 탭: 모든 활동 유형 표시
            activityTypes = Object.values(CATEGORY_TYPES).flat();
            // 중복 제거
            activityTypes = [...new Set(activityTypes)];
        } else if (CATEGORY_TYPES[this.category]) {
            // 특정 카테고리: 해당 카테고리의 활동 유형만 표시
            activityTypes = CATEGORY_TYPES[this.category];
        }
        
        // 활동 유형 한글 번역 맵
        const activityTypeMap = {
            'TOKEN_CHARGE': '💰 결제/충전',
            'TOKEN_USE': '💸 토큰 사용',
            'TOKEN_GRANT_BY_ADMIN': '🎁 관리자 지급',
            'TOKEN_RESET_BY_ADMIN': '🔄 토큰 초기화',
            'TOKEN_PURCHASE': '💰 토큰 구매',
            'PAYMENT_CANCEL': '↩️ 결제 취소',
            'GRADE_CHANGE': '👑 등급 변경',
            'GRADE_CHANGE_BY_ADMIN': '👑 등급 변경',
            'SUBSCRIPTION_UPDATE': '📋 구독 업데이트',
            'USER_LOGIN': '🔑 로그인',
            'USER_LOGOUT': '🚪 로그아웃',
            'FILE_CONVERT': '📂 파일 변환',
            'PROFILE_UPDATE': '✏️ 프로필 수정',
            'USER_SOFT_DELETE_BY_ADMIN': '🚫 계정 비활성화',
            'USER_RESTORE_BY_ADMIN': '✅ 계정 복구',
            'USER_PURGE_BY_ADMIN': '🗑️ 계정 영구 삭제'
        };
        
        // 옵션 생성
        activityTypes.forEach(type => {
            const label = activityTypeMap[type] || type;
            const option = document.createElement('option');
            option.value = type;
            option.textContent = label;
            this.activityTypeSelect.appendChild(option);
        });
    }

    /**
     * API에서 데이터 가져오기
     * @param {number} page - 페이지 번호
     * @param {number} limit - 페이지당 항목 수
     * @returns {Promise<Object>} API 응답 데이터
     */
    async fetchData(page = 1, limit = 50) {
        console.log('=== [ActivityLogManager.fetchData] 디버깅 시작 ===');
        console.log('1. page:', page, 'limit:', limit);
        console.log('2. this.category:', this.category);
        
        this.currentPage = page;
        this.currentLimit = limit;

        // 필터 값 읽기 (방어적 코딩: optional chain 사용)
        console.log('3. 필터 요소 참조 확인:');
        console.log('   - this.startDateInput:', this.startDateInput);
        console.log('   - this.endDateInput:', this.endDateInput);
        console.log('   - this.activityTypeSelect:', this.activityTypeSelect);
        console.log('   - this.userSearchInput:', this.userSearchInput);
        
        // optional chain을 사용하여 안전하게 값 읽기 (null이면 빈 문자열 반환)
        const startDate = this.startDateInput?.value || '';
        const endDate = this.endDateInput?.value || '';
        const activityType = this.activityTypeSelect?.value || '';
        const userSearch = this.userSearchInput?.value || '';
        
        console.log('4. 필터 값 읽기 결과:');
        console.log('   - startDate:', startDate);
        console.log('   - endDate:', endDate);
        console.log('   - activityType:', activityType);
        console.log('   - userSearch:', userSearch);

    const params = new URLSearchParams({ page, limit });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (activityType) params.append('activity_type', activityType);
    if (userSearch) params.append('user_search', userSearch);
        
        // 카테고리 필터 추가
        if (this.category !== 'ALL') {
            params.append('category', this.category);
        }
        
        console.log('5. 최종 API 파라미터:');
        console.log('   - params.toString():', params.toString());
        console.log('   - 전체 URL:', `/admin/api/activity-logs?${params.toString()}`);

    try {
        const response = await fetch(`/admin/api/activity-logs?${params.toString()}`, {
            headers: { 'X-CSRF-Token': csrfToken() }
        });
        const result = await response.json();
            
            console.log('6. API 응답:');
            console.log('   - response.status:', response.status);
            console.log('   - result.success:', result.success);
            console.log('   - result.data.logs 개수:', result.data?.logs?.length || 0);

        if (!result.success || !result.data.logs) {
                throw new Error(result.error || '알 수 없는 오류');
            }

            console.log('=== [ActivityLogManager.fetchData] 디버깅 종료 (성공) ===');
            return result.data;
        } catch (error) {
            console.error(`[ActivityLogManager] 데이터 가져오기 실패:`, error);
            console.log('=== [ActivityLogManager.fetchData] 디버깅 종료 (실패) ===');
            throw error;
        }
    }

    /**
     * 활동 유형 한글 번역
         * @param {string} activityType - 활동 유형 코드
         * @returns {string} 한글 번역 및 아이콘
         */
    getActivityTypeLabel(activityType) {
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
                'USER_LOGIN': '🔑 로그인',
            'USER_LOGOUT': '🚪 로그아웃',
                'PROFILE_UPDATE': '✏️ 프로필 수정',
            };
            return typeMap[activityType] || activityType;
        }

        /**
         * 활동 유형별 배지 스타일 반환
         * @param {string} activityType - 활동 유형 코드
         * @returns {string} Bootstrap 배지 클래스
         */
    renderActivityTypeBadge(activityType) {
            const badgeMap = {
            'TOKEN_CHARGE': 'bg-success',
            'PAYMENT_CANCEL': 'bg-secondary',
            'GRADE_CHANGE': 'bg-warning text-dark',
                'GRADE_CHANGE_BY_ADMIN': 'bg-warning text-dark',
            'TOKEN_GRANT_BY_ADMIN': 'bg-info',
            'FILE_CONVERT': 'bg-primary',
                'TOKEN_PURCHASE': 'bg-success',
                'TOKEN_RESET_BY_ADMIN': 'bg-danger',
                'USER_SOFT_DELETE_BY_ADMIN': 'bg-secondary',
                'USER_RESTORE_BY_ADMIN': 'bg-success',
                'USER_PURGE_BY_ADMIN': 'bg-danger',
            'USER_LOGIN': 'bg-info',
            'USER_LOGOUT': 'bg-secondary',
            'PROFILE_UPDATE': 'bg-primary',
            };
            return badgeMap[activityType] || 'bg-secondary';
        }

        /**
         * 상세 내용에서 태그 강조 처리
         * @param {string} detailsSummary - 상세 내용 요약
         * @returns {string} 태그가 강조된 HTML
         */
    highlightTags(detailsSummary) {
            if (!detailsSummary) return detailsSummary;
            
            let highlighted = detailsSummary.replace(
                /\(결제\s*(자동|연동)\)/g,
                '<span class="badge bg-success text-white fw-bold">(결제 자동)</span>'
            );
            
            highlighted = highlighted.replace(
                /\(결제\s*취소\/환불\)/g,
                '<span class="badge bg-secondary text-white fw-bold">(결제 취소/환불)</span>'
            );
            
            highlighted = highlighted.replace(
                /\(관리자\s*수동\)/g,
                '<span class="badge bg-info text-white fw-bold">(관리자 수동)</span>'
            );
            
            return highlighted;
        }

    /**
     * 상세 내용 요약 생성
     * @param {Object} log - 로그 객체
     * @param {Object} details - 파싱된 details 객체
     * @returns {string} 상세 내용 요약
     */
    summarizeDetails(log, details) {
        let detailsSummary = '';
        
            switch (log.activity_type) {
                case 'FILE_CONVERT':
                    detailsSummary = `${details.filename} (${details.extracted_rows}건)`;
                    break;
                case 'TOKEN_CHARGE':
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
                case 'PROFILE_UPDATE':
                    if (details.changed_fields_kr && Array.isArray(details.changed_fields_kr) && details.changed_fields_kr.length > 0) {
                        if (details.changed_fields_kr.length === 1) {
                            detailsSummary = `프로필 수정: ${details.changed_fields_kr[0]}`;
                        } else if (details.changed_fields_kr.length <= 3) {
                            detailsSummary = `프로필 수정: ${details.changed_fields_kr.join(', ')}`;
                        } else {
                            const remaining = details.changed_fields_kr.length - 1;
                            detailsSummary = `프로필 수정: ${details.changed_fields_kr[0]} 외 ${remaining}건`;
                        }
                    } else if (details.changed_fields && Array.isArray(details.changed_fields) && details.changed_fields.length > 0) {
                        const fieldNamesKr = {
                            'company_name': '회사명',
                            'representative_name': '대표자명',
                            'phone': '전화번호',
                            'email': '이메일',
                            'address': '주소',
                            'business_type': '업태',
                            'business_category': '종목'
                        };
                        const translatedFields = details.changed_fields.map(field => fieldNamesKr[field] || field);
                        if (translatedFields.length === 1) {
                            detailsSummary = `프로필 수정: ${translatedFields[0]}`;
                        } else if (translatedFields.length <= 3) {
                            detailsSummary = `프로필 수정: ${translatedFields.join(', ')}`;
                        } else {
                            const remaining = translatedFields.length - 1;
                            detailsSummary = `프로필 수정: ${translatedFields[0]} 외 ${remaining}건`;
                        }
                    } else if (details.action) {
                        detailsSummary = details.action;
                    } else {
                        detailsSummary = '프로필 수정';
                    }
                    break;
                default:
                    detailsSummary = '상세 정보 없음';
            }
            
        return this.highlightTags(detailsSummary);
    }

    /**
     * 로그 행 HTML 생성
     * @param {Object} log - 로그 객체
     * @returns {string} HTML 문자열
     */
    renderLogRow(log) {
        const timestamp = new Date(log.timestamp).toLocaleString('ko-KR', { hour12: false });
        const details = log.details ? JSON.parse(log.details) : {};

        // 관리자 표시
        let adminDisplay = (log.performed_by_type === 'ADMIN') ? log.actor_username : 
                           (log.performed_by_type === 'SYSTEM') ? 'system' : '-';

        // 상세 내용 요약
        const detailsSummary = this.summarizeDetails(log, details);

        // 토큰 충전량/사용량 표시
            let chargeDisplay = '';
            let usageDisplay = '';
            const isUnlimited = ['unlimited', 'gold', 'gold-vip'].includes(log.user_plan_snapshot);

            if (log.activity_type === 'TOKEN_RESET_BY_ADMIN') {
                chargeDisplay = '-';
                usageDisplay = '-';
            } else if (log.token_change > 0) {
            chargeDisplay = `+${log.token_change}`;
            } else {
                if (isUnlimited && log.activity_type === 'FILE_CONVERT') {
                    usageDisplay = `무제한사용(${Math.abs(log.potential_cost)})`;
                } else if (log.token_change < 0) {
                usageDisplay = log.token_change;
                }
            }
            
        const translatedActivityType = this.getActivityTypeLabel(log.activity_type);
        const badgeClass = this.renderActivityTypeBadge(log.activity_type);

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
                    <button class="btn btn-sm btn-outline-danger" onclick="ActivityLogManager.deleteLog(${log.id}, '${this.category}')" title="기록 삭제">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
    }

    /**
     * 페이지네이션 HTML 생성
     * @param {Object} pagination - 페이지네이션 정보
     * @returns {string} 페이지네이션 HTML
     */
    renderPagination(pagination) {
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
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="ActivityLogManager.instances['${this.category}'].load(${current_page - 1}, ${items_per_page}); return false;">이전</a></li>`;
        } else {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">이전</span></li>`;
        }
        
        // 페이지 번호 버튼
        const startPage = Math.max(1, current_page - 2);
        const endPage = Math.min(total_pages, current_page + 2);
        
        if (startPage > 1) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="ActivityLogManager.instances['${this.category}'].load(1, ${items_per_page}); return false;">1</a></li>`;
            if (startPage > 2) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === current_page ? 'active' : '';
            paginationHTML += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="ActivityLogManager.instances['${this.category}'].load(${i}, ${items_per_page}); return false;">${i}</a></li>`;
        }
        
        if (endPage < total_pages) {
            if (endPage < total_pages - 1) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="ActivityLogManager.instances['${this.category}'].load(${total_pages}, ${items_per_page}); return false;">${total_pages}</a></li>`;
        }
        
        // 다음 버튼
        if (current_page < total_pages) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="ActivityLogManager.instances['${this.category}'].load(${current_page + 1}, ${items_per_page}); return false;">다음</a></li>`;
        } else {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">다음</span></li>`;
        }
        
        paginationHTML += '</ul></nav>';
        
        paginationHTML += `
            <div class="d-flex justify-content-between align-items-center mt-2">
                <div class="text-muted small">전체 ${total_items}건 (페이지 ${current_page}/${total_pages})</div>
            </div>
        `;
        
        return paginationHTML;
    }

    /**
     * 데이터 로드 및 렌더링
     * @param {number} page - 페이지 번호
     * @param {number} limit - 페이지당 항목 수
     */
    async load(page = 1, limit = 50) {
        // init()은 인스턴스 생성 시 한 번만 호출되므로 여기서는 호출하지 않음
        // DOM 요소가 초기화되지 않은 경우에만 경고
        if (!this.tableContainer) {
            console.error('[ActivityLogManager.load] tableContainer가 초기화되지 않았습니다. init()을 먼저 호출하세요.');
            return;
        }

        this.tableContainer.innerHTML = '<p class="muted">활동 로그를 불러오는 중...</p>';

        try {
            const { logs, pagination } = await this.fetchData(page, limit);

            if (logs.length === 0) {
                this.tableContainer.innerHTML = '<p class="muted">기록된 활동 로그가 없습니다.</p>';
                return;
            }

            const tableRows = logs.map(log => this.renderLogRow(log)).join('');

            const paginationHtml = this.renderPagination(pagination);
        
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
        
            this.tableContainer.innerHTML = tableHtml;

    } catch (error) {
            console.error(`[ActivityLogManager] 로드 실패:`, error);
            this.tableContainer.innerHTML = `<p class="text-danger">데이터를 불러오는 데 실패했습니다: ${error.message}</p>`;
    }
}

/**
     * 정적 메서드: 로그 삭제
 * @param {number} logId - 삭제할 로그 ID
     * @param {string} category - 카테고리 (삭제 후 리로드용)
 */
    static async deleteLog(logId, category = 'ALL') {
    if (!confirm('정말 이 활동 로그를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.')) {
        return;
    }
    
    try {
            const csrfTokenValue = typeof csrfToken === 'function' ? csrfToken() : 
                                   (document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '');
        
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
                throw new Error(errorData.error || `활동 로그 삭제 실패: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            alert('활동 로그가 성공적으로 삭제되었습니다.');
            
                // 해당 카테고리의 Manager 인스턴스로 리로드
                if (ActivityLogManager.instances && ActivityLogManager.instances[category]) {
                    const manager = ActivityLogManager.instances[category];
                    await manager.load(manager.currentPage, manager.currentLimit);
                }
        } else {
                throw new Error(result.error || '활동 로그 삭제에 실패했습니다.');
        }
        
    } catch (error) {
            console.error('[ActivityLogManager.deleteLog] 오류:', error);
        alert(`활동 로그 삭제 중 오류가 발생했습니다: ${error.message}`);
    }
}
}

// Manager 인스턴스 저장소
ActivityLogManager.instances = {};

// 전역 초기화 함수
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== [DOMContentLoaded] 활동 로그 초기화 시작 ===');
    
    // 각 탭별 Manager 인스턴스 생성 (탭 패널 ID를 전달)
    console.log('1. Manager 인스턴스 생성 시작');
    
    console.log('   - ALL 인스턴스 생성 (panel-all)');
    ActivityLogManager.instances['ALL'] = new ActivityLogManager('panel-all', 'ALL');
    console.log('     인스턴스 생성 완료, init() 호출 전');
    if (ActivityLogManager.instances['ALL'].init()) {
        console.log('     init() 성공');
    } else {
        console.error('     init() 실패');
    }
    
    console.log('   - FINANCIAL 인스턴스 생성 (panel-financial)');
    ActivityLogManager.instances['FINANCIAL'] = new ActivityLogManager('panel-financial', 'FINANCIAL');
    console.log('     인스턴스 생성 완료, init() 호출 전');
    if (ActivityLogManager.instances['FINANCIAL'].init()) {
        console.log('     init() 성공');
    } else {
        console.error('     init() 실패');
    }
    
    console.log('   - ACTIVITY 인스턴스 생성 (panel-activity)');
    ActivityLogManager.instances['ACTIVITY'] = new ActivityLogManager('panel-activity', 'ACTIVITY');
    console.log('     인스턴스 생성 완료, init() 호출 전');
    if (ActivityLogManager.instances['ACTIVITY'].init()) {
        console.log('     init() 성공');
    } else {
        console.error('     init() 실패');
    }
    
    console.log('   - SECURITY 인스턴스 생성 (panel-security)');
    ActivityLogManager.instances['SECURITY'] = new ActivityLogManager('panel-security', 'SECURITY');
    console.log('     인스턴스 생성 완료, init() 호출 전');
    if (ActivityLogManager.instances['SECURITY'].init()) {
        console.log('     init() 성공');
    } else {
        console.error('     init() 실패');
    }
    
    console.log('2. 탭 버튼 이벤트 리스너 등록 시작');
    // 탭 클릭 이벤트 리스너
    const tabButtons = document.querySelectorAll('#activity-log-tabs button[data-category]');
    console.log('   - 찾은 탭 버튼 개수:', tabButtons.length);
    tabButtons.forEach((button, index) => {
        const category = button.getAttribute('data-category');
        console.log(`   - 탭 버튼 ${index + 1}: category="${category}"`);
        button.addEventListener('shown.bs.tab', (e) => {
            console.log(`[탭 전환] category="${category}"`);
            const manager = ActivityLogManager.instances[category];
            console.log('   - manager 인스턴스:', manager);
            if (manager) {
                // 탭 전환 시 필터 요소 재참조 및 드롭다운 옵션 재생성
                console.log('   - manager.init() 호출');
                manager.init();
                console.log('   - manager.load() 호출');
                manager.load(1, 50);
            } else {
                console.error(`   - manager 인스턴스를 찾을 수 없음: ${category}`);
            }
        });
    });

    // 필터 적용 버튼 이벤트는 각 Manager의 init()에서 개별적으로 등록됨
    // (각 탭의 필터 버튼이 해당 탭의 Manager에만 연결됨)

    console.log('3. 초기 로드 (전체 탭)');
    // 초기 로드 (전체 탭)
    if (ActivityLogManager.instances['ALL']) {
        console.log('   - ALL 인스턴스 존재 확인, load() 호출');
        ActivityLogManager.instances['ALL'].load(1, 50);
    } else {
        console.error('   - ALL 인스턴스가 존재하지 않음');
    }
    
    console.log('=== [DOMContentLoaded] 활동 로그 초기화 종료 ===');
});

// 하위 호환성을 위한 전역 함수 (기존 코드와의 호환)
window.loadActivityLogs = (page = 1, limit = 50) => {
    const manager = ActivityLogManager.instances['ALL'];
    if (manager) {
        manager.load(page, limit);
    }
};

window.deleteActivityLog = (logId) => {
    ActivityLogManager.deleteLog(logId, 'ALL');
};
