/**
 * Admin Dashboard 통계 모듈
 *
 * 이 파일은 admin.html에서 분리된 통계 관련 함수들을 포함합니다.
 * - 통계 데이터 로드
 * - 통계 콘텐츠 업데이트
 */

/**
 * 상세 통계 로드
 * @returns {Promise<void>}
 */
async function loadStats() {
    try {
        const response = await fetch('/api/admin/dashboard');
        const data = await response.json();
        
        if (data.success) {
            updateStatsContent(data.data);
        } else {
            document.getElementById('statsContent').innerHTML = '<p class="muted">통계 로드 실패</p>';
        }
    } catch (error) {
        document.getElementById('statsContent').innerHTML = '<p class="muted">통계 요청 실패</p>';
    }
}

/**
 * 통계 콘텐츠 업데이트
 * @param {Object} data - 통계 데이터 객체
 */
function updateStatsContent(data) {
    const statsHtml = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">${data.user_stats.active_users || 0}</div>
                <div style="font-size: 0.8rem; color: #6B7280;">활성 사용자</div>
            </div>
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">${data.user_stats.vip_users || 0}</div>
                <div style="font-size: 0.8rem; color: #6B7280;">VIP 사용자</div>
            </div>
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">${data.token_stats.total_used || 0}</div>
                <div style="font-size: 0.8rem; color: #6B7280;">사용된 토큰</div>
            </div>
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">${data.conversion_stats.avg_time || 0}초</div>
                <div style="font-size: 0.8rem; color: #6B7280;">평균 처리시간</div>
            </div>
        </div>
    `;
    
    document.getElementById('statsContent').innerHTML = statsHtml;
}

// 전역 함수로 노출 (다른 모듈에서 호출 가능하도록)
window.loadStats = loadStats;
window.updateStatsContent = updateStatsContent;

