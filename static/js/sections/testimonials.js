/* ================================================================
   Testimonials Auto Scroll - RohaTax
   ================================================================ */

(function () {
  'use strict';

  const TestimonialsAutoScroll = {
    grid: null,
    scrollInterval: null,
    scrollSpeed: 1, // 픽셀 단위 스크롤 속도
    pauseOnHover: true,
    isPaused: false,
    isUserScrolling: false,
    userScrollTimeout: null,

    init: function () {
      this.grid = document.querySelector('.testimonials-grid');
      if (!this.grid) return;

      // 가로 스크롤이 필요한지 확인
      if (this.needsScroll()) {
        this.setupAutoScroll();
        this.setupEventListeners();
      }
    },

    needsScroll: function () {
      // 컨테이너 너비보다 콘텐츠가 더 넓은지 확인
      return this.grid.scrollWidth > this.grid.clientWidth;
    },

    setupAutoScroll: function () {
      // 자동 스크롤 시작
      this.startAutoScroll();
    },

    startAutoScroll: function () {
      if (this.scrollInterval) return;

      this.scrollInterval = setInterval(() => {
        if (this.isPaused || this.isUserScrolling) return;

        const maxScroll = this.grid.scrollWidth - this.grid.clientWidth;
        const currentScroll = this.grid.scrollLeft;

        // 끝에 도달하면 처음으로 리셋
        if (currentScroll >= maxScroll - 1) {
          this.grid.scrollTo({
            left: 0,
            behavior: 'smooth',
          });
        } else {
          // 자동 스크롤 진행
          this.grid.scrollLeft += this.scrollSpeed;
        }
      }, 20); // 20ms마다 실행 (50fps)
    },

    stopAutoScroll: function () {
      if (this.scrollInterval) {
        clearInterval(this.scrollInterval);
        this.scrollInterval = null;
      }
    },

    setupEventListeners: function () {
      // 호버 시 일시 정지
      if (this.pauseOnHover) {
        this.grid.addEventListener('mouseenter', () => {
          this.isPaused = true;
        });

        this.grid.addEventListener('mouseleave', () => {
          this.isPaused = false;
        });
      }

      // 사용자 스크롤 감지
      let scrollTimeout;
      this.grid.addEventListener('scroll', () => {
        this.isUserScrolling = true;

        // 사용자 스크롤 후 2초 뒤에 자동 스크롤 재개
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          this.isUserScrolling = false;
        }, 2000);
      });

      // 터치 이벤트 지원
      this.grid.addEventListener('touchstart', () => {
        this.isPaused = true;
      });

      this.grid.addEventListener('touchend', () => {
        setTimeout(() => {
          this.isPaused = false;
        }, 2000);
      });

      // Intersection Observer로 뷰포트에 보일 때만 스크롤
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              this.startAutoScroll();
            } else {
              this.stopAutoScroll();
            }
          });
        },
        {
          threshold: 0.3,
        }
      );

      observer.observe(this.grid);
    },
  };

  // DOM 로드 완료 후 초기화
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      TestimonialsAutoScroll.init();
    });
  } else {
    TestimonialsAutoScroll.init();
  }

  // 전역으로 노출 (필요시)
  window.TestimonialsAutoScroll = TestimonialsAutoScroll;
})();
