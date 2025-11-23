/**
 * 결제 관리 대시보드 모듈
 * 금융 앱 스타일의 결제 관리 UI
 */

// CSRF 토큰 함수 (전역 함수가 없을 때만 선언)
if (typeof window.getCSRFToken === 'undefined') {
    window.getCSRFToken = function() {
        if (typeof csrfToken === 'function') {
            return csrfToken();
        }
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') || '' : '';
    };
}

// 차트 인스턴스
let revenueChart = null;

// 현재 페이지 상태
let currentPage = 1;
let currentStatusFilter = '';
let currentStartDate = null;
let currentEndDate = null;
let currentPeriod = 'all'; // 'today', 'week', 'month', 'all'

// 테마 색상 (전역 변수가 없을 때만 선언)
if (typeof window.themeColors === 'undefined') {
    window.themeColors = {
        primary: '#10B981',
        primaryDark: '#059669',
        primaryLight: '#34D399',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        info: '#3B82F6',
        muted: '#6B7280'
    };
}

/**
 * 숫자에 천 단위 콤마 추가
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('ko-KR').format(amount) + '원';
}

/**
 * 숫자에 콤마만 추가 (원 없이)
 */
function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR').format(num);
}

/**
 * 날짜 계산 함수 (순수 JS)
 */
function getDateRange(period) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    let startDate = null;
    let endDate = new Date(today);
    endDate.setHours(23, 59, 59, 999);
    
    switch(period) {
        case 'today':
            startDate = new Date(today);
            break;
        case 'week':
            // 이번 주 월요일부터 오늘까지
            const dayOfWeek = today.getDay();
            const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // 월요일로 조정
            startDate = new Date(today);
            startDate.setDate(diff);
            startDate.setHours(0, 0, 0, 0);
            break;
        case 'month':
            // 이번 달 1일부터 오늘까지
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            break;
        case 'all':
        default:
            startDate = null;
            endDate = null;
            break;
    }
    
    return {
        start: startDate ? startDate.toISOString().split('T')[0] : null,
        end: endDate ? endDate.toISOString().split('T')[0] : null
    };
}

/**
 * 날짜 범위를 YYYY-MM-DD 형식으로 변환
 */
function formatDateForAPI(date) {
    if (!date) return null;
    if (typeof date === 'string') return date;
    return date.toISOString().split('T')[0];
}

/**
 * 상품 아이콘 및 색상 HTML 생성
 */
function getProductBadge(tokenAmount) {
    if (tokenAmount === -1) {
        // Gold
        return '<span class="badge rounded-pill" style="background: linear-gradient(135deg, #FCD34D 0%, #FBBF24 100%); color: #78350F;"><i class="bi bi-star-fill"></i> Gold</span>';
    } else if (tokenAmount >= 100) {
        // Premium
        return '<span class="badge rounded-pill" style="background: linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%); color: white;"><i class="bi bi-star"></i> Premium</span>';
    } else {
        // Standard
        return '<span class="badge rounded-pill" style="background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%); color: white;"><i class="bi bi-circle-fill"></i> Standard</span>';
    }
}

/**
 * 결제 상태에 따른 Pill Badge HTML 생성
 */
function getStatusBadge(status) {
    const statusMap = {
        'pending': { text: '대기중', class: 'bg-warning text-dark' },
        'completed': { text: '완료', class: 'bg-success' },
        'failed': { text: '실패', class: 'bg-danger' },
        'cancelled': { text: '취소', class: 'bg-secondary' }
    };
    
    const statusInfo = statusMap[status.toLowerCase()] || { text: status, class: 'bg-secondary' };
    return `<span class="badge rounded-pill ${statusInfo.class}">${statusInfo.text}</span>`;
}

/**
 * 결제 목록 로드
 */
async function loadPayments(page = 1, status = '', startDate = null, endDate = null) {
    try {
        currentPage = page;
        currentStatusFilter = status;
        currentStartDate = startDate;
        currentEndDate = endDate;
        
        // 로딩 표시
        const tbody = document.getElementById('paymentLedgerBody');
        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">결제 데이터를 불러오는 중...</td></tr>';
        
        // API 호출
        const params = new URLSearchParams({
            page: page,
            per_page: 20
        });
        
        if (status) {
            params.append('status', status);
        }
        
        // 날짜 파라미터 추가 (null이 아닐 때만)
        const formattedStartDate = formatDateForAPI(startDate);
        if (formattedStartDate) {
            params.append('start_date', formattedStartDate);
        }
        
        const formattedEndDate = formatDateForAPI(endDate);
        if (formattedEndDate) {
            params.append('end_date', formattedEndDate);
        }
        
        const response = await fetch(`/admin/api/payments?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                const errorData = await response.json();
                tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-danger">${errorData.message || '인증 오류'}</td></tr>`;
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 디버깅: API 응답 구조 확인
        console.log('[Payment API Response]', result);
        console.log('[Payment API Data]', result.data);
        
        if (result.success && result.data) {
            console.log('[Payment Data Structure]', {
                hasPayments: 'payments' in result.data,
                paymentsCount: result.data.payments ? result.data.payments.length : 0,
                hasKpiStats: 'kpi_stats' in result.data,
                hasDailyTrend: 'daily_revenue_trend' in result.data,
                hasLatestPayments: 'latest_payments' in result.data
            });
            
            try {
                renderPaymentTable(result.data);
                updateKPICards(result.data);
                // API에서 제공하는 latest_payments 사용
                updateRecentPaymentsFeed(result.data.latest_payments || result.data.payments || []);
                renderPagination(result.data);
            } catch (renderError) {
                console.error('[Render Error]', renderError);
                tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-danger">렌더링 오류: ${renderError.message}</td></tr>`;
            }
        } else {
            console.warn('[Payment API] success=false or data missing', result);
            tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">결제 데이터가 없습니다.</td></tr>';
        }
        
    } catch (error) {
        console.error('[Payment Load Error]', error);
        console.error('[Error Stack]', error.stack);
        const tbody = document.getElementById('paymentLedgerBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-danger">결제 데이터 로드 실패: ${error.message}</td></tr>`;
        }
    }
}

/**
 * 결제 테이블 렌더링
 */
function renderPaymentTable(data) {
    console.log('[renderPaymentTable] data:', data);
    
    const tbody = document.getElementById('paymentLedgerBody');
    if (!tbody) {
        console.error('[renderPaymentTable] paymentLedgerBody 요소를 찾을 수 없음');
        return;
    }
    
    const payments = data.payments || [];
    console.log('[renderPaymentTable] payments 개수:', payments.length);
    
    if (payments.length === 0) {
        console.warn('[renderPaymentTable] 결제 데이터가 없음');
        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">결제 데이터가 없습니다.</td></tr>';
        return;
    }
    
    try {
        tbody.innerHTML = payments.map(payment => {
            console.log('[renderPaymentTable] payment:', payment);
            
            // 유저 정보 표시 (이름과 이메일)
            const userName = payment.user_name || `유저 #${payment.user_id || 'N/A'}`;
            const userEmail = payment.user_email || '';
            const userDisplay = userEmail 
                ? `<div class="fw-semibold">${userName}</div><div class="text-muted small">${userEmail}</div>`
                : `<div class="fw-semibold">${userName}</div>`;
            
            return `
                <tr>
                    <td><code class="text-primary">${payment.order_id || 'N/A'}</code></td>
                    <td>${userDisplay}</td>
                    <td>${getProductBadge(payment.token_amount || 0)}</td>
                    <td class="text-end payment-amount fw-bold">${formatCurrency(payment.amount || 0)}</td>
                    <td class="payment-token">${payment.token_amount === -1 ? '<span class="text-warning">무제한</span>' : formatNumber(payment.token_amount || 0) + '개'}</td>
                    <td>${getStatusBadge(payment.status || 'pending')}</td>
                    <td><small class="text-muted">${payment.pg_provider || '-'}</small></td>
                    <td><small class="text-muted">${formatDateTime(payment.created_at || '')}</small></td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-primary" onclick="viewPaymentDetail(${payment.id || 0})" title="상세보기">
                            <i class="bi bi-eye"></i>
                        </button>
                        ${payment.status === 'pending' ? `
                            <button class="btn btn-sm btn-outline-success" onclick="updatePaymentStatus(${payment.id || 0}, 'completed')" title="완료 처리">
                                <i class="bi bi-check-circle"></i>
                            </button>
                        ` : ''}
                        ${(payment.status === 'cancelled' || payment.status === 'failed') ? `
                            <button class="btn btn-sm btn-outline-danger" onclick="deletePayment(${payment.id || 0})" title="기록 삭제">
                                <i class="bi bi-trash"></i>
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `;
        }).join('');
        console.log('[renderPaymentTable] 테이블 렌더링 완료');
    } catch (error) {
        console.error('[renderPaymentTable] 렌더링 오류:', error);
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-danger">렌더링 오류: ${error.message}</td></tr>`;
    }
}

/**
 * KPI 카드 업데이트
 */
function updateKPICards(data) {
    console.log('[updateKPICards] data:', data);
    
    // API에서 제공하는 KPI 통계 사용
    const kpiStats = data.kpi_stats || {};
    console.log('[updateKPICards] kpiStats:', kpiStats);
    
    // KPI 카드 업데이트
    const periodRevenueEl = document.getElementById('periodRevenue');
    const periodCountEl = document.getElementById('periodCount');
    const refundCountEl = document.getElementById('refundCount');
    
    if (periodRevenueEl) {
        periodRevenueEl.textContent = formatCurrency(kpiStats.period_revenue || 0);
    } else {
        console.error('[updateKPICards] periodRevenue element not found');
    }
    
    if (periodCountEl) {
        periodCountEl.textContent = `${formatNumber(kpiStats.period_payment_count || 0)}건`;
    } else {
        console.error('[updateKPICards] periodCount element not found');
    }
    
    if (refundCountEl) {
        refundCountEl.textContent = `${formatNumber(kpiStats.refund_requests || 0)}건`;
    } else {
        console.error('[updateKPICards] refundCount element not found');
    }
    
    // 상태별 건수 계산 및 배지 업데이트 (백엔드에서 제공하는 status_counts 사용)
    const statusCounts = data.status_counts || {
        'all': data.total || 0,
        'completed': 0,
        'pending': 0,
        'cancelled': 0,
        'failed': 0
    };
    
    // 전체 건수는 total 사용 (status_counts에 없을 경우)
    if (!statusCounts.all && data.total !== undefined) {
        statusCounts.all = data.total;
    }
    
    // 배지 업데이트
    updateStatusBadges(statusCounts);
    
    // 매출 추이 차트 업데이트 (API에서 제공하는 daily_revenue_trend 사용)
    if (data.daily_revenue_trend) {
        console.log('[updateKPICards] Using daily_revenue_trend:', data.daily_revenue_trend);
        updateRevenueChartFromTrend(data.daily_revenue_trend);
    } else {
        console.warn('[updateKPICards] daily_revenue_trend not found, using fallback');
        // Fallback: 기존 방식 (payments 배열 사용)
        const payments = data.payments || [];
        updateRevenueChart(payments);
    }
}

/**
 * 최신 결제 피드 업데이트
 */
function updateRecentPaymentsFeed(payments) {
    const feed = document.getElementById('recentPaymentsFeed');
    const recentPayments = payments.slice(0, 5);
    
    if (recentPayments.length === 0) {
        feed.innerHTML = '<div class="text-center py-4 text-muted"><small>최근 결제 내역이 없습니다.</small></div>';
        return;
    }
    
    feed.innerHTML = recentPayments.map(payment => `
        <div class="payment-feed-item">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                    <div class="fw-bold small">${payment.order_id}</div>
                    <div class="text-muted" style="font-size: 0.75rem;">유저 #${payment.user_id}</div>
                </div>
                <div class="text-end">
                    <div class="payment-feed-amount">${formatCurrency(payment.amount)}</div>
                    <div class="text-muted" style="font-size: 0.7rem;">${payment.token_amount === -1 ? '<span class="text-warning">♾️ 무제한</span>' : formatNumber(payment.token_amount) + ' 토큰'}</div>
                </div>
            </div>
            <div class="d-flex justify-content-between align-items-center">
                ${getStatusBadge(payment.status)}
                <small class="text-muted">${formatDateTime(payment.created_at)}</small>
            </div>
        </div>
    `).join('');
}

/**
 * 매출 추이 차트 업데이트 (API의 daily_revenue_trend 사용)
 */
function updateRevenueChartFromTrend(dailyRevenueTrend) {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;
    
    // 날짜 포맷팅 (MM/DD)
    const labels = dailyRevenueTrend.map(item => {
        const d = new Date(item.date);
        return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')}`;
    });
    
    const revenueData = dailyRevenueTrend.map(item => item.revenue);
    
    // 기존 차트가 있으면 파괴
    if (revenueChart) {
        revenueChart.destroy();
    }
    
    // 새 차트 생성
    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '매출 (원)',
                data: revenueData,
                borderColor: window.themeColors.primary,
                backgroundColor: `${window.themeColors.primary}20`,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: window.themeColors.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `매출: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    },
                    grid: {
                        color: '#E5E7EB'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * 매출 추이 차트 업데이트 (Fallback: payments 배열 사용)
 */
function updateRevenueChart(payments) {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;
    
    // 최근 7일간 매출 데이터 집계
    const last7Days = [];
    const revenueData = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        last7Days.push(dateStr);
        
        const dayRevenue = payments
            .filter(p => p.created_at.startsWith(dateStr) && p.status === 'completed')
            .reduce((sum, p) => sum + p.amount, 0);
        
        revenueData.push(dayRevenue);
    }
    
    // 날짜 포맷팅 (MM/DD)
    const labels = last7Days.map(date => {
        const d = new Date(date);
        return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')}`;
    });
    
    // 기존 차트가 있으면 파괴
    if (revenueChart) {
        revenueChart.destroy();
    }
    
    // 새 차트 생성
    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '매출 (원)',
                data: revenueData,
                borderColor: window.themeColors.primary,
                backgroundColor: `${window.themeColors.primary}20`,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: window.themeColors.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `매출: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    },
                    grid: {
                        color: '#E5E7EB'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * 페이징 렌더링
 */
function renderPagination(data) {
    const pagination = document.getElementById('paymentPagination');
    const info = document.getElementById('paymentPaginationInfo');
    
    const total = data.total || 0;
    const page = data.page || 1;
    const perPage = data.per_page || 20;
    const totalPages = Math.ceil(total / perPage);
    
    // 정보 업데이트
    info.textContent = `전체 ${formatNumber(total)}건 (페이지 ${page}/${totalPages})`;
    
    // 페이징 버튼 생성
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 이전 버튼
    if (page > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="currentPage = ${page - 1}; refreshPaymentData(); return false;">이전</a></li>`;
    }
    
    // 페이지 번호 버튼
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);
    
    if (startPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="currentPage = 1; refreshPaymentData(); return false;">1</a></li>`;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === page ? 'active' : '';
        paginationHTML += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="currentPage = ${i}; refreshPaymentData(); return false;">${i}</a></li>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="currentPage = ${totalPages}; refreshPaymentData(); return false;">${totalPages}</a></li>`;
    }
    
    // 다음 버튼
    if (page < totalPages) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="currentPage = ${page + 1}; refreshPaymentData(); return false;">다음</a></li>`;
    }
    
    pagination.innerHTML = paginationHTML;
}

/**
 * 날짜/시간 포맷팅
 */
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '-';
    const date = new Date(dateTimeStr);
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

/**
 * 결제 상세보기
 */
async function viewPaymentDetail(paymentId) {
    try {
        console.log('[viewPaymentDetail] 결제 상세 정보 로드 시작:', paymentId);
        
        // 모달 열기
        const modal = new bootstrap.Modal(document.getElementById('paymentDetailModal'));
        modal.show();
        
        // 로딩 표시
        const contentEl = document.getElementById('paymentDetailContent');
        const footerEl = document.getElementById('paymentDetailFooter');
        contentEl.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">결제 정보를 불러오는 중...</p>
            </div>
        `;
        footerEl.innerHTML = '';
        
        // API 호출
        const response = await fetch(`/admin/api/payments/${paymentId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `결제 정보 조회 실패: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[viewPaymentDetail] API 응답:', result);
        
        if (!result.success || !result.data) {
            throw new Error('결제 정보를 불러올 수 없습니다.');
        }
        
        const payment = result.data;
        
        // 유저 정보 조회 (유저명 가져오기)
        let userName = `유저 #${payment.user_id}`;
        try {
            const userResponse = await fetch(`/admin/api/users/${payment.user_id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.getCSRFToken()
                },
                credentials: 'include'
            });
            if (userResponse.ok) {
                const userResult = await userResponse.json();
                if (userResult.success && userResult.data) {
                    userName = userResult.data.username || userName;
                }
            }
        } catch (e) {
            console.warn('[viewPaymentDetail] 유저 정보 조회 실패:', e);
        }
        
        // 상품 정보 조회 (상품명 가져오기)
        let productName = '알 수 없음';
        let isGoldProduct = false;
        try {
            // payment_history에는 product_id가 없으므로, order_id나 다른 방법으로 추론
            // 일단 토큰 양으로 표시
            if (payment.token_amount === -1) {
                productName = 'Gold (무제한)';
                isGoldProduct = true;
            } else if (payment.token_amount >= 100) {
                productName = 'Premium';
            } else {
                productName = 'Standard';
            }
        } catch (e) {
            console.warn('[viewPaymentDetail] 상품 정보 조회 실패:', e);
        }
        
        // Gold 상품인 경우 사용자의 구독 종료일 조회
        let subscriptionInfo = '';
        if (isGoldProduct) {
            try {
                const userResponse = await fetch(`/admin/api/users/${payment.user_id}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': window.getCSRFToken()
                    },
                    credentials: 'include'
                });
                if (userResponse.ok) {
                    const userResult = await userResponse.json();
                    if (userResult.success && userResult.data && userResult.data.subscription_end_date) {
                        const endDate = new Date(userResult.data.subscription_end_date);
                        subscriptionInfo = `
                            <tr>
                                <td class="text-muted" style="padding: 0.5rem 0;">구독 기간</td>
                                <td style="padding: 0.5rem 0;">
                                    <strong>30일</strong><br>
                                    <small class="text-success">만료일: ${endDate.toLocaleDateString('ko-KR')} ${endDate.toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'})}</small>
                                </td>
                            </tr>
                        `;
                    }
                }
            } catch (e) {
                console.warn('[viewPaymentDetail] 구독 정보 조회 실패:', e);
            }
        }
        
        // 유저 이메일 조회
        let userEmail = '';
        try {
            const userResponse = await fetch(`/admin/api/users/${payment.user_id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.getCSRFToken()
                },
                credentials: 'include'
            });
            if (userResponse.ok) {
                const userResult = await userResponse.json();
                if (userResult.success && userResult.data) {
                    userEmail = userResult.data.email || '';
                }
            }
        } catch (e) {
            console.warn('[viewPaymentDetail] 유저 이메일 조회 실패:', e);
        }
        
        // 영수증 스타일 상세 정보 렌더링
        const paymentDate = payment.created_at ? new Date(payment.created_at) : new Date();
        const formattedDate = paymentDate.toLocaleDateString('ko-KR', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        contentEl.innerHTML = `
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <!-- 영수증 정보 테이블 -->
                <table class="table table-borderless mb-0" style="font-size: 0.95rem;">
                    <tbody>
                        <tr>
                            <td class="text-muted" style="width: 120px; padding: 0.5rem 0;">주문번호</td>
                            <td style="padding: 0.5rem 0;"><code class="text-primary fw-bold">${payment.order_id || 'N/A'}</code></td>
                        </tr>
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
                            <td style="padding: 0.5rem 0;">${formattedDate}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">결제수단</td>
                            <td style="padding: 0.5rem 0;">${payment.pg_provider || '수동 결제'}</td>
                        </tr>
                        <tr>
                            <td class="text-muted" style="padding: 0.5rem 0;">상태</td>
                            <td style="padding: 0.5rem 0;">${getStatusBadge(payment.status || 'pending')}</td>
                        </tr>
                        ${subscriptionInfo}
                    </tbody>
                </table>
                
                <!-- 구분선 -->
                <hr style="border-top: 2px dashed #d1d5db; margin: 1.5rem 0;">
                
                <!-- 총액 -->
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted" style="font-size: 1.1rem; font-weight: 600;">Total</span>
                    <span class="fw-bold" style="font-size: 1.5rem; color: #10B981;">₩ ${(payment.amount || 0).toLocaleString()}</span>
                </div>
            </div>
        `;
        
        // 결제 취소 버튼 (completed 상태인 경우만)
        // 삭제 버튼 (cancelled 또는 failed 상태인 경우만)
        if (payment.status === 'completed') {
            footerEl.innerHTML = `
                <div class="w-100 d-flex justify-content-end gap-2">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">닫기</button>
                    <button type="button" class="btn btn-danger" onclick="cancelPayment(${payment.id})">
                        <i class="bi bi-x-circle"></i> 결제 취소
                    </button>
                </div>
            `;
        } else if (payment.status === 'cancelled' || payment.status === 'failed') {
            footerEl.innerHTML = `
                <div class="w-100 d-flex justify-content-end gap-2">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">닫기</button>
                    <button type="button" class="btn btn-danger" onclick="deletePayment(${payment.id})">
                        <i class="bi bi-trash"></i> 기록 삭제
                    </button>
                </div>
            `;
        } else {
            footerEl.innerHTML = `
                <div class="w-100 d-flex justify-content-end">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">닫기</button>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('[viewPaymentDetail] 오류:', error);
        const contentEl = document.getElementById('paymentDetailContent');
        contentEl.innerHTML = `
            <div class="alert alert-danger">
                <h6 class="alert-heading">오류 발생</h6>
                <p class="mb-0">${error.message}</p>
            </div>
        `;
        const footerEl = document.getElementById('paymentDetailFooter');
        footerEl.innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
        `;
    }
}

/**
 * 결제 기록 삭제
 */
async function deletePayment(paymentId) {
    // 확인 창
    if (!confirm('정말 이 결제 기록을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.')) {
        return;
    }
    
    try {
        console.log('[deletePayment] 결제 삭제 시작:', paymentId);
        
        const response = await fetch(`/admin/api/payments/${paymentId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `결제 삭제 실패: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[deletePayment] API 응답:', result);
        
        if (result.success) {
            // 모달 닫기 (열려있다면)
            const modal = bootstrap.Modal.getInstance(document.getElementById('paymentDetailModal'));
            if (modal) {
                modal.hide();
            }
            
            alert('결제 기록이 성공적으로 삭제되었습니다.');
            
            // 테이블 새로고침
            refreshPaymentData();
        } else {
            throw new Error(result.message || '결제 삭제에 실패했습니다.');
        }
        
    } catch (error) {
        console.error('[deletePayment] 오류:', error);
        alert(`결제 삭제 중 오류가 발생했습니다: ${error.message}`);
    }
}

/**
 * 결제 취소
 */
async function cancelPayment(paymentId) {
    // 확인 창
    if (!confirm('정말 취소하시겠습니까?\n\n토큰이 회수됩니다.')) {
        return;
    }
    
    try {
        console.log('[cancelPayment] 결제 취소 시작:', paymentId);
        
        const response = await fetch(`/admin/api/payments/${paymentId}/cancel`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `결제 취소 실패: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[cancelPayment] API 응답:', result);
        
        if (result.success) {
            // 모달 닫기
            const modal = bootstrap.Modal.getInstance(document.getElementById('paymentDetailModal'));
            if (modal) {
                modal.hide();
            }
            
            alert('결제가 성공적으로 취소되었습니다.\n토큰이 회수되었습니다.');
            
            // 테이블 새로고침
            loadPayments(currentPage, currentStatusFilter);
        } else {
            throw new Error(result.message || '결제 취소에 실패했습니다.');
        }
        
    } catch (error) {
        console.error('[cancelPayment] 오류:', error);
        alert(`결제 취소 중 오류가 발생했습니다: ${error.message}`);
    }
}

/**
 * 결제 상태 업데이트
 */
async function updatePaymentStatus(paymentId, newStatus) {
    if (!confirm('결제 상태를 변경하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/payments/${paymentId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include',
            body: JSON.stringify({ status: newStatus })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            alert(`상태 업데이트 실패: ${errorData.message || '알 수 없는 오류'}`);
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            alert('결제 상태가 업데이트되었습니다.');
            refreshPaymentData();
        }
        
    } catch (error) {
        console.error('결제 상태 업데이트 오류:', error);
        alert(`상태 업데이트 중 오류가 발생했습니다: ${error.message}`);
    }
}

/**
 * 상태별 건수 배지 업데이트
 */
function updateStatusBadges(statusCounts) {
    const badges = {
        'all': document.getElementById('badge-all'),
        'completed': document.getElementById('badge-completed'),
        'pending': document.getElementById('badge-pending'),
        'cancelled': document.getElementById('badge-cancelled'),
        'failed': document.getElementById('badge-failed')
    };
    
    for (const [status, badgeEl] of Object.entries(badges)) {
        if (badgeEl) {
            badgeEl.textContent = statusCounts[status] || 0;
        }
    }
}

/**
 * 기간 버튼 클릭 이벤트 처리
 */
function handlePeriodButtonClick(period) {
    currentPeriod = period;
    
    // 모든 버튼에서 active 클래스 제거
    document.querySelectorAll('#periodButtonGroup button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 클릭된 버튼에 active 클래스 추가
    const clickedButton = document.querySelector(`#periodButtonGroup button[data-period="${period}"]`);
    if (clickedButton) {
        clickedButton.classList.add('active');
    }
    
    // 날짜 범위 계산
    const dateRange = getDateRange(period);
    currentStartDate = dateRange.start;
    currentEndDate = dateRange.end;
    
    // Date Picker 업데이트
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) {
        startDateInput.value = dateRange.start || '';
    }
    if (endDateInput) {
        endDateInput.value = dateRange.end || '';
    }
    
    // 데이터 새로고침
    refreshPaymentData();
}

/**
 * Date Picker 변경 이벤트 처리
 */
function handleDatePickerChange() {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        currentStartDate = startDateInput.value || null;
        currentEndDate = endDateInput.value || null;
        
        // 수동 날짜 선택 시 기간 버튼 active 제거
        if (currentStartDate || currentEndDate) {
            document.querySelectorAll('#periodButtonGroup button').forEach(btn => {
                btn.classList.remove('active');
            });
            currentPeriod = 'custom';
        }
        
        // 데이터 새로고침
        refreshPaymentData();
    }
}

/**
 * 상태 탭 클릭 이벤트 처리
 */
function handleStatusTabClick(status) {
    currentStatusFilter = status;
    currentPage = 1;
    refreshPaymentData();
}

/**
 * 결제 데이터 전체 새로고침 (KPI, 차트, 리스트 모두)
 */
function refreshPaymentData() {
    loadPayments(currentPage, currentStatusFilter, currentStartDate, currentEndDate);
}

/**
 * 결제 관리 탭 초기화
 */
function initPaymentManagement() {
    console.log('[initPaymentManagement] 함수 호출됨');
    
    // 기간 버튼 클릭 이벤트
    document.querySelectorAll('#periodButtonGroup button').forEach(button => {
        button.addEventListener('click', (e) => {
            const period = e.target.dataset.period;
            handlePeriodButtonClick(period);
        });
    });
    
    // Date Picker 변경 이벤트
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) {
        startDateInput.addEventListener('change', handleDatePickerChange);
    }
    
    if (endDateInput) {
        endDateInput.addEventListener('change', handleDatePickerChange);
    }
    
    // 상태 탭 클릭 이벤트
    document.querySelectorAll('#paymentStatusTabs button[data-status]').forEach(button => {
        button.addEventListener('click', (e) => {
            const status = e.target.dataset.status || '';
            handleStatusTabClick(status);
        });
    });
    
    // 초기 데이터 로드 (전체 기간)
    console.log('[initPaymentManagement] 초기 데이터 로드 시작');
    currentPeriod = 'all';
    refreshPaymentData();
}

/**
 * 결제 생성 모달 열기
 */
async function openCreatePaymentModal() {
    console.log('[openCreatePaymentModal] 모달 열기');
    
    // 폼 초기화
    document.getElementById('createPaymentForm').reset();
    document.getElementById('expectedPaymentAmount').textContent = '상품을 선택하면 예상 결제액이 표시됩니다.';
    document.getElementById('quantityFieldContainer').style.display = 'none';
    
    // 상품 목록 로드
    await loadProductsForPayment();
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('createPaymentModal'));
    modal.show();
    
    // 상품 선택 이벤트 리스너 등록
    const productSelect = document.getElementById('createPaymentProductId');
    productSelect.addEventListener('change', calculateExpectedAmount);
    
    // 수량 입력 이벤트 리스너 등록 (Standard일 경우만)
    const quantityInput = document.getElementById('createPaymentQuantity');
    quantityInput.addEventListener('input', calculateExpectedAmount);
}

/**
 * 결제 생성용 상품 목록 로드
 */
async function loadProductsForPayment() {
    try {
        console.log('[loadProductsForPayment] 상품 목록 로드 시작');
        
        const response = await fetch('/admin/api/products?is_active=true', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`상품 목록 조회 실패: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[loadProductsForPayment] API 응답:', result);
        
        if (!result.success || !result.data || !result.data.products) {
            throw new Error('상품 목록 데이터 형식이 올바르지 않습니다');
        }
        
        const products = result.data.products;
        const productSelect = document.getElementById('createPaymentProductId');
        
        // 기존 옵션 제거 (첫 번째 옵션 제외)
        while (productSelect.options.length > 1) {
            productSelect.remove(1);
        }
        
        // 상품 옵션 추가
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            
            // 상품명 및 가격 표시
            let displayText = product.name;
            if (product.token_amount === -1) {
                displayText += ` (무제한, ${formatCurrency(product.price)})`;
            } else {
                displayText += ` (${formatNumber(product.token_amount)}토큰, ${formatCurrency(product.price)})`;
            }
            
            option.textContent = displayText;
            option.dataset.price = product.price;
            option.dataset.tokenAmount = product.token_amount;
            option.dataset.productId = product.id;
            
            productSelect.appendChild(option);
        });
        
        console.log('[loadProductsForPayment] 상품 목록 로드 완료:', products.length, '개');
        
    } catch (error) {
        console.error('[loadProductsForPayment] 오류:', error);
        alert(`상품 목록을 불러오는 데 실패했습니다: ${error.message}`);
    }
}

/**
 * 예상 결제액 계산 및 표시
 */
function calculateExpectedAmount() {
    const productSelect = document.getElementById('createPaymentProductId');
    const quantityInput = document.getElementById('createPaymentQuantity');
    const quantityFieldContainer = document.getElementById('quantityFieldContainer');
    const expectedAmountEl = document.getElementById('expectedPaymentAmount');
    
    const selectedOption = productSelect.options[productSelect.selectedIndex];
    
    if (!selectedOption || !selectedOption.value) {
        expectedAmountEl.textContent = '상품을 선택하면 예상 결제액이 표시됩니다.';
        quantityFieldContainer.style.display = 'none';
        return;
    }
    
    const productId = parseInt(selectedOption.value);
    const productPrice = parseInt(selectedOption.dataset.price || 0);
    const tokenAmount = parseInt(selectedOption.dataset.tokenAmount || 0);
    
    // Standard (ID: 1)인 경우 수량 입력 필드 표시
    if (productId === 1) {
        quantityFieldContainer.style.display = 'block';
        const quantity = parseInt(quantityInput.value) || 1;
        const totalAmount = productPrice * quantity;
        const totalTokens = quantity;
        
        expectedAmountEl.innerHTML = `
            <strong>${formatCurrency(totalAmount)}</strong> (${formatNumber(totalTokens)}토큰)
        `;
    } else {
        quantityFieldContainer.style.display = 'none';
        quantityInput.value = 1;
        
        if (tokenAmount === -1) {
            expectedAmountEl.innerHTML = `
                <strong>${formatCurrency(productPrice)}</strong> (무제한 토큰)
            `;
        } else {
            expectedAmountEl.innerHTML = `
                <strong>${formatCurrency(productPrice)}</strong> (${formatNumber(tokenAmount)}토큰)
            `;
        }
    }
}

/**
 * 결제 생성 제출
 */
async function submitCreatePayment() {
    try {
        console.log('[submitCreatePayment] 결제 생성 시작');
        
        const userId = parseInt(document.getElementById('createPaymentUserId').value);
        const productId = parseInt(document.getElementById('createPaymentProductId').value);
        const quantity = parseInt(document.getElementById('createPaymentQuantity').value) || 1;
        
        // 유효성 검사
        if (!userId || userId <= 0) {
            alert('유효한 유저 ID를 입력해주세요.');
            return;
        }
        
        if (!productId || productId <= 0) {
            alert('상품을 선택해주세요.');
            return;
        }
        
        // Standard가 아닌 경우 수량은 무시됨 (1로 고정)
        const finalQuantity = (productId === 1) ? quantity : 1;
        
        if (finalQuantity <= 0) {
            alert('수량은 1 이상이어야 합니다.');
            return;
        }
        
        // API 호출
        const response = await fetch('/admin/api/payments-manual/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            body: JSON.stringify({
                user_id: userId,
                product_id: productId,
                quantity: finalQuantity,
                status: 'completed'
            }),
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `결제 생성 실패: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[submitCreatePayment] API 응답:', result);
        
        if (result.success) {
            // 모달 닫기
            const modal = bootstrap.Modal.getInstance(document.getElementById('createPaymentModal'));
            if (modal) {
                modal.hide();
            }
            
            alert('결제가 성공적으로 생성되었습니다.');
            
            // 테이블 새로고침
            refreshPaymentData();
        } else {
            throw new Error(result.message || '결제 생성에 실패했습니다.');
        }
        
    } catch (error) {
        console.error('[submitCreatePayment] 오류:', error);
        alert(`결제 생성 중 오류가 발생했습니다: ${error.message}`);
    }
}

// 전역 함수로 노출
window.loadPayments = loadPayments;
window.refreshPaymentData = refreshPaymentData;
window.viewPaymentDetail = viewPaymentDetail;
window.updatePaymentStatus = updatePaymentStatus;
window.initPaymentManagement = initPaymentManagement;
window.openCreatePaymentModal = openCreatePaymentModal;
window.submitCreatePayment = submitCreatePayment;
window.cancelPayment = cancelPayment;
window.deletePayment = deletePayment;

console.log('[payment.js] 모듈 로드 완료, 전역 함수 등록됨');

// DOM 로드 완료 시 자동 초기화는 하지 않음 (admin.html의 탭 클릭 시 호출)
// 탭이 활성화될 때만 initPaymentManagement가 호출되도록 함

