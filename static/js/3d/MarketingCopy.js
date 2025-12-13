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
        width: 280px;
        background: linear-gradient(145deg, rgba(20, 20, 25, 0.98) 0%, rgba(30, 30, 40, 0.95) 100%);
        border: 1px solid rgba(255, 215, 0, 0.3);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), inset 0 0 0 1px rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #ffffff;
        transform: translateY(0);
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        pointer-events: auto !important;
        user-select: none;
        will-change: transform;
        backface-visibility: hidden;
      }
      .smart-console .console-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
      }
      .smart-console .badge {
        background: rgba(255, 215, 0, 0.15);
        color: #FFD700;
        border: 1px solid rgba(255, 215, 0, 0.3);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
        text-transform: uppercase;
      }
      .smart-console .title {
        font-size: 18px;
        font-weight: 800;
        color: #FFD700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0;
        margin-bottom: 4px;
      }
      .smart-console .console-body {
        margin-bottom: 16px;
      }
      .smart-console .desc {
        font-size: 13px;
        color: #a0a0b0;
        line-height: 1.5;
        margin: 0 0 16px 0;
      }
      .smart-console .price-tag {
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin: 15px 0;
        padding-bottom: 15px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }
      .smart-console .highlight {
        color: #00ffff;
        font-weight: 700;
      }
      .smart-console .discount {
        background: #ff0055;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 12px;
        font-weight: 700;
        color: #ffffff;
        margin-left: 3px;
      }
      .smart-console .console-footer {
        margin-top: 16px;
      }
      .smart-console .action-btn {
        width: 100%;
        padding: 14px;
        background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
        color: white;
        font-weight: 700;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
        transition: transform 0.2s ease;
        pointer-events: auto !important;
        font-size: 16px;
        will-change: transform;
        backface-visibility: hidden;
      }
      .smart-console .action-btn:hover {
        transform: translateY(-2px);
      }
      .smart-console .action-btn:active {
        transform: translateY(0);
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

