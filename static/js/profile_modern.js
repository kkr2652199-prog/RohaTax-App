/**
 * Profile Modern - 통합 관제실 스타일 JavaScript
 * 단일 데이터 소스 + 필터링 기반 렌더링
 */

// ===== 수정 1: 한글 번역기 탑재 (Dictionary) =====
const MESSAGE_TRANSLATOR = {
    'User logged in successfully': '로그인 성공',
    'User logged out successfully': '로그아웃 성공',
    'User logged out': '로그아웃',
    'Profile updated': '프로필 정보가 수정되었습니다',
    'Account deactivated': '계정 비활성화됨',
    'Account activated': '계정 활성화됨',
    'Token charge': '토큰 충전',
    'Token used': '토큰 사용',
    'File conversion': '파일 변환',
    'Payment success': '결제 성공',
    'Payment failed': '결제 실패',
    'System check': '시스템 점검',
    'Admin granted token': '관리자 토큰 지급',
    'Token reset by admin': '관리자에 의한 토큰 리셋',
    'System': '시스템',
    'Standard 결제 완료': 'Standard 요금제 결제 완료',
    'Premium 결제 완료': 'Premium 요금제 결제 완료',
    'Enterprise 결제 완료': 'Enterprise 요금제 결제 완료'
};

// ===== 수정 2: 탭별 엄격한 '분류 통제' (Strict Filtering) =====
const TAB_CATEGORY_MAP = {
    // 토큰 내역: 돈, 포인트와 관련된 모든 것
    'tokens': [
        'TOKEN_CHARGE', 
        'TOKEN_USE', 
        'FILE_CONVERT', // 파일 변환 시 토큰 사용됨
        'FILE_CONVERSION',
        'TOKEN_GRANT_BY_ADMIN', 
        'TOKEN_RESET', 
        'TOKEN_RESET_BY_ADMIN',
        'TOKEN_REFUND',
        'PAYMENT_SUCCESS',
        'PAYMENT_CANCEL', 
        'PAYMENT_FAILED',
        'GRADE_CHANGE', 
        'SUBSCRIPTION_UPDATE'
    ],
    // 시스템/보안: 계정, 로그인, 개인정보 관련
    'system': [
        'USER_LOGIN', 
        'USER_LOGOUT', 
        'PROFILE_UPDATE', 
        'ACCOUNT_DEACTIVATE', 
        'ACCOUNT_DEACTIVATED',
        'ACCOUNT_RESTORE', 
        'ACCOUNT_ACTIVATED',
        'ACCOUNT_DELETE',
        'SYSTEM'
    ],
    // 전체: 빈 배열이면 필터링 안 함
    'all': []
};

// ===== 수정 3: 드롭다운(유형) 동기화 옵션 맵 =====
const DROPDOWN_OPTIONS_MAP = {
    'tokens': [
        { value: '', text: '전체' },
        { value: 'TOKEN_CHARGE', text: '토큰 충전' },
        { value: 'TOKEN_USE', text: '토큰 사용' },
        { value: 'FILE_CONVERT', text: '파일 변환' },
        { value: 'TOKEN_REFUND', text: '환불/취소' }
    ],
    'system': [
        { value: '', text: '전체' },
        { value: 'USER_LOGIN', text: '회원 로그인' },
        { value: 'USER_LOGOUT', text: '로그아웃' },
        { value: 'PROFILE_UPDATE', text: '정보 수정' },
        { value: 'SYSTEM', text: '시스템' }
    ],
    'all': [
        { value: '', text: '전체' },
        { value: 'USER_LOGIN', text: '회원 로그인' },
        { value: 'TOKEN_CHARGE', text: '토큰 충전' },
        { value: 'TOKEN_USE', text: '토큰 사용' },
        { value: 'FILE_CONVERT', text: '파일 변환' },
        { value: 'PROFILE_UPDATE', text: '정보 수정' },
        { value: 'SYSTEM', text: '시스템' }
    ]
};

// ===== 전역 변수 (State Management) =====
let allActivities = []; // 서버에서 가져온 원본 데이터 저장소
const activityViewState = {
    isLoading: false,
    filters: {
        startDate: '',
        endDate: '',
        type: ''
    },
    pagination: {
        currentPage: 1,
        totalPages: 1,
        totalCount: 0,
        limit: 10
    },
    currentTab: 'all' // 현재 탭 추적용
};

// ===== 유틸리티 함수 =====

/**
 * 활동 유형 한글화
 */
function translateActivityType(activityType) {
    const typeMap = {
        'USER_LOGIN': '회원 로그인',
        'USER_LOGOUT': '로그아웃',
        'TOKEN_CHARGE': '토큰 충전',
        'TOKEN_USE': '토큰 사용',
        'TOKEN_REFUND': '토큰 환불',
        'TOKEN_RESET_BY_ADMIN': '토큰 리셋',
        'TOKEN_GRANT_BY_ADMIN': '관리자 지급',
        'PROFILE_UPDATE': '프로필 수정',
        'FILE_CONVERSION': '파일 변환',
        'FILE_CONVERT': '파일 변환',
        'PAYMENT_SUCCESS': '결제 성공',
        'PAYMENT_FAILED': '결제 실패',
        'ACCOUNT_DEACTIVATED': '계정 비활성화',
        'ACCOUNT_ACTIVATED': '계정 활성화',
        'SYSTEM': '시스템'
    };
    return typeMap[activityType] || activityType;
}

/**
 * 상세 정보 파싱 및 번역 (개조됨)
 */
function parseDetails(details, activityType) {
    if (!details) return '세부 정보 없음';
    
    // 1. JSON 파싱 시도
    let parsedData = details;
    if (typeof details === 'string') {
        // 이미 객체처럼 보이지 않는 단순 문자열이면 번역기 돌리기
        if (!details.trim().startsWith('{') && !details.trim().startsWith('[')) {
            return MESSAGE_TRANSLATOR[details] || details;
        }
        try {
            parsedData = JSON.parse(details);
        } catch (e) {
            // 파싱 실패시 문자열 정리 후 번역 시도
            const cleaned = details.replace(/[{}[\]]/g, '').replace(/"/g, '').replace(/:/g, ': ').trim();
            return MESSAGE_TRANSLATOR[cleaned] || cleaned;
        }
    }
    
    // 2. 파일 변환 특수 처리 (파일명 + 건수)
    if (activityType === 'FILE_CONVERT' || activityType === 'FILE_CONVERSION') {
        if (parsedData.filename) {
            const count = parsedData.count || parsedData.extracted_rows || parsedData.file_count || 0;
            // "세금계산서...xlsx (53건)"
            return `${parsedData.filename} <span class="fw-bold text-primary">(${count}건)</span>`;
        }
    }

    // 3. 메시지 번역 적용
    if (parsedData.message) {
        return MESSAGE_TRANSLATOR[parsedData.message] || parsedData.message;
    }
    if (parsedData.reason) return `사유: ${parsedData.reason}`;
    
    if (parsedData.product_name) {
        // Welcome Event를 회원가입 토큰이벤트로 변환
        // Welcome Period를 회원가입 무제한이벤트로 변환
        let productName = parsedData.product_name;
        const productNameLower = productName.toLowerCase();
        if (productName === 'Welcome Event' || productNameLower === 'welcome event') {
            productName = '회원가입 토큰이벤트';
        } else if (productName === 'Welcome Period' || productName === 'Welcome Period Event' || 
                   productNameLower === 'welcome period' || productNameLower === 'welcome period event' ||
                   productNameLower.includes('welcome period')) {
            productName = '회원가입 무제한이벤트';
        }
        const amount = parsedData.amount ? `(${parseInt(parsedData.amount).toLocaleString('ko-KR')}원)` : '';
        return `${productName} ${amount}`.trim();
    }
    
    // 4. 기타 키 찾기
    const meaningfulKeys = ['message', 'reason', 'filename', 'description', 'note', 'info'];
    for (const key of meaningfulKeys) {
        if (parsedData[key]) {
            return String(parsedData[key]);
        }
    }
    
    // 5. 첫 번째 값 사용
    const firstValue = Object.values(parsedData)[0];
    if (firstValue && typeof firstValue !== 'object') {
        return String(firstValue);
    }
    
    return '세부 정보 없음';
}

/**
 * 토큰 수량 포맷팅 (-1 -> 무제한)
 */
function formatTokenAmount(amount) {
    if (amount === -1 || amount === '-1') {
        return '무제한';
    }
    const numAmount = parseInt(amount) || 0;
    return numAmount.toLocaleString('ko-KR');
}

/**
 * HTML 안전 문자 변환
 */
function sanitizeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return String(text ?? '').replace(/[&<>"']/g, char => map[char]);
}

function formatDateInputValue(dateObj) {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function ensureDefaultActivityFilters() {
    const today = new Date();
    const past = new Date();
    past.setDate(today.getDate() - 29);

    if (!activityViewState.filters.startDate) {
        activityViewState.filters.startDate = formatDateInputValue(past);
    }
    if (!activityViewState.filters.endDate) {
        activityViewState.filters.endDate = formatDateInputValue(today);
    }

    const startInput = document.getElementById('filter-start-date');
    const endInput = document.getElementById('filter-end-date');

    if (startInput && !startInput.value) {
        startInput.value = activityViewState.filters.startDate;
    }
    if (endInput && !endInput.value) {
        endInput.value = activityViewState.filters.endDate;
    }
}

// ===== 데이터 로딩 (Single Fetch) =====

/**
 * 토큰 상태 로드 (상단 3개 카드용)
 */
async function loadTokenStatus() {
    console.log('[DEBUG] ===== 토큰 상태 로드 함수 시작 =====');
    console.log('[DEBUG] API 호출 시작: /api/v2/user/token-summary');
    console.log('[DEBUG] 현재 시간:', new Date().toISOString());
    
    try {
        console.log('[DEBUG] fetch() 호출 직전...');
        const response = await fetch('/api/v2/user/token-summary');
        console.log('[DEBUG] fetch() 완료. 응답 상태:', response.status, response.statusText);
        console.log('[DEBUG] 응답 헤더:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            console.error('[CRITICAL] HTTP 에러 발생:', response.status, response.statusText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        console.log('[DEBUG] JSON 파싱 시작...');
        const result = await response.json();
        console.log('[DEBUG] 응답 도착 (전체):', JSON.stringify(result, null, 2));
        console.log('[DEBUG] result 타입:', typeof result);
        console.log('[DEBUG] result.success:', result.success);
        console.log('[DEBUG] result.data 타입:', typeof result.data);
        console.log('[DEBUG] result.data:', result.data);
        
        if (!result.success || !result.data) {
            console.error('[CRITICAL] API 응답 실패:', result.message || result.error || '알 수 없는 오류');
            console.error('[CRITICAL] result 객체 전체:', result);
            // 기본값 표시
            updateTokenDisplay(0, 0, 0);
            return;
        }
        
        console.log('[DEBUG] 데이터 추출 시도...');
        const data = result.data;
        console.log('[DEBUG] data 객체:', data);
        console.log('[DEBUG] data.total_tokens:', data.total_tokens, '타입:', typeof data.total_tokens);
        console.log('[DEBUG] data.used_tokens:', data.used_tokens, '타입:', typeof data.used_tokens);
        console.log('[DEBUG] data.available_tokens:', data.available_tokens, '타입:', typeof data.available_tokens);
        
        // API 응답 필드명 확인: total_tokens, used_tokens, available_tokens
        const totalTokens = Number.parseInt(data.total_tokens) || 0;
        const usedTokens = Number.parseInt(data.used_tokens) || 0;
        const availableTokens = Number.parseInt(data.available_tokens) || 0;
        
        console.log('[DEBUG] 파싱된 값:', { 
            totalTokens, 
            usedTokens, 
            availableTokens,
            rawData: {
                total_tokens: data.total_tokens,
                used_tokens: data.used_tokens,
                available_tokens: data.available_tokens
            }
        });
        
        console.log('[DEBUG] DOM 업데이트 시작. 타겟 요소 확인...');
        const totalEl = document.getElementById('total-tokens-display');
        const usedEl = document.getElementById('tokens-used-display');
        const availableEl = document.getElementById('available-tokens-display');
        console.log('[DEBUG] total-tokens-display 요소:', totalEl ? '찾음' : '없음');
        console.log('[DEBUG] tokens-used-display 요소:', usedEl ? '찾음' : '없음');
        console.log('[DEBUG] available-tokens-display 요소:', availableEl ? '찾음' : '없음');
        
        // UI 업데이트
        updateTokenDisplay(totalTokens, usedTokens, availableTokens);
        console.log('[DEBUG] ===== 토큰 상태 로드 함수 완료 =====');
        
    } catch (error) {
        console.error('[CRITICAL] ===== 토큰 상태 로드 중 에러 발생 =====');
        console.error('[CRITICAL] 에러 타입:', error.constructor.name);
        console.error('[CRITICAL] 에러 메시지:', error.message);
        console.error('[CRITICAL] 에러 스택:', error.stack);
        console.error('[CRITICAL] 에러 객체 전체:', error);
        // 에러 발생 시 기본값 표시
        updateTokenDisplay(0, 0, 0);
    }
}

/**
 * 토큰 표시 업데이트
 */
function updateTokenDisplay(total, used, available) {
    const totalEl = document.getElementById('total-tokens-display');
    const usedEl = document.getElementById('tokens-used-display');
    const availableEl = document.getElementById('available-tokens-display');
    
    if (totalEl) {
        totalEl.textContent = total.toLocaleString('ko-KR');
        console.log('[토큰 표시] total-tokens-display 업데이트:', total.toLocaleString('ko-KR'));
    } else {
        console.warn('[토큰 표시] total-tokens-display 요소를 찾을 수 없습니다.');
    }
    
    if (usedEl) {
        usedEl.textContent = used.toLocaleString('ko-KR');
        console.log('[토큰 표시] tokens-used-display 업데이트:', used.toLocaleString('ko-KR'));
    } else {
        console.warn('[토큰 표시] tokens-used-display 요소를 찾을 수 없습니다.');
    }
    
    if (availableEl) {
        availableEl.textContent = available.toLocaleString('ko-KR');
        console.log('[토큰 표시] available-tokens-display 업데이트:', available.toLocaleString('ko-KR'));
    } else {
        console.warn('[토큰 표시] available-tokens-display 요소를 찾을 수 없습니다.');
    }
    
    console.log('[토큰 표시] UI 업데이트 완료:', { total, used, available });
}

/**
 * 활동 내역 데이터 로드
 * @param {{page?:number, resetPage?:boolean}} options
 */
async function loadActivityLogs(options = {}) {
    console.log('[CCTV] loadActivityLogs 실행 시작. 현재 탭:', activityViewState.currentTab); // CCTV 추가
    console.log('[DEBUG] ===== 활동 내역 로드 함수 시작 =====');
    console.log('[DEBUG] 현재 시간:', new Date().toISOString());
    console.log('[DEBUG] 옵션:', options);

    if (options.resetPage) {
        activityViewState.pagination.currentPage = 1;
    }
    if (typeof options.page === 'number') {
        activityViewState.pagination.currentPage = Math.max(1, options.page);
    }

    ensureDefaultActivityFilters();

    if (activityViewState.isLoading) {
        console.warn('[DEBUG] 중복 요청 방지 - 이미 로딩 중입니다.');
        return;
    }

    const tabPane = document.getElementById('tab-content-all');
    const container = tabPane?.querySelector('.activity-table-body-target');

    if (!tabPane || !container) {
        console.error('[CRITICAL] 전체 활동 탭 패널 또는 컨테이너를 찾을 수 없습니다.');
        return;
    }

    activityViewState.isLoading = true;
    console.log('[DEBUG] activityViewState.isLoading = true');

    container.innerHTML = `
        <tr class="activity-loading-row">
            <td colspan="5">
                <div class="activity-loading">
                    <div class="loading-spinner"></div>
                    <p class="loading-text">데이터를 불러오는 중입니다...</p>
                </div>
            </td>
        </tr>
    `;

    try {
        const params = new URLSearchParams({
            page: activityViewState.pagination.currentPage,
            limit: activityViewState.pagination.limit
        });

        if (activityViewState.filters.startDate) {
            params.set('start_date', activityViewState.filters.startDate);
        }
        if (activityViewState.filters.endDate) {
            params.set('end_date', activityViewState.filters.endDate);
        }
        
        // [수정 2] 탭별 페이지네이션 정확성 보장
        // 사용자가 명시적으로 선택한 필터가 있으면 그것을 우선 사용
        // 없으면 현재 탭의 카테고리 전체를 전송 (서버 사이드 필터링 유도)
        let typeToSend = activityViewState.filters.type;
        
        if (!typeToSend || typeToSend === 'all') {
            const currentTab = activityViewState.currentTab || 'all';
            const tabTypes = TAB_CATEGORY_MAP[currentTab];
            
            if (tabTypes && tabTypes.length > 0) {
                typeToSend = tabTypes.join(',');
            } else {
                typeToSend = ''; // 'all' 탭이거나 매핑 없을 때
            }
        }
        
        if (typeToSend) {
            params.set('type', typeToSend);
        }

        const query = params.toString();
        console.log('[DEBUG] API 호출:', `/api/v2/user/activity-logs?${query}`);
        const response = await fetch(`/api/v2/user/activity-logs?${query}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('[DEBUG] 활동 로그 응답:', result);
        
        // [GEMINI_DEBUG] 데이터 구조 확인용 CCTV
        console.log('[GEMINI_DEBUG] 전체 응답:', result);
        console.log('[GEMINI_DEBUG] 데이터 타입:', typeof result.data);
        console.log('[GEMINI_DEBUG] 로그 배열:', result.data?.logs);
        console.log('[GEMINI_DEBUG] 배열 길이:', result.data?.logs?.length);

        container.innerHTML = '';

        if (!result.success) {
            container.innerHTML = `
                <tr class="activity-empty-row">
                    <td colspan="5">
                        <div class="activity-empty">
                            <div class="activity-empty-icon">⚠️</div>
                            <p class="activity-empty-text">거래 내역을 불러오는 데 실패했습니다.</p>
                        </div>
                    </td>
                </tr>
            `;
            allActivities = [];
            updateActivityPaginationUI();
            return;
        }

        let logs = [];
        let pagination = {};

        if (Array.isArray(result.data)) {
            // Case 1: 백엔드가 그냥 배열을 준 경우
            logs = result.data;
            console.log('[DEBUG] 데이터 구조: 단순 배열 감지');
            pagination = {}; // 단순 배열인 경우 페이지네이션 정보 없음
        } else if (result.data && Array.isArray(result.data.logs)) {
            // Case 2: 백엔드가 v2 구조(logs 키)를 준 경우
            logs = result.data.logs;
            pagination = result.data.pagination || {};
            console.log('[DEBUG] 데이터 구조: v2 객체 감지');
        } else {
            console.error('[CRITICAL] 알 수 없는 데이터 구조:', result.data);
            logs = [];
        }

        // 최신순 강제 정렬 (내림차순)
        logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        allActivities = logs;
        activityViewState.pagination.totalCount = pagination.total_count ?? logs.length;
        activityViewState.pagination.totalPages = pagination.total_pages
            || Math.max(1, Math.ceil(activityViewState.pagination.totalCount / activityViewState.pagination.limit));
        activityViewState.pagination.currentPage = pagination.current_page || activityViewState.pagination.currentPage;
        activityViewState.pagination.limit = pagination.limit || activityViewState.pagination.limit;
        activityViewState.pagination.currentPage = Math.min(
            Math.max(1, activityViewState.pagination.currentPage),
            activityViewState.pagination.totalPages
        );

        if (logs.length === 0) {
            container.innerHTML = `
                <tr class="activity-empty-row">
                    <td colspan="5">
                        <div class="activity-empty">
                            <div class="activity-empty-icon">📭</div>
                            <p class="activity-empty-text">거래 내역이 없습니다.</p>
                        </div>
                    </td>
                </tr>
            `;
        }

        if (!Array.isArray(logs)) {
            console.error('[CRITICAL] logs가 배열이 아닙니다:', logs);
            container.innerHTML = `
                <tr class="activity-empty-row">
                    <td colspan="5">
                        <div class="activity-empty">
                            <div class="activity-empty-icon">⚠️</div>
                            <p class="activity-empty-text">데이터 형식이 올바르지 않습니다.</p>
                        </div>
                    </td>
                </tr>
            `;
            allActivities = [];
            updateActivityPaginationUI();
            return;
        }

        // 수정 3: 현재 탭 기반 렌더링 (Smart Rendering)
        // 모든 탭을 다 그리는 대신, 현재 사용자가 보고 있는 탭을 우선적으로 그림
        const currentTab = activityViewState.currentTab || 'all';
        console.log(`[DEBUG] 현재 활성 탭(${currentTab}) 렌더링 시작`);
        
        // 1. 현재 탭 즉시 렌더링
        renderList(currentTab);
        
        // 2. 나머지 탭들은 데이터 동기화를 위해 백그라운드 렌더링 (선택 사항)
        // UX상 다른 탭 눌렀을 때 이미 로딩되어 있으면 좋으므로 다 그려두는 것이 좋음.
        // 단, 'gold' 탭은 별도 로직이므로 제외
        ['all', 'tokens', 'system'].forEach(tab => {
            if (tab !== currentTab) {
                renderList(tab);
            }
        });

        updateActivityPaginationUI();
        console.log('[DEBUG] ===== 활동 내역 로드 함수 완료 =====');
    } catch (error) {
        console.error('[CRITICAL] 활동 내역 로드 중 오류:', error);
        container.innerHTML = `
            <tr class="activity-empty-row">
                <td colspan="5">
                    <div class="activity-empty">
                        <div class="activity-empty-icon">❌</div>
                        <p class="activity-empty-text">네트워크 오류가 발생했습니다.</p>
                    </div>
                </td>
            </tr>
        `;
        allActivities = [];
    } finally {
        activityViewState.isLoading = false;
        updateActivityPaginationUI();
    }
}

function updateActivityPaginationUI() {
    const infoEl = document.getElementById('activity-page-info');
    const prevBtn = document.getElementById('activity-page-prev');
    const nextBtn = document.getElementById('activity-page-next');

    if (!infoEl && !prevBtn && !nextBtn) {
        return;
    }

    const { currentPage, totalPages, totalCount } = activityViewState.pagination;
    if (infoEl) {
        infoEl.textContent = `${currentPage} / ${totalPages} (${totalCount.toLocaleString('ko-KR')}건)`;
    }
    if (prevBtn) {
        prevBtn.disabled = activityViewState.isLoading || currentPage <= 1;
    }
    if (nextBtn) {
        nextBtn.disabled = activityViewState.isLoading || currentPage >= totalPages;
    }
}

function initActivityFilterBar() {
    // 기본값 설정 (입력창이 있을 때만)
    ensureDefaultActivityFilters();
    
    // 이미 전역 리스너가 등록되었다면 중복 실행 방지
    if (window.isGlobalFilterInitialized) {
        console.log('[DEBUG] 필터바 리스너는 이미 등록되어 있습니다.');
        return true;
    }

    console.log('[DEBUG] 필터바 전역 이벤트 리스너 등록 시작');

    // 1. 검색 버튼 클릭 이벤트 위임 (Event Delegation)
    document.addEventListener('click', function(e) {
        const applyBtn = e.target.closest('#btn-apply-filter');
        if (applyBtn) {
            console.log('[CCTV] 검색 버튼이 물리적으로 클릭되었습니다!'); // CCTV 추가
            
            // 현재 입력값 가져오기
            const startInput = document.getElementById('filter-start-date');
            const endInput = document.getElementById('filter-end-date');
            const typeSelect = document.getElementById('filter-type');

            activityViewState.filters.startDate = startInput?.value || '';
            activityViewState.filters.endDate = endInput?.value || '';
            activityViewState.filters.type = typeSelect?.value || '';
            
            loadActivityLogs({ resetPage: true });
        }
    });

    // 2. 입력창 엔터키 이벤트 위임
    document.addEventListener('keydown', function(e) {
        if (e.key !== 'Enter') return;

        const target = e.target;
        if (target.matches('#filter-start-date, #filter-end-date, #filter-type')) {
            console.log('[DEBUG] 필터 입력창에서 엔터키 감지');
            e.preventDefault();
            
            // 검색 로직 실행
            const startInput = document.getElementById('filter-start-date');
            const endInput = document.getElementById('filter-end-date');
            const typeSelect = document.getElementById('filter-type');

            activityViewState.filters.startDate = startInput?.value || '';
            activityViewState.filters.endDate = endInput?.value || '';
            activityViewState.filters.type = typeSelect?.value || '';
            
            loadActivityLogs({ resetPage: true });
        }
    });

    // 3. 드롭다운 변경 감지 위임
    document.addEventListener('change', function(e) {
        if (e.target.matches('#filter-type')) {
            console.log('[DEBUG] 유형 드롭다운 변경 감지');
            activityViewState.filters.type = e.target.value || '';
            loadActivityLogs({ resetPage: true });
        }
    });

    // 4. 페이지네이션 버튼 위임 (기존 로직 통합)
    if (!window.paginationListenerAdded) {
        document.addEventListener('click', function(e) {
            const prevBtn = e.target.closest('#activity-page-prev');
            const nextBtn = e.target.closest('#activity-page-next');
            
            if (prevBtn && !prevBtn.disabled) {
                if (activityViewState.pagination.currentPage > 1) {
                    loadActivityLogs({ page: activityViewState.pagination.currentPage - 1 });
                }
            }
            
            if (nextBtn && !nextBtn.disabled) {
                if (activityViewState.pagination.currentPage < activityViewState.pagination.totalPages) {
                    loadActivityLogs({ page: activityViewState.pagination.currentPage + 1 });
                }
            }
        });
        window.paginationListenerAdded = true;
    }

    window.isGlobalFilterInitialized = true;
    updateActivityPaginationUI();
    return true;
}

/**
 * 상세 내역 모달 띄우기 (결제 관리 영수증 스타일 - 완전 동일)
 */
function showActivityDetailsModal(encodedDetails, date) {
    const modalEl = document.getElementById('activityDetailModal');
    const contentEl = document.getElementById('detail-modal-content');
    const headerEl = document.getElementById('activity-receipt-header');
    const subtitleEl = document.getElementById('activity-receipt-subtitle');

    if (!modalEl || !contentEl) {
        console.error('[CRITICAL] 상세 모달 요소를 찾을 수 없습니다.');
        alert('상세 내용을 표시할 수 없습니다. (모달 누락)');
        return;
    }

    let data = {};
    let activityType = '';
    
    if (!encodedDetails) {
        data = { '내용': '세부 정보가 없습니다.' };
    } else {
        try {
            const decoded = decodeURIComponent(encodedDetails);
            data = JSON.parse(decoded);
            activityType = data.activity_type || data.type || '';
            
            // activity_type이 없으면 데이터에서 추출 시도
            if (!activityType && decoded) {
                // 문자열에서 activity_type 패턴 찾기
                const activityTypeMatch = decoded.match(/activity_type["\s]*[:=]["\s]*([^",}\s]+)/i);
                if (activityTypeMatch) {
                    activityType = activityTypeMatch[1];
                    data.activity_type = activityType;
                }
            }
        } catch (e) {
            // JSON 파싱 실패 시, 문자열에서 정보 추출 시도
            try {
                const decoded = decodeURIComponent(encodedDetails);
                
                // activity_type 추출 시도
                const activityTypeMatch = decoded.match(/activity_type["\s]*[:=]["\s]*([^",}\s]+)/i) ||
                                        decoded.match(/GRADE_CHANGE|TOKEN_CHARGE|PAYMENT|LOGIN|LOGOUT|PROFILE/i);
                if (activityTypeMatch) {
                    activityType = activityTypeMatch[1] || activityTypeMatch[0];
                }
                
                // 등급 변경 정보 추출
                const oldPlanMatch = decoded.match(/변경\s*전\s*등급\s*(\w+)/i) || decoded.match(/old_plan["\s]*[:=]["\s]*([^",}\s]+)/i);
                const newPlanMatch = decoded.match(/변경\s*후\s*등급\s*(\w+)/i) || decoded.match(/new_plan["\s]*[:=]["\s]*([^",}\s]+)/i);
                const reasonMatch = decoded.match(/사유[:\s]+([^activity_type]+)/i) || decoded.match(/reason["\s]*[:=]["\s]*([^",}]+)/i);
                
                data = {
                    '내용': decoded,
                    activity_type: activityType || 'UNKNOWN'
                };
                
                if (oldPlanMatch) data.old_plan = oldPlanMatch[1];
                if (newPlanMatch) data.new_plan = newPlanMatch[1];
                if (reasonMatch) data.reason = reasonMatch[1].trim();
            } catch (_) {
                data = { 
                    '내용': encodedDetails,
                    activity_type: ''
                };
            }
        }
    }

    // 헤더 색상 고정 (관리자 페이지와 100% 동일)
    if (headerEl) {
        headerEl.style.background = 'linear-gradient(135deg, #10B981 0%, #059669 100%)';
    }
    if (subtitleEl) {
        subtitleEl.textContent = 'Payment Receipt';
    }

    // ===== 사용자 정보 가져오기 (모든 영수증에 유저명 표시를 위해) =====
    const fetchUserInfo = async () => {
        try {
            const response = await fetch('/api/user-info', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.getCSRFToken ? window.getCSRFToken() : ''
                },
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    const userData = result.data.user || result.data;
                    if (userData) {
                        // username과 email을 data 객체에 추가
                        if (userData.username) {
                            data.username = userData.username;
                        }
                        if (userData.email) {
                            data.email = userData.email;
                        }
                        // subscription_end_date도 추가 (Gold 상품용)
                        if (userData.subscription_end_date) {
                            data.subscription_end_date = userData.subscription_end_date;
                        }
                        // free_trial_expired_at도 추가 (기간제 이벤트용)
                        if (userData.free_trial_expired_at) {
                            data.free_trial_expired_at = userData.free_trial_expired_at;
                        }
                        // 무료 토큰 이벤트 기간 정보 (관리자 일반 사용자 관리 화면과 동일)
                        if (userData.token_event_start_date) {
                            data.token_event_start_date = userData.token_event_start_date;
                        }
                        if (userData.token_event_expires_at) {
                            data.token_event_expires_at = userData.token_event_expires_at;
                        }
                    }
                }
            }
        } catch (e) {
            console.warn('[showActivityDetailsModal] 사용자 정보 조회 실패:', e);
        }
    };

    // ===== 활동 유형별 맞춤 렌더링 함수 =====
    const renderByActivityType = () => {
        console.log('[showActivityDetailsModal] activityType:', activityType, 'data keys:', Object.keys(data));
        
        // 등급 변경 데이터가 있지만 activityType이 없는 경우도 처리 (우선순위 높임)
        if ((data.old_plan || data.from_plan) && (data.new_plan || data.to_plan)) {
            console.log('[showActivityDetailsModal] 등급 변경 영수증 렌더링 (데이터 기반)');
            return renderGradeChangeReceipt(data, date);
        }
        
        // activityType이 없으면 기본 영수증 반환
        if (!activityType) {
            console.log('[showActivityDetailsModal] activityType 없음, 기본 영수증 렌더링');
            return renderDefaultReceipt(data, date, activityType);
        }
        
        // 1. 결제 관련 (PAYMENT_SUCCESS, PAYMENT_CANCEL, PAYMENT_REFUND)
        if (activityType.includes('PAYMENT')) {
            console.log('[showActivityDetailsModal] 결제 영수증 렌더링');
            return renderPaymentReceipt(data, date);
        }
        
        // 2. 토큰 충전 (TOKEN_CHARGE, TOKEN_GRANT_BY_ADMIN)
        if (activityType.includes('TOKEN_CHARGE') || activityType.includes('TOKEN_GRANT')) {
            console.log('[showActivityDetailsModal] 토큰 충전 영수증 렌더링');
            // Gold 상품이거나 기간제 이벤트이고 subscription_end_date 또는 free_trial_expired_at이 없으면 비동기로 사용자 정보 가져오기
            const tokenAmount = data.charge_token_amount || data.token_amount || data.token_change || 0;
            const isUnlimited = tokenAmount === -1 || tokenAmount === '-1';
            const productName = data.product_name || '';
            const productNameLower = productName.toLowerCase();
            const isPeriodEvent = productName === 'Welcome Period' || productName === 'Welcome Period Event' || 
                                  productNameLower === 'welcome period' || productNameLower === 'welcome period event' ||
                                  productNameLower.includes('welcome period');
            
            // Gold 상품이거나 기간제 이벤트인 경우 사용자 정보 가져오기
            if ((isUnlimited && !data.subscription_end_date) || (isPeriodEvent && !data.free_trial_expired_at)) {
                renderTokenChargeReceiptAsync(data, date, contentEl);
                return '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2 text-muted">영수증 정보를 불러오는 중...</p></div>';
            }
            return renderTokenChargeReceipt(data, date);
        }
        
        // 2-1. 토큰 리셋 (TOKEN_RESET_BY_ADMIN)
        if (activityType.includes('TOKEN_RESET')) {
            console.log('[showActivityDetailsModal] 토큰 리셋 영수증 렌더링');
            return renderTokenResetReceipt(data, date);
        }
        
        // 3. 토큰 사용 (TOKEN_USE, FILE_CONVERT)
        if (activityType.includes('TOKEN_USE') || activityType.includes('FILE_CONVERT')) {
            console.log('[showActivityDetailsModal] 토큰 사용 영수증 렌더링');
            return renderTokenUseReceipt(data, date, activityType);
        }
        
        // 4. 토큰 환불 (TOKEN_REFUND, PAYMENT_CANCEL)
        if (activityType.includes('TOKEN_REFUND') || activityType.includes('REFUND')) {
            console.log('[showActivityDetailsModal] 토큰 환불 영수증 렌더링');
            return renderTokenRefundReceipt(data, date);
        }
        
        // 5. 등급 변경 (GRADE_CHANGE)
        if (activityType.includes('GRADE')) {
            console.log('[showActivityDetailsModal] 등급 변경 영수증 렌더링');
            return renderGradeChangeReceipt(data, date);
        }
        
        // 6. 프로필 수정 (PROFILE_UPDATE)
        if (activityType.includes('PROFILE')) {
            console.log('[showActivityDetailsModal] 프로필 수정 영수증 렌더링');
            return renderProfileUpdateReceipt(data, date);
        }
        
        // 7. 로그인/로그아웃 (USER_LOGIN, USER_LOGOUT, LOGIN, LOGOUT)
        if (activityType.includes('LOGIN') || activityType.includes('LOGOUT')) {
            console.log('[showActivityDetailsModal] 로그인 영수증 렌더링');
            return renderLoginReceipt(data, date, activityType);
        }
        
        // 8. 기타 (기본 영수증)
        console.log('[showActivityDetailsModal] 기본 영수증 렌더링');
        return renderDefaultReceipt(data, date, activityType);
    };

    // ===== 유저명과 이메일을 렌더링하는 헬퍼 함수 =====
    function renderUserAndEmail(data) {
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        return `
            <tr>
                <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
            </tr>
        `;
    }

    // ===== 결제 영수증 렌더링 =====
    function renderPaymentReceipt(data, date) {
        let productName = data.product_name || '알 수 없음';
        // Welcome Event / Welcome Period 한글 변환 및 이벤트 플래그 설정
        const originalProductName = productName;
        const productNameLower = productName.toLowerCase();
        let isTokenEvent = false;     // 회원가입 토큰이벤트
        let isPeriodEvent = false;    // 회원가입 무제한이벤트

        if (productName === 'Welcome Event' || productNameLower === 'welcome event') {
            productName = '회원가입 토큰이벤트';
            isTokenEvent = true;
        } else if (productName === 'Welcome Period' || productName === 'Welcome Period Event' || 
                   productNameLower === 'welcome period' || productNameLower === 'welcome period event' ||
                   productNameLower.includes('welcome period')) {
            productName = '회원가입 무제한이벤트';
            isPeriodEvent = true;
        }

        const amount = data.amount || 0;
        const orderId = data.order_id || '';
        let paymentMethod = data.payment_method || data.method || '수동 결제';
        const status = data.status || 'completed';
        
        // 결제수단: 이벤트인 경우 빨간색 "1회 이용권 사용" (금액과 무관하게)
        if (isTokenEvent || isPeriodEvent) {
            paymentMethod = '<span style="color: #dc2626; font-weight: 600;">1회 이용권 사용</span>';
        }

        // 상태 배지
        const getStatusBadge = (status) => {
            // 이벤트 + 완료 상태인 경우 텍스트 변경 (금액과 무관하게)
            if ((isTokenEvent || isPeriodEvent) && status === 'completed') {
                if (isTokenEvent) {
                    return '<span class="badge bg-success">이벤트 토큰 사용가능</span>';
                } else if (isPeriodEvent) {
                    return '<span class="badge bg-success">이벤트 무제한 사용가능</span>';
                }
            }
            const statusMap = {
                'completed': '<span class="badge bg-success">완료</span>',
                'pending': '<span class="badge bg-warning">대기</span>',
                'cancelled': '<span class="badge bg-danger">취소</span>',
                'failed': '<span class="badge bg-secondary">실패</span>'
            };
            return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
        };
        
        // 총액 표시: 이벤트인 경우 "이벤트"로 표시 (금액과 무관하게)
        const totalDisplay = (isTokenEvent || isPeriodEvent)
            ? '이벤트'
            : (amount === 0 ? '무료' : `₩ ${amount.toLocaleString('ko-KR')}`);
        
        // 이용 기간 계산 (구독 상품인 경우)
        let subscriptionInfo = '';
        if (data.subscription_end_date || data.free_trial_expired_at) {
            const endDate = data.subscription_end_date ? new Date(data.subscription_end_date) : 
                          data.free_trial_expired_at ? new Date(data.free_trial_expired_at) : null;
            const startDate = date ? new Date(date) : new Date();
            
            if (endDate) {
                const diffTime = endDate.getTime() - startDate.getTime();
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                
                // 날짜 포맷 개선: YYYY. MM. DD 형식
                const startLabel = startDate.toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                }).replace(/\./g, '.').replace(/\s+/g, ' ').trim();
                const endLabel = endDate.toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                }).replace(/\./g, '.').replace(/\s+/g, ' ').trim();
                
                // 만료일 포맷: YYYY. MM. DD HH:MM
                const expiredDateStr = endDate.toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                }).replace(/\./g, '.').replace(/\s+/g, ' ').trim();
                const expiredTimeStr = endDate.toLocaleTimeString('ko-KR', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                });
                
                subscriptionInfo = `
                    <tr>
                        <td class="text-muted" style="padding: 0.5rem 0;">이용 기간</td>
                        <td style="padding: 0.5rem 0;">
                            <div style="margin-bottom: 0.25rem;">
                                <strong style="font-size: 1rem; color: #1f2937;">${startLabel} ~ ${endLabel}</strong>
                                <span style="color: #6b7280; font-size: 0.9rem; margin-left: 0.5rem;">(${diffDays}일)</span>
                            </div>
                            <small class="text-success" style="font-size: 0.85rem;">만료일: ${expiredDateStr} ${expiredTimeStr}</small>
                        </td>
                    </tr>
                `;
            }
        }
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        ${orderId ? `<tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">주문번호</td>
                            <td style="padding: 0.5rem 0;"><code class="text-primary fw-bold">${orderId}</code></td>
                        </tr>` : ''}
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">유저명</td>
                            <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">상품명</td>
                            <td style="padding: 0.5rem 0;"><strong>${productName}</strong></td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">결제일시</td>
                            <td style="padding: 0.5rem 0;">${date || '알 수 없음'}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">결제수단</td>
                            <td style="padding: 0.5rem 0;">${paymentMethod}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">상태</td>
                            <td style="padding: 0.5rem 0;">${getStatusBadge(status)}</td>
                        </tr>
                        ${subscriptionInfo}
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${totalDisplay}</span>
                </div>
            </div>
        `;
    }

    // ===== 토큰 충전 영수증 렌더링 (관리자 결제 관리 영수증과 100% 동일 구조) =====
    function renderTokenChargeReceipt(data, date) {
        const tokenAmount = data.charge_token_amount || data.token_amount || data.token_change || 0;
        const orderId = data.order_id || '';
        const isUnlimited = tokenAmount === -1 || tokenAmount === '-1';
        
        // 상품명 결정 (product_name 우선 확인, 없으면 tokenAmount로 판단)
        let productName = '알 수 없음';
        let isGoldProduct = false;
        let isPeriodEvent = false; // 기간제 이벤트 여부 (회원가입 무제한이벤트)
        let isTokenEvent = false;  // 토큰 이벤트 여부 (회원가입 토큰이벤트)
        
        // product_name이 있으면 우선 사용 (Welcome Period 구분을 위해)
        if (data.product_name) {
            const productNameLower = data.product_name.toLowerCase();
            if (data.product_name === 'Welcome Period' || data.product_name === 'Welcome Period Event' || 
                productNameLower === 'welcome period' || productNameLower === 'welcome period event' ||
                productNameLower.includes('welcome period')) {
                productName = '회원가입 무제한이벤트';
                isPeriodEvent = true; // 기간제 이벤트로 표시
            } else if (data.product_name === 'Welcome Event' || productNameLower === 'welcome event' ||
                       data.product_name === '회원가입 토큰이벤트') {
                productName = '회원가입 토큰이벤트';
                isTokenEvent = true; // 토큰 이벤트로 표시
            } else {
                productName = data.product_name;
            }
        } else {
            // product_name이 없으면 tokenAmount로 판단
            if (isUnlimited) {
                productName = 'Gold (무제한)';
                isGoldProduct = true;
            } else if (tokenAmount >= 100) {
                productName = 'Premium';
            } else {
                // Standard는 회원가입 토큰이벤트로 표시
                productName = '회원가입 토큰이벤트';
                isTokenEvent = true; // 토큰 이벤트로 표시
            }
        }
        
        // 결제일시 포맷팅 (관리자와 동일한 형식)
        let formattedDate = date || '알 수 없음';
        if (date && typeof date === 'string') {
            try {
                const dateObj = new Date(date);
                if (!isNaN(dateObj.getTime())) {
                    formattedDate = dateObj.toLocaleDateString('ko-KR', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                }
            } catch (e) {
                // 날짜 파싱 실패 시 원본 사용
            }
        }
        
        // 결제수단 결정 (이벤트인 경우 특별 처리)
        let paymentMethod = data.payment_method || data.pg_provider || data.method || '수동 결제';
        if (isPeriodEvent || isTokenEvent) {
            paymentMethod = '<span style="color: #dc2626; font-weight: 600;">1회 이용권 사용</span>';
        }
        
        // 상태 배지 (이벤트인 경우 특별 처리)
        const status = data.status || 'completed';
        const getStatusBadge = (status) => {
            // 이벤트인 경우 특별 표시
            if ((isPeriodEvent || isTokenEvent) && status === 'completed') {
                if (isPeriodEvent) {
                    return '<span class="badge bg-success">이벤트 무제한 사용가능</span>';
                } else if (isTokenEvent) {
                    return '<span class="badge bg-success">이벤트 토큰 사용가능</span>';
                }
            }
            const statusMap = {
                'completed': '<span class="badge bg-success">완료</span>',
                'pending': '<span class="badge bg-warning">대기</span>',
                'cancelled': '<span class="badge bg-danger">취소</span>',
                'failed': '<span class="badge bg-secondary">실패</span>'
            };
            return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
        };
        
        // Total 금액 표시 (이벤트인 경우 "이벤트"로 표시)
        // order_id가 있으면 결제 기록으로 간주하고 금액 표시
        let amount = data.amount || data.payment_amount || 0;
        
        // amount가 없고 order_id가 있으면 결제 기록으로 간주
        // (실제로는 결제 API를 호출해야 하지만, 일단 데이터에서 추출 시도)
        if (!amount && orderId) {
            // order_id가 있으면 결제 기록이므로, 토큰 개수로 금액 추정 (임시)
            // 실제로는 결제 API를 호출해야 하지만, 일단 토큰 개수로 표시
            // Premium: 100토큰 = 30,000원, Standard: 50토큰 = 15,000원 (예시)
            if (tokenAmount >= 100) {
                amount = 30000; // Premium 가격
            } else if (tokenAmount >= 50) {
                amount = 15000; // Standard 가격
            }
        }
        
        const isFreePayment = amount === 0;
        // 이벤트인 경우 Total을 "이벤트"로 표시 (금액과 무관하게)
        const totalDisplay = (isPeriodEvent || isTokenEvent)
            ? '이벤트'
            : (isFreePayment
                ? '무료'
                : `₩ ${amount.toLocaleString('ko-KR')}`);
        
        // 이용 기간 정보 (Gold 상품 / 기간제 이벤트 / 무료 토큰 이벤트)
        let subscriptionInfo = '';
        // 기간제 이벤트(Welcome Period), Gold 상품, 무료 체험, 무료 토큰 이벤트인 경우 이용 기간 표시
        if (
            isPeriodEvent ||
            (isGoldProduct && data.subscription_end_date) ||
            data.free_trial_expired_at ||
            (isTokenEvent && data.token_event_expires_at)
        ) {
            try {
                let endDate = null;
                let paymentDate = date ? new Date(date) : new Date();

                // 1) 무료 토큰 이벤트: token_event_start_date ~ token_event_expires_at 사용
                if (isTokenEvent && data.token_event_expires_at) {
                    endDate = new Date(data.token_event_expires_at);
                    if (data.token_event_start_date) {
                        paymentDate = new Date(data.token_event_start_date);
                    }
                } else {
                    // 2) 기간제 / 골드 / 무료 체험: 기존 로직 유지
                    endDate = data.subscription_end_date
                        ? new Date(data.subscription_end_date)
                        : data.free_trial_expired_at
                            ? new Date(data.free_trial_expired_at)
                            : null;
                }
                
                if (endDate) {
                    const diffTime = endDate.getTime() - paymentDate.getTime();
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    
                    // 날짜 포맷 개선: YYYY. MM. DD 형식
                    const startLabel = paymentDate.toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit'
                    }).replace(/\./g, '.').replace(/\s+/g, ' ').trim();
                    const endLabel = endDate.toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit'
                    }).replace(/\./g, '.').replace(/\s+/g, ' ').trim();
                    
                    // 만료일 포맷: YYYY. MM. DD HH:MM
                    const expiredDateStr = endDate.toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit'
                    }).replace(/\./g, '.').replace(/\s+/g, ' ').trim();
                    const expiredTimeStr = endDate.toLocaleTimeString('ko-KR', {
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: false
                    });
                    
                    if (diffDays > 0) {
                        subscriptionInfo = `
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">이용 기간</td>
                                <td style="padding: 0.5rem 0;">
                                    <div style="margin-bottom: 0.25rem;">
                                        <strong style="font-size: 1rem; color: #1f2937;">${startLabel} ~ ${endLabel}</strong>
                                        <span style="color: #6b7280; font-size: 0.9rem; margin-left: 0.5rem;">(${diffDays}일)</span>
                                    </div>
                                    <small class="text-success" style="font-size: 0.85rem;">만료일: ${expiredDateStr} ${expiredTimeStr}</small>
                                </td>
                            </tr>
                        `;
                    } else {
                        subscriptionInfo = `
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">이용 기간</td>
                                <td style="padding: 0.5rem 0;">
                                    <strong class="text-danger" style="font-size: 1rem;">만료됨</strong><br>
                                    <small class="text-muted" style="font-size: 0.85rem;">${endLabel} 기준 만료</small>
                                </td>
                            </tr>
                        `;
                    }
                }
            } catch (e) {
                console.warn('[renderTokenChargeReceipt] 구독 정보 처리 실패:', e);
            }
        }
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        <tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">주문번호</td>
                            <td style="padding: 0.5rem 0;"><code class="text-primary fw-bold">${orderId || 'N/A'}</code></td>
                        </tr>
                        ${renderUserAndEmail(data)}
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">상품명</td>
                            <td style="padding: 0.5rem 0;"><strong>${productName}</strong></td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">결제일시</td>
                            <td style="padding: 0.5rem 0;">${formattedDate}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">결제수단</td>
                            <td style="padding: 0.5rem 0;">${paymentMethod}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">상태</td>
                            <td style="padding: 0.5rem 0;">${getStatusBadge(status)}</td>
                        </tr>
                        ${subscriptionInfo}
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${totalDisplay}</span>
                </div>
            </div>
        `;
    }

    // ===== 토큰 충전 영수증 비동기 렌더링 (사용자 정보 가져오기) =====
    async function renderTokenChargeReceiptAsync(data, date, contentEl) {
        try {
            // 현재 사용자 정보 가져오기 (subscription_end_date 포함)
            const response = await fetch('/api/user-info', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.getCSRFToken ? window.getCSRFToken() : ''
                },
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    // 사용자 정보에서 subscription_end_date 및 username 가져오기
                    // API 응답 구조: result.data.user 또는 result.data
                    const userData = result.data.user || result.data;
                    if (userData) {
                        if (userData.subscription_end_date) {
                            data.subscription_end_date = userData.subscription_end_date;
                        }
                        // free_trial_expired_at도 추가 (기간제 이벤트용)
                        if (userData.free_trial_expired_at) {
                            data.free_trial_expired_at = userData.free_trial_expired_at;
                        }
                        // 실제 사용자 아이디(username) 가져오기
                        if (userData.username) {
                            data.username = userData.username;
                        }
                        // 이메일도 가져오기
                        if (userData.email) {
                            data.email = userData.email;
                        }
                        // 무료 토큰 이벤트 기간 정보도 함께 주입
                        if (userData.token_event_start_date) {
                            data.token_event_start_date = userData.token_event_start_date;
                        }
                        if (userData.token_event_expires_at) {
                            data.token_event_expires_at = userData.token_event_expires_at;
                        }
                    }
                }
            }
        } catch (e) {
            console.warn('[renderTokenChargeReceiptAsync] 사용자 정보 조회 실패:', e);
        }
        
        // 영수증 렌더링
        if (contentEl) {
            contentEl.innerHTML = renderTokenChargeReceipt(data, date);
        }
    }

    // ===== 토큰 리셋 영수증 렌더링 =====
    function renderTokenResetReceipt(data, date) {
        const totalDisplay = '초기화 완료';
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        <tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                            <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">처리 내용</td>
                            <td style="padding: 0.5rem 0;"><strong>토큰 잔액 초기화</strong></td>
                        </tr>
                        ${data.reason ? `<tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">처리 사유</td>
                            <td style="padding: 0.5rem 0;">${data.reason}</td>
                        </tr>` : ''}
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">처리일시</td>
                            <td style="padding: 0.5rem 0;">${date || '알 수 없음'}</td>
                        </tr>
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${totalDisplay}</span>
                </div>
            </div>
        `;
    }

    // ===== 토큰 사용 영수증 렌더링 =====
    function renderTokenUseReceipt(data, date, activityType) {
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        
        if (activityType.includes('FILE_CONVERT')) {
            // 파일 변환
            const filename = data.filename || data.file_name || '알 수 없음';
            const extractedRows = data.extracted_rows || data.count || 0;
            const tokensUsed = data.tokens_deducted || data.token_change || 0;
            const tokensDisplay = Math.abs(tokensUsed).toLocaleString('ko-KR') + '개';
            
            return `
                <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                        <tbody>
                            <tr>
                                <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                                <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                            </tr>
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">변환 파일명</td>
                                <td style="padding: 0.5rem 0;"><strong>${filename}</strong></td>
                            </tr>
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">변환 건수</td>
                                <td style="padding: 0.5rem 0;"><strong>${extractedRows.toLocaleString('ko-KR')}건</strong></td>
                            </tr>
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">사용된 토큰</td>
                                <td style="padding: 0.5rem 0;"><strong>${tokensDisplay}</strong></td>
                            </tr>
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">변환일시</td>
                                <td style="padding: 0.5rem 0;">${date || '알 수 없음'}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                        <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${tokensDisplay}</span>
                    </div>
                </div>
            `;
        } else {
            // 일반 토큰 사용
            const tokensUsed = data.tokens_deducted || data.token_change || 0;
            const tokensDisplay = Math.abs(tokensUsed).toLocaleString('ko-KR') + '개';
            
            return `
                <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                        <tbody>
                            <tr>
                                <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                                <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                            </tr>
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">사용된 토큰</td>
                                <td style="padding: 0.5rem 0;"><strong>${tokensDisplay}</strong></td>
                            </tr>
                            ${data.message ? `<tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">사용 목적</td>
                                <td style="padding: 0.5rem 0;">${data.message}</td>
                            </tr>` : ''}
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">사용일시</td>
                                <td style="padding: 0.5rem 0;">${date || '알 수 없음'}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                        <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${tokensDisplay}</span>
                    </div>
                </div>
            `;
        }
    }

    // ===== 토큰 환불 영수증 렌더링 =====
    function renderTokenRefundReceipt(data, date) {
        const refundAmount = data.refund_token_amount || data.token_change || 0;
        const refundDisplay = Math.abs(refundAmount).toLocaleString('ko-KR') + '개';
        const orderId = data.order_id || '';
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        ${orderId ? `<tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">주문번호</td>
                            <td style="padding: 0.5rem 0;"><code class="text-primary fw-bold">${orderId}</code></td>
                        </tr>` : ''}
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">유저명</td>
                            <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">환불된 토큰</td>
                            <td style="padding: 0.5rem 0;"><strong>${refundDisplay}</strong></td>
                        </tr>
                        ${data.reason ? `<tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">환불 사유</td>
                            <td style="padding: 0.5rem 0;">${data.reason}</td>
                        </tr>` : ''}
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">환불일시</td>
                            <td style="padding: 0.5rem 0;">${date || '알 수 없음'}</td>
                        </tr>
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${refundDisplay}</span>
                </div>
            </div>
        `;
    }

    // ===== 등급명 한글 변환 함수 =====
    function translatePlanName(planName) {
        const planMap = {
            'free': '무료',
            'basic': '베이직',
            'premium': '프리미엄',
            'gold': '골드',
            'gold-vip': '골드 VIP',
            'platinum': '플래티넘',
            'enterprise': '엔터프라이즈'
        };
        return planMap[planName?.toLowerCase()] || planName || '알 수 없음';
    }

    // ===== 등급 변경 영수증 렌더링 =====
    function renderGradeChangeReceipt(data, date) {
        const oldPlanRaw = data.old_plan || data.from_plan || '알 수 없음';
        const newPlanRaw = data.new_plan || data.to_plan || '알 수 없음';
        const oldPlan = translatePlanName(oldPlanRaw);
        const newPlan = translatePlanName(newPlanRaw);
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        
        // 사유 한글화 (기술적 표현 제거)
        let reasonText = '';
        if (data.reason) {
            reasonText = data.reason
                .replace(/관리자에 의한 변경/i, '관리자 변경')
                .replace(/\(관리자 수동\)/i, '')
                .replace(/\(.*?\)/g, '')
                .trim();
        }
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        <tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                            <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">이전 등급</td>
                            <td style="padding: 0.5rem 0;"><strong>${oldPlan}</strong></td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">새 등급</td>
                            <td style="padding: 0.5rem 0;"><strong>${newPlan}</strong></td>
                        </tr>
                        ${reasonText ? `<tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">변경 사유</td>
                            <td style="padding: 0.5rem 0;">${reasonText}</td>
                        </tr>` : ''}
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">변경일시</td>
                            <td style="padding: 0.5rem 0;">${date || '알 수 없음'}</td>
                        </tr>
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">등급 변경 완료</span>
                </div>
            </div>
        `;
    }

    // ===== 프로필 수정 영수증 렌더링 =====
    function renderProfileUpdateReceipt(data, date) {
        const changedFields = data.changed_fields_kr || data.changed_fields || [];
        const fieldsText = Array.isArray(changedFields) ? changedFields.join(', ') : changedFields;
        const totalDisplay = '수정 완료';
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        <tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                            <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">수정 항목</td>
                            <td style="padding: 0.5rem 0;"><strong>${fieldsText || '프로필 정보'}</strong></td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">수정일시</td>
                            <td style="padding: 0.5rem 0;">${date || '알 수 없음'}</td>
                        </tr>
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${totalDisplay}</span>
                </div>
            </div>
        `;
    }

    // ===== 로그인/로그아웃 영수증 렌더링 (날짜/시간만) =====
    function renderLoginReceipt(data, date, activityType) {
        const isLogin = activityType.includes('LOGIN');
        const actionText = isLogin ? '로그인' : '로그아웃';
        const totalDisplay = actionText;
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        <tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                            <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">${actionText} 일시</td>
                            <td style="padding: 0.5rem 0;"><strong>${date || '알 수 없음'}</strong></td>
                        </tr>
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${totalDisplay}</span>
                </div>
            </div>
        `;
    }

    // ===== 기본 영수증 렌더링 =====
    function renderDefaultReceipt(data, date, activityType) {
        // 숨겨야 할 기술적 필드명 목록
        const hiddenKeys = new Set([
            'activity_type', 'type', 'log_type', 'id', '_id', 'timestamp', 'created_at', 'updated_at',
            'old_plan', 'new_plan', 'from_plan', 'to_plan', // 등급 변경 필드는 별도 처리
            'user_id', 'user_id_str', 'details_summary', 'meta'
        ]);
        
        // 의미있는 필드만 추출하여 표시
        const displayFields = [];
        
        // 기술적 필드명을 한글로 매핑
        const fieldLabelMap = {
            'product_name': '상품명',
            'amount': '금액',
            'token_change': '토큰 변동량',
            'tokens': '토큰',
            'message': '상세 내용',
            'reason': '사유',
            'filename': '파일명',
            'file_name': '파일명',
            'count': '건수',
            'extracted_rows': '변환 건수',
            'order_id': '주문번호',
            'payment_id': '결제 번호',
            'payment_method': '결제 수단',
            'method': '결제 수단',
            'status': '상태'
        };
        
        // 데이터의 모든 키를 순회하면서 의미있는 필드만 추출
        Object.keys(data).forEach(key => {
            // 숨겨야 할 필드는 건너뛰기
            if (hiddenKeys.has(key)) return;
            
            const value = data[key];
            if (value === null || value === undefined || value === '') return;
            
            // 이미 처리된 필드는 건너뛰기
            if (['product_name', 'amount', 'token_change', 'message', 'reason'].includes(key)) return;
            
            // 필드 레이블 가져오기 (매핑에 없으면 원본 키 사용)
            const label = fieldLabelMap[key] || key.replace(/_/g, ' ');
            
            // 값 포맷팅
            let formattedValue = value;
            if (typeof value === 'number') {
                if (key.includes('amount') || key.includes('price') || key.includes('cost')) {
                    formattedValue = `${value.toLocaleString('ko-KR')}원`;
                } else if (key.includes('token')) {
                    formattedValue = `${value.toLocaleString('ko-KR')}개`;
                } else {
                    formattedValue = value.toLocaleString('ko-KR');
                }
            } else if (typeof value === 'string' && value.length > 100) {
                formattedValue = value.substring(0, 100) + '...';
            }
            
            displayFields.push({ label, value: formattedValue });
        });
        
        // 우선순위 필드 먼저 추가
        if (data.product_name) {
            // Welcome Event를 회원가입 토큰이벤트로 변환
            // Welcome Period를 회원가입 무제한이벤트로 변환
            let productName = data.product_name;
            const productNameLower = productName.toLowerCase();
            if (productName === 'Welcome Event' || productNameLower === 'welcome event') {
                productName = '회원가입 토큰이벤트';
            } else if (productName === 'Welcome Period' || productName === 'Welcome Period Event' || 
                       productNameLower === 'welcome period' || productNameLower === 'welcome period event' ||
                       productNameLower.includes('welcome period')) {
                productName = '회원가입 무제한이벤트';
            }
            displayFields.unshift({ label: '상품명', value: productName });
        }
        if (data.amount !== undefined && data.amount !== null) {
            displayFields.push({ label: '금액', value: `${data.amount.toLocaleString('ko-KR')}원` });
        }
        if (data.token_change !== undefined && data.token_change !== null) {
            const change = Number(data.token_change);
            displayFields.push({ 
                label: change > 0 ? '충전된 토큰' : '사용된 토큰', 
                value: `${change > 0 ? '+' : ''}${Math.abs(change).toLocaleString('ko-KR')}개` 
            });
        }
        if (data.message) displayFields.push({ label: '상세 내용', value: data.message });
        if (data.reason) displayFields.push({ label: '사유', value: data.reason });
        
        // 유저명 먼저 추가
        const userName = data.username || data.user_name || '사용자';
        const userEmail = data.email || data.user_email || '';
        let rowsHtml = `
            <tr>
                <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">유저명</td>
                <td style="padding: 0.5rem 0;"><strong>${userName}</strong>${userEmail ? `<br><small class="text-muted">${userEmail}</small>` : ''}</td>
            </tr>
        `;
        
        displayFields.forEach(field => {
            rowsHtml += `
                <tr>
                    <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">${field.label}</td>
                    <td style="padding: 0.5rem 0;"><strong>${field.value}</strong></td>
                </tr>
            `;
        });
        
        if (date) {
            rowsHtml += `
                <tr>
                    <td class="text-muted" style="padding: 0.5rem 0;">거래일시</td>
                    <td style="padding: 0.5rem 0;">${date}</td>
                </tr>
            `;
        }
        
        // 총액 계산 (금액 또는 토큰이 있으면 표시)
        let totalDisplay = '처리 완료';
        if (data.amount !== undefined && data.amount !== null && data.amount !== 0) {
            totalDisplay = data.amount === 0 ? '무료' : `₩ ${data.amount.toLocaleString('ko-KR')}`;
        } else if (data.token_change !== undefined && data.token_change !== null) {
            const change = Number(data.token_change);
            totalDisplay = `${change > 0 ? '+' : ''}${Math.abs(change).toLocaleString('ko-KR')}개`;
        }
        
        return `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        ${rowsHtml || '<tr><td colspan="2" class="text-center text-muted">상세 정보 없음</td></tr>'}
                    </tbody>
                </table>
                
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">${totalDisplay}</span>
                </div>
            </div>
        `;
    }

    // ===== 영수증 렌더링 실행 (비동기 사용자 정보 가져오기) =====
    // 사용자 정보를 먼저 가져온 후 영수증 렌더링
    fetchUserInfo().then(() => {
        const receiptHtml = renderByActivityType();
        contentEl.innerHTML = receiptHtml;
        
        // 모달 표시
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }).catch(() => {
        // 사용자 정보 가져오기 실패 시에도 영수증 표시
        const receiptHtml = renderByActivityType();
        contentEl.innerHTML = receiptHtml;
        
        // 모달 표시
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    });
}

// ===== 렌더링 함수 =====

/**
 * 필터링된 활동 내역 렌더링
 * @param {string} tabName - 'all', 'tokens', 'system' (탭 이름)
 */
function renderList(tabName) {
    console.log(`[CCTV] renderList('${tabName}') 호출됨. 원본 데이터:`, allActivities.length);
    
    // 각 탭의 컨테이너 찾기
    const tabPaneId = `tab-content-${tabName}`;
    const tabPane = document.getElementById(tabPaneId);
    if (!tabPane) return;
    
    const container = tabPane.querySelector('.activity-table-body-target');
    if (!container) return;
    
    // 컨테이너 초기화
    container.innerHTML = '';
    
    // 1. 탭별 1차 분류 (Category Filter)
    const allowedTypes = TAB_CATEGORY_MAP[tabName] || [];
    let filteredActivities = allActivities;

    // 'tokens', 'system' 탭은 자기 분야만 남김 (교집합)
    if (allowedTypes.length > 0) {
        const allowedTypesUpper = allowedTypes.map(t => t.toUpperCase());
        filteredActivities = filteredActivities.filter(log => {
            const typeRaw = log.activity_type || log.type || '';
            return allowedTypesUpper.includes(typeRaw.toUpperCase());
        });
    }

    // 2. 사용자 선택 2차 분류 (Dropdown Filter) - [수정됨: 모든 탭 적용]
    // 기존에는 'all' 탭일 때만 적용되었으나, 이제 모든 탭에서 추가 필터링 가능
    const currentFilterType = activityViewState.filters.type;
    if (currentFilterType && currentFilterType !== 'all') {
        console.log(`[DEBUG] 추가 필터링 적용: ${currentFilterType} (탭: ${tabName})`);
        filteredActivities = filteredActivities.filter(log => {
            const typeRaw = log.activity_type || log.type || '';
            // 정확히 일치하는 유형만 통과
            return typeRaw.toUpperCase() === currentFilterType.toUpperCase();
        });
    }
    
    console.log(`[DEBUG] 탭 '${tabName}' 렌더링: ${filteredActivities.length} / ${allActivities.length} 건`);
    
    // 3. 데이터 없음 처리
    if (filteredActivities.length === 0) {
        container.innerHTML = `
            <tr class="activity-empty-row">
                <td colspan="5">
                    <div class="activity-empty">
                        <div class="activity-empty-icon">📭</div>
                        <p class="activity-empty-text">조건에 맞는 내역이 없습니다.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    // 4. 렌더링
    filteredActivities.forEach((log, index) => {
        try {
            const itemHtml = createActivityItemHtml(log, index);
            container.insertAdjacentHTML('beforeend', itemHtml);
        } catch (error) {
            console.error('[CRITICAL] 항목 렌더링 중 오류:', error);
        }
    });

    // 미션 1: DOM 강제 확인 로그
    console.log('[CCTV] 렌더링 직후 컨테이너 HTML:', container.innerHTML);
    console.log('[CCTV] 컨테이너의 자식 노드 개수:', container.children.length);

    // 미션 2: 강제 표시 (Force Display)
    container.style.display = 'table-row-group';
    container.style.visibility = 'visible';
    container.style.opacity = '1';
}

/**
 * 활동 항목 HTML 생성 (디자인 밸런스 수정)
 */
function createActivityItemHtml(log, index) {
    try {
        // 날짜 포맷팅
        const date = new Date(log.timestamp);
        const dateStr = date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
        }) + ' ' + date.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
        
        // 활동 유형 한글화
        const activityTypeRaw = log.activity_type || log.type || log.log_type || '';
        let activityTypeText = log.activity_type_korean || translateActivityType(activityTypeRaw);
        
        // 상세 정보 파싱 및 번역 적용
        const detailsSource = log.details || log.details_summary || log.meta || log.message || '';
        let detailsText = '';
        
        if (detailsSource) {
            try {
                detailsText = parseDetails(detailsSource, activityTypeRaw);
            } catch (error) {
                detailsText = '내용 없음';
            }
        }

        if (!detailsText || detailsText === '세부 정보 없음' || detailsText.trim() === '') {
            detailsText = activityTypeText;
        }
        
        // 모달용 페이로드 (원본 보존 + activity_type 포함)
        const detailsPayload = detailsSource || detailsText || '';
        let detailPayloadObj = {};
        
        // details를 객체로 변환
        if (typeof detailsPayload === 'string') {
            try {
                detailPayloadObj = JSON.parse(detailsPayload);
            } catch (_) {
                detailPayloadObj = { '내용': detailsPayload };
            }
        } else if (typeof detailsPayload === 'object' && detailsPayload !== null) {
            detailPayloadObj = detailsPayload;
        } else {
            detailPayloadObj = { '내용': String(detailsPayload) };
        }
        
        // activity_type 추가 (모달에서 사용)
        if (activityTypeRaw) {
            detailPayloadObj.activity_type = activityTypeRaw;
        }
        
        const encodedDetailPayload = encodeURIComponent(JSON.stringify(detailPayloadObj));
        
        // 토큰 변화량 포맷팅
        let tokenChange = '';
        let tokenChangeClass = 'text-secondary'; // 기본 회색
        
        const tokenChangeValue = log.token_change !== undefined ? log.token_change : 
                                (log.change !== undefined ? log.change : 
                                (log.amount !== undefined ? log.amount : 0));
        
        const numericValue = Number(tokenChangeValue) || 0;
        
        if (numericValue > 0) {
            const chargeAmount = formatTokenAmount(numericValue);
            tokenChange = chargeAmount === '무제한' ? '무제한' : `+${chargeAmount}`;
            tokenChangeClass = 'text-success'; // 초록색
        } else if (numericValue < 0 && log.activity_type !== 'TOKEN_RESET_BY_ADMIN') {
            const usageAmount = formatTokenAmount(Math.abs(numericValue));
            tokenChange = usageAmount === '무제한' ? '무제한' : `-${usageAmount}`;
            tokenChangeClass = 'text-danger'; // 빨간색
        } else {
            tokenChange = '-';
            tokenChangeClass = 'text-secondary'; // 회색
        }
        
        const safeDate = sanitizeHtml(dateStr);
        const safeType = sanitizeHtml(activityTypeText);
        const safeTokenChange = sanitizeHtml(tokenChange);
        // detailsText는 이미 HTML 태그가 포함될 수 있음 (파일명 강조 등) -> sanitize 최소화하고 믿을 수 있는 소스만
        // 여기서는 안전하게 처리하되, 위에서 넣은 span 태그를 살려야 함.
        // 하지만 parseDetails에서 넣은 HTML이 sanitize에 의해 죽을 수 있음.
        // parseDetails는 내부 로직이므로 신뢰한다고 가정하고, sanitizeHtml은 텍스트 부분만 적용해야 하는데 복잡함.
        // 따라서, parseDetails 리턴값이 HTML을 포함할 수 있음을 인지하고 그대로 사용 (XSS 주의)
        // 단, 파일명 등 외부 입력값은 parseDetails 내부에서 처리하거나 여기서 해야 함.
        // 현재 구조상 parseDetails가 1차 가공하므로 그대로 둠.
        
        const activityId = sanitizeHtml(String(log.id ?? index ?? ''));
        
        // HTML 생성 (테이블 행)
        // 수정 4: 디자인 밸런스 (text-truncate, max-width, Nanum Gothic)
        return `
            <tr class="activity-item" style="font-family: 'Nanum Gothic', sans-serif;">
                <td class="activity-date text-secondary small text-nowrap text-center">${safeDate}</td>
                <td class="activity-type text-center">
                    <span class="badge bg-light text-dark border fw-normal">${safeType}</span>
                </td>
                <td class="activity-details text-start text-truncate" style="max-width: 400px;" title="${sanitizeHtml(detailsText.replace(/<[^>]*>?/gm, ''))}">
                    ${detailsText}
                </td>
                <td class="activity-change text-center fw-bold ${tokenChangeClass}">${safeTokenChange}</td>
                <td class="activity-action text-center">
                    <button type="button"
                        class="btn btn-outline-secondary btn-sm btn-detail"
                        data-activity-id="${activityId}"
                        data-activity-date="${safeDate}"
                        data-activity-detail="${encodedDetailPayload}">
                        상세
                    </button>
                </td>
            </tr>
        `;
    } catch (error) {
        console.error('[CRITICAL] 아이템 HTML 생성 실패:', error, log);
        return `<tr class="table-danger"><td colspan="5">데이터 오류 (ID: ${log.id || 'Unknown'})</td></tr>`;
    }
}

// ===== 탭 전환 로직 =====

/**
 * 탭 전환 핸들러
 */
function handleTabSwitch(event) {
    const tabButton = event.target.closest('.nav-link');
    if (!tabButton) return;
    
    const tabValue = tabButton.getAttribute('data-tab');
    if (!tabValue) return;
    
    // 골드 탭은 별도 처리
    if (tabValue === 'gold') {
        // ... (기존 골드 탭 처리 로직 유지)
        const allTabPanes = document.querySelectorAll('.tab-pane');
        allTabPanes.forEach(pane => pane.classList.remove('show', 'active'));
        
        const goldPane = document.getElementById('tab-content-gold');
        if (goldPane) goldPane.classList.add('show', 'active');
        return;
    }
    
    // 탭 UI 업데이트
    const allTabButtons = document.querySelectorAll('#myhome-tabs .nav-link');
    allTabButtons.forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
    });
    tabButton.classList.add('active');
    tabButton.setAttribute('aria-selected', 'true');
    
    // 탭 패널 활성화
    const allTabPanes = document.querySelectorAll('.tab-pane');
    allTabPanes.forEach(pane => pane.classList.remove('show', 'active'));
    
    const targetPane = document.getElementById(`tab-content-${tabValue}`);
    if (targetPane) {
        targetPane.classList.add('show', 'active');
    }

    activityViewState.currentTab = tabValue; // 수정 2: 탭 전환 시 위치 기록 (이미 존재)

    // 수정 3: 드롭다운(유형) 동기화 및 검색 버튼 로직 강화
    updateTypeDropdown(tabValue);

    // 필터 초기화 (탭 전환 시 필터는 '전체'로 리셋하는 것이 UX상 자연스러움)
    activityViewState.filters.type = '';

    // 데이터 다시 로드 (현재 탭에 맞는 데이터 렌더링을 위해)
    // loadActivityLogs 내부에서 currentTab을 활용하여 해당 탭만 렌더링하도록 수정 예정
    loadActivityLogs({ resetPage: true });
}

/**
 * 탭에 따른 유형 드롭다운 업데이트
 */
function updateTypeDropdown(tabName) {
    const typeSelect = document.getElementById('filter-type');
    if (!typeSelect) return;

    const options = DROPDOWN_OPTIONS_MAP[tabName] || DROPDOWN_OPTIONS_MAP['all'];
    
    // 기존 옵션 제거
    typeSelect.innerHTML = '';
    
    // 새 옵션 추가
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.text;
        typeSelect.appendChild(option);
    });
    
    // 선택값 초기화
    typeSelect.value = '';
}

// ===== 초기화 =====

document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] ========================================');
    console.log('[DEBUG] Profile Modern 초기화 시작');
    console.log('[DEBUG] 현재 시간:', new Date().toISOString());
    console.log('[DEBUG] ========================================');
    
    // 탭 버튼 이벤트 리스너 등록
    console.log('[DEBUG] 탭 버튼 찾기 시작...');
    const tabButtons = document.querySelectorAll('#myhome-tabs .nav-link');
    console.log(`[DEBUG] 탭 버튼 ${tabButtons.length}개 발견`);
    tabButtons.forEach((button, index) => {
        console.log(`[DEBUG] 탭 버튼 ${index + 1} 이벤트 리스너 등록:`, button.getAttribute('data-tab'));
        button.addEventListener('click', handleTabSwitch);
    });
    
    // Bootstrap 탭 이벤트 (fallback)
    if (typeof bootstrap !== 'undefined') {
        console.log('[DEBUG] Bootstrap 탭 이벤트 등록 시작...');
        const tabElements = document.querySelectorAll('#myhome-tabs button[data-bs-toggle="tab"]');
        console.log(`[DEBUG] Bootstrap 탭 요소 ${tabElements.length}개 발견`);
        tabElements.forEach(tab => {
            tab.addEventListener('shown.bs.tab', function(event) {
                const tabValue = event.target.getAttribute('data-tab');
                if (tabValue && tabValue !== 'gold') {
                    renderList(tabValue);
                }
            });
        });
    } else {
        console.warn('[DEBUG] Bootstrap이 정의되지 않았습니다.');
    }
    
    // 토큰 상태 로드 (상단 카드용) - Task 1
    console.log('[DEBUG] loadTokenStatus() 호출 시작');
    loadTokenStatus().catch(err => {
        console.error('[CRITICAL] loadTokenStatus() 실행 중 오류:', err);
        console.error('[CRITICAL] 에러 스택:', err.stack);
    });
    
    // 초기화 시 기본 드롭다운 설정
    updateTypeDropdown('all');
    
    initActivityFilterBar();
    
    // 활동 내역 데이터 로드 (한 번만) - Task 2
    console.log('[DEBUG] loadActivityLogs() 호출 시작');
    loadActivityLogs().catch(err => {
        console.error('[CRITICAL] loadActivityLogs() 실행 중 오류:', err);
        console.error('[CRITICAL] 에러 스택:', err.stack);
    });
    
    console.log('[DEBUG] 초기화 완료 - 두 함수 호출됨');
    console.log('[DEBUG] ========================================');
    
    // ===== 폼 유효성 검사 및 미리보기 (정보 수정 모달용) =====
    // 모달이 열릴 때마다 폼 초기화
    const profileEditModalEl = document.getElementById('editProfileModal');
    if (profileEditModalEl) {
        profileEditModalEl.addEventListener('shown.bs.modal', function() {
            console.log('[DEBUG] 정보 수정 모달이 열렸습니다. 폼 초기화 시작...');
            initProfileForm();
        });

        // 🔥 이중 모달 트리거 제거: HTML의 data-bs-toggle="modal"이 이미 모달을 열고 있음
        // JS에서 추가로 modal.show()를 호출하면 충돌 발생
        // HTML 방식(data-bs-*)을 신뢰하므로, JS 클릭 이벤트는 제거함
        /*
        const editProfileButton = document.querySelector('.btn-edit-profile');
        if (editProfileButton && typeof bootstrap !== 'undefined') {
            const modalInstance = bootstrap.Modal.getOrCreateInstance(profileEditModalEl);
            editProfileButton.addEventListener('click', () => {
                console.log('[DEBUG] 정보 수정 버튼 클릭 - 모달 표시');
                modalInstance.show();
            });
        }
        */
    } else {
        // 모달이 아직 DOM에 없을 수 있으므로, 초기화 시도
        initProfileForm();
    }

    // 골드 고객 관리 모듈 초기화
    initGoldCustomerModule();
});

document.addEventListener('click', function(event) {
    const detailBtn = event.target.closest('.btn-detail');
    if (!detailBtn) return;
    const payload = detailBtn.getAttribute('data-activity-detail') || '';
    const date = detailBtn.getAttribute('data-activity-date') || '';
    showActivityDetailsModal(payload, date);
});

// ===== 폼 유효성 검사 및 미리보기 =====

/**
 * 프로필 폼 초기화
 */
function initProfileForm() {
    const form = document.getElementById('profileForm');
    if (!form) {
        console.log('[DEBUG] profileForm을 찾을 수 없습니다. 모달이 아직 열리지 않았을 수 있습니다.');
        return;
    }
    
    const inputs = form.querySelectorAll('input[required]');
    const saveDirectBtn = document.getElementById('btn-save-direct');
    
    // 실시간 유효성 검사
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            validateProfileField(this);
        });
        
        input.addEventListener('blur', function() {
            validateProfileField(this);
        });
    });
    
    if (saveDirectBtn) {
        saveDirectBtn.addEventListener('click', function() {
            console.log('💾 저장하기 버튼 클릭됨');
            if (validateAllProfileFields()) {
                console.log('✅ 유효성 검사 통과 - 저장 진행');
                saveProfile();
            } else {
                console.log('❌ 유효성 검사 실패');
                showToast('입력 정보를 다시 확인해주세요.', 'error');
            }
        });
    }
    
    // 폼 제출 시 전체 검증 (AJAX로 처리하므로 기본 제출 방지)
    form.addEventListener('submit', function(e) {
        console.log('📋 폼 제출 이벤트 발생');
        e.preventDefault(); // 기본 폼 제출 방지
        
        if (validateAllProfileFields()) {
            console.log('✅ 유효성 검사 통과 - AJAX 저장 시작');
            saveProfile();
        } else {
            console.log('❌ 유효성 검사 실패 - 제출 차단');
            showToast('입력 정보를 다시 확인해주세요.', 'error');
        }
    });
}

/**
 * AJAX로 프로필 저장하는 함수
 */
async function saveProfile() {
    if (!validateAllProfileFields()) {
        showToast('입력 정보를 다시 확인해주세요.', 'error');
        return;
    }
    
    const data = {
        company_name: document.getElementById('company_name')?.value || '',
        representative_name: document.getElementById('representative_name')?.value || '',
        phone: document.getElementById('phone')?.value || '',
        email: document.getElementById('email')?.value || '',
        address: document.getElementById('address')?.value || '',
        business_type: document.getElementById('business_type')?.value || '',
        business_category: document.getElementById('business_category')?.value || ''
    };
    
    if (!data.company_name || !data.representative_name || !data.phone || !data.email || 
        !data.business_type || !data.business_category) {
        showToast('모든 필수 항목을 입력해주세요.', 'error');
        return;
    }
    
    // CSRF 토큰 가져오기
    const csrfToken = getCsrfTokenValue();
    if (!csrfToken) {
        showToast('보안 토큰을 찾을 수 없습니다. 페이지를 새로고침해주세요.', 'error');
        console.error('CSRF Token not found. Check meta tag or hidden input.');
        return;
    }
    
    try {
        const requestBody = {
            ...data,
            csrf_token: csrfToken
        };
        
        const response = await fetch('/profile/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const contentType = response.headers.get('content-type');
        let result;
        
        const responseText = await response.text();
        
        if (contentType && contentType.includes('application/json')) {
            try {
                result = JSON.parse(responseText);
            } catch (e) {
                console.error('JSON 파싱 오류:', e, '응답 텍스트:', responseText);
                result = { success: false, message: responseText || '저장에 실패했습니다' };
            }
        } else {
            console.error('서버 응답 오류: JSON이 아닌 응답 수신', responseText.substring(0, 200));
            showToast('서버 응답 오류가 발생했습니다. 페이지를 새로고침해주세요.', 'error');
            return;
        }
        
        if (response.ok && result.success) {
            showToast(result.message || '저장되었습니다', 'success');
            
            // 정보 수정 모달 닫기
            const profileEditModal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
            if (profileEditModal) {
                profileEditModal.hide();
            }
            
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            let errorMsg = '저장에 실패했습니다. 다시 시도해주세요.';
            if (result) {
                if (typeof result === 'string') {
                    errorMsg = result;
                } else if (result.message) {
                    errorMsg = result.message;
                } else if (result.error) {
                    errorMsg = result.error;
                } else if (result.errors && Array.isArray(result.errors)) {
                    errorMsg = result.errors.join(', ');
                } else if (result.errors && typeof result.errors === 'object') {
                    errorMsg = Object.values(result.errors).flat().join(', ');
                }
            }
            showToast(errorMsg, 'error');
            console.error('저장 실패:', result, 'Response status:', response.status);
        }
    } catch (error) {
        console.error('네트워크 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    }
}

/**
 * 골드 고객 관리 모듈
 */
function initGoldCustomerModule() {
    const goldCard = document.getElementById('gold-customer-card');
    if (!goldCard) {
        return;
    }

    const GOLD_API_BASE = '/api/gold/customers';
    const searchInput = document.getElementById('gold-search');
    const searchBtn = document.getElementById('gold-search-btn');
    const addRowBtn = document.getElementById('gold-add-row');
    const tbody = document.getElementById('gold-tbody');
    const paginationEl = document.getElementById('gold-pagination');
    const summaryCountEl = document.getElementById('gold-summary-count');

    const state = {
        page: 1,
        pageSize: 15,
        search: '',
        hasLoaded: false
    };

    const loadingRow = '<tr><td colspan="8" class="gold-empty-row">불러오는 중...</td></tr>';

    const updateSummaryCount = (count = 0) => {
        if (summaryCountEl) {
            summaryCountEl.textContent = `${Number(count || 0).toLocaleString('ko-KR')}명`;
        }
    };

    updateSummaryCount(0);

    const loadIfNeeded = () => {
        if (state.hasLoaded) {
            return;
        }
        state.hasLoaded = true;
        fetchCustomers(1, state.search);
    };

    loadIfNeeded();

    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const keyword = (searchInput?.value || '').trim();
            fetchCustomers(1, keyword);
        });
    }

    if (searchInput) {
        searchInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                fetchCustomers(1, searchInput.value.trim());
            }
        });
    }

    if (addRowBtn && tbody) {
        addRowBtn.addEventListener('click', () => {
            const tempId = `temp-${Date.now()}`;
            tbody.insertAdjacentHTML('afterbegin', createEditRow({
                id: tempId,
                representative_name: '',
                company_name: '',
                business_number: '',
                address: '',
                email: '',
                business_kind: JSON.stringify({ 업태: '', 종목: '' })
            }));
            bindRowActions();
            const firstInput = tbody.querySelector(`tr[data-id="${tempId}"] input[data-edit="representative_name"]`);
            if (firstInput) {
                firstInput.focus();
            }
        });
    }

    async function fetchCustomers(page = state.page, search = state.search) {
        if (!tbody) {
            return;
        }

        state.page = page;
        state.search = search;
        tbody.innerHTML = loadingRow;

        try {
            const params = new URLSearchParams();
            params.set('limit', String(state.pageSize));
            params.set('offset', String((page - 1) * state.pageSize));
            if (search) {
                params.set('search', search);
            }

            const response = await fetch(`${GOLD_API_BASE}?${params.toString()}`, {
                credentials: 'same-origin'
            });
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || '목록을 불러올 수 없습니다.');
            }

            renderRows(result.data || [], result.total);
            renderPagination(result.total || 0);
        } catch (error) {
            console.error('[GOLD] 목록 로드 실패:', error);
            tbody.innerHTML = `<tr><td colspan="8" class="gold-empty-row">오류: ${escapeHtml(error.message)}</td></tr>`;
            updateSummaryCount(0);
        }
    }

    function renderRows(customers, totalCount) {
        if (!tbody) {
            return;
        }
        const effectiveTotal = typeof totalCount === 'number' ? totalCount : customers.length;
        updateSummaryCount(effectiveTotal);

        if (!customers.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="gold-empty-row">데이터가 없습니다</td></tr>';
            paginationEl && (paginationEl.innerHTML = '');
            return;
        }

        const rowsHtml = customers.map(customer => createReadRow(customer)).join('');
        tbody.innerHTML = rowsHtml;
        bindRowActions();
    }

    function renderPagination(total) {
        if (!paginationEl) {
            return;
        }

        const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
        if (totalPages <= 1) {
            paginationEl.innerHTML = '';
            return;
        }

        let html = '';
        for (let page = 1; page <= totalPages; page++) {
            const activeClass = page === state.page ? 'active' : '';
            html += `<button type="button" class="gold-page-btn ${activeClass}" data-page="${page}">${page}</button>`;
        }

        paginationEl.innerHTML = html;
        paginationEl.querySelectorAll('button[data-page]').forEach(button => {
            button.addEventListener('click', () => {
                const targetPage = Number(button.getAttribute('data-page'));
                fetchCustomers(targetPage, state.search);
            });
        });
    }

    function bindRowActions() {
        if (!tbody) {
            return;
        }

        tbody.querySelectorAll('.js-gold-edit').forEach(button => {
            button.addEventListener('click', () => {
                const row = button.closest('tr');
                if (!row) return;
                const customerData = createCustomerPayloadFromRow(row, true);
                row.outerHTML = createEditRow({
                    id: row.getAttribute('data-id') || '',
                    representative_name: customerData.representative_name,
                    company_name: customerData.company_name,
                    business_number: customerData.business_number,
                    address: customerData.address,
                    email: customerData.email,
                    business_kind: customerData.business_kind
                });
                bindRowActions();
            });
        });

        tbody.querySelectorAll('.js-gold-delete').forEach(button => {
            button.addEventListener('click', async () => {
                const id = button.getAttribute('data-id');
                if (!id) return;
                const confirmed = window.confirm('선택한 고객을 삭제하시겠습니까?');
                if (!confirmed) return;
                await deleteCustomer(id);
            });
        });

        tbody.querySelectorAll('.js-gold-save').forEach(button => {
            button.addEventListener('click', async () => {
                const row = button.closest('tr');
                if (!row) return;
                await persistRow(row);
            });
        });

        tbody.querySelectorAll('.js-gold-cancel').forEach(button => {
            button.addEventListener('click', () => {
                fetchCustomers(state.page, state.search);
            });
        });
    }

    async function deleteCustomer(id) {
        try {
            const response = await fetch(`${GOLD_API_BASE}/${id}`, {
                method: 'DELETE',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': getCsrfTokenValue()
                }
            });
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || '삭제에 실패했습니다.');
            }
            showToast('삭제되었습니다', 'success');
            fetchCustomers(state.page, state.search);
        } catch (error) {
            console.error('[GOLD] 삭제 실패:', error);
            showToast(error.message, 'error');
        }
    }

    async function persistRow(row) {
        const payload = createCustomerPayloadFromRow(row, false);
        const validationMessage = validateGoldPayload(payload);
        if (validationMessage) {
            showToast(validationMessage, 'error');
            return;
        }

        const rowId = row.getAttribute('data-id') || '';
        const isNew = !rowId || rowId.startsWith('temp-');
        const method = isNew ? 'POST' : 'PUT';
        const url = isNew ? GOLD_API_BASE : `${GOLD_API_BASE}/${rowId}`;

        try {
            const response = await fetch(url, {
                method,
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfTokenValue()
                },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || '저장에 실패했습니다.');
            }
            showToast('저장되었습니다', 'success');
            fetchCustomers(state.page, state.search);
        } catch (error) {
            console.error('[GOLD] 저장 실패:', error);
            showToast(error.message, 'error');
        }
    }

    function createCustomerPayloadFromRow(row, fromViewRow) {
        if (fromViewRow) {
            const businessKind = parseBusinessKind(JSON.stringify({
                업태: row.querySelector('td[data-k="business_type"] input')?.value || '',
                종목: row.querySelector('td[data-k="business_item"] input')?.value || ''
            }));
            return {
                representative_name: row.querySelector('td[data-k="representative_name"] input')?.value || '',
                company_name: row.querySelector('td[data-k="company_name"] input')?.value || '',
                business_number: (row.querySelector('td[data-k="business_number"] input')?.value || '').replace(/[^0-9]/g, ''),
                address: row.querySelector('td[data-k="address"] input')?.value || '',
                email: row.querySelector('td[data-k="email"] input')?.value || '',
                business_kind: JSON.stringify(businessKind)
            };
        }

        const businessKindObj = {
            업태: row.querySelector('input[data-edit="business_type"]')?.value || '',
            종목: row.querySelector('input[data-edit="business_item"]')?.value || ''
        };

        return {
            representative_name: row.querySelector('input[data-edit="representative_name"]')?.value || '',
            company_name: row.querySelector('input[data-edit="company_name"]')?.value || '',
            business_number: (row.querySelector('input[data-edit="business_number"]')?.value || '').replace(/[^0-9]/g, ''),
            address: row.querySelector('input[data-edit="address"]')?.value || '',
            email: row.querySelector('input[data-edit="email"]')?.value || '',
            business_kind: JSON.stringify(businessKindObj)
        };
    }

    function validateGoldPayload(payload) {
        if (!payload.company_name) return '업체명을 입력해주세요';
        if (!payload.representative_name) return '대표자명을 입력해주세요';
        if (!/^\d{10}$/.test(payload.business_number)) return '사업자등록번호는 하이픈 없이 10자리여야 합니다';
        if (!payload.address) return '주소를 입력해주세요';
        if (payload.email && !/^[-\w.+]+@[-\w.]+\.[A-Za-z]{2,}$/.test(payload.email)) return '이메일 형식이 올바르지 않습니다';
        return '';
    }

    function createReadRow(customer) {
        const formattedBn = formatBusinessNumber(customer.business_number || '');
        const businessInfo = parseBusinessKind(customer.business_kind);
        const id = escapeHtml(String(customer.id || ''));
        return `
            <tr class="gold-row-view" data-id="${id}">
                <td data-k="representative_name"><input type="text" class="sheet-input" value="${escapeHtml(customer.representative_name || '')}" readonly></td>
                <td data-k="company_name"><input type="text" class="sheet-input" value="${escapeHtml(customer.company_name || '')}" readonly></td>
                <td data-k="business_number"><input type="text" class="sheet-input" value="${escapeHtml(formattedBn)}" readonly></td>
                <td data-k="address"><input type="text" class="sheet-input" value="${escapeHtml(customer.address || '')}" readonly></td>
                <td data-k="email"><input type="text" class="sheet-input" value="${escapeHtml(customer.email || '')}" readonly></td>
                <td data-k="business_type"><input type="text" class="sheet-input" value="${escapeHtml(businessInfo.업태)}" readonly></td>
                <td data-k="business_item"><input type="text" class="sheet-input" value="${escapeHtml(businessInfo.종목)}" readonly></td>
                <td>
                    <div class="actions-wrap">
                        <button type="button" class="icon-btn js-gold-edit" data-id="${id}" aria-label="수정">✏️</button>
                        <button type="button" class="icon-btn js-gold-delete" data-id="${id}" aria-label="삭제">🗑️</button>
                    </div>
                </td>
            </tr>
        `;
    }

    function createEditRow(customer) {
        const businessInfo = parseBusinessKind(customer.business_kind);
        const id = escapeHtml(String(customer.id || ''));
        return `
            <tr class="gold-row-edit" data-id="${id}">
                <td><input type="text" class="sheet-input" data-edit="representative_name" value="${escapeHtml(customer.representative_name || '')}" placeholder="대표자명"></td>
                <td><input type="text" class="sheet-input" data-edit="company_name" value="${escapeHtml(customer.company_name || '')}" placeholder="업체명"></td>
                <td><input type="text" class="sheet-input" data-edit="business_number" value="${escapeHtml(customer.business_number || '')}" placeholder="10자리"></td>
                <td><input type="text" class="sheet-input" data-edit="address" value="${escapeHtml(customer.address || '')}" placeholder="주소"></td>
                <td><input type="text" class="sheet-input" data-edit="email" value="${escapeHtml(customer.email || '')}" placeholder="이메일"></td>
                <td><input type="text" class="sheet-input" data-edit="business_type" value="${escapeHtml(businessInfo.업태)}" placeholder="업태"></td>
                <td><input type="text" class="sheet-input" data-edit="business_item" value="${escapeHtml(businessInfo.종목)}" placeholder="종목"></td>
                <td>
                    <div class="actions-wrap">
                        <button type="button" class="icon-btn js-gold-save" data-id="${id}" aria-label="저장">✔️</button>
                        <button type="button" class="icon-btn js-gold-cancel" data-id="${id}" aria-label="취소">❌</button>
                    </div>
                </td>
            </tr>
        `;
    }

    function parseBusinessKind(value) {
        try {
            const parsed = typeof value === 'string' ? JSON.parse(value || '{}') : (value || {});
            return {
                업태: parsed.업태 || parsed.business_type || '',
                종목: parsed.종목 || parsed.business_item || ''
            };
        } catch (_) {
            return { 업태: '', 종목: '' };
        }
    }

    function formatBusinessNumber(value) {
        const digits = String(value || '').replace(/\D/g, '');
        if (digits.length !== 10) {
            return digits;
        }
        return digits.replace(/(\d{3})(\d{2})(\d{5})/, '$1-$2-$3');
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        };
        return String(text || '').replace(/[&<>"']/g, char => map[char]);
    }
}

/**
 * 토스트 알림 표시 함수
 */
function showToast(message, type = 'info') {
    // 기존 토스트 제거
    const existingToast = document.getElementById('toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    // 새 토스트 생성
    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = 'toast-notification';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        animation: slideInRight 0.3s ease-out;
        max-width: 400px;
        word-wrap: break-word;
    `;
    
    if (type === 'success') {
        toast.style.background = 'linear-gradient(135deg, rgb(16, 185, 129) 0%, rgb(5, 150, 105) 100%)';
    } else if (type === 'error') {
        toast.style.background = 'linear-gradient(135deg, rgb(220, 38, 38) 0%, rgb(185, 28, 28) 100%)';
    } else {
        toast.style.background = 'linear-gradient(135deg, rgb(59, 130, 246) 0%, rgb(37, 99, 235) 100%)';
    }
    
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// CSS 애니메이션 추가
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * 필드 유효성 검사
 */
function validateProfileField(field) {
    const value = field.value.trim();
    const fieldName = field.name;
    const msgElement = document.getElementById(fieldName + '_msg');
    
    let isValid = true;
    let message = '';
    
    switch(fieldName) {
        case 'company_name':
            if (value.length < 1) {
                isValid = false;
                message = '❌ 회사명을 입력해주세요';
            } else if (value.length > 50) {
                isValid = false;
                message = '❌ 회사명은 50자 이하로 입력해주세요';
            } else {
                message = '✅ 올바른 회사명입니다';
            }
            break;
            
        case 'representative_name':
            if (value.length < 1) {
                isValid = false;
                message = '❌ 대표자명을 입력해주세요';
            } else if (!/^[가-힣a-zA-Z\s]+$/.test(value)) {
                isValid = false;
                message = '❌ 대표자명은 한글, 영문만 입력 가능합니다';
            } else {
                message = '✅ 올바른 대표자명입니다';
            }
            break;
            
        case 'phone':
            if (value.length < 1) {
                isValid = false;
                message = '❌ 전화번호를 입력해주세요';
            } else {
                const digits = value.replace(/\D/g, '');
                if (!/^(02|0[3-9]\d|010|070)\d{3,4}\d{4}$/.test(digits)) {
                    isValid = false;
                    message = '❌ 올바른 전화번호 형식이 아닙니다 (예: 010-9702-3996 또는 01097023996)';
                } else {
                    message = '✅ 올바른 전화번호입니다';
                }
            }
            break;
            
        case 'email':
            if (value.length < 1) {
                isValid = false;
                message = '❌ 이메일을 입력해주세요';
            } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value)) {
                isValid = false;
                message = '❌ 올바른 이메일 형식이 아닙니다';
            } else {
                message = '✅ 올바른 이메일입니다';
            }
            break;
            
        case 'business_type':
            if (value.length < 1) {
                isValid = false;
                message = '❌ 업태를 입력해주세요';
            } else if (value.length < 2) {
                isValid = false;
                message = '❌ 업태는 2자 이상 입력해주세요';
            } else if (!/^[가-힣a-zA-Z0-9\s]+$/.test(value)) {
                isValid = false;
                message = '❌ 업태는 한글, 영문, 숫자만 입력 가능합니다';
            } else {
                message = '✅ 올바른 업태입니다';
            }
            break;
            
        case 'business_category':
            if (value.length < 1) {
                isValid = false;
                message = '❌ 종목을 입력해주세요';
            } else if (value.length < 3) {
                isValid = false;
                message = '❌ 종목은 3자 이상 입력해주세요';
            } else if (!/^[가-힣a-zA-Z0-9\s]+$/.test(value)) {
                isValid = false;
                message = '❌ 종목은 한글, 영문, 숫자만 입력 가능합니다';
            } else {
                message = '✅ 올바른 종목입니다';
            }
            break;
    }
    
    if (msgElement) {
        msgElement.textContent = message;
        msgElement.className = 'validation-message ' + (isValid ? 'success' : 'error');
    }
    
    return isValid;
}

/**
 * 모든 필드 유효성 검사
 */
function validateAllProfileFields() {
    const form = document.getElementById('profileForm');
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required]');
    let allValid = true;
    inputs.forEach(input => {
        if (!validateProfileField(input)) {
            allValid = false;
        }
    });
    return allValid;
}

/**
 * CSRF 토큰 헬퍼
 */
function getCsrfTokenValue() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
        || document.querySelector('input[name="csrf_token"]')?.value
        || document.querySelector('input[type="hidden"][name="csrf_token"]')?.value
        || '';
}


