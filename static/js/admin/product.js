/**
 * 요금제 관리 대시보드 모듈
 * 3가지 고정 요금제(Standard, Premium, Gold) 가격 정책 관리
 */

// CSRF 토큰 함수 (전역 함수가 없을 때만 선언)
if (typeof window.getCSRFToken === 'undefined') {
    window.getCSRFToken = function() {
        if (typeof csrfToken === 'function') {
            return csrfToken();
        }
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    };
}

// 상품 데이터 캐시
let productData = {
    standard: null,  // ID: 1
    premium: null,   // ID: 2
    gold: null,      // ID: 3
    event: null,     // type 'event'
    periodEvent: null // type 'event_period'
};

/**
 * dataset에 상품 ID가 없는 경우 사용자에게 안내하고 동작을 중단한다.
 */
function resolveProductId(element, label = '상품') {
    if (!element) {
        alert(`${label} 요소를 찾을 수 없습니다. 페이지를 새로고침해주세요.`);
        return null;
    }
    
    const rawId = element.dataset ? element.dataset.productId : undefined;
    const productId = Number.parseInt(rawId);
    
    if (!Number.isInteger(productId)) {
        alert(`${label} 데이터가 아직 준비되지 않았습니다. 잠시 후 다시 시도해주세요.`);
        return null;
    }
    
    return productId;
}

/**
 * 상품 데이터 로드 (동적 전체 조회)
 */
async function loadProducts() {
    console.log('[loadProducts] 요금제 데이터 로드 시작');
    
    try {
        const response = await fetch(`/admin/api/products?per_page=100`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success && result.data && Array.isArray(result.data.products)) {
            const products = result.data.products;
            console.log('[DEBUG] 서버 응답 전체:', products);
            if (products.length === 0) {
                console.warn('[loadProducts] 상품 데이터 없음');
                return;
            }
            
            products.forEach(product => {
                const normalizedType = (product.type || '').toLowerCase();
                const normalizedName = (product.name || '').trim().toLowerCase();

                if (
                    normalizedType === 'basic' ||
                    normalizedName === 'basic' ||
                    normalizedName === 'standard'
                ) {
                    productData.standard = product;
                    updateStandardCard(product);
                } else if (normalizedType === 'package' || normalizedName === 'premium package' || normalizedName === 'premium') {
                    productData.premium = product;
                    updatePremiumCard(product);
                } else if (normalizedType === 'subscription' || normalizedName === 'gold membership' || normalizedName === 'gold') {
                    productData.gold = product;
                    updateGoldCard(product);
                } else if (normalizedType === 'event' || normalizedName === 'welcome event') {
                    productData.event = product;
                    updateEventCard(product);
                } else if (normalizedType === 'event_period' || normalizedType === 'event-period' || normalizedName === 'welcome period event') {
                    productData.periodEvent = product;
                    updatePeriodEventCard(product);
                }
            });
            console.log('[loadProducts] 요금제 데이터 로드 완료', productData);
        } else {
            console.warn('[loadProducts] 상품 목록 응답이 유효하지 않습니다.', result);
        }
        
    } catch (error) {
        console.error('[loadProducts] 요금제 데이터 로드 오류:', error);
        alert('요금제 데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

/**
 * Standard 카드 업데이트
 */
function updateStandardCard(product) {
    const form = document.getElementById('standardForm');
    if (form) form.dataset.productId = product.id;

    const priceInput = document.getElementById('standardPrice');
    if (priceInput) {
        priceInput.value = product.price || 500;
    }
}

/**
 * Premium 카드 업데이트
 */
function updatePremiumCard(product) {
    const tokenInput = document.getElementById('premiumTokenAmount');
    const priceInput = document.getElementById('premiumPrice');
    const toggle = document.getElementById('premiumToggle');
    
    if (tokenInput) {
        tokenInput.value = product.token_amount || 100;
    }
    if (priceInput) {
        priceInput.value = product.price || 25000;
    }
    if (toggle) {
        toggle.checked = product.is_active !== false;
    }
    
    // 할인율 계산
    calculatePremiumDiscount();
}

/**
 * Gold 카드 업데이트
 */
function updateGoldCard(product) {
    const priceInput = document.getElementById('goldPrice');
    const toggle = document.getElementById('goldToggle');
    
    if (priceInput) {
        priceInput.value = product.price || 50000;
    }
    if (toggle) {
        toggle.checked = product.is_active !== false;
    }
}

function updateEventCard(product) {
    const form = document.getElementById('eventForm');
    if (form) form.dataset.productId = product.id;

    const toggle = document.getElementById('eventToggle');
    if (toggle) toggle.dataset.productId = product.id;

    const tokenInput = document.getElementById('eventTokenAmount');
    if (tokenInput) {
        const tokenValue = Number.isInteger(product.token_amount) && product.token_amount > 0
            ? product.token_amount
            : 50;
        tokenInput.value = tokenValue;
        tokenInput.setAttribute('value', tokenValue);
    }
    if (toggle) {
        toggle.checked = product.is_active !== false;
    }
}

function updatePeriodEventCard(product) {
    const form = document.getElementById('periodEventForm');
    if (form) form.dataset.productId = product.id;

    const toggle = document.getElementById('periodEventToggle');
    if (toggle) toggle.dataset.productId = product.id;

    const durationInput = document.getElementById('periodDuration');
    if (durationInput) {
        const durationValue = Number.isInteger(product.duration_days) && product.duration_days > 0
            ? product.duration_days
            : 3;
        durationInput.value = durationValue;
        durationInput.setAttribute('value', durationValue);
    }
    if (toggle) {
        toggle.checked = product.is_active !== false;
    }
}

/**
 * Premium 할인율 계산
 */
function calculatePremiumDiscount() {
    const standardPrice = parseFloat(document.getElementById('standardPrice')?.value) || 500;
    const premiumTokenAmount = parseFloat(document.getElementById('premiumTokenAmount')?.value) || 100;
    const premiumPrice = parseFloat(document.getElementById('premiumPrice')?.value) || 25000;
    
    if (standardPrice > 0 && premiumTokenAmount > 0) {
        const standardTotalPrice = standardPrice * premiumTokenAmount;
        const discount = standardTotalPrice > 0 
            ? ((standardTotalPrice - premiumPrice) / standardTotalPrice * 100).toFixed(1)
            : 0;
        
        const discountElement = document.getElementById('premiumDiscountValue');
        if (discountElement) {
            discountElement.textContent = discount;
        }
    }
}

/**
 * 상품 정보 업데이트 (PATCH)
 */
async function updateProduct(productId, productData) {
    console.log(`[updateProduct] 상품 ID ${productId} 업데이트`, productData);
    
    try {
        const response = await fetch(`/admin/api/products/${productId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.getCSRFToken()
            },
            credentials: 'include',
            body: JSON.stringify(productData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`[updateProduct] 상품 ID ${productId} 업데이트 성공`);
            // 데이터 다시 로드
            await loadProducts();
            return true;
        } else {
            console.error(`[updateProduct] 상품 ID ${productId} 업데이트 실패:`, result);
            alert(result.message || '상품 정보 업데이트에 실패했습니다.');
            return false;
        }
    } catch (error) {
        console.error(`[updateProduct] 상품 ID ${productId} 업데이트 오류:`, error);
        alert('상품 정보 업데이트 중 오류가 발생했습니다.');
        return false;
    }
}

/**
 * Standard 폼 제출 처리
 */
async function handleStandardSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const productId = resolveProductId(form, '기준 단가');
    if (productId === null) {
        return;
    }
    
    const price = parseFloat(document.getElementById('standardPrice').value);
    if (isNaN(price) || price < 0) {
        alert('올바른 가격을 입력해주세요.');
        return;
    }
    
    const productData = {
        price: Math.round(price)
    };
    
    const success = await updateProduct(productId, productData);
    if (success) {
        alert('기준 단가가 저장되었습니다.');
    }
}

/**
 * Premium 폼 제출 처리
 */
async function handlePremiumSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const productId = resolveProductId(form, '할인 패키지');
    if (productId === null) {
        return;
    }
    
    const tokenAmount = parseInt(document.getElementById('premiumTokenAmount').value);
    const price = parseFloat(document.getElementById('premiumPrice').value);
    const isActive = document.getElementById('premiumToggle').checked;
    
    if (isNaN(tokenAmount) || tokenAmount < 1) {
        alert('올바른 토큰 개수를 입력해주세요.');
        return;
    }
    if (isNaN(price) || price < 0) {
        alert('올바른 가격을 입력해주세요.');
        return;
    }
    
    const productData = {
        token_amount: tokenAmount,
        price: Math.round(price),
        is_active: isActive
    };
    
    const success = await updateProduct(productId, productData);
    if (success) {
        alert('할인 패키지 정보가 저장되었습니다.');
    }
}

/**
 * Gold 폼 제출 처리
 */
async function handleGoldSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const productId = resolveProductId(form, '무제한권');
    if (productId === null) {
        return;
    }
    
    const price = parseFloat(document.getElementById('goldPrice').value);
    const isActive = document.getElementById('goldToggle').checked;
    
    if (isNaN(price) || price < 0) {
        alert('올바른 가격을 입력해주세요.');
        return;
    }
    
    const productData = {
        price: Math.round(price),
        is_active: isActive,
        token_amount: -1  // 무제한은 항상 -1
    };
    
    const success = await updateProduct(productId, productData);
    if (success) {
        alert('무제한권 정보가 저장되었습니다.');
    }
}

/**
 * Token Event 폼 제출 처리
 */
async function handleEventSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const productId = resolveProductId(form, '토큰 이벤트');
    if (productId === null) {
        return;
    }
    
    const tokenAmount = parseInt(document.getElementById('eventTokenAmount').value);
    const isActive = document.getElementById('eventToggle').checked;
    
    if (isNaN(tokenAmount) || tokenAmount < 1) {
        alert('올바른 토큰 개수를 입력해주세요.');
        return;
    }
    
    const productData = {
        token_amount: tokenAmount,
        price: 0,
        is_active: isActive
    };
    
    const success = await updateProduct(productId, productData);
    if (success) {
        alert('이벤트 혜택 정보가 저장되었습니다.');
    }
}

/**
 * Period Event 폼 제출 처리
 */
async function handlePeriodEventSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const productId = resolveProductId(form, '기간 이벤트');
    if (productId === null) {
        return;
    }
    
    const durationDays = parseInt(document.getElementById('periodDuration').value);
    const isActive = document.getElementById('periodEventToggle').checked;
    
    if (isNaN(durationDays) || durationDays < 1) {
        alert('올바른 기간(일)을 입력해주세요.');
        return;
    }
    
    const productData = {
        duration_days: durationDays,
        price: 0,
        token_amount: 0,
        is_active: isActive
    };
    
    const success = await updateProduct(productId, productData);
    if (success) {
        alert('기간제 이벤트 정보가 저장되었습니다.');
    }
}

/**
 * Token Event 토글 처리
 */
async function handleEventToggle(event) {
    const productId = resolveProductId(event.target, '토큰 이벤트');
    if (productId === null) {
        event.target.checked = !event.target.checked;
        return;
    }
    const isActive = event.target.checked;
    
    const productData = { is_active: isActive };
    const success = await updateProduct(productId, productData);
    if (!success) {
        event.target.checked = !isActive;
    }
}

/**
 * Period Event 토글 처리
 */
async function handlePeriodEventToggle(event) {
    const productId = resolveProductId(event.target, '기간 이벤트');
    if (productId === null) {
        event.target.checked = !event.target.checked;
        return;
    }
    const isActive = event.target.checked;
    
    const productData = { is_active: isActive };
    const success = await updateProduct(productId, productData);
    if (!success) {
        event.target.checked = !isActive;
    }
}

/**
 * Premium 토글 처리
 */
async function handlePremiumToggle(event) {
    const productId = resolveProductId(event.target, '할인 패키지');
    if (productId === null) {
        event.target.checked = !event.target.checked;
        return;
    }
    const isActive = event.target.checked;
    
    const productData = {
        is_active: isActive
    };
    
    const success = await updateProduct(productId, productData);
    if (!success) {
        event.target.checked = !isActive;
    }
}

/**
 * Gold 토글 처리
 */
async function handleGoldToggle(event) {
    const productId = resolveProductId(event.target, '무제한권');
    if (productId === null) {
        event.target.checked = !event.target.checked;
        return;
    }
    const isActive = event.target.checked;
    
    const productData = {
        is_active: isActive
    };
    
    const success = await updateProduct(productId, productData);
    if (!success) {
        event.target.checked = !isActive;
    }
}

/**
 * 요금제 관리 초기화
 */
function initProductManagement() {
    console.log('[initProductManagement] 요금제 관리 초기화 시작');
    
    // 폼 제출 이벤트 리스너
    const standardForm = document.getElementById('standardForm');
    if (standardForm) {
        standardForm.addEventListener('submit', handleStandardSubmit);
    }
    
    const premiumForm = document.getElementById('premiumForm');
    if (premiumForm) {
        premiumForm.addEventListener('submit', handlePremiumSubmit);
    }
    
    const goldForm = document.getElementById('goldForm');
    if (goldForm) {
        goldForm.addEventListener('submit', handleGoldSubmit);
    }
    
    // Premium 토글 이벤트
    const premiumToggle = document.getElementById('premiumToggle');
    if (premiumToggle) {
        premiumToggle.addEventListener('change', handlePremiumToggle);
    }
    
    // Gold 토글 이벤트
    const goldToggle = document.getElementById('goldToggle');
    if (goldToggle) {
        goldToggle.addEventListener('change', handleGoldToggle);
    }

    const eventForm = document.getElementById('eventForm');
    if (eventForm) {
        eventForm.addEventListener('submit', handleEventSubmit);
    }

    const periodEventForm = document.getElementById('periodEventForm');
    if (periodEventForm) {
        periodEventForm.addEventListener('submit', handlePeriodEventSubmit);
    }

    const eventToggle = document.getElementById('eventToggle');
    if (eventToggle) {
        eventToggle.addEventListener('change', handleEventToggle);
    }

    const periodEventToggle = document.getElementById('periodEventToggle');
    if (periodEventToggle) {
        periodEventToggle.addEventListener('change', handlePeriodEventToggle);
    }
    
    // Premium 할인율 실시간 계산
    const premiumTokenInput = document.getElementById('premiumTokenAmount');
    const premiumPriceInput = document.getElementById('premiumPrice');
    const standardPriceInput = document.getElementById('standardPrice');
    
    if (premiumTokenInput) {
        premiumTokenInput.addEventListener('input', calculatePremiumDiscount);
    }
    if (premiumPriceInput) {
        premiumPriceInput.addEventListener('input', calculatePremiumDiscount);
    }
    if (standardPriceInput) {
        standardPriceInput.addEventListener('input', calculatePremiumDiscount);
    }
    
    // 초기 데이터 로드
    loadProducts();
}

// 전역 함수로 노출
window.loadProducts = loadProducts;
window.initProductManagement = initProductManagement;

// 모듈 로드 완료 로그
console.log('[product.js] 요금제 관리 모듈 로드 완료');
