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
 * 결제 상태에 따른 배지 HTML 생성
 */
function getStatusBadge(status) {
    const statusMap = {
        'pending': { text: '대기중', class: 'payment-status-pending' },
        'completed': { text: '완료', class: 'payment-status-completed' },
        'failed': { text: '실패', class: 'payment-status-failed' },
        'cancelled': { text: '취소', class: 'payment-status-cancelled' }
    };
    
    const statusInfo = statusMap[status.toLowerCase()] || { text: status, class: 'payment-status-pending' };
    return `<span class="payment-status-badge ${statusInfo.class}">${statusInfo.text}</span>`;
}

/**
 * 결제 목록 로드
 */
async function loadPayments(page = 1, status = '') {
    try {
        currentPage = page;
        currentStatusFilter = status;
        
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
        
        const response = await fetch(`/admin/api/payments?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCSRFToken()
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
            return `
                <tr>
                    <td><code class="text-primary">${payment.order_id || 'N/A'}</code></td>
                    <td>${payment.user_id || 'N/A'}</td>
                    <td>토큰 ${formatNumber(payment.token_amount || 0)}개</td>
                    <td class="text-end payment-amount">${formatCurrency(payment.amount || 0)}</td>
                    <td class="payment-token">${formatNumber(payment.token_amount || 0)}</td>
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
    const todayRevenueEl = document.getElementById('todayRevenue');
    const monthRevenueEl = document.getElementById('monthRevenue');
    const todayCountEl = document.getElementById('todayCount');
    const refundCountEl = document.getElementById('refundCount');
    
    if (todayRevenueEl) {
        todayRevenueEl.textContent = formatCurrency(kpiStats.today_revenue || 0);
    } else {
        console.error('[updateKPICards] todayRevenue element not found');
    }
    
    if (monthRevenueEl) {
        monthRevenueEl.textContent = formatCurrency(kpiStats.month_revenue || 0);
    } else {
        console.error('[updateKPICards] monthRevenue element not found');
    }
    
    if (todayCountEl) {
        todayCountEl.textContent = `${formatNumber(kpiStats.today_payment_count || 0)}건`;
    } else {
        console.error('[updateKPICards] todayCount element not found');
    }
    
    if (refundCountEl) {
        refundCountEl.textContent = `${formatNumber(kpiStats.refund_requests || 0)}건`;
    } else {
        console.error('[updateKPICards] refundCount element not found');
    }
    
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
                    <div class="text-muted" style="font-size: 0.7rem;">${formatNumber(payment.token_amount)} 토큰</div>
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
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadPayments(${page - 1}, '${currentStatusFilter}'); return false;">이전</a></li>`;
    }
    
    // 페이지 번호 버튼
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);
    
    if (startPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadPayments(1, '${currentStatusFilter}'); return false;">1</a></li>`;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === page ? 'active' : '';
        paginationHTML += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="loadPayments(${i}, '${currentStatusFilter}'); return false;">${i}</a></li>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadPayments(${totalPages}, '${currentStatusFilter}'); return false;">${totalPages}</a></li>`;
    }
    
    // 다음 버튼
    if (page < totalPages) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadPayments(${page + 1}, '${currentStatusFilter}'); return false;">다음</a></li>`;
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
function viewPaymentDetail(paymentId) {
    // TODO: 모달 또는 상세 페이지로 이동 (2단계에서 구현 예정)
    alert(`결제 상세보기: ID ${paymentId}\n\n상세보기 기능은 2단계에서 구현 예정입니다.`);
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
                'X-CSRF-Token': getCSRFToken()
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
            loadPayments(currentPage, currentStatusFilter);
        }
        
    } catch (error) {
        console.error('결제 상태 업데이트 오류:', error);
        alert(`상태 업데이트 중 오류가 발생했습니다: ${error.message}`);
    }
}

/**
 * 결제 관리 탭 초기화
 */
function initPaymentManagement() {
    console.log('[initPaymentManagement] 함수 호출됨');
    
    // 상태 필터 변경 이벤트
    const statusFilter = document.getElementById('paymentStatusFilter');
    if (statusFilter) {
        console.log('[initPaymentManagement] 상태 필터 요소 찾음');
        statusFilter.addEventListener('change', (e) => {
            console.log('[initPaymentManagement] 상태 필터 변경:', e.target.value);
            loadPayments(1, e.target.value);
        });
    } else {
        console.error('[initPaymentManagement] paymentStatusFilter 요소를 찾을 수 없음');
    }
    
    // 초기 데이터 로드
    console.log('[initPaymentManagement] 초기 데이터 로드 시작');
    loadPayments(1, '');
}

// 전역 함수로 노출
window.loadPayments = loadPayments;
window.viewPaymentDetail = viewPaymentDetail;
window.updatePaymentStatus = updatePaymentStatus;
window.initPaymentManagement = initPaymentManagement;

console.log('[payment.js] 모듈 로드 완료, 전역 함수 등록됨');

// DOM 로드 완료 시 자동 초기화는 하지 않음 (admin.html의 탭 클릭 시 호출)
// 탭이 활성화될 때만 initPaymentManagement가 호출되도록 함

