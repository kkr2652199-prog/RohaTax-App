/**
 * 상점 페이지 주문 연동 스크립트
 * 상용화 준비: 결제 확인 모달 및 수량 제어 기능
 */

(function() {
    'use strict';

    // 현재 선택된 상품 정보 저장
    let currentProduct = {
        id: null,
        name: null,
        price: 0,
        type: null,
        token: 0,
        duration: 0
    };

    /**
     * 결제 확인 모달 열기 (현대적 디자인)
     * @param {HTMLElement} btn - 클릭된 구매하기 버튼
     */
    function openCheckoutModal(btn) {
        // 버튼의 data-* 속성 읽기
        currentProduct.id = parseInt(btn.getAttribute('data-id'), 10);
        currentProduct.name = btn.getAttribute('data-name') || '';
        currentProduct.price = parseFloat(btn.getAttribute('data-price')) || 0;
        currentProduct.type = btn.getAttribute('data-type') || '';
        currentProduct.token = parseInt(btn.getAttribute('data-token'), 10) || 0;
        currentProduct.duration = parseInt(btn.getAttribute('data-duration'), 10) || 0;

        const modalContent = document.getElementById('modalContent');
        const isEventType = currentProduct.type === 'event' || currentProduct.type === 'event_period';
        const isBasicType = currentProduct.type === 'basic';

        // 테마 클래스 적용/제거
        modalContent.classList.remove('theme-event', 'theme-basic');
        if (isEventType) {
            modalContent.classList.add('theme-event');
        } else {
            modalContent.classList.add('theme-basic');
        }

        // Hero Section: 아이콘 및 상품명
        const heroIcon = document.getElementById('modalHeroIcon');
        const productName = document.getElementById('modalProductName');
        
        if (currentProduct.type === 'event') {
            heroIcon.textContent = '🎉';
        } else if (currentProduct.type === 'event_period') {
            heroIcon.textContent = '⏳';
        } else if (currentProduct.type === 'package') {
            heroIcon.textContent = '💎';
        } else if (currentProduct.type === 'subscription') {
            heroIcon.textContent = '👑';
        } else {
            heroIcon.textContent = '🛒';
        }
        
        productName.textContent = currentProduct.name;

        // Info Section: 가격 및 스펙
        const productPrice = document.getElementById('modalProductPrice');
        const productSpecs = document.getElementById('modalProductSpecs');
        
        productPrice.textContent = formatCurrency(currentProduct.price);
        
        let specsText = '';
        if (currentProduct.duration > 0) {
            specsText = `⏳ 이용 기간: ${currentProduct.duration}일`;
        } else if (currentProduct.token === -1) {
            specsText = '♾️ 무제한 이용';
        } else if (currentProduct.token > 0) {
            specsText = `💰 포함 토큰: ${currentProduct.token}개`;
        } else {
            specsText = '📦 기본 상품';
        }
        productSpecs.textContent = specsText;

        // Control Section: Event는 배지, Basic은 Stepper
        const eventBadge = document.getElementById('modalEventBadge');
        const quantityStepper = document.getElementById('modalQuantityStepper');
        const quantityInput = document.getElementById('modalQuantityInput');
        const stepperDecrease = document.getElementById('stepperDecrease');
        
        if (isEventType) {
            eventBadge.classList.remove('hidden');
            quantityStepper.classList.add('hidden');
        } else if (isBasicType) {
            eventBadge.classList.add('hidden');
            quantityStepper.classList.remove('hidden');
            if (quantityInput) {
                quantityInput.value = ''; // 초기값 빈 문자열
            }
            // 초기값이 비어있으므로 감소 버튼 비활성화
            if (stepperDecrease) {
                stepperDecrease.disabled = true;
            }
        } else {
            eventBadge.classList.add('hidden');
            quantityStepper.classList.add('hidden');
        }

        // Action Button: 텍스트 동적 변경
        const confirmBtn = document.getElementById('btnConfirmPayment');
        const totalLabel = document.getElementById('modalTotalLabel');
        
        if (isEventType) {
            confirmBtn.textContent = '🎁 무료 혜택 받기';
            totalLabel.textContent = '총 혜택 금액';
        } else {
            confirmBtn.textContent = '💳 결제하기';
            totalLabel.textContent = '총 결제 예상액';
        }

        // 총 결제 예상액 계산 및 표시
        updateTotalPrice();

        // 모달 표시
        const modal = document.getElementById('checkoutModal');
        modal.classList.add('show');
    }

    /**
     * 총 결제 예상액 계산 및 업데이트
     */
    function updateTotalPrice() {
        let quantity = 0;
        
        // Input 필드에서 수량 가져오기
        const quantityInput = document.getElementById('modalQuantityInput');
        if (quantityInput && !quantityInput.closest('.hidden')) {
            const inputValue = quantityInput.value.trim();
            if (inputValue === '' || inputValue === null || inputValue === undefined) {
                quantity = 0;
            } else {
                quantity = parseInt(inputValue, 10);
                if (isNaN(quantity) || quantity < 0) {
                    quantity = 0;
                }
            }
        }
        
        const totalPrice = currentProduct.price * quantity;
        document.getElementById('modalTotalPrice').textContent = formatCurrency(totalPrice);
    }

    /**
     * Stepper 증가 버튼 클릭
     */
    function handleStepperIncrease() {
        const quantityInput = document.getElementById('modalQuantityInput');
        const stepperDecrease = document.getElementById('stepperDecrease');
        
        if (!quantityInput) return;
        
        const inputValue = quantityInput.value.trim();
        let currentValue = 0;
        
        // 빈 값이면 1로 시작, 아니면 현재 값 + 1
        if (inputValue === '' || inputValue === null || inputValue === undefined) {
            currentValue = 0;
        } else {
            currentValue = parseInt(inputValue, 10);
            if (isNaN(currentValue) || currentValue < 0) {
                currentValue = 0;
            }
        }
        
        const newValue = currentValue + 1;
        quantityInput.value = newValue.toString();
        
        // 감소 버튼 활성화 (값이 1 이상이면)
        if (stepperDecrease) {
            stepperDecrease.disabled = (newValue <= 1);
        }
        
        updateTotalPrice();
    }

    /**
     * Stepper 감소 버튼 클릭
     */
    function handleStepperDecrease() {
        const quantityInput = document.getElementById('modalQuantityInput');
        const stepperDecrease = document.getElementById('stepperDecrease');
        
        if (!quantityInput) return;
        
        const inputValue = quantityInput.value.trim();
        let currentValue = 0;
        
        // 빈 값이면 반응하지 않음
        if (inputValue === '' || inputValue === null || inputValue === undefined) {
            return;
        }
        
        currentValue = parseInt(inputValue, 10);
        if (isNaN(currentValue) || currentValue <= 0) {
            return;
        }
        
        if (currentValue > 1) {
            const newValue = currentValue - 1;
            quantityInput.value = newValue.toString();
            
            // 값이 1이 되면 감소 버튼 비활성화
            if (newValue === 1 && stepperDecrease) {
                stepperDecrease.disabled = true;
            }
            
            updateTotalPrice();
        } else if (currentValue === 1) {
            // 값이 1이면 빈 문자열로 변경
            quantityInput.value = '';
            if (stepperDecrease) {
                stepperDecrease.disabled = true;
            }
            updateTotalPrice();
        }
    }

    /**
     * 수량 입력 필드 변경 이벤트 핸들러
     */
    function handleQuantityInputChange() {
        const quantityInput = document.getElementById('modalQuantityInput');
        const stepperDecrease = document.getElementById('stepperDecrease');
        
        if (!quantityInput) return;
        
        const inputValue = quantityInput.value.trim();
        
        // 빈 값이면 그대로 유지 (0원 표시)
        if (inputValue === '' || inputValue === null || inputValue === undefined) {
            if (stepperDecrease) {
                stepperDecrease.disabled = true;
            }
            updateTotalPrice();
            return;
        }
        
        let value = parseInt(inputValue, 10);
        
        // 유효하지 않은 값이면 빈 문자열로 초기화
        if (isNaN(value) || value < 0) {
            quantityInput.value = '';
            if (stepperDecrease) {
                stepperDecrease.disabled = true;
            }
            updateTotalPrice();
            return;
        }
        
        // 0이면 빈 문자열로 변경
        if (value === 0) {
            quantityInput.value = '';
            if (stepperDecrease) {
                stepperDecrease.disabled = true;
            }
            updateTotalPrice();
            return;
        }
        
        // 감소 버튼 상태 업데이트
        if (stepperDecrease) {
            stepperDecrease.disabled = (value <= 1);
        }
        
        updateTotalPrice();
    }

    /**
     * 금액 포맷팅 (천단위 구분자)
     * @param {number} amount - 금액
     * @returns {string} 포맷된 금액 문자열
     */
    function formatCurrency(amount) {
        return new Intl.NumberFormat('ko-KR').format(Math.round(amount)) + '원';
    }

    /**
     * 결제 확인 및 실행
     */
    async function confirmPurchase() {
        let quantity = 0;
        
        // Input 필드에서 수량 가져오기
        const quantityInput = document.getElementById('modalQuantityInput');
        if (quantityInput && !quantityInput.closest('.hidden')) {
            const inputValue = quantityInput.value.trim();
            if (inputValue === '' || inputValue === null || inputValue === undefined) {
                quantity = 0;
            } else {
                quantity = parseInt(inputValue, 10);
                if (isNaN(quantity) || quantity < 1) {
                    quantity = 0;
                }
            }
        }

        // 수량 검증
        if (quantity <= 0) {
            alert('수량을 입력해주세요.');
            if (quantityInput) {
                quantityInput.focus();
            }
            return;
        }

        // 모달 닫기
        closeCheckoutModal();

        // 주문 생성
        await createOrder(currentProduct.id, quantity);
    }

    /**
     * 결제 확인 모달 닫기
     */
    function closeCheckoutModal() {
        const modal = document.getElementById('checkoutModal');
        modal.classList.remove('show');
    }

    /**
     * 주문 생성 API 호출
     * @param {number} productId - 상품 ID
     * @param {number} quantity - 수량 (기본값: 1)
     */
    async function createOrder(productId, quantity = 1) {
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
                    product_id: productId,
                    quantity: quantity
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
                    buyer_name: data.data.buyer_name,
                    quantity: quantity
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
                e.preventDefault();
                openCheckoutModal(e.target);
            }
        });
    }

    /**
     * 모달 이벤트 리스너 초기화
     */
    function initModalEvents() {
        // 닫기 버튼 (X)
        const btnClose = document.getElementById('btnCloseModal');
        if (btnClose) {
            btnClose.addEventListener('click', closeCheckoutModal);
        }

        // 취소 버튼
        const btnCancel = document.getElementById('btnCancelPayment');
        if (btnCancel) {
            btnCancel.addEventListener('click', closeCheckoutModal);
        }

        // 결제하기 버튼
        const btnConfirm = document.getElementById('btnConfirmPayment');
        if (btnConfirm) {
            btnConfirm.addEventListener('click', confirmPurchase);
        }

        // Stepper 증가 버튼
        const stepperIncrease = document.getElementById('stepperIncrease');
        if (stepperIncrease) {
            stepperIncrease.addEventListener('click', handleStepperIncrease);
        }

        // Stepper 감소 버튼
        const stepperDecrease = document.getElementById('stepperDecrease');
        if (stepperDecrease) {
            stepperDecrease.addEventListener('click', handleStepperDecrease);
        }

        // 수량 입력 필드 이벤트 리스너
        const quantityInput = document.getElementById('modalQuantityInput');
        if (quantityInput) {
            quantityInput.addEventListener('input', handleQuantityInputChange);
            quantityInput.addEventListener('change', handleQuantityInputChange);
            quantityInput.addEventListener('blur', handleQuantityInputChange);
        }

        // 모달 오버레이 클릭 시 닫기
        const modal = document.getElementById('checkoutModal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeCheckoutModal();
                }
            });
        }

        // ESC 키로 모달 닫기
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const modal = document.getElementById('checkoutModal');
                if (modal && modal.classList.contains('show')) {
                    closeCheckoutModal();
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
            document.addEventListener('DOMContentLoaded', function() {
                initPurchaseButtons();
                initModalEvents();
            });
        } else {
            initPurchaseButtons();
            initModalEvents();
        }
    }

    // 초기화 실행
    init();

})();
