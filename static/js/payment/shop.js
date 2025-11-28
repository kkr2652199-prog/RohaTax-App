/**
 * 상점 페이지 주문 연동 스크립트
 * 상용화 준비: 주문 생성 API 연동
 */

(function() {
    'use strict';

    /**
     * 주문 생성 API 호출
     * @param {number} productId - 상품 ID
     */
    async function createOrder(productId) {
        try {
            // 버튼 비활성화
            const buttons = document.querySelectorAll('.btn-purchase');
            buttons.forEach(btn => {
                btn.disabled = true;
            });

            // API 호출
            const response = await fetch('/api/orders/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId
                }),
                credentials: 'same-origin' // 세션 쿠키 포함
            });

            const data = await response.json();

            // 버튼 활성화
            buttons.forEach(btn => {
                btn.disabled = false;
            });

            // 응답 처리
            if (response.ok && data.success) {
                // 성공 시
                const merchantUid = data.data.merchant_uid;
                
                // 콘솔에 전체 응답 데이터 출력
                console.log('[주문 생성 성공] 전체 응답 데이터:', data);
                console.log('[주문 생성 성공] 주문 정보:', {
                    merchant_uid: data.data.merchant_uid,
                    amount: data.data.amount,
                    supply_price: data.data.supply_price,
                    vat: data.data.vat,
                    product_name: data.data.product_name,
                    buyer_email: data.data.buyer_email,
                    buyer_name: data.data.buyer_name
                });
                
                // 주문 생성 직후 가상 결제 완료 처리
                await completePayment(merchantUid);
            } else {
                // 실패 시
                const errorMessage = data.message || '주문 생성에 실패했습니다';
                alert(`오류: ${errorMessage}`);
                console.error('[주문 생성 실패]', data);
            }

        } catch (error) {
            // 네트워크 오류 등
            console.error('[주문 생성 오류]', error);
            alert('주문 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
            
            // 버튼 활성화
            const buttons = document.querySelectorAll('.btn-purchase');
            buttons.forEach(btn => {
                btn.disabled = false;
            });
        }
    }

    /**
     * 가상 결제 완료 처리
     * @param {string} merchantUid - 주문 번호
     */
    async function completePayment(merchantUid) {
        try {
            // API 호출
            const response = await fetch('/api/payment/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    merchant_uid: merchantUid
                }),
                credentials: 'same-origin' // 세션 쿠키 포함
            });

            const data = await response.json();

            // 응답 처리
            if (response.ok && data.success) {
                // 성공 시
                const newTokenBalance = data.data.new_token_balance;
                const tokenAmount = data.data.token_amount || 0;
                
                let message = '결제가 (가상으로) 완료되었습니다!';
                if (tokenAmount > 0) {
                    message += `\n토큰 ${tokenAmount}개가 지급되었습니다.`;
                    if (newTokenBalance !== null && newTokenBalance !== undefined) {
                        message += `\n현재 토큰 잔액: ${newTokenBalance}개`;
                    }
                }
                
                alert(message);
                
                // 콘솔에 전체 응답 데이터 출력
                console.log('[결제 완료 성공] 전체 응답 데이터:', data);
                console.log('[결제 완료 성공] 결제 정보:', {
                    payment_id: data.data.payment_id,
                    merchant_uid: data.data.merchant_uid,
                    new_token_balance: data.data.new_token_balance,
                    token_amount: data.data.token_amount,
                    product_type: data.data.product_type
                });
            } else {
                // 실패 시
                const errorMessage = data.message || '결제 처리에 실패했습니다';
                alert(`오류: ${errorMessage}`);
                console.error('[결제 완료 실패]', data);
            }

        } catch (error) {
            // 네트워크 오류 등
            console.error('[결제 완료 오류]', error);
            alert('결제 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
        }
    }

    /**
     * 구매하기 버튼 클릭 이벤트 리스너
     */
    function initPurchaseButtons() {
        document.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('btn-purchase')) {
                const productId = e.target.getAttribute('data-id');
                
                if (!productId) {
                    console.error('[주문 생성 오류] product_id가 없습니다');
                    alert('상품 정보를 찾을 수 없습니다.');
                    return;
                }

                // 확인 대화상자
                const confirmed = confirm('이 상품을 구매하시겠습니까?');
                if (confirmed) {
                    createOrder(parseInt(productId, 10));
                }
            }
        });
    }

    /**
     * 초기화
     */
    function init() {
        // DOM 로드 완료 후 이벤트 리스너 등록
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initPurchaseButtons);
        } else {
            initPurchaseButtons();
        }
    }

    // 초기화 실행
    init();

})();

