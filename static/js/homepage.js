// 1Tax App 홈페이지 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 네비게이션 스크롤 효과
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelectorAll('.nav-link');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            navbar.style.background = 'rgba(255, 255, 255, 0.98)';
            navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.boxShadow = 'none';
        }
    });
    
    // 부드러운 스크롤
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // 통계 숫자 카운트 애니메이션
    function animateCounters() {
        const counters = document.querySelectorAll('.stat-number');
        
        counters.forEach(counter => {
            const target = parseInt(counter.textContent.replace(/[^\d]/g, ''));
            const duration = 2000;
            const increment = target / (duration / 16);
            let current = 0;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                
                if (counter.textContent.includes('+')) {
                    counter.textContent = Math.floor(current).toLocaleString() + '+';
                } else if (counter.textContent.includes('%')) {
                    counter.textContent = Math.floor(current) + '%';
                } else if (counter.textContent.includes('초')) {
                    counter.textContent = Math.floor(current) + '초';
                }
            }, 16);
        });
    }
    
    // Intersection Observer로 스크롤 애니메이션
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                
                // 통계 섹션이 보이면 카운터 애니메이션 실행
                if (entry.target.classList.contains('hero-stats')) {
                    animateCounters();
                }
            }
        });
    }, observerOptions);
    
    // 애니메이션 대상 요소들 관찰
    const animateElements = document.querySelectorAll('.feature-card, .pricing-card, .testimonial-card, .hero-stats, .process-step');
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
    
    // CTA 버튼 클릭 이벤트
    const ctaButtons = document.querySelectorAll('.cta-primary, .cta-button.primary, .plan-button');
    ctaButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 버튼 클릭 애니메이션
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            // 변환 페이지로 이동
            window.location.href = '/conversion';
        });
    });
    
    // 데모 보기 버튼 클릭 이벤트
    const demoButtons = document.querySelectorAll('.cta-secondary');
    demoButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 버튼 클릭 애니메이션
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            // 기능 섹션으로 스크롤
            const featuresSection = document.querySelector('#features');
            if (featuresSection) {
                featuresSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            } else {
                showNotification('기능을 확인해보세요!', 'info');
            }
        });
    });
    
    // 알림 표시 함수
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${type === 'success' ? '✅' : 'ℹ️'}</span>
                <span class="notification-message">${message}</span>
            </div>
        `;
        
        // 스타일 추가
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10B981' : '#3B82F6'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // 애니메이션
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // 3초 후 제거
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    // 플로팅 요소 마우스 추적
    const floatingElements = document.querySelectorAll('.float-item');
    document.addEventListener('mousemove', function(e) {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        floatingElements.forEach((element, index) => {
            const speed = (index + 1) * 0.5;
            const x = (mouseX - 0.5) * speed * 20;
            const y = (mouseY - 0.5) * speed * 20;
            
            element.style.transform = `translate(${x}px, ${y}px)`;
        });
    });
    
    // 가격 카드 호버 효과
    const pricingCards = document.querySelectorAll('.pricing-card');
    pricingCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            if (this.classList.contains('featured')) {
                this.style.transform = 'scale(1.05)';
            } else {
                this.style.transform = 'translateY(0) scale(1)';
            }
        });
    });
    
    // 기능 카드 호버 효과
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1.2) rotate(5deg)';
            icon.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1) rotate(0deg)';
        });
    });
    
    // 스크롤 진행률 표시
    function updateScrollProgress() {
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = (scrollTop / docHeight) * 100;
        
        // 진행률 바 생성 (없으면)
        let progressBar = document.querySelector('.scroll-progress');
        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.className = 'scroll-progress';
            progressBar.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 3px;
                background: linear-gradient(90deg, #10B981, #3B82F6);
                transform-origin: left;
                z-index: 10001;
            `;
            document.body.appendChild(progressBar);
        }
        
        progressBar.style.transform = `scaleX(${scrollPercent / 100})`;
    }
    
    window.addEventListener('scroll', updateScrollProgress);
    
    // 키보드 네비게이션
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // ESC 키로 모든 모달 닫기
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                modal.style.display = 'none';
            });
        }
    });
    
    // 터치 디바이스 지원
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
        
        // 터치 이벤트 최적화
        const touchElements = document.querySelectorAll('.cta-primary, .cta-secondary, .plan-button');
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.95)';
            });
            
            element.addEventListener('touchend', function() {
                this.style.transform = 'scale(1)';
            });
        });
    }
    
    // 성능 최적화: 이미지 lazy loading
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
    
    // 섹션으로 스크롤하는 함수
    function scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
    
    // 홈택스 가이드 슬라이더 기능
    function initHometaxGuideSlider() {
        const sliderContainer = document.querySelector('.hometax-guide-slider-container');
        if (!sliderContainer) return;
        
        const slides = sliderContainer.querySelectorAll('.slide');
        const tabItems = sliderContainer.querySelectorAll('.tab-item');
        const prevBtn = sliderContainer.querySelector('#prevBtn');
        const nextBtn = sliderContainer.querySelector('#nextBtn');
        const progressFill = sliderContainer.querySelector('#progressFill');
        // 닫기 버튼 제거됨 (HTML에서 삭제)
        const subtitleText = sliderContainer.querySelector('#subtitleText');
        // const neonSignContainer = sliderContainer.querySelector('#neonSignContainer'); // 네온사인 삭제됨
        
        let currentSlide = 0;
        const totalSlides = slides.length;
        let autoPlayInterval = null;
        let isUserInteracting = false;
        let isAutoPlaying = false; // 초기 상태를 일시정지로 변경
        
        // 8단계 자막 텍스트 (수정된 버전)
        const subtitleTexts = [
            "1단계: 홈택스 메인 화면 로그인",
            "2단계: 로그인 후 사업자전환",
            "3단계: 일괄/공동발급 발급 메뉴 클릭",
            "4단계: 전자(세금)계산서 일괄발급 메뉴 클릭",
            "5단계: 로.하 TAX 변환한 파일 업로드",
            "6단계: 엑셀파일 변환하기 클릭",
            "7단계: 변환 결과물 및 작성일자 꼭 확인!!!",
            "8단계: VIP 회원님 일괄 50건 처리 확인 일괄발급진행"
        ];
        
        // 가이드 헤더 애니메이션 초기화
        initGuideHeaderAnimation();
        
        // 가이드 헤더 애니메이션 함수
        function initGuideHeaderAnimation() {
            const guideHeader = document.querySelector('.guide-header');
            const strategyItems = document.querySelectorAll('.strategy-item');
            const securityHighlight = document.querySelector('.security-highlight');
            
            if (!guideHeader) return;
            
            // Intersection Observer로 스크롤 애니메이션
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });
            
            // 각 요소 관찰
            observer.observe(guideHeader);
            strategyItems.forEach(item => observer.observe(item));
            if (securityHighlight) observer.observe(securityHighlight);
            
            // 전략 아이템 순차 애니메이션
            strategyItems.forEach((item, index) => {
                item.style.animationDelay = `${index * 0.2}s`;
            });
        }
        
        // 타이핑 애니메이션 함수 (개선된 버전)
        let currentTypeInterval = null;
        
        function typeText(element, text, callback) {
            // 기존 타이핑 애니메이션 중단
            if (currentTypeInterval) {
                clearInterval(currentTypeInterval);
                currentTypeInterval = null;
            }
            
            element.textContent = '';
            element.classList.add('typing');
            
            let i = 0;
            currentTypeInterval = setInterval(() => {
                if (i < text.length) {
                    element.textContent += text.charAt(i);
                    i++;
                } else {
                    clearInterval(currentTypeInterval);
                    currentTypeInterval = null;
                    element.classList.remove('typing');
                    if (callback) callback();
                }
            }, 50);
        }
        
        // 네온사인 효과 표시 함수 (삭제됨)
        // function showNeonSign() {
        //     neonSignContainer.classList.add('show');
        //     setTimeout(() => {
        //         neonSignContainer.classList.remove('show');
        //     }, 3000);
        // }
        
        // 하이라이트 효과 표시
        function showHighlight(step) {
            const highlight = sliderContainer.querySelector(`.slide-highlight[data-step="${step}"]`);
            if (highlight) {
                highlight.classList.add('active');
                setTimeout(() => {
                    highlight.classList.remove('active');
                }, 2000);
            }
        }
        
        // 프로그레스 바 리셋 및 재시작
        function resetTabProgress(tabIndex) {
            // 모든 탭의 프로그레스 바 리셋
            tabItems.forEach((tab, idx) => {
                const progressFill = tab.querySelector('.tab-progress-fill');
                if (progressFill) {
                    progressFill.style.width = '0%';
                    progressFill.style.animation = 'none';
                }
            });
            
            // 현재 탭의 프로그레스 바 재시작
            if (tabItems[tabIndex]) {
                const currentProgressFill = tabItems[tabIndex].querySelector('.tab-progress-fill');
                if (currentProgressFill) {
                    // 애니메이션 리셋을 위한 강제 리플로우
                    currentProgressFill.offsetHeight;
                    currentProgressFill.style.animation = 'progressFill 5s linear forwards';
                }
            }
        }
        
        // 슬라이드 표시 함수 (개선된 버전)
        function showSlide(index) {
            // 모든 슬라이드 숨기기
            slides.forEach(slide => slide.classList.remove('active'));
            tabItems.forEach(tab => tab.classList.remove('active'));
            
            // 현재 슬라이드 표시
            slides[index].classList.add('active');
            if (tabItems[index]) {
                tabItems[index].classList.add('active');
            }
            
            // 7번, 8번 이미지에 특별한 object-position 적용
            const currentImage = slides[index].querySelector('.guide-image');
            if (index === 6 || index === 7) { // 7번, 8번 이미지 (0-based index)
                currentImage.style.objectPosition = 'center bottom';
            } else {
                currentImage.style.objectPosition = 'center center';
            }
            
            // 진행률 업데이트 (기존 progressFill은 유지하되, 탭 프로그레스 바 리셋)
            if (progressFill) {
                const progressPercent = ((index + 1) / totalSlides) * 100;
                progressFill.style.width = progressPercent + '%';
            }
            
            // 탭 프로그레스 바 리셋 및 재시작
            resetTabProgress(index);
            
            // 버튼 상태 업데이트 (무한 루프이므로 항상 활성화)
            if (prevBtn) prevBtn.disabled = false;
            if (nextBtn) nextBtn.disabled = false;
            
            // 자막 텍스트 즉시 표시 (타이핑 애니메이션 없이)
            if (subtitleText) {
                subtitleText.textContent = subtitleTexts[index];
                subtitleText.classList.remove('typing');
            }
            
            // 특정 단계에서 하이라이트 효과
            if (index === 2) { // 3단계: 일괄/공동발급 발급
                setTimeout(() => {
                    showHighlight(index + 1);
                }, 500);
            }
        }
        
        // 다음 슬라이드 (무한 루프) - 디바운스 적용
        let isTransitioning = false;
        
        function nextSlide() {
            if (isTransitioning) return;
            isTransitioning = true;
            
            currentSlide = (currentSlide + 1) % totalSlides; // 0~7 순환
            showSlide(currentSlide);
            
            setTimeout(() => {
                isTransitioning = false;
            }, 300);
        }
        
        // 이전 슬라이드 (무한 루프) - 디바운스 적용
        function prevSlide() {
            if (isTransitioning) return;
            isTransitioning = true;
            
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides; // 0~7 역순환
            showSlide(currentSlide);
            
            setTimeout(() => {
                isTransitioning = false;
            }, 300);
        }
        
        // 자동 재생 시작
        function startAutoPlay() {
            if (autoPlayInterval) clearInterval(autoPlayInterval);
            autoPlayInterval = setInterval(() => {
                if (!isUserInteracting) {
                    nextSlide();
                }
            }, 5000); // 5초 간격
        }
        
        // 자동 재생 중지
        function stopAutoPlay() {
            if (autoPlayInterval) {
                clearInterval(autoPlayInterval);
                autoPlayInterval = null;
            }
        }
        
        // 플레이/일시정지 토글
        function togglePlayPause() {
            const playPauseBtn = document.getElementById('playPauseBtn');
            const btnIcon = playPauseBtn.querySelector('.btn-icon');
            
            if (isAutoPlaying) {
                // 현재 재생 중이면 일시정지
                stopAutoPlay();
                isAutoPlaying = false;
                // Lucide 아이콘을 play로 변경
                btnIcon.setAttribute('data-lucide', 'play');
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
                playPauseBtn.title = '재생';
            } else {
                // 현재 일시정지 중이면 재생
                startAutoPlay();
                isAutoPlaying = true;
                // Lucide 아이콘을 pause로 변경
                btnIcon.setAttribute('data-lucide', 'pause');
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
                playPauseBtn.title = '일시정지';
            }
        }
        
        // 닫기 버튼 관련 함수 제거됨 (HTML에서 닫기 버튼 삭제)
        
        // 이벤트 리스너 등록
        if (nextBtn) nextBtn.addEventListener('click', () => {
            isUserInteracting = true;
            nextSlide();
            setTimeout(() => { isUserInteracting = false; }, 1000);
        });
        
        if (prevBtn) prevBtn.addEventListener('click', () => {
            isUserInteracting = true;
            prevSlide();
            setTimeout(() => { isUserInteracting = false; }, 1000);
        });
        
        // 닫기 버튼 제거됨 (HTML에서 삭제)
        
        // 플레이/일시정지 버튼 이벤트 리스너
        const playPauseBtn = document.getElementById('playPauseBtn');
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', togglePlayPause);
        }
        
        // 탭 클릭 이벤트
        tabItems.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                isUserInteracting = true;
                currentSlide = index;
                showSlide(currentSlide);
                
                // 자동 재생 타이머 리셋
                if (isAutoPlaying) {
                    stopAutoPlay();
                    startAutoPlay();
                }
                
                setTimeout(() => { isUserInteracting = false; }, 1000);
            });
        });
        
        // 마우스 호버 시 자동 재생 일시 중지
        sliderContainer.addEventListener('mouseenter', () => {
            if (isAutoPlaying) {
                stopAutoPlay();
            }
        });
        sliderContainer.addEventListener('mouseleave', () => {
            if (isAutoPlaying) {
                startAutoPlay();
            }
        });
        
        // 키보드 네비게이션
        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft') {
                isUserInteracting = true;
                prevSlide();
                setTimeout(() => { isUserInteracting = false; }, 1000);
            }
            if (e.key === 'ArrowRight') {
                isUserInteracting = true;
                nextSlide();
                setTimeout(() => { isUserInteracting = false; }, 1000);
            }
        });
        
        // 진행률 업데이트 함수
        function updateProgressBar(currentIndex) {
            if (progressFill) {
                const progress = ((currentIndex + 1) / totalSlides) * 100;
                progressFill.style.width = progress + '%';
            }
        }
        
        // 초기 슬라이드 표시 및 자동 재생 시작
        showSlide(0);
        if (progressFill) {
            updateProgressBar(0);
        }
        // typeText(subtitleText, subtitleTexts[0]); // 1단계는 빈 텍스트이므로 제거
        // startAutoPlay(); // 자동 재생은 사용자가 플레이 버튼을 클릭할 때만 시작
        
        // 초기 재생 버튼 아이콘 설정 (play 상태)
        const playPauseBtnInit = document.getElementById('playPauseBtn');
        if (playPauseBtnInit) {
            const btnIconInit = playPauseBtnInit.querySelector('.btn-icon');
            if (btnIconInit) {
                btnIconInit.setAttribute('data-lucide', 'play');
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        }
        
        console.log('🎯 홈택스 가이드 슬라이더가 고도화되어 초기화되었습니다.');
        
        // 마우스 클릭 효과 초기화
        initMouseClickEffect();
    }
    
    // 마우스 클릭 효과 관리 - 강화된 디버깅 버전
    function initMouseClickEffect() {
        console.log('🔍 마우스 효과 초기화 시작...');
        
        const mouseEffect1 = document.querySelector('.mouse-click-effect[data-step="1"]');
        const mouseEffect2 = document.querySelector('.mouse-click-effect[data-step="2"]');
        console.log('🔍 1번 마우스 효과 요소:', mouseEffect1);
        console.log('🔍 2번 마우스 효과 요소:', mouseEffect2);
        
        if (!mouseEffect1 && !mouseEffect2) {
            console.log('❌ 마우스 클릭 효과 요소를 찾을 수 없습니다.');
            console.log('🔍 전체 슬라이드 요소들:', document.querySelectorAll('.slide'));
            console.log('🔍 첫 번째 슬라이드:', document.querySelector('.slide[data-step="1"]'));
            console.log('🔍 두 번째 슬라이드:', document.querySelector('.slide[data-step="2"]'));
            return;
        }
        
        // 1번과 2번 슬라이드 모두 처리
        [mouseEffect1, mouseEffect2].forEach((mouseEffect, index) => {
            if (!mouseEffect) return;
            
            const stepNumber = index + 1;
            console.log(`🔍 ${stepNumber}번 슬라이드 마우스 효과 설정 중...`);
            
            // 강제로 스타일 적용 (손가락 클릭 버전)
            mouseEffect.style.opacity = '1';
            mouseEffect.style.zIndex = '9999';
            // 빨간 배경 제거
            mouseEffect.style.background = 'transparent';
            mouseEffect.style.border = 'none';
            
            // 물방울 효과 제거
            const ripple = mouseEffect.querySelector('.click-ripple');
            if (ripple) {
                ripple.style.display = 'none';
                console.log(`💧 ${stepNumber}번 슬라이드 물방울 효과 제거 완료`);
            }
            
            console.log(`✅ ${stepNumber}번 슬라이드 손가락 클릭 효과 요소 발견 및 스타일 적용 완료`);
        });
        
        let isEffectPlaying = false;
        
        // 슬라이드 변경 시 효과 제어
        function showMouseClickEffect(slideIndex) {
            if (isEffectPlaying) return;
            
            const currentMouseEffect = document.querySelector(`.mouse-click-effect[data-step="${slideIndex + 1}"]`);
            if (!currentMouseEffect) return;
            
            console.log(`🖱️ ${slideIndex + 1}번 슬라이드 마우스 클릭 효과 시작`);
            isEffectPlaying = true;
            currentMouseEffect.classList.add('active');
            
            // 효과 완료 후 정리
            setTimeout(() => {
                currentMouseEffect.classList.remove('active');
                isEffectPlaying = false;
                console.log(`🖱️ ${slideIndex + 1}번 슬라이드 마우스 클릭 효과 완료`);
            }, 4000); // 전체 애니메이션 시간
        }
        
        // 1~8번 슬라이드가 활성화될 때 효과 실행
        function onSlideChange(slideIndex) {
            console.log('📊 슬라이드 변경:', slideIndex);
            if (slideIndex >= 0 && slideIndex <= 7) { // 1~8번 슬라이드 (0-based index)
                setTimeout(() => showMouseClickEffect(slideIndex), 1000); // 1초 후 시작
            }
        }
        
        // 테스트 모드 - 즉시 효과 표시 (1~8번 슬라이드)
        for (let i = 1; i <= 8; i++) {
            const mouseEffect = document.querySelector(`.mouse-click-effect[data-step="${i}"]`);
            if (mouseEffect) {
                mouseEffect.classList.add('test-mode');
                console.log(`🧪 ${i}번 슬라이드 테스트 모드 활성화 - 마우스 효과가 즉시 표시됩니다`);
            }
        }
        
        // 즉시 효과 실행 (테스트용) - 1~8번 슬라이드
        for (let i = 0; i < 8; i++) {
            setTimeout(() => {
                console.log(`🎯 ${i + 1}번 슬라이드 즉시 효과 실행`);
                showMouseClickEffect(i);
            }, (i + 1) * 2000); // 각 슬라이드마다 2초 간격
        }
        
        // 초기 로드 시 효과 실행
        setTimeout(() => {
            console.log('🎯 초기 로드 - 현재 슬라이드:', 0);
            showMouseClickEffect(0);
        }, 2000);
        
        // 슬라이드 변경 이벤트 리스너 추가
        const slides = document.querySelectorAll('.slide');
        slides.forEach((slide, index) => {
            slide.addEventListener('transitionend', () => {
                if (slide.classList.contains('active')) {
                    onSlideChange(index);
                }
            });
        });
        
        console.log('🖱️ 마우스 클릭 효과가 초기화되었습니다.');
        console.log('🔍 마우스 효과 최종 상태:', {
            element: mouseEffect,
            opacity: mouseEffect.style.opacity,
            zIndex: mouseEffect.style.zIndex,
            background: mouseEffect.style.background
        });
    }
    
    // 홈택스 가이드 슬라이더 초기화
    initHometaxGuideSlider();
    
    // 전역 함수로 등록
    window.scrollToSection = scrollToSection;
    
    // 콘솔 로그 (개발용)
    console.log('🚀 1Tax App 홈페이지가 로드되었습니다!');
    console.log('📊 현재 시간:', new Date().toLocaleString('ko-KR'));
    console.log('🌐 사용자 에이전트:', navigator.userAgent);
});
