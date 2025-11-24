/**
 * Profile V2 - Modern JavaScript
 * 분리된 스크립트: 인라인 스크립트를 외부 파일로 이동 및 정리
 */

// ===== 폼 유효성 검사 및 미리보기 =====
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('profileForm');
  if (!form) return;
  
  const inputs = form.querySelectorAll('input[required]');
  const previewBtn = document.getElementById('preview-btn');
  const confirmBtn = document.getElementById('confirm-btn');
  const previewModal = document.getElementById('preview-modal');
  const closeBtn = document.querySelector('.close');
  const confirmUpdateBtn = document.getElementById('confirm-update');
  const cancelUpdateBtn = document.getElementById('cancel-update');
  
  // 원본 데이터 저장 (Jinja2 변수는 서버에서 주입)
  const originalData = {
    company_name: '{{ user.company_name or "" }}',
    representative_name: '{{ user.representative_name or "" }}',
    phone: '{{ user.phone or "" }}',
    email: '{{ user.email or "" }}',
    address: '{{ user.address or "" }}',
    business_type: '{{ user.business_type or "" }}',
    business_category: '{{ user.business_category or "" }}'
  };
  
  // 실시간 유효성 검사
  inputs.forEach(input => {
    input.addEventListener('input', function() {
      validateField(this);
    });
    
    input.addEventListener('blur', function() {
      validateField(this);
    });
  });
  
  // 미리보기 버튼 클릭
  if (previewBtn) {
    previewBtn.addEventListener('click', function() {
      console.log('👁️ 미리보기 버튼 클릭됨');
      if (validateAllFields()) {
        console.log('✅ 미리보기 유효성 검사 통과');
        showPreview();
      } else {
        console.log('❌ 미리보기 유효성 검사 실패');
        alert('입력 정보를 다시 확인해주세요.');
      }
    });
  }
  
  // 모달 닫기
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelUpdateBtn) cancelUpdateBtn.addEventListener('click', closeModal);
  
  // 모달 외부 클릭 시 닫기
  if (previewModal) {
    previewModal.addEventListener('click', function(e) {
      if (e.target === previewModal) {
        closeModal();
      }
    });
  }
  
  // 확인 및 적용 버튼 클릭
  if (confirmUpdateBtn) {
    confirmUpdateBtn.addEventListener('click', function() {
      console.log('🔍 확인 및 적용 버튼 클릭됨');
      closeModal();
      
      if (validateAllFields()) {
        console.log('✅ 유효성 검사 통과');
        if (confirmBtn) confirmBtn.style.display = 'inline-block';
        if (previewBtn) previewBtn.style.display = 'none';
        console.log('📤 폼 제출 시작');
        form.submit();
      } else {
        console.log('❌ 유효성 검사 실패');
        alert('입력 정보를 다시 확인해주세요.');
      }
    });
  }
  
  function validateField(field) {
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
  
  function validateAllFields() {
    let allValid = true;
    inputs.forEach(input => {
      if (!validateField(input)) {
        allValid = false;
      }
    });
    return allValid;
  }
  
  function showPreview() {
    console.log('📋 미리보기 표시 시작');
    const currentData = {
      company_name: document.getElementById('company_name').value.trim(),
      representative_name: document.getElementById('representative_name').value.trim(),
      phone: document.getElementById('phone').value.trim(),
      email: document.getElementById('email').value.trim(),
      address: document.getElementById('address').value.trim(),
      business_type: document.getElementById('business_type').value.trim(),
      business_category: document.getElementById('business_category').value.trim()
    };
    
    const changesHTML = Object.keys(currentData).map(key => {
      const oldValue = originalData[key] || '-';
      const newValue = currentData[key] || '-';
      const isChanged = oldValue !== newValue;
      
      return `
        <div class="preview-item ${isChanged ? 'changed' : 'unchanged'}">
          <span class="preview-label">${getFieldLabel(key)}</span>
          <div class="preview-value">
            ${isChanged ? `<span class="preview-value old">${oldValue}</span>` : ''}
            <span class="preview-value ${isChanged ? 'new' : ''}">${newValue}</span>
          </div>
        </div>
      `;
    }).join('');
    
    const previewChangesEl = document.getElementById('preview-changes');
    if (previewChangesEl) previewChangesEl.innerHTML = changesHTML;
    
    const finalHTML = Object.keys(currentData).map(key => {
      return `
        <div class="preview-item">
          <span class="preview-label">${getFieldLabel(key)}</span>
          <span class="preview-value">${currentData[key] || '-'}</span>
        </div>
      `;
    }).join('');
    
    const previewFinalEl = document.getElementById('preview-final');
    if (previewFinalEl) previewFinalEl.innerHTML = finalHTML;
    
    if (previewModal) previewModal.style.display = 'block';
  }
  
  function getFieldLabel(fieldName) {
    const labels = {
      company_name: '🏢 회사명',
      representative_name: '👤 대표자명',
      phone: '📱 전화번호',
      email: '📧 이메일',
      address: '📍 주소',
      business_type: '🏭 업태',
      business_category: '📋 종목'
    };
    return labels[fieldName] || fieldName;
  }
  
  function closeModal() {
    console.log('❌ 미리보기 모달 닫기');
    if (previewModal) previewModal.style.display = 'none';
  }
  
  // 폼 제출 시 전체 검증
  form.addEventListener('submit', function(e) {
    console.log('📋 폼 제출 이벤트 발생');
    
    if (confirmBtn && confirmBtn.style.display === 'inline-block') {
      console.log('✅ 확인 버튼이 표시됨 - 제출 허용');
      return true;
    }
    
    console.log('🔍 일반 제출 - 유효성 검사 수행');
    if (!validateAllFields()) {
      console.log('❌ 유효성 검사 실패 - 제출 차단');
      e.preventDefault();
      alert('입력 정보를 다시 확인해주세요.');
    } else {
      console.log('✅ 유효성 검사 통과 - 제출 허용');
    }
  });
});

// ===== 실시간 토큰 관리자 =====
class RealtimeTokenManager {
    constructor() {
        this.updateInterval = 30000; // 30초마다 업데이트
        this.isUpdating = false;
        this.init();
    }
    
    init() {
        this.updateTokenStatus().catch(err => {
            console.error('초기 토큰 상태 로드 실패:', err);
            const totalEl = document.getElementById('total-tokens-display');
            const usedEl = document.getElementById('tokens-used-display');
            const availableEl = document.getElementById('available-tokens-display');
            if (totalEl) totalEl.textContent = '0';
            if (usedEl) usedEl.textContent = '0';
            if (availableEl) availableEl.textContent = '0';
        });
        this.startAutoUpdate();
        this.bindEvents();
    }
    
    async updateTokenStatus() {
        if (this.isUpdating) return Promise.resolve();
        
        this.isUpdating = true;
        this.showLoadingIndicator();
        
        try {
            const response = await fetch('/api/v2/user/token-summary');
            const data = await response.json();
            
            if (data.success) {
                this.updateUI(data.data);
                this.showLastUpdated();
                return Promise.resolve(data.data);
            } else {
                console.error('토큰 상태 업데이트 실패:', data.error);
                this.showError('토큰 상태를 불러올 수 없습니다');
                return Promise.reject(new Error(data.error || '토큰 상태 업데이트 실패'));
            }
        } catch (error) {
            console.error('API 요청 실패:', error);
            this.showError('네트워크 오류가 발생했습니다');
            return Promise.reject(error);
        } finally {
            this.isUpdating = false;
            this.hideLoadingIndicator();
        }
    }
    
    updateUI(data) {
        const totalEl = document.getElementById('total-tokens-display');
        const usedEl = document.getElementById('tokens-used-display');
        const availableEl = document.getElementById('available-tokens-display');
        
        // 카운팅 애니메이션 적용
        if (totalEl) {
            this.animateCount(totalEl, parseInt(data.total_tokens) || 0);
        }
        if (usedEl) {
            this.animateCount(usedEl, parseInt(data.used_tokens) || 0);
        }
        if (availableEl) {
            this.animateCount(availableEl, parseInt(data.available_tokens) || 0);
        }
        
        // 하위 호환성
        const tokenCards = document.querySelectorAll('.token-stat-card');
        if (tokenCards.length >= 3) {
            if (!totalEl) {
                const el = tokenCards[0].querySelector('.stat-value');
                if (el) this.animateCount(el, parseInt(data.total_tokens) || 0);
            }
            if (!usedEl) {
                const el = tokenCards[1].querySelector('.stat-value');
                if (el) this.animateCount(el, parseInt(data.used_tokens) || 0);
            }
            if (!availableEl) {
                const el = tokenCards[2].querySelector('.stat-value');
                if (el) this.animateCount(el, parseInt(data.available_tokens) || 0);
            }
        }
    }

    /**
     * 카운팅 애니메이션 (CountUp)
     * 0부터 목표 숫자까지 부드럽게 증가하는 애니메이션
     */
    animateCount(element, targetValue) {
        if (!element) return;
        
        const startValue = parseInt(element.textContent) || 0;
        const duration = 1500; // 1.5초
        const startTime = performance.now();
        
        // 카운팅 애니메이션 클래스 추가
        element.classList.add('counting');
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing 함수 (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOut);
            
            element.textContent = currentValue.toLocaleString('ko-KR');
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = targetValue.toLocaleString('ko-KR');
                element.classList.remove('counting');
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    showLoadingIndicator() {
        const refreshIcon = document.querySelector('.refresh-icon');
        if (refreshIcon) {
            refreshIcon.style.animation = 'spin 1s linear infinite';
        }
    }
    
    hideLoadingIndicator() {
        const refreshIcon = document.querySelector('.refresh-icon');
        if (refreshIcon) {
            refreshIcon.style.animation = 'spin 2s linear infinite';
        }
    }
    
    showLastUpdated() {
        const refreshText = document.querySelector('.refresh-text');
        if (refreshText) {
            refreshText.textContent = `마지막 업데이트: ${new Date().toLocaleTimeString('ko-KR')}`;
        }
    }
    
    showError(message) {
        if (typeof showNotification === 'function') {
            showNotification(message, 'error');
        } else {
            console.error(message);
        }
    }
    
    startAutoUpdate() {
        setInterval(() => {
            this.updateTokenStatus();
        }, this.updateInterval);
    }
    
    bindEvents() {
        const refreshButton = document.querySelector('.refresh-indicator');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.updateTokenStatus();
            });
        }
        
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.updateTokenStatus();
            }
        });
    }
}

// 페이지 로드 시 실시간 토큰 매니저 초기화
document.addEventListener('DOMContentLoaded', function() {
    window.tokenManager = new RealtimeTokenManager();
});

// ===== 활동 내역 한글화 및 파싱 유틸리티 =====

/**
 * 활동 유형을 한글로 변환
 * @param {string} activityType - 활동 유형 코드
 * @returns {string} 한글 활동 유형
 */
function translateActivityType(activityType) {
    if (!activityType) return '-';
    
    // 이미 한글이 포함되어 있으면 그대로 반환
    if (/[가-힣]/.test(activityType)) {
        return activityType;
    }
    
    const translationMap = {
        // 결제 관련
        'PAYMENT_CANCEL': '결제 취소',
        'PAYMENT_SUCCESS': '결제 완료',
        'PAYMENT_FAILED': '결제 실패',
        'PAYMENT_REFUND': '결제 환불',
        
        // 토큰 관련
        'TOKEN_CHARGE': '토큰 충전',
        'TOKEN_USE': '토큰 사용',
        'TOKEN_REFUND': '토큰 환불',
        'TOKEN_RESET': '토큰 초기화',
        'TOKEN_RESET_BY_ADMIN': '관리자 토큰 초기화',
        'TOKEN_ADJUST': '토큰 조정',
        'TOKEN_GRANT_BY_ADMIN': '관리자 토큰 지급',
        
        // 파일 변환 관련
        'FILE_CONVERT': '파일 변환',
        'FILE_CONVERT_SUCCESS': '파일 변환 성공',
        'FILE_CONVERT_FAILED': '파일 변환 실패',
        
        // 등급 관련
        'GRADE_CHANGE': '등급 변경',
        'GRADE_UPGRADE': '등급 상승',
        'GRADE_DOWNGRADE': '등급 하락',
        'GRADE_CHANGE_BY_ADMIN': '관리자 등급 변경',
        
        // 사용자 관련
        'USER_REGISTER': '회원 가입',
        'USER_UPDATE': '회원 정보 수정',
        'USER_LOGIN': '로그인',
        'USER_LOGOUT': '로그아웃',
        'USER_RESTORE_BY_ADMIN': '계정 복구',
        'USER_SOFT_DELETE_BY_ADMIN': '계정 비활성화',
        'PROFILE_UPDATE': '프로필 수정',
        
        // 기타
        'SYSTEM_EVENT': '시스템 이벤트',
        'ADMIN_ACTION': '관리자 작업',
        'AUTO_CHARGE': '자동 충전',
        'BONUS_GIFT': '보너스 지급',
        'LOGIN': '로그인',
        'LOGOUT': '로그아웃'
    };
    
    return translationMap[activityType] || activityType;
}

/**
 * 상세 정보 JSON을 파싱하여 한글 문장으로 재구성
 * @param {string|object} details - 상세 정보 (JSON 문자열 또는 객체)
 * @param {string} activityType - 활동 유형 (컨텍스트 제공)
 * @returns {string} 한글화된 상세 정보
 */
function parseDetails(details, activityType) {
    if (!details) return '세부 정보 없음';
    
    // 이미 문자열이고 JSON이 아닌 경우
    if (typeof details === 'string' && !details.trim().startsWith('{') && !details.trim().startsWith('[')) {
        return details;
    }
    
    let parsedData;
    
    // JSON 문자열 파싱 시도
    try {
        if (typeof details === 'string') {
            parsedData = JSON.parse(details);
        } else {
            parsedData = details;
        }
    } catch (e) {
        // JSON 파싱 실패 시 원본 텍스트 반환 (깔끔하게 처리)
        const cleanText = typeof details === 'string' 
            ? details.replace(/[{}[\]]/g, '').trim() 
            : String(details);
        return cleanText || '세부 정보 없음';
    }
    
    // 객체가 아닌 경우
    if (typeof parsedData !== 'object' || parsedData === null) {
        return String(parsedData);
    }
    
    // 활동 유형별 맞춤 파싱 (깔끔한 한글 문장만 표시)
    const formatTokenForDetails = (amount) => {
        if (amount === -1 || amount === '-1') {
            return '무제한';
        }
        return parseInt(amount).toLocaleString('ko-KR');
    };
    
    const formatAmount = (amount) => {
        if (amount === null || amount === undefined) return '';
        return parseInt(amount).toLocaleString('ko-KR');
    };
    
    // 활동 유형별 맞춤 처리
    const currentActivityType = activityType || '';
    
    // 1. 결제 관련 로그 (PAYMENT_CANCEL, PAYMENT_SUCCESS, PAYMENT_REFUND 등)
    if (currentActivityType.includes('PAYMENT') || parsedData.payment_id !== undefined || parsedData.order_id !== undefined) {
        const parts = [];
        
        // 상품명 표시
        if (parsedData.product_name) {
            parts.push(parsedData.product_name);
        }
        
        // 금액 표시
        if (parsedData.amount !== undefined && parsedData.amount !== null) {
            const amount = formatAmount(parsedData.amount);
            if (amount) {
                parts.push(`(${amount}원)`);
            }
        }
        
        if (parts.length > 0) {
            return parts.join(' ');
        }
        
        // 상품명이나 금액이 없으면 기본 메시지
        if (parsedData.amount !== undefined && parsedData.amount !== null) {
            return `${formatAmount(parsedData.amount)}원 결제`;
        }
        
        return '결제 정보';
    }
    
    // 2. 파일 변환 로그 (FILE_CONVERT)
    if (currentActivityType.includes('FILE_CONVERT') || currentActivityType.includes('CONVERT') || parsedData.filename !== undefined || parsedData.file_name !== undefined) {
        const filename = parsedData.filename || parsedData.file_name || '';
        const extractedRows = parsedData.extracted_row || parsedData.extracted_rows || parsedData.count || parsedData.file_count || '';
        
        if (filename && extractedRows) {
            return `${filename} (${extractedRows}건 변환)`;
        } else if (filename) {
            return `${filename} 변환`;
        } else if (extractedRows) {
            return `${extractedRows}건 변환`;
        }
        
        return '파일 변환';
    }
    
    // 3. 관리자 지급 로그 (TOKEN_GRANT_BY_ADMIN)
    if (currentActivityType.includes('GRANT') || currentActivityType.includes('ADMIN')) {
        const parts = [];
        
        if (parsedData.reason) {
            parts.push(`사유: ${parsedData.reason}`);
        }
        
        if (parsedData.amount !== undefined && parsedData.amount !== null) {
            const amount = formatTokenForDetails(parsedData.amount);
            parts.push(`(${amount} 토큰)`);
        } else if (parsedData.token_amount !== undefined) {
            const amount = formatTokenForDetails(parsedData.token_amount);
            parts.push(`(${amount} 토큰)`);
        }
        
        if (parts.length > 0) {
            return parts.join(' ');
        }
        
        return '관리자 지급';
    }
    
    // 4. 토큰 충전 로그 (TOKEN_CHARGE)
    if (currentActivityType.includes('CHARGE') || parsedData.charge_token_amount !== undefined) {
        const amount = parsedData.charge_token_amount || parsedData.token_amount || parsedData.amount;
        if (amount !== undefined && amount !== null) {
            return `${formatTokenForDetails(amount)} 토큰 충전`;
        }
        return '토큰 충전';
    }
    
    // 5. 토큰 환불 로그 (TOKEN_REFUND, PAYMENT_CANCEL)
    if (currentActivityType.includes('REFUND') || currentActivityType.includes('CANCEL') || parsedData.refund_token_amount !== undefined) {
        const amount = parsedData.refund_token_amount || parsedData.amount;
        if (amount !== undefined && amount !== null) {
            return `${formatTokenForDetails(amount)} 토큰 환불`;
        }
        return '토큰 환불';
    }
    
    // 6. 토큰 사용 로그 (TOKEN_USE)
    if (currentActivityType.includes('USE') || parsedData.used_tokens !== undefined) {
        const amount = parsedData.used_tokens || parsedData.token_amount;
        if (amount !== undefined && amount !== null) {
            return `${formatTokenForDetails(amount)} 토큰 사용`;
        }
        return '토큰 사용';
    }
    
    // 7. 등급 변경 로그 (GRADE_CHANGE)
    if (currentActivityType.includes('GRADE') || parsedData.old_grade !== undefined || parsedData.from_plan !== undefined) {
        const from = parsedData.from_plan || parsedData.old_grade || '';
        const to = parsedData.to_plan || parsedData.new_grade || '';
        
        if (from && to) {
            return `${from} → ${to}`;
        } else if (to) {
            return `${to}로 변경`;
        }
        
        return '등급 변경';
    }
    
    // 8. 메시지나 설명이 있는 경우 (이미 한글 문장인 경우)
    if (parsedData.message) {
        return parsedData.message;
    }
    if (parsedData.description) {
        return parsedData.description;
    }
    
    // 9. 기타: 최소한의 정보만 표시
    const simpleInfo = [];
    
    if (parsedData.reason) {
        simpleInfo.push(`사유: ${parsedData.reason}`);
    }
    
    if (parsedData.amount !== undefined && parsedData.amount !== null && !currentActivityType.includes('PAYMENT')) {
        simpleInfo.push(`${formatAmount(parsedData.amount)}원`);
    }
    
    if (simpleInfo.length > 0) {
        return simpleInfo.join(' ');
    }
    
    // 모든 필터링을 통과하지 못한 경우 (개발용 정보는 숨김)
    return '세부 정보 없음';
}

// ===== 활동 내역 로드 =====
async function loadAndRenderActivityLogs() {
    const activityList = document.querySelector('#activity-list');
    if (!activityList) {
        console.error('활동 내역 리스트를 찾을 수 없습니다.');
        return;
    }

    try {
        const response = await fetch('/api/v2/user/activity-logs');
        const result = await response.json();

        if (!result.success || !Array.isArray(result.data)) {
            activityList.innerHTML = '<div class="activity-item"><div class="activity-content"><div class="activity-main">거래 내역을 불러오는 데 실패했습니다.</div></div></div>';
            return;
        }

        if (result.data.length === 0) {
            activityList.innerHTML = '<div class="activity-item"><div class="activity-content"><div class="activity-main">거래 내역이 없습니다.</div></div></div>';
            return;
        }

        let previousBalance = 0;
        const cardsHtml = result.data.map(log => {
            let currentBalance;
            if (log.activity_type === 'TOKEN_RESET_BY_ADMIN') {
                currentBalance = 0;
            } else {
                currentBalance = previousBalance + (log.token_change || 0);
            }

            // 토큰 수량 포맷팅 함수 (-1 -> 무제한)
            const formatTokenAmount = (amount) => {
                if (amount === -1 || amount === '-1') {
                    return '무제한';
                }
                const numAmount = parseInt(amount) || 0;
                return numAmount.toLocaleString('ko-KR');
            };
            
            // 토큰 변화량 계산 및 포맷팅
            let tokenChange = '';
            let tokenChangeClass = '';
            if (log.token_change > 0) {
                const chargeAmount = formatTokenAmount(log.token_change);
                tokenChange = chargeAmount === '무제한' ? '무제한' : `+${chargeAmount}`;
                tokenChangeClass = 'token-change charge';
            } else if (log.token_change < 0 && log.activity_type !== 'TOKEN_RESET_BY_ADMIN') {
                const usageAmount = formatTokenAmount(Math.abs(log.token_change));
                tokenChange = usageAmount === '무제한' ? '무제한' : `-${usageAmount}`;
                tokenChangeClass = 'token-change usage';
            } else {
                tokenChange = '-';
                tokenChangeClass = 'token-change';
            }
            
            // 활동 유형 한글화 (필드명 다양성 대응: activity_type, type, log_type 등)
            const activityTypeRaw = log.activity_type || log.type || log.log_type || '';
            let activityTypeText = log.activity_type_korean || translateActivityType(activityTypeRaw);
            
            // 활동 유형이 여전히 영문이면 강제 변환
            if (activityTypeText && !/[가-힣]/.test(activityTypeText)) {
                activityTypeText = translateActivityType(activityTypeText);
            }
            
            // 상세 정보 파싱 및 한글화 (필드명 다양성 대응)
            const detailsSource = log.details || log.details_summary || log.meta || log.message || '';
            let detailsText = '';
            
            // 1차: parseDetails 함수 사용
            if (detailsSource) {
                detailsText = parseDetails(detailsSource, activityTypeRaw);
            }
            
            // 2차: parseDetails가 실패하거나 빈 문자열이면 직접 파싱
            if (!detailsText || detailsText === '세부 정보 없음' || detailsText.trim() === '' || detailsText.includes('{') || detailsText.includes('}')) {
                // JSON 문자열 직접 파싱 시도
                if (typeof detailsSource === 'string' && detailsSource.trim().startsWith('{')) {
                    try {
                        const parsed = JSON.parse(detailsSource);
                        if (parsed.message) {
                            detailsText = parsed.message;
                        } else if (parsed.reason) {
                            detailsText = `사유: ${parsed.reason}`;
                        } else if (parsed.filename) {
                            const count = parsed.count || parsed.extracted_rows || parsed.file_count || '';
                            detailsText = count ? `${parsed.filename} (${count}건)` : parsed.filename;
                        } else if (parsed.product_name) {
                            const amount = parsed.amount ? `(${parseInt(parsed.amount).toLocaleString('ko-KR')}원)` : '';
                            detailsText = `${parsed.product_name} ${amount}`.trim();
                        } else {
                            // 객체의 첫 번째 의미있는 값 사용
                            const meaningfulKeys = ['message', 'reason', 'filename', 'description', 'note', 'info'];
                            for (const key of meaningfulKeys) {
                                if (parsed[key]) {
                                    detailsText = String(parsed[key]);
                                    break;
                                }
                            }
                            // 의미있는 키가 없으면 첫 번째 값 사용
                            if (!detailsText) {
                                const firstValue = Object.values(parsed)[0];
                                if (firstValue && typeof firstValue !== 'object') {
                                    detailsText = String(firstValue);
                                }
                            }
                        }
                    } catch (e) {
                        // JSON 파싱 실패 시 원본에서 JSON 구조 제거
                        detailsText = detailsSource.replace(/[{}[\]]/g, '').replace(/"/g, '').replace(/:/g, ': ').trim();
                    }
                } else if (detailsSource && typeof detailsSource === 'string') {
                    // JSON 구조가 포함된 문자열 정리
                    detailsText = detailsSource.replace(/[{}[\]]/g, '').replace(/"/g, '').replace(/:/g, ': ').trim();
                }
            }
            
            // 3차: 여전히 빈 문자열이면 활동 유형을 기본값으로 사용
            if (!detailsText || detailsText.trim() === '') {
                detailsText = activityTypeText;
            }
            
            // 날짜 포맷팅
            const date = new Date(log.timestamp);
            const dateStr = date.toLocaleDateString('ko-KR', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            // 아이콘 결정 (활동 유형에 따라)
            let icon = '●';
            if (log.activity_type && log.activity_type.includes('CHARGE')) {
                icon = '⬆';
            } else if (log.activity_type && (log.activity_type.includes('USE') || log.activity_type.includes('REFUND'))) {
                icon = '⬇';
            } else if (log.activity_type && log.activity_type.includes('PAYMENT')) {
                icon = '💳';
            } else if (log.activity_type && log.activity_type.includes('FILE')) {
                icon = '📄';
            }

            const cardHtml = `
                <div class="activity-item">
                    <div class="activity-icon">${icon}</div>
                    <div class="activity-content">
                        <div class="activity-main">${detailsText || activityTypeText}</div>
                        <div class="activity-meta">
                            <span class="activity-date">${dateStr}</span>
                            <span class="activity-type">${activityTypeText}</span>
                            ${log.user_plan_snapshot ? `<span class="activity-grade">${log.user_plan_snapshot}</span>` : ''}
                        </div>
                    </div>
                    <div class="${tokenChangeClass}">${tokenChange}</div>
                </div>
            `;

            if (log.activity_type === 'TOKEN_RESET_BY_ADMIN') {
                previousBalance = 0;
            } else {
                previousBalance = currentBalance;
            }
            return cardHtml;
        });

        activityList.innerHTML = cardsHtml.reverse().join('');

    } catch (error) {
        console.error('API 요청 실패:', error);
        activityList.innerHTML = '<div class="activity-item"><div class="activity-content"><div class="activity-main">네트워크 오류가 발생했습니다.</div></div></div>';
    }
}

document.addEventListener('DOMContentLoaded', loadAndRenderActivityLogs);

// ===== 골드 고객 관리 =====
document.addEventListener('DOMContentLoaded', function(){
  const card = document.getElementById('gold-customer-card');
  if (!card) return;

  const apiBase = '/api/gold/customers';
  const form = document.getElementById('goldCustomerForm');
  const tbody = document.getElementById('gold-tbody');
  const btnSave = document.getElementById('gold-save');
  const btnReset = document.getElementById('gold-reset');
  const btnSearch = document.getElementById('gold-search-btn');
  const btnRefresh = document.getElementById('gold-refresh');
  const iptSearch = document.getElementById('gold-search');
  const toggleBtn = document.getElementById('gold-toggle');
  const sheetWrap = document.getElementById('gold-sheet-wrap');
  const btnAddRow = document.getElementById('gold-add-row');

  // 아코디언 토글
  if (toggleBtn && sheetWrap) {
    toggleBtn.addEventListener('click', () => {
      const opened = sheetWrap.style.display !== 'none';
      sheetWrap.style.display = opened ? 'none' : 'block';
      toggleBtn.textContent = opened ? '열기' : '접기';
      toggleBtn.setAttribute('aria-expanded', String(!opened));
    });
  }

  function getFormData(){
    return {
      id: (document.getElementById('gold_id').value||'').trim(),
      company_name: (document.getElementById('gold_company_name').value||'').trim(),
      representative_name: (document.getElementById('gold_representative_name').value||'').trim(),
      business_number: (document.getElementById('gold_business_number').value||'').replace(/[^0-9]/g,''),
      address: (document.getElementById('gold_address').value||'').trim(),
      phone: (document.getElementById('gold_phone').value||'').trim(),
      email: (document.getElementById('gold_email').value||'').trim(),
      business_kind: (function(){
        const up = document.getElementById('gold_business_type')?.value || '';
        const it = document.getElementById('gold_business_item')?.value || '';
        try { return JSON.stringify({업태: up, 종목: it}); } catch(_) { return '{"업태":"","종목":""}'; }
      })()
    };
  }

  function setForm(data){
    document.getElementById('gold_id').value = data.id || '';
    document.getElementById('gold_company_name').value = data.company_name || '';
    document.getElementById('gold_representative_name').value = data.representative_name || '';
    document.getElementById('gold_business_number').value = data.business_number || '';
    document.getElementById('gold_address').value = data.address || '';
    document.getElementById('gold_phone').value = data.phone || '';
    document.getElementById('gold_email').value = data.email || '';
    try{
      const bk = JSON.parse(data.business_kind||'{}');
      const up = document.getElementById('gold_business_type');
      const it = document.getElementById('gold_business_item');
      if (up) up.value = bk.업태 || '';
      if (it) it.value = bk.종목 || '';
    }catch(_){
      const up = document.getElementById('gold_business_type');
      const it = document.getElementById('gold_business_item');
      if (up) up.value = '';
      if (it) it.value = '';
    }
  }

  function resetForm(){ setForm({}); }

  function escapeHtml(str){ return String(str).replace(/[&<>\"]/g, s=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[s])); }

  function bindRowActions(){
    tbody.querySelectorAll('button[data-action="save"]').forEach(b=>{
      b.addEventListener('click', async function(){
        const id = this.getAttribute('data-id');
        const tr = this.closest('tr');
        if (!tr) return;
        
        const business_kind_obj = {
          업태: tr.querySelector('input[data-edit="business_type"]').value.trim(),
          종목: tr.querySelector('input[data-edit="business_item"]').value.trim()
        };
        
        const d = {
          representative_name: tr.querySelector('input[data-edit="representative_name"]').value.trim(),
          company_name: tr.querySelector('input[data-edit="company_name"]').value.trim(),
          business_number: tr.querySelector('input[data-edit="business_number"]').value.replace(/[^0-9]/g,''),
          address: tr.querySelector('input[data-edit="address"]').value.trim(),
          email: tr.querySelector('input[data-edit="email"]').value.trim(),
          phone: '',
          business_kind: JSON.stringify(business_kind_obj)
        };
        
        const msg = validate({ ...d, business_kind: '' });
        if (msg){ alert(msg); return; }
        
        const isNew = String(id).startsWith('new-');
        const method = isNew ? 'POST' : 'PUT';
        const url = isNew ? apiBase : (apiBase + '/' + id);
        
        try {
          const res = await fetch(url, {
            method: method,
            credentials:'same-origin',
            headers:{ 'Content-Type':'application/json', 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')||'' },
            body: JSON.stringify(d)
          });
          
          const r = await res.json();
          console.log('저장 응답:', r);
          
          if (!r.success){
            const errorMsg = r.error || (r.errors && r.errors.join(', ')) || '저장 실패';
            console.error('저장 실패:', errorMsg);
            alert(errorMsg);
            return;
          }
          
          alert('저장되었습니다');
          await listCustomers(iptSearch.value||'');
        } catch (error) {
          console.error('저장 중 오류:', error);
          alert('저장 중 오류가 발생했습니다: ' + error.message);
        }
      });
    });
    tbody.querySelectorAll('button[data-action="cancel"]').forEach(b=>{
      b.addEventListener('click', async function(){
        await listCustomers(iptSearch.value||'');
      });
    });
  }

  function viewRow(c){
        const bn = String(c.business_number||'').replace(/(\d{3})(\d{2})(\d{5})/,'$1-$2-$3');
        const bk = (function(){ try{return JSON.parse(c.business_kind||'{}')}catch(_){return {}} })();
        return `<tr data-id="${c.id}">
          <td data-k="representative_name"><input type="text" class="sheet-input" value="${escapeHtml(c.representative_name||'')}" readonly></td>
          <td data-k="company_name"><input type="text" class="sheet-input" value="${escapeHtml(c.company_name||'')}" readonly></td>
          <td data-k="business_number"><input type="text" class="sheet-input" value="${escapeHtml(bn)}" readonly></td>
          <td data-k="address"><input type="text" class="sheet-input" value="${escapeHtml(c.address||'')}" readonly></td>
          <td data-k="email"><input type="text" class="sheet-input" value="${escapeHtml(c.email||'')}" readonly></td>
          <td data-k="business_type"><input type="text" class="sheet-input" value="${escapeHtml(bk.업태||'')}" readonly></td>
          <td data-k="business_item"><input type="text" class="sheet-input" value="${escapeHtml(bk.종목||'')}" readonly></td>
          <td>
            <div class="actions-wrap">
              <button class="icon-btn" data-action="edit" data-id="${c.id}" aria-label="수정">✏️</button>
              <button class="icon-btn" data-action="delete" data-id="${c.id}" aria-label="삭제">🗑️</button>
            </div>
          </td>
        </tr>`;
  }

  function editRow(c){
    const bn = String(c.business_number||'');
    const bk = (function(){ try{return JSON.parse(c.business_kind||'{}')}catch(_){return {}} })();
    return `<tr data-id="${c.id}" data-mode="edit">
          <td><input type="text" value="${escapeHtml(c.representative_name||'')}" data-edit="representative_name" class="sheet-input" placeholder="대표자명"></td>
          <td><input type="text" value="${escapeHtml(c.company_name||'')}" data-edit="company_name" class="sheet-input" placeholder="업체명"></td>
          <td><input type="text" value="${escapeHtml(bn)}" data-edit="business_number" class="sheet-input" placeholder="10자리"></td>
          <td><input type="text" value="${escapeHtml(c.address||'')}" data-edit="address" class="sheet-input" placeholder="주소"></td>
          <td><input type="text" value="${escapeHtml(c.email||'')}" data-edit="email" class="sheet-input" placeholder="이메일"></td>
          <td><input type="text" value="${escapeHtml(bk.업태||'')}" data-edit="business_type" class="sheet-input" placeholder="업태"></td>
          <td><input type="text" value="${escapeHtml(bk.종목||'')}" data-edit="business_item" class="sheet-input" placeholder="종목"></td>
          <td>
            <div class="actions-wrap">
              <button class="icon-btn" data-action="save" data-id="${c.id}" aria-label="저장">✔️</button>
              <button class="icon-btn" data-action="cancel" data-id="${c.id}" aria-label="취소">❌</button>
            </div>
          </td>
        </tr>`;
  }

  let currentPage = 1;
  const pageSize = 15;

  async function listCustomers(q='', page=1){
    currentPage = page;
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#6B7280;">불러오는 중...</td></tr>';
    try{
      const params = new URLSearchParams();
      params.set('limit', String(pageSize));
      params.set('offset', String((page-1)*pageSize));
      if (q) params.set('search', q);
      const url = apiBase + '?' + params.toString();
      const res = await fetch(url, { credentials:'same-origin' });
      const data = await res.json();
      if (!data.success){ throw new Error(data.error||'목록 오류'); }
      
      const rows = (data.data||[]).map(c => viewRow(c)).join('');
      tbody.innerHTML = rows || '<tr><td colspan="8" style="text-align:center;color:#6B7280;">데이터가 없습니다</td></tr>';

      const total = data.total || 0;
      const totalPages = Math.max(1, Math.ceil(total / pageSize));
      const pagEl = document.getElementById('gold-pagination');
      if (pagEl){
        if (totalPages <= 1){ pagEl.innerHTML = ''; }
        else {
          let html = '';
          for (let p = 1; p <= totalPages; p++){
            const active = p === currentPage ? 'background:#10B981;color:#fff;border-color:#10B981;' : '';
            html += `<button data-page="${p}" class="btn btn-secondary" style="padding:6px 10px;border-radius:8px;${active}">${p}</button>`;
          }
          pagEl.innerHTML = html;
          pagEl.querySelectorAll('button[data-page]').forEach(b=>{
            b.addEventListener('click', ()=> listCustomers(iptSearch.value||'', Number(b.getAttribute('data-page'))));
          });
        }
      }

      tbody.querySelectorAll('button[data-action="edit"]').forEach(b=>{
        b.addEventListener('click', async function(){
          const id = Number(this.getAttribute('data-id'));
          const tr = this.closest('tr');
          if (!tr) return;
          const current = {
            id,
            representative_name: tr.querySelector('td[data-k="representative_name"] input').value.trim(),
            company_name: tr.querySelector('td[data-k="company_name"] input').value.trim(),
            business_number: tr.querySelector('td[data-k="business_number"] input').value.replace(/[^0-9]/g,'').trim(),
            address: tr.querySelector('td[data-k="address"] input').value.trim(),
            email: tr.querySelector('td[data-k="email"] input').value.trim(),
            phone: '',
            business_kind: JSON.stringify({
              업태: tr.querySelector('td[data-k="business_type"] input').value.trim(),
              종목: tr.querySelector('td[data-k="business_item"] input').value.trim()
            })
          };
          tr.outerHTML = editRow(current);
          bindRowActions();
        });
      });
      tbody.querySelectorAll('button[data-action="delete"]').forEach(b=>{
        b.addEventListener('click', async function(){
          const id = this.getAttribute('data-id');
          if (!confirm('삭제하시겠습니까?')) return;
          const res = await fetch(apiBase + '/' + id, { method:'DELETE', credentials:'same-origin', headers: { 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')||'' }});
          const d = await res.json();
          if (!d.success){ alert(d.error||'삭제 실패'); return; }
          await listCustomers(iptSearch.value||'', currentPage);
        });
      });

    }catch(e){
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#ef4444;">오류가 발생했습니다</td></tr>';
    }
  }

  function validate(data){
    if (!data.company_name) return '업체명을 입력해주세요';
    if (!data.representative_name) return '대표자명을 입력해주세요';
    if (!/^\d{10}$/.test(data.business_number)) return '사업자등록번호는 하이픈 없이 10자리여야 합니다';
    if (!data.address) return '주소를 입력해주세요';
    if (data.email && !/^[-\w.+]+@[-\w.]+\.[A-Za-z]{2,}$/.test(data.email)) return '이메일 형식이 올바르지 않습니다';
    if (data.phone && !/^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$/.test(data.phone)) return '전화번호 형식이 올바르지 않습니다';
    if (data.business_kind){
      try{ const o = JSON.parse(data.business_kind); if (!o || typeof o!=='object') return '업태·종목은 JSON 객체여야 합니다'; }
      catch(_){ return '업태·종목은 JSON 형식이어야 합니다'; }
    }
    return '';
  }

  async function save(){
    const d = getFormData();
    const msg = validate(d);
    if (msg){ alert(msg); return; }
    const method = d.id ? 'PUT' : 'POST';
    const url = d.id ? (apiBase + '/' + d.id) : apiBase;
    const res = await fetch(url, {
      method,
      credentials:'same-origin',
      headers:{ 'Content-Type':'application/json', 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')||'' },
      body: JSON.stringify({
        company_name: d.company_name,
        representative_name: d.representative_name,
        business_number: d.business_number,
        address: d.address,
        phone: d.phone,
        email: d.email,
        business_kind: d.business_kind
      })
    });
    const r = await res.json();
    if (!r.success){ alert((r.error || (r.errors && r.errors.join(', ')) || '저장 실패')); return; }
    resetForm();
    await listCustomers(iptSearch.value||'');
  }

  if (btnSave) btnSave.addEventListener('click', save);
  if (btnReset) btnReset.addEventListener('click', resetForm);
  if (btnSearch) btnSearch.addEventListener('click', ()=> listCustomers(iptSearch.value||'', 1));
  if (btnRefresh) btnRefresh.addEventListener('click', ()=> listCustomers('', 1));
  if (iptSearch) iptSearch.addEventListener('input', ()=> listCustomers(iptSearch.value||'', 1));
  if (btnAddRow) btnAddRow.addEventListener('click', ()=>{
    const temp = {
      id: 'new-'+Date.now(),
      representative_name: '', company_name: '', business_number: '', address: '', email: '', phone: '', business_kind: '{"업태":"","종목":""}'
    };
    tbody.insertAdjacentHTML('afterbegin', editRow(temp));
    bindRowActions();
  });

  listCustomers('', 1);
  
});

// ===== 아코디언 토글 =====
(function(){
  try {
    const tokenHeader = document.getElementById('token-usage-header');
    const tokenContent = document.getElementById('token-usage-content');
    const tokenArrow = document.getElementById('token-usage-arrow');
    let tokenActivityLoaded = false;

    async function initializeTokenActivity() {
      if (typeof window.initializeTokenActivity === 'function') {
        try {
          await window.initializeTokenActivity();
          tokenActivityLoaded = true;
        } catch (err) {
          console.error('[token-usage] 초기화 실패:', err);
        }
      } else {
        tokenActivityLoaded = true;
      }
    }

    if (tokenHeader && tokenContent) {
      tokenHeader.addEventListener('click', function(){
        const isOpen = getComputedStyle(tokenContent).display === 'block';
        tokenContent.style.setProperty('display', isOpen ? 'none' : 'block', 'important');
        if (tokenArrow) tokenArrow.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';

        if (!isOpen && !tokenActivityLoaded) {
          initializeTokenActivity();
        }
      });
    }
  } catch(_) {/* no-op */}

  try {
    const basicHeader = document.getElementById('basic-info-header');
    const basicContent = document.getElementById('basic-info-content');
    const basicArrow = basicHeader ? basicHeader.querySelector('.accordion-icon') : null;
    if (basicHeader && basicContent) {
      basicHeader.addEventListener('click', function(){
        const isOpen = getComputedStyle(basicContent).display === 'block';
        basicContent.style.setProperty('display', isOpen ? 'none' : 'block', 'important');
        if (basicArrow) basicArrow.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
      });
    }
  } catch(_) {/* no-op */}
})();

