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
  
  /**
   * 상품별 혜택 리스트 가져오기
   * @param {Object} product - 상품 데이터
   * @returns {Array<string>} - 혜택 리스트
   */
  static getProductBenefits(product) {
    const productType = (product?.type || '').trim().toLowerCase();
    const productName = (product?.name || '').trim().toLowerCase();
    const tokenAmount = product?.token_amount || 0;
    const price = product?.price || 0;
    
    // 상품 타입별 혜택 리스트
    if (productType === 'event' || productType === 'event_period') {
      // 이벤트 상품
      if (tokenAmount > 0) {
        return [
          `✔ 토큰 ${tokenAmount}개 즉시 지급`,
          '✔ 평생 소장 가능',
          '✔ VIP 전용 서포트'
        ];
      } else {
        return [
          '✔ 무료 기간 즉시 시작',
          '✔ 모든 기능 무제한 이용',
          '✔ 기간 내 무료 서포트'
        ];
      }
    } else if (productType === 'basic') {
      // Standard 상품
      return [
        '✔ 급할 때 한 건씩 부담 없는 시작',
        '✔ 소상공인을 위한 맞춤형 플랜',
        '✔ 건당 투자 대비 최고의 효율'
      ];
    } else if (productType === 'package') {
      // Premium Package 상품
      return [
        '✔ 대량 처리 전문가의 선택',
        '✔ 100건 패키지 시간 절약의 달인',
        '✔ 건당 50% 할인 혜택으로 절약'
      ];
    } else if (productType === 'subscription') {
      // Gold Membership 상품
      return [
        '✔ 전문가를 위한 프리미엄 솔루션',
        '✔ 무제한 이용으로 자유로운 업무',
        '✔ 우선 지원 및 전용 서포트'
      ];
    }
    
    // 기본 혜택
    return [
      '✔ 즉시 사용 가능',
      '✔ 안전한 결제 시스템',
      '✔ 전문 고객 지원'
    ];
  }

  /**
   * 메뉴판 CanvasTexture 생성 (4K 해상도 - Real 3D Mesh용)
   * @param {Object} product - 상품 데이터
   * @returns {THREE.CanvasTexture} - 메뉴판 텍스처
   */
  static getMenuTexture(product) {
    // Canvas 생성 (1024x1365 해상도 - 세로 방향으로 크기 증가, 비율 1.5:2.0)
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1365;
    const ctx = canvas.getContext('2d');
    
    // 상품 정보 가져오기
    const cardContent = MarketingCopy.getCardContent(product);
    const productType = (product?.type || '').trim().toLowerCase();
    const isFree = (product?.price === 0 || product?.price === null || cardContent.price === 'FREE');
    const buttonText = isFree ? '🎁 무료 체험' : '지금 시작하기';
    
    // 배경 (완전한 검정에 가까운 다크 그레이)
    ctx.fillStyle = '#111111';
    ctx.fillRect(0, 0, 1024, 1365);
    
    // 골드 테두리 (2px 두께)
    ctx.strokeStyle = '#D4AF37';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(16, 16, 992, 1333, 32);
    ctx.stroke();
    
    // 패딩 설정
    const paddingX = 48;
    const paddingY = 48;
    
    // 헤더: 상품 타입 (중앙 상단) - 크기 증가 및 중앙 정렬
    ctx.fillStyle = '#D4AF37'; // 골드 색상
    ctx.font = 'bold 60px Pretendard, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    const typeText = cardContent.type.toUpperCase();
    ctx.fillText(typeText, 512, paddingY);
    
    // 메인 타이틀: 상품명 (아주 크게) - 가독성 향상을 위해 크기 증가
    const titleY = paddingY + 80;
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 80px Pretendard, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(cardContent.title.toUpperCase(), paddingX, titleY);
    
    // 구분선 (얇은 실선)
    const dividerY = titleY + 100;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(paddingX, dividerY);
    ctx.lineTo(1024 - paddingX, dividerY);
    ctx.stroke();
    
    // 혜택 리스트 (체크리스트 형태) - 가독성 향상을 위해 크기 증가
    const benefits = MarketingCopy.getProductBenefits(product);
    const benefitsY = dividerY + 50;
    ctx.fillStyle = '#DDDDDD';
    ctx.font = '400 60px Pretendard, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    
    benefits.forEach((benefit, index) => {
      const benefitY = benefitsY + index * 80;
      ctx.fillText(benefit, paddingX, benefitY);
    });
    
    // 가격 (우측 하단 또는 중앙 하단, 매우 크게) - 가독성 향상을 위해 크기 증가
    const priceY = 1365 - 350; // 하단에서 350px 위 (밸런스 조정)
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 90px Pretendard, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(cardContent.price, 512, priceY);
    
    // 버튼 (하단 Full-width 스타일) - 세로 크기 증가에 맞춰 조정
    const buttonY = 1365 - 200; // 하단에서 200px 위 (밸런스 조정)
    const buttonHeight = 150; // 버튼 높이 증가
    const buttonPadding = 32;
    
    // 버튼 배경 (브랜드 블루)
    ctx.fillStyle = '#3366FF';
    ctx.beginPath();
    ctx.roundRect(buttonPadding, buttonY, 1024 - buttonPadding * 2, buttonHeight, 16);
    ctx.fill();
    
    // 버튼 텍스트 (가독성 향상을 위해 크기 대폭 증가)
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '700 70px Pretendard, sans-serif'; // 50px → 70px로 증가
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(buttonText, 512, buttonY + buttonHeight / 2);
    
    // CanvasTexture 생성 및 반환
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    texture.flipY = false; // UV 좌표 맞추기
    
    return texture;
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

