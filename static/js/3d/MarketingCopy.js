/**
 * MarketingCopy - 마케팅 문구 생성 모듈
 * 3D 쇼룸의 상품 라벨 HTML 콘텐츠를 생성
 */
class MarketingCopy {
  /**
   * 상품 타입별 마케팅 문구 생성
   * @param {Object} product - 상품 데이터
   * @returns {Object} cardContent - { type, title, detail, price }
   */
  static getCardContent(product) {
    const productName = (product?.name || '').toLowerCase().replace(/\s+/g, '');
    const productType = (product?.type || '').toLowerCase().trim();
    
    let cardContent = {
      type: '',
      title: '',
      detail: '',
      price: ''
    };
    
    // 케이스별 콘텐츠 구성 (업그레이드된 문구)
    if (productType === 'event' || productType === 'event_period') {
      // Event 1 (토큰지급) 또는 Event 2 (기간제) 구분
      if (product?.token_amount && product.token_amount > 0) {
        // Event 1: 토큰지급
        cardContent = {
          type: 'EVENT',
          title: '🎁 첫 만남의 선물',
          detail: `가입 즉시 무료 혜택<br>토큰 <span class="highlight">${product.token_amount}개</span> 지급`,
          price: 'FREE'
        };
      } else if (product?.duration_days && product.duration_days > 0) {
        // Event 2: 기간제
        cardContent = {
          type: 'EVENT',
          title: '🚀 비즈니스 확장팩',
          detail: `고객사의 고객까지 케어<br><span class="highlight">${product.duration_days}일</span> 무제한 이용`,
          price: 'FREE'
        };
      } else {
        // 기본 이벤트
        cardContent = {
          type: 'EVENT',
          title: '🎁 첫 만남의 선물',
          detail: '가입 즉시 무료 혜택',
          price: 'FREE'
        };
      }
    } else if (productName.includes('standard')) {
      // Standard
      cardContent = {
        type: 'STANDARD',
        title: '🪙 알뜰 요금제',
        detail: '필요한 만큼만 가볍게',
        price: `${Number(product.price || 0).toLocaleString('ko-KR')}원 / 건`
      };
    } else if (productName.includes('premium')) {
      // Premium - 할인율 적용
      const discountRate = (window.SHOWROOM_DATA?.discount_rate || 0);
      const hasDiscount = discountRate > 0;
      
      cardContent = {
        type: 'PREMIUM',
        title: '💎 파워 패키지',
        detail: `대량 처리를 위한 정석<br>토큰 <span class="highlight">${product.token_amount || 0}개</span>${hasDiscount ? ` (<span class="discount">${discountRate}% SAVE</span>)` : ''}`,
        price: `${Number(product.price || 0).toLocaleString('ko-KR')}원`
      };
    } else if (productName.includes('gold')) {
      // Gold
      cardContent = {
        type: 'GOLD',
        title: '👑 VIP 멤버십',
        detail: '세무대행 완벽 자동화<br>기간 내 <span class="highlight">무제한</span>',
        price: `${Number(product.price || 0).toLocaleString('ko-KR')}원 / 월`
      };
    } else {
      // Fallback
      cardContent = {
        type: 'PRODUCT',
        title: product?.name || 'PRODUCT',
        detail: '상세 정보',
        price: product?.price ? `${Number(product.price).toLocaleString('ko-KR')}원` : 'N/A'
      };
    }
    
    return cardContent;
  }
  
  /**
   * 스마트 콘솔 HTML 콘텐츠 생성
   * @param {Object} product - 상품 데이터
   * @returns {String} innerHTML - 스마트 콘솔의 innerHTML 문자열
   */
  static getLabelContent(product) {
    const cardContent = MarketingCopy.getCardContent(product);
    const productType = (product?.type || '').toLowerCase().trim();
    
    // 버튼 텍스트 결정 (가격이 0원이면 "무료 체험", 유료면 "구매하기")
    const isFree = (product?.price === 0 || product?.price === null || cardContent.price === 'FREE');
    const buttonText = isFree ? '🎁 무료 체험' : '💳 구매하기';
    
    // HTML 구조 생성
    const innerHTML = `
      <div class="console-header">
        <span class="badge">[${cardContent.type}]</span>
        <h3 class="title">${cardContent.title}</h3>
      </div>
      <div class="console-body">
        <p class="desc">${cardContent.detail}</p>
        <div class="price-tag">${cardContent.price}</div>
      </div>
      <div class="console-footer">
        <button class="action-btn" data-product-id="${product?.id || product?.product_id || ''}" 
                data-product-name="${product?.name || ''}" 
                data-product-price="${product?.price || 0}" 
                data-product-type="${productType}" 
                data-product-token="${product?.token_amount || 0}" 
                data-product-duration="${product?.duration_days || 0}">
          ${buttonText}
        </button>
      </div>
    `;
    
    return innerHTML;
  }
  
  /**
   * CSS 스타일 반환 (한 번만 추가되도록 외부에서 관리)
   * @returns {String} CSS 스타일 문자열
   */
  static getStyles() {
    return `
      .smart-console {
        width: 300px;
        background: rgba(0, 0, 0, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 20px;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #ffffff;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        pointer-events: auto !important;
        user-select: none;
      }
      .smart-console .console-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
      }
      .smart-console .badge {
        padding: 4px 10px;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        color: #10b981;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .smart-console .title {
        font-size: 20px;
        font-weight: 700;
        color: #ffd700;
        letter-spacing: 1px;
        margin: 0;
        text-transform: uppercase;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9), 0 0 4px rgba(255, 215, 0, 0.5);
      }
      .smart-console .console-body {
        margin-bottom: 16px;
      }
      .smart-console .desc {
        font-size: 14px;
        color: #ffffff;
        line-height: 1.4;
        margin: 0 0 10px 0;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
      }
      .smart-console .price-tag {
        font-size: 24px;
        font-weight: 800;
        color: #ffffff;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.9), 0 0 6px rgba(255, 255, 255, 0.3);
      }
      .smart-console .highlight {
        color: #00ffff;
        font-weight: 700;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9), 0 0 6px rgba(0, 255, 255, 0.8);
      }
      .smart-console .discount {
        background: #ff0055;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 12px;
        font-weight: 700;
        color: #ffffff;
        margin-left: 3px;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
      }
      .smart-console .console-footer {
        margin-top: 16px;
      }
      .smart-console .action-btn {
        width: 100%;
        padding: 12px;
        background: #007aff;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        transition: background 0.3s ease, transform 0.1s ease;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        pointer-events: auto !important;
      }
      .smart-console .action-btn:hover {
        background: #0051d5;
        transform: translateY(-1px);
      }
      .smart-console .action-btn:active {
        transform: translateY(0);
        background: #003d9e;
      }
    `;
  }
  
  /**
   * CSS 스타일을 문서에 추가 (한 번만 실행)
   */
  static injectStyles() {
    if (!document.getElementById('smart-console-styles')) {
      const style = document.createElement('style');
      style.id = 'smart-console-styles';
      style.textContent = MarketingCopy.getStyles();
      document.head.appendChild(style);
    }
  }
}

// 전역 노출 (ES6 모듈이 아닌 경우 대비)
if (typeof window !== 'undefined') {
  window.MarketingCopy = MarketingCopy;
}

// 스타일 자동 주입 (모듈 로드 시)
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      MarketingCopy.injectStyles();
    });
  } else {
    MarketingCopy.injectStyles();
  }
}

