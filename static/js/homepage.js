// 1Tax App 홈페이지 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // [안전장치] JS 로드 완료 플래그 → 이때부터 CSS가 reveal 요소를 숨기고 애니메이션 준비
    document.body.classList.add('js-loaded');

    // Scroll Reveal Animation (IntersectionObserver)
    const revealElements = document.querySelectorAll('.reveal');
    
    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target); // 한 번 나타나면 관찰 중단
            }
        });
    }, {
        root: null,
        threshold: 0.1, // 10%만 보여도 등장 시작
        rootMargin: '0px 0px -50px 0px' // 약간 미리 등장
    });
    
    revealElements.forEach(el => revealObserver.observe(el));

    // 네비게이션 스크롤 효과
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelectorAll('.nav-link');
    
    window.addEventListener('scroll', function() {
        if (!navbar) return;
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
            if (href && href.startsWith('#')) {
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
            if (isNaN(target)) return;
            
            const duration = 2000;
            const increment = target / (duration / 16);
            let current = 0;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                
                const currentText = counter.textContent;
                if (currentText.includes('+')) {
                    counter.textContent = Math.floor(current).toLocaleString() + '+';
                } else if (currentText.includes('%')) {
                    counter.textContent = Math.floor(current) + '%';
                } else if (currentText.includes('초')) {
                    counter.textContent = Math.floor(current) + '초';
                } else {
                    counter.textContent = Math.floor(current).toLocaleString();
                }
            }, 16);
        });
    }
    
    // Intersection Observer로 통계 섹션 감지
    const statsSection = document.querySelector('.hero-stats');
    if (statsSection) {
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    statsObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        statsObserver.observe(statsSection);
    }

    // 부드러운 이동 함수
    function scrollToSection(sectionId) {
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }

    // 홈택스 가이드 슬라이더 로직
    function initHometaxGuideSlider() {
        const slider = document.querySelector('.hometax-guide-slider');
        const slides = document.querySelectorAll('.guide-slide');
        const prevBtn = document.getElementById('prevGuide');
        const nextBtn = document.getElementById('nextGuide');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const progressFill = document.querySelector('.progress-fill');
        const subtitleText = document.querySelector('.guide-subtitle');
        
        if (!slider || slides.length === 0) return;
        
        let currentIndex = 0;
        let isPlaying = false;
        let autoPlayInterval = null;
        const totalSlides = slides.length;
        
        // 단계별 설명 텍스트
        const subtitleTexts = [
            "", // 1단계 (메인)
            "국세청 홈택스 로그인 후 '사업장선택'을 클릭합니다.",
            "변환할 사업자를 선택하고 '사업자전환' 버튼을 누릅니다.",
            "상단 메뉴에서 '전자세금계산서' → '일괄발급'을 선택합니다.",
            "일괄발급 화면에서 '전자세금계산서(세금계산서)'를 클릭합니다.",
            "로하택스에서 내려받은 엑셀 파일을 업로드합니다.",
            "'일괄변환하기' 버튼을 클릭하여 데이터를 변환합니다.",
            "변환된 결과를 확인하고 오류가 없는지 체크합니다.",
            "최종적으로 '일괄발급' 버튼을 눌러 발행을 완료합니다."
        ];

        // 텍스트 타이핑 효과
        function typeText(element, text) {
            if (!element) return;
            element.textContent = text;
        }

        function showSlide(index) {
            slides.forEach((slide, i) => {
                slide.classList.remove('active');
                if (i === index) {
                    slide.classList.add('active');
                }
            });
            
            // 텍스트 업데이트
typeText(subtitleText, subtitleTexts[index] || "");
            
            // 프로그레스 바 업데이트
            updateProgressBar(index);
        }

        function nextSlide() {
            currentIndex = (currentIndex + 1) % totalSlides;
            showSlide(currentIndex);
        }

        function prevSlide() {
            currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
            showSlide(currentIndex);
        }

        function togglePlay() {
            isPlaying = !isPlaying;
            const btnIcon = playPauseBtn.querySelector('.btn-icon');
            
            if (isPlaying) {
                btnIcon.setAttribute('data-lucide', 'pause');
                autoPlayInterval = setInterval(nextSlide, 5000);
            } else {
                btnIcon.setAttribute('data-lucide', 'play');
                clearInterval(autoPlayInterval);
            }
            
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }

        if (prevBtn) prevBtn.addEventListener('click', () => {
            prevSlide();
            if (isPlaying) togglePlay();
        });

        if (nextBtn) nextBtn.addEventListener('click', () => {
            nextSlide();
            if (isPlaying) togglePlay();
        });

        if (playPauseBtn) playPauseBtn.addEventListener('click', togglePlay);

        function updateProgressBar(index) {
            if (progressFill) {
                const progress = ((index + 1) / totalSlides) * 100;
                progressFill.style.width = progress + '%';
            }
        }
        
        // 초기화
        showSlide(0);
        
        // 마우스 클릭 효과 초기화 (슬라이더 내부에서 호출)
        initMouseClickEffect();
    }
    
    // 마우스 클릭 효과 관리
    function initMouseClickEffect() {
        const effects = document.querySelectorAll('.mouse-click-effect');
        if (effects.length === 0) return;
        
        effects.forEach(effect => {
            effect.style.opacity = '1';
            effect.style.zIndex = '9999';
            effect.style.background = 'transparent';
            effect.style.border = 'none';
            
            const ripple = effect.querySelector('.click-ripple');
            if (ripple) ripple.style.display = 'none';
        });
        
        let isEffectPlaying = false;
        
        function showEffect(slideIndex) {
            if (isEffectPlaying) return;
            
            const currentEffect = document.querySelector(`.mouse-click-effect[data-step="${slideIndex + 1}"]`);
            if (!currentEffect) return;
            
            isEffectPlaying = true;
            currentEffect.classList.add('active');
            
            setTimeout(() => {
                currentEffect.classList.remove('active');
                isEffectPlaying = false;
            }, 4000);
        }
        
        const guideSlides = document.querySelectorAll('.guide-slide');
        guideSlides.forEach((slide, index) => {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        if (slide.classList.contains('active')) {
                            setTimeout(() => showEffect(index), 1000);
                        }
                    }
                });
            });
            observer.observe(slide, { attributes: true });
        });
    }
    
    // 초기 실행
    initHometaxGuideSlider();
    
    // 전역 함수 등록
    window.scrollToSection = scrollToSection;
    
    // Lucide 아이콘 초기화 안전장치
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log('🚀 RohaTax homepage initialized');
});