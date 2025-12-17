/**
 * 토큰 부족 알림 모달 연동 모듈
 * conversion.js의 토큰 부족 알림을 고품질 모달로 변환
 */

(function() {
    'use strict';

    const TokenAlertModal = {
        /**
         * 토큰 부족 모달 생성 및 표시
         * 
         * @param {Object} data - 서버 응답 데이터
         * @param {number} data.template_count - 생성된 템플릿 수
         * @param {number} data.required_tokens - 필요한 토큰 수
         * @param {number} data.available_tokens - 현재 보유 토큰
         * @param {number} data.shortage - 부족한 토큰 수
         */
        show: function(data) {
            const { template_count, required_tokens, available_tokens, shortage } = data;

            // 기존 모달이 있으면 제거
            const existing = document.getElementById('token-alert-overlay');
            if (existing) {
                existing.remove();
            }

            // 모달 HTML 생성
            const modalHTML = `
                <div id="token-alert-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.6); z-index: 9999; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.3s ease-out;">
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); padding: 24px 20px; border-radius: 12px; max-width: 260px; width: 90%; text-align: center; box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.1); transform: scale(1); animation: popIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);">
                        <!-- 아이콘 -->
                        <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #ff6b6b, #ee5a52); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; box-shadow: 0 10px 25px rgba(255, 107, 107, 0.3);">
                            <span style="font-size: 1.25rem; color: white;">🔒</span>
                        </div>
                        
                        <!-- 제목 -->
                        <h2 style="margin: 0 0 8px 0; color: #1a202c; font-size: 1rem; font-weight: 700; letter-spacing: -0.025em;">회원님 알림창</h2>
                        
                        <!-- 내용 -->
                        <div style="margin: 0 0 16px 0; color: #4a5568; font-size: 0.875rem; line-height: 1.6;">
                            <div style="margin-bottom: 6px;">
                                <strong style="color: #2d3748;">전자세금계산서</strong> <span style="color: #e53e3e; font-weight: 700; font-size: 1rem;">${template_count}개</span> 생성
                            </div>
                            <div style="margin-bottom: 6px;">
                                <strong style="color: #2d3748;">회원님 토큰잔량</strong> <span style="color: #2d3748; font-weight: 700; font-size: 1rem;">${available_tokens}개</span>
                            </div>
                            <div style="margin-bottom: 6px;">
                                <strong style="color: #2d3748;">부족한 토큰수량</strong> <span style="color: #e53e3e; font-weight: 700; font-size: 1rem;">${shortage}개</span>
                            </div>
                            <div style="background: #fff5f5; padding: 8px; border-radius: 6px; border: 1px solid #feb2b2; margin-top: 8px;">
                                <strong style="color: #e53e3e; font-size: 0.9rem;">충전하세요</strong>
                            </div>
                        </div>
                        
                        <!-- 버튼 -->
                        <button onclick="TokenAlertModal.close()" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #ff6b6b, #ee5a52); color: white; border: none; border-radius: 6px; font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 8px 20px rgba(255, 107, 107, 0.3);">
                            확인
                        </button>
                    </div>
                </div>
                
                <style>
                    @keyframes fadeIn {
                        from { opacity: 0; }
                        to { opacity: 1; }
                    }
                    
                    @keyframes popIn {
                        from { 
                            transform: scale(0.8);
                            opacity: 0;
                        }
                        to { 
                            transform: scale(1);
                            opacity: 1;
                        }
                    }
                </style>
            `;

            // 모달 생성
            document.body.insertAdjacentHTML('beforeend', modalHTML);

            // 모달 내부 클릭 시 이벤트 전파 방지
            const modal = document.getElementById('token-alert-overlay');
            if (modal) {
                modal.querySelector('div').addEventListener('click', function(e) {
                    e.stopPropagation();
                });
            }
        },

        /**
         * 모달 닫기
         */
        close: function() {
            const overlay = document.getElementById('token-alert-overlay');
            if (overlay) {
                overlay.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    overlay.remove();
                }, 300);
            }
        }
    };

    // 전역으로 노출
    window.TokenAlertModal = TokenAlertModal;
})();

