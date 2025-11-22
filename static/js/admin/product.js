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
    gold: null       // ID: 3
};

/**
 * 상품 데이터 로드 (3개 고정 요금제)
 */
async function loadProducts() {
    console.log('[loadProducts] 요금제 데이터 로드 시작');
    
    try {
        // 3개 상품을 개별적으로 조회
        const productIds = [1, 2, 3];
        const promises = productIds.map(id => 
            fetch(`/admin/api/products/${id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.getCSRFToken()
                },
                credentials: 'include'
            }).then(res => res.json())
        );
        
        const results = await Promise.all(promises);
        
        // 각 상품 데이터 저장 및 UI 업데이트
        results.forEach((result, index) => {
            const productId = productIds[index];
            if (result.success && result.data) {
                const product = result.data;
                
                if (productId === 1) {
                    productData.standard = product;
                    updateStandardCard(product);
                } else if (productId === 2) {
                    productData.premium = product;
                    updatePremiumCard(product);
                } else if (productId === 3) {
                    productData.gold = product;
                    updateGoldCard(product);
                }
            } else {
                console.warn(`[loadProducts] 상품 ID ${productId} 로드 실패:`, result);
            }
        });
        
        console.log('[loadProducts] 요금제 데이터 로드 완료', productData);
        
    } catch (error) {
        console.error('[loadProducts] 요금제 데이터 로드 오류:', error);
        alert('요금제 데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

/**
 * Standard 카드 업데이트
 */
function updateStandardCard(product) {
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
    const productId = parseInt(form.dataset.productId);
    
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
    const productId = parseInt(form.dataset.productId);
    
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
    const productId = parseInt(form.dataset.productId);
    
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
 * Premium 토글 처리
 */
async function handlePremiumToggle(event) {
    const productId = parseInt(event.target.dataset.productId);
    const isActive = event.target.checked;
    
    const productData = {
        is_active: isActive
    };
    
    await updateProduct(productId, productData);
}

/**
 * Gold 토글 처리
 */
async function handleGoldToggle(event) {
    const productId = parseInt(event.target.dataset.productId);
    const isActive = event.target.checked;
    
    const productData = {
        is_active: isActive
    };
    
    await updateProduct(productId, productData);
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
