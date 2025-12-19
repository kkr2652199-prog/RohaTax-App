/* ================================================================
   Testimonials Auto Scroll - RohaTax
   ================================================================ */

(function() {
    'use strict';
    
    const TestimonialsAutoScroll = {
        grid: null,
        animationFrameId: null,
        lastTimestamp: null,
        contentWidth: 0,
        // 초당 이동 속도(px/sec) - 영상처럼 부드럽게, 하지만 충분히 빠르게
        scrollSpeed: 250,
        pauseOnHover: true,
        isPaused: false,
        isUserScrolling: false,
        userScrollTimeout: null,
        
        init: function() {
            this.grid = document.querySelector('.testimonials-grid');
            if (!this.grid) return;

            // 무한 루프처럼 끊김 없이 보이도록 콘텐츠를 두 번 이어 붙임
            this.cloneContentForLoop();
            
            // 가로 스크롤이 필요한지 확인
            if (this.needsScroll()) {
                this.setupAutoScroll();
                this.setupEventListeners();
            }
        },

        // 콘텐츠를 복제해서 양쪽으로 이어 붙여, 끝과 처음이 자연스럽게 이어지도록 처리
        cloneContentForLoop: function() {
            const items = Array.from(this.grid.children);
            if (!items.length) return;

            items.forEach((item) => {
                const clone = item.cloneNode(true);
                clone.setAttribute('aria-hidden', 'true');
                this.grid.appendChild(clone);
            });

            // 실제 한 바퀴 넓이 저장 (원본 영역만큼 스크롤하면 다시 0으로 보정)
            this.contentWidth = this.grid.scrollWidth / 2;
        },
        
        needsScroll: function() {
            // 컨테이너 너비보다 콘텐츠가 더 넓은지 확인
            return this.grid.scrollWidth > this.grid.clientWidth;
        },
        
        setupAutoScroll: function() {
            // 자동 스크롤 시작
            this.startAutoScroll();
        },
        
        startAutoScroll: function() {
            if (this.animationFrameId) return;

            const step = (timestamp) => {
                if (this.isPaused || this.isUserScrolling) {
                    this.lastTimestamp = timestamp;
                    this.animationFrameId = requestAnimationFrame(step);
                    return;
                }

                if (this.lastTimestamp === null) {
                    this.lastTimestamp = timestamp;
                }

                const delta = timestamp - this.lastTimestamp; // ms
                this.lastTimestamp = timestamp;

                // delta 시간 동안 이동할 거리(px) = 속도(px/sec) * (delta/1000)
                const distance = (this.scrollSpeed * delta) / 1000;
                let nextScroll = this.grid.scrollLeft + distance;

                // 한 바퀴(원본 콘텐츠 폭)만큼 이동하면, 그만큼만 되돌려 끊김 없이 루프
                if (this.contentWidth > 0 && nextScroll >= this.contentWidth) {
                    nextScroll = nextScroll - this.contentWidth;
                }

                this.grid.scrollLeft = nextScroll;
                this.animationFrameId = requestAnimationFrame(step);
            };

            this.animationFrameId = requestAnimationFrame(step);
        },
        
        stopAutoScroll: function() {
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
                this.animationFrameId = null;
                this.lastTimestamp = null;
            }
        },
        
        setupEventListeners: function() {
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
            let touchStartX = 0;
            let touchStartY = 0;
            
            this.grid.addEventListener('touchstart', (e) => {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                this.isPaused = true;
            });
            
            this.grid.addEventListener('touchend', () => {
                setTimeout(() => {
                    this.isPaused = false;
                }, 2000);
            });
            
            // Intersection Observer로 뷰포트에 보일 때만 스크롤
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.startAutoScroll();
                    } else {
                        this.stopAutoScroll();
                    }
                });
            }, {
                threshold: 0.3
            });
            
            observer.observe(this.grid);
        }
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

