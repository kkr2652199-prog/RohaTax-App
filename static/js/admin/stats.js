/**
 * Admin Dashboard 통계 모듈 - Chart.js 시각화
 *
 * 이 파일은 admin.html에서 분리된 통계 관련 함수들을 포함합니다.
 * - 통계 데이터 로드 (새로운 API: /admin/api/dashboard-stats)
 * - Chart.js를 사용한 차트 렌더링
 * - 3가지 차트: 일일 토큰 사용량 (Line), 활동 유형 분포 (Doughnut), 시간대별 트래픽 (Bar)
 */

// CSRF 토큰 함수 (전역 함수가 없을 때만 선언)
if (typeof window.getCSRFToken === 'undefined') {
    window.getCSRFToken = function() {
        if (typeof csrfToken === 'function') {
            return csrfToken();
        }
        // 폴백: 직접 메타 태그에서 읽기
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') || '' : '';
    };
}

// 차트 인스턴스 저장
let dailyTokenUsageChart = null;
let activityDistributionChart = null;
let hourlyTrafficChart = null;

// 앱 테마 색상 (전역 변수가 없을 때만 선언)
if (typeof window.themeColors === 'undefined') {
    window.themeColors = {
    primary: '#10B981',
    primaryDark: '#059669',
    primaryLight: '#34D399',
    secondary: '#6EE7B7',
    accent: '#A7F3D0',
    background: '#F0FDF4',
    text: '#1F2937',
    textMuted: '#6B7280',
    border: '#E5E7EB',
    // 차트용 색상 팔레트
    chartColors: [
        '#10B981', // Primary Green
        '#059669', // Primary Dark
        '#34D399', // Primary Light
        '#6EE7B7', // Secondary
        '#A7F3D0', // Accent
        '#D1FAE5', // Light Mint
        '#065F46', // Dark Green
        '#047857', // Medium Green
    ]
    };
}

// themeColors는 window.themeColors로 직접 사용

/**
 * 상세 통계 로드
 * @returns {Promise<void>}
 */
async function loadStats() {
    try {
        const response = await fetch('/admin/api/dashboard-stats', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.window.getCSRFToken()
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            // 401 또는 403 에러인 경우 세션 만료로 처리하지 않음
            if (response.status === 401 || response.status === 403) {
                const errorData = await response.json().catch(() => ({}));
                document.getElementById('statsContent').innerHTML = 
                    '<p class="muted">인증 오류: ' + (errorData.message || '권한이 없습니다') + '</p>';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            updateStatsContent(data.data);
            renderCharts(data.data);
        } else {
            document.getElementById('statsContent').innerHTML = 
                '<p class="muted">통계 로드 실패: ' + (data.message || '알 수 없는 오류') + '</p>';
        }
    } catch (error) {
        console.error('통계 로드 오류:', error);
        // 네트워크 오류 등 기타 에러는 로그아웃으로 처리하지 않음
        document.getElementById('statsContent').innerHTML = 
            '<p class="muted">통계 요청 실패: ' + error.message + '</p>';
    }
}

/**
 * 통계 카드 콘텐츠 업데이트 (기존 숫자 카드들)
 * @param {Object} data - 통계 데이터 객체
 */
function updateStatsContent(data) {
    // 기존 통계 카드는 다른 API에서 가져오므로 여기서는 기본 메시지만 표시
    // 실제 카드 데이터는 dashboard_core.js에서 로드됨
    const statsCardsHtml = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: ${window.themeColors.primary};">
                    ${data.daily_token_usage ? data.daily_token_usage.reduce((sum, item) => sum + item.usage, 0) : 0}
                </div>
                <div style="font-size: 0.8rem; color: ${window.themeColors.textMuted};">최근 7일 토큰 사용량</div>
            </div>
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: ${window.themeColors.primary};">
                    ${data.activity_distribution ? data.activity_distribution.reduce((sum, item) => sum + item.count, 0) : 0}
                </div>
                <div style="font-size: 0.8rem; color: ${window.themeColors.textMuted};">최근 30일 활동 건수</div>
            </div>
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: ${window.themeColors.primary};">
                    ${data.hourly_traffic ? data.hourly_traffic.reduce((sum, item) => sum + item.count, 0) : 0}
                </div>
                <div style="font-size: 0.8rem; color: ${window.themeColors.textMuted};">최근 24시간 활동 건수</div>
            </div>
        </div>
    `;
    
    document.getElementById('statsCards').innerHTML = statsCardsHtml;
    
    // 차트 컨테이너 표시
    document.getElementById('chartsContainer').style.display = 'block';
}

/**
 * Chart.js를 사용한 차트 렌더링
 * @param {Object} data - 통계 데이터 객체
 */
function renderCharts(data) {
    // 기존 차트가 있으면 파괴
    if (dailyTokenUsageChart) {
        dailyTokenUsageChart.destroy();
    }
    if (activityDistributionChart) {
        activityDistributionChart.destroy();
    }
    if (hourlyTrafficChart) {
        hourlyTrafficChart.destroy();
    }
    
    // 1. 일일 토큰 사용량 (Line Chart)
    renderDailyTokenUsageChart(data.daily_token_usage || []);
    
    // 2. 활동 유형 분포 (Doughnut Chart)
    renderActivityDistributionChart(data.activity_distribution || []);
    
    // 3. 시간대별 트래픽 (Bar Chart)
    renderHourlyTrafficChart(data.hourly_traffic || []);
}

/**
 * 일일 토큰 사용량 Line Chart 렌더링
 * @param {Array} data - 날짜별 토큰 사용량 데이터
 */
function renderDailyTokenUsageChart(data) {
    const ctx = document.getElementById('dailyTokenUsageChart');
    if (!ctx) return;
    
    const labels = data.map(item => {
        // 날짜 포맷팅 (YYYY-MM-DD -> MM/DD)
        const date = new Date(item.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });
    
    const usageData = data.map(item => item.usage);
    
    dailyTokenUsageChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '토큰 사용량',
                data: usageData,
                borderColor: window.themeColors.primary,
                backgroundColor: window.themeColors.background,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: window.themeColors.primary,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CSS에서 높이 제어
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: window.themeColors.text,
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: window.themeColors.primary,
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: window.themeColors.border,
                        drawBorder: false
                    },
                    ticks: {
                        color: window.themeColors.textMuted,
                        font: {
                            size: 11
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: window.themeColors.textMuted,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

/**
 * 활동 유형 분포 Doughnut Chart 렌더링
 * @param {Array} data - 활동 유형별 건수 데이터
 */
function renderActivityDistributionChart(data) {
    const ctx = document.getElementById('activityDistributionChart');
    if (!ctx) return;
    
    const labels = data.map(item => item.label);
    const counts = data.map(item => item.count);
    
    // 색상 할당 (데이터가 많으면 색상 반복)
    const backgroundColors = counts.map((_, index) => 
        window.themeColors.chartColors[index % window.themeColors.chartColors.length]
    );
    
    activityDistributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: backgroundColors,
                borderColor: '#ffffff',
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CSS에서 높이 제어
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        color: window.themeColors.text,
                        font: {
                            size: 11
                        },
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: window.themeColors.primary,
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value}건 (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 시간대별 트래픽 Bar Chart 렌더링
 * @param {Array} data - 시간대별 활동 건수 데이터
 */
function renderHourlyTrafficChart(data) {
    const ctx = document.getElementById('hourlyTrafficChart');
    if (!ctx) return;
    
    const labels = data.map(item => `${item.hour}시`);
    const counts = data.map(item => item.count);
    
    hourlyTrafficChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '활동 건수',
                data: counts,
                backgroundColor: window.themeColors.chartColors.map((color, index) => 
                    index < counts.length ? color : window.themeColors.primary
                ),
                borderColor: window.themeColors.primaryDark,
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CSS에서 높이 제어
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: window.themeColors.primary,
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return `활동 건수: ${context.parsed.y}건`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: window.themeColors.border,
                        drawBorder: false
                    },
                    ticks: {
                        color: window.themeColors.textMuted,
                        font: {
                            size: 11
                        },
                        stepSize: 1
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: window.themeColors.textMuted,
                        font: {
                            size: 10
                        },
                        maxRotation: 45,
                        minRotation: 0
                    }
                }
            }
        }
    });
}

// 전역 함수로 노출 (다른 모듈에서 호출 가능하도록)
window.loadStats = loadStats;
window.updateStatsContent = updateStatsContent;
window.renderCharts = renderCharts;
