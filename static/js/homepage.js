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

    // 홈택스 가이드 슬라이더 로직 (How it Works 섹션)
    function initHometaxGuideSlider() {
        const sliderContainer = document.querySelector('.hometax-guide-slider-container');
        const slides = document.querySelectorAll('.slide');
        const tabs = document.querySelectorAll('.tab-item');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const subtitleText = document.getElementById('subtitleText');
        
        if (!sliderContainer || slides.length === 0) return;
        
        let currentIndex = 0;
        let isPlaying = false;
        let autoPlayInterval = null;
        const totalSlides = slides.length;
        
        // 단계별 설명 텍스트
        const subtitleTexts = [
            "국세청 홈택스 로그인 후 '사업장선택'을 클릭합니다.",
            "변환할 사업자를 선택하고 '사업자전환' 버튼을 누릅니다.",
            "상단 메뉴에서 '전자세금계산서' → '일괄발급'을 선택합니다.",
            "일괄발급 화면에서 '전자세금계산서(세금계산서)'를 클릭합니다.",
            "로하택스에서 내려받은 엑셀 파일을 업로드합니다.",
            "'일괄변환하기' 버튼을 클릭하여 데이터를 변환합니다.",
            "변환된 결과를 확인하고 오류가 없는지 체크합니다.",
            "최종적으로 '일괄발급' 버튼을 눌러 발행을 완료합니다."
        ];

        function showSlide(index) {
            // 모든 슬라이드와 탭 비활성화
            slides.forEach(slide => slide.classList.remove('active'));
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // 현재 슬라이드와 탭 활성화
            if (slides[index]) slides[index].classList.add('active');
            if (tabs[index]) tabs[index].classList.add('active');
            
            // 텍스트 업데이트
            if (subtitleText) {
                subtitleText.textContent = subtitleTexts[index] || "";
            }
            
            currentIndex = index;
        }

        function nextSlide() {
            let nextIndex = (currentIndex + 1) % totalSlides;
            showSlide(nextIndex);
        }

        function prevSlide() {
            let prevIndex = (currentIndex - 1 + totalSlides) % totalSlides;
            showSlide(prevIndex);
        }

        function togglePlay() {
            isPlaying = !isPlaying;
            if (!playPauseBtn) return;
            
            const btnIcon = playPauseBtn.querySelector('.btn-icon');
            
            if (isPlaying) {
                if (btnIcon) {
                    btnIcon.setAttribute('data-lucide', 'pause');
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }
                autoPlayInterval = setInterval(nextSlide, 5000);
            } else {
                if (btnIcon) {
                    btnIcon.setAttribute('data-lucide', 'play');
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }
                clearInterval(autoPlayInterval);
            }
        }

        // 탭 클릭 이벤트 바인딩
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                showSlide(index);
                if (isPlaying) togglePlay(); // 클릭 시 자동 재생 중지
            });
        });

        if (prevBtn) prevBtn.addEventListener('click', () => {
            prevSlide();
            if (isPlaying) togglePlay();
        });

        if (nextBtn) nextBtn.addEventListener('click', () => {
            nextSlide();
            if (isPlaying) togglePlay();
        });

        if (playPauseBtn) playPauseBtn.addEventListener('click', togglePlay);
        
        // 초기화
        showSlide(0);
        
        // 마우스 클릭 효과 초기화 (슬라이더 내부에서 호출)
        initMouseClickEffect();
    }
    
    // 마우스 클릭 효과 관리
    function initMouseClickEffect() {
        const effects = document.querySelectorAll('.mouse-click-effect');
        if (effects.length === 0) return;
        
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
        
        const slides = document.querySelectorAll('.slide');
        slides.forEach((slide, index) => {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        if (slide.classList.contains('active')) {
                            setTimeout(() => showEffect(index), 500);
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