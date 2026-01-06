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
        const subtitleContainer = document.querySelector('.subtitle-container');
        const monitorFrame = document.getElementById('monitor-frame');
        
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

        function scrollToSlide(index, behavior = 'auto') {
            if (!monitorFrame) return;
            if (window.innerWidth > 480) return; // ✅ 모바일에서만
            
            // ✅ 간단하게 계산: 프레임 폭 × 인덱스
            const frameWidth = monitorFrame.clientWidth;
            const scrollTarget = index * frameWidth;
            
            // ✅ 스크롤 적용
            if (behavior === 'smooth') {
                monitorFrame.scrollTo({ left: scrollTarget, behavior: 'smooth' });
            } else {
                monitorFrame.scrollLeft = scrollTarget;
            }
        }

        function showSlide(index) {
            // 모든 슬라이드와 탭 비활성화
            slides.forEach(slide => slide.classList.remove('active'));
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // 현재 슬라이드와 탭 활성화
            if (slides[index]) slides[index].classList.add('active');
            if (tabs[index]) tabs[index].classList.add('active');

            // ✅ 모바일: "가로 스크롤 + 스냅" 방식으로 1~8을 확실히 노출 - 즉각 이동
            scrollToSlide(index, 'auto');
            
            // 텍스트 업데이트
            if (subtitleText) {
                subtitleText.textContent = subtitleTexts[index] || "";
            }

            // 자막은 항상 업데이트(모바일에서는 하단 풀폭 영역으로 표시)
            if (subtitleContainer) {
                subtitleContainer.classList.add('show');
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
        
        // ✅ 모바일: 초기 스크롤 위치 확실히 설정(1번이 보이도록)
        if (monitorFrame && window.innerWidth <= 480) {
            // DOM이 완전히 렌더링된 후 스크롤 위치 설정
            setTimeout(() => {
                monitorFrame.scrollTo({ left: 0, behavior: 'auto' });
                // 추가 확인: 스크롤 위치가 0인지 확인
                requestAnimationFrame(() => {
                    if (monitorFrame.scrollLeft !== 0) {
                        monitorFrame.scrollLeft = 0;
                    }
                });
            }, 150);
        }
        
        // ✅ 모바일: 이미지 더블탭 확대 기능 (간섭 요소 제거, 안정성 개선)
        if (window.innerWidth <= 480 && monitorFrame) {
            // 확대 상태 관리 (전역 변수로 중복 방지)
            let lockedScrollPosition = null;
            let zoomStateObserver = null; // 단일 observer로 통합
            
            // 확대 상태 감지 및 스크롤 제어 (단일 함수로 통합)
            const updateScrollLock = (img) => {
                const slide = img ? img.closest('.slide') : null;
                const zoomedImages = document.querySelectorAll('.guide-image.zoomed');
                const hasZoomed = zoomedImages.length > 0;
                
                if (hasZoomed) {
                    // 확대 상태: 가로 스크롤 차단, 세로는 visible로 확대된 이미지 전체 표시
                    monitorFrame.classList.add('scroll-locked');
                    monitorFrame.style.overflowX = 'hidden';
                    monitorFrame.style.overflowY = 'visible'; // ✅ 확대된 이미지가 위아래로 나가도 보이도록
                    monitorFrame.style.scrollSnapType = 'none';
                    monitorFrame.style.touchAction = 'none'; // ✅ JavaScript로 직접 제어
                    
                    // 확대된 이미지가 있는 슬라이드 위치 저장
                    zoomedImages.forEach(zoomedImg => {
                        const zoomedSlide = zoomedImg.closest('.slide');
                        if (zoomedSlide) {
                            const slideIndex = Array.from(monitorFrame.querySelectorAll('.slide')).indexOf(zoomedSlide);
                            const slideWidth = monitorFrame.offsetWidth;
                            lockedScrollPosition = slideIndex * slideWidth;
                            
                            // 슬라이드 컨테이너도 잠금 (overflow visible로 전체 영역 표시)
                            zoomedSlide.classList.add('scroll-locked');
                            zoomedSlide.style.overflow = 'visible'; // ✅ 확대된 이미지 전체를 볼 수 있도록
                            zoomedSlide.style.touchAction = 'none'; // ✅ JavaScript로 직접 제어
                        }
                    });
                } else {
                    // 축소 상태: 가로 스크롤 복원
                    monitorFrame.classList.remove('scroll-locked');
                    monitorFrame.style.overflowX = 'auto';
                    monitorFrame.style.overflowY = 'hidden';
                    monitorFrame.style.scrollSnapType = 'x mandatory';
                    monitorFrame.style.touchAction = 'pan-x';
                    lockedScrollPosition = null;
                    
                    // 모든 슬라이드 잠금 해제
                    document.querySelectorAll('.slide.scroll-locked').forEach(slide => {
                        slide.classList.remove('scroll-locked');
                        slide.style.overflow = '';
                        slide.style.touchAction = '';
                    });
                }
            };
            
            // 이미지별 터치 이벤트 처리 (핀치 줌, 부드러운 팬 동작)
            // ✅ 이미지가 아닌 여백 클릭 방지: 이미지 요소에만 이벤트 등록
            const images = document.querySelectorAll('.guide-image');
            images.forEach(img => {
                let lastTap = 0;
                let tapTimer = null;
                let isDragging = false;
                let isPinching = false;
                let startX = 0;
                let startY = 0;
                let currentTranslateX = 0;
                let currentTranslateY = 0;
                let initialTranslateX = 0;
                let initialTranslateY = 0;
                let touchStartTime = 0;
                let hasMoved = false;
                let currentScale = 1; // ✅ 현재 확대 비율 (핀치 줌용)
                let initialDistance = 0; // ✅ 핀치 시작 거리
                let initialScale = 1; // ✅ 핀치 시작 시 확대 비율
                
                // ✅ 이미지 요소에만 터치 이벤트 등록 (여백 클릭 방지, 핀치 줌 지원)
                img.addEventListener('touchstart', (e) => {
                    // ✅ 이미지 요소가 아닌 다른 요소를 클릭한 경우 무시
                    const target = e.target;
                    if (target !== img && !img.contains(target)) {
                        e.stopPropagation();
                        return;
                    }
                    
                    // ✅ slide나 slide-wrapper를 클릭한 경우 무시 (여백 클릭 방지)
                    const slide = img.closest('.slide');
                    const clickedElement = target.closest('.slide');
                    if (clickedElement && clickedElement !== slide) {
                        e.stopPropagation();
                        return;
                    }
                    
                    // ✅ 이미지가 아닌 요소(slide-highlight, mouse-click-effect 등) 클릭 방지
                    if (target.classList.contains('slide-highlight') || 
                        target.classList.contains('mouse-click-effect') ||
                        target.closest('.slide-highlight') ||
                        target.closest('.mouse-click-effect')) {
                        e.stopPropagation();
                        return;
                    }
                    
                    touchStartTime = Date.now();
                    hasMoved = false;
                    
                    // ✅ 핀치 줌 감지 (2개 손가락)
                    if (e.touches.length === 2) {
                        isPinching = true;
                        isDragging = false;
                        
                        const touch1 = e.touches[0];
                        const touch2 = e.touches[1];
                        initialDistance = Math.hypot(
                            touch2.clientX - touch1.clientX,
                            touch2.clientY - touch1.clientY
                        );
                        
                        // 현재 scale 값 가져오기
                        const currentTransform = img.style.transform || '';
                        const scaleMatch = currentTransform.match(/scale\(([^)]+)\)/);
                        initialScale = scaleMatch ? Number.parseFloat(scaleMatch[1]) : 1;
                        currentScale = initialScale;
                        
                        // 현재 translate 값 저장
                        const translateMatch = currentTransform.match(/translate\(([^,]+),\s*([^)]+)\)/);
                        if (translateMatch) {
                            initialTranslateX = Number.parseFloat(translateMatch[1]) || 0;
                            initialTranslateY = Number.parseFloat(translateMatch[2]) || 0;
                        } else {
                            initialTranslateX = 0;
                            initialTranslateY = 0;
                        }
                        
                        // 확대 상태로 표시
                        if (currentScale > 1) {
                            img.classList.add('zoomed');
                        }
                        
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                    }
                    
                    // ✅ 단일 터치: 팬 또는 탭
                    if (e.touches.length === 1) {
                        isPinching = false;
                        
                        if (img.classList.contains('zoomed') || currentScale > 1) {
                            // 확대 상태: 드래그 시작 (이미지 내부 팬)
                            isDragging = true;
                            startX = e.touches[0].clientX;
                            startY = e.touches[0].clientY;
                            
                            // 현재 translate 값 저장
                            const currentTransform = img.style.transform || '';
                            const translateMatch = currentTransform.match(/translate\(([^,]+),\s*([^)]+)\)/);
                            if (translateMatch) {
                                initialTranslateX = Number.parseFloat(translateMatch[1]) || 0;
                                initialTranslateY = Number.parseFloat(translateMatch[2]) || 0;
                            } else {
                                initialTranslateX = 0;
                                initialTranslateY = 0;
                            }
                            
                            e.preventDefault();
                            e.stopPropagation();
                        }
                    }
                }, { passive: false });
                
                img.addEventListener('touchmove', (e) => {
                    // ✅ 이미지 요소가 아닌 경우 무시
                    if (e.target !== img && !img.contains(e.target)) {
                        return;
                    }
                    
                    // ✅ 핀치 줌 처리 (2개 손가락)
                    if (e.touches.length === 2 && isPinching) {
                        const touch1 = e.touches[0];
                        const touch2 = e.touches[1];
                        const currentDistance = Math.hypot(
                            touch2.clientX - touch1.clientX,
                            touch2.clientY - touch1.clientY
                        );
                        
                        // ✅ 확대 비율 계산 (더 안정적인 계산)
                        const scaleChange = currentDistance / initialDistance;
                        // ✅ 최소 1배, 최대 3배로 제한 (더 안정적)
                        currentScale = Math.max(1, Math.min(3, initialScale * scaleChange));
                        
                        // 확대 상태 업데이트
                        if (currentScale > 1.05) { // ✅ 약간의 여유 (1.05 이상에서만 확대로 인식)
                            img.classList.add('zoomed');
                        } else {
                            img.classList.remove('zoomed');
                            currentScale = 1; // ✅ 거의 1배면 정확히 1로 설정
                        }
                        
                        // ✅ transform 적용 (소수점 2자리로 반올림하여 안정성 향상)
                        const roundedScale = Math.round(currentScale * 100) / 100;
                        img.style.transform = `scale(${roundedScale}) translate(${initialTranslateX}px, ${initialTranslateY}px)`;
                        
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                    }
                    
                    // 이동 감지
                    if (e.touches.length === 1 && e.touches[0]) {
                        const moveX = Math.abs(e.touches[0].clientX - startX);
                        const moveY = Math.abs(e.touches[0].clientY - startY);
                        if (moveX > 5 || moveY > 5) {
                            hasMoved = true;
                        }
                    }
                    
                    // ✅ 팬 처리 (확대 상태에서 단일 터치 드래그)
                    if ((img.classList.contains('zoomed') || currentScale > 1) && isDragging && e.touches.length === 1) {
                        // 확대 상태: 이미지 내부에서 부드러운 팬 허용
                        const currentX = e.touches[0].clientX;
                        const currentY = e.touches[0].clientY;
                        
                        // 이동 거리 계산
                        const deltaX = currentX - startX;
                        const deltaY = currentY - startY;
                        
                        // 이미지의 실제 크기 가져오기 (로드된 이미지 크기)
                        const slide = img.closest('.slide');
                        const slideRect = slide ? slide.getBoundingClientRect() : null;
                        
                        // 이미지의 자연스러운 크기 (scale 적용 전)
                        const naturalWidth = img.naturalWidth || img.offsetWidth;
                        const naturalHeight = img.naturalHeight || img.offsetHeight;
                        
                        // 컨테이너 크기 대비 이미지 비율 계산
                        const containerWidth = slideRect ? slideRect.width : img.offsetWidth;
                        const containerHeight = slideRect ? slideRect.height : img.offsetHeight;
                        
                        // 이미지가 컨테이너에 맞춰 표시되는 실제 크기 (object-fit: contain 기준)
                        const imgAspect = naturalWidth / naturalHeight;
                        const containerAspect = containerWidth / containerHeight;
                        
                        let displayWidth, displayHeight;
                        if (imgAspect > containerAspect) {
                            displayWidth = containerWidth;
                            displayHeight = containerWidth / imgAspect;
                        } else {
                            displayHeight = containerHeight;
                            displayWidth = containerHeight * imgAspect;
                        }
                        
                        // ✅ 현재 확대 비율 사용 (핀치 줌으로 변경된 값)
                        const actualScale = currentScale > 1 ? currentScale : 1;
                        const scaledWidth = displayWidth * actualScale;
                        const scaledHeight = displayHeight * actualScale;
                        
                        // ✅ 새로운 translate 값 계산 (scale로 나눠서 정규화)
                        // scale 후 translate는 증폭되므로, 미리 scale로 나눔
                        const normalizedDeltaX = deltaX / actualScale;
                        const normalizedDeltaY = deltaY / actualScale;
                        
                        currentTranslateX = initialTranslateX + normalizedDeltaX;
                        currentTranslateY = initialTranslateY + normalizedDeltaY;
                        
                        // 이동 범위 제한 (이미지의 모든 영역을 볼 수 있도록)
                        if (slideRect) {
                            // 확대된 이미지가 컨테이너보다 큰 경우에만 이동 제한
                            // ✅ maxTranslate도 scale로 나눠서 정규화
                            const maxTranslateX = scaledWidth > containerWidth 
                                ? (scaledWidth - containerWidth) / (2 * actualScale)
                                : 0;
                            const maxTranslateY = scaledHeight > containerHeight 
                                ? (scaledHeight - containerHeight) / (2 * actualScale)
                                : 0;
                            
                            currentTranslateX = Math.max(-maxTranslateX, Math.min(maxTranslateX, currentTranslateX));
                            currentTranslateY = Math.max(-maxTranslateY, Math.min(maxTranslateY, currentTranslateY));
                        }
                        
                        // ✅ transform 적용 (translate를 먼저, scale을 나중에 - 더 직관적인 동작)
                        img.style.transform = `scale(${actualScale}) translate(${currentTranslateX}px, ${currentTranslateY}px)`;
                        
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }, { passive: false });
                
                img.addEventListener('touchend', (e) => {
                    // ✅ 이미지 요소가 아닌 경우 무시 (여백 클릭 방지)
                    if (e.target !== img && !img.contains(e.target)) {
                        return;
                    }
                    
                    // ✅ 핀치 줌 종료
                    if (isPinching && e.touches.length < 2) {
                        isPinching = false;
                        initialScale = currentScale;
                        
                        // 확대 비율이 1 이하면 축소
                        if (currentScale <= 1) {
                            img.classList.remove('zoomed');
                            currentScale = 1;
                            currentTranslateX = 0;
                            currentTranslateY = 0;
                            initialTranslateX = 0;
                            initialTranslateY = 0;
                            img.style.transform = '';
                            updateScrollLock(img);
                        } else {
                            // 확대 상태 유지
                            img.style.transform = `scale(${currentScale}) translate(${initialTranslateX}px, ${initialTranslateY}px)`;
                            updateScrollLock(img);
                        }
                        return;
                    }
                    
                    const touchEndTime = Date.now();
                    const touchDuration = touchEndTime - touchStartTime;
                    
                    if (img.classList.contains('zoomed') || currentScale > 1) {
                        isDragging = false;
                        // 최종 translate 값 저장
                        initialTranslateX = currentTranslateX;
                        initialTranslateY = currentTranslateY;
                        
                        // 확대 상태에서 이동 없이 짧은 탭이면 축소
                        if (!hasMoved && touchDuration < 300 && e.touches.length === 0) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            // 축소: translate 초기화
                            img.classList.remove('zoomed');
                            currentScale = 1;
                            img.style.transform = '';
                            currentTranslateX = 0;
                            currentTranslateY = 0;
                            initialTranslateX = 0;
                            initialTranslateY = 0;
                            
                            // 스크롤 제어 업데이트
                            updateScrollLock(img);
                            return;
                        }
                    }
                    
                    // 이동이 없고 짧은 탭인 경우에만 확대/축소 처리
                    if (!hasMoved && touchDuration < 300) {
                        const now = Date.now();
                        const diff = now - lastTap;
                        
                        if (diff < 400 && diff > 0) {
                            // 더블탭 감지
                            e.preventDefault();
                            e.stopPropagation();
                            clearTimeout(tapTimer);
                            lastTap = 0; // ✅ 더블탭 후 초기화
                            
                            // 확대/축소 토글 (더블탭)
                            const isZoomed = img.classList.contains('zoomed') || currentScale > 1;
                            if (isZoomed) {
                                // 축소: translate 초기화
                                img.classList.remove('zoomed');
                                currentScale = 1;
                                img.style.transform = '';
                                currentTranslateX = 0;
                                currentTranslateY = 0;
                                initialTranslateX = 0;
                                initialTranslateY = 0;
                            } else {
                                // 다른 확대된 이미지가 있으면 먼저 축소
                                document.querySelectorAll('.guide-image.zoomed').forEach(otherImg => {
                                    if (otherImg !== img) {
                                        otherImg.classList.remove('zoomed');
                                        otherImg.style.transform = '';
                                    }
                                });
                                // 확대: 기본 2배로 시작 (핀치 줌으로 조절 가능)
                                img.classList.add('zoomed');
                                currentScale = 2;
                                img.style.transform = 'scale(2) translate(0, 0)';
                                currentTranslateX = 0;
                                currentTranslateY = 0;
                                initialTranslateX = 0;
                                initialTranslateY = 0;
                            }
                            
                            // 스크롤 제어 업데이트
                            updateScrollLock(img);
                        } else {
                            // ✅ 단일 탭: 더블탭 대기만 함 (자동 확대 제거 - 더블탭으로만 확대)
                            lastTap = now;
                            // 확대 상태가 아니면 단일 탭은 무시 (더블탭 대기)
                        }
                        lastTap = now;
                    }
                }, { passive: false });
            });
            
            // ✅ 단일 MutationObserver로 모든 이미지 감지 (중복 제거)
            if (!zoomStateObserver) {
                zoomStateObserver = new MutationObserver(() => {
                    updateScrollLock();
                });
                
                // 모든 이미지에 대해 단일 observer 등록
                images.forEach(img => {
                    zoomStateObserver.observe(img, { attributes: true, attributeFilter: ['class'] });
                });
            }
            
            // 초기 상태 설정
            updateScrollLock();
        }
        
        // 마우스 클릭 효과 초기화 (슬라이더 내부에서 호출)
        initMouseClickEffect();

        // ✅ 모바일: 네이티브 스크롤로 스와이프가 되므로 커스텀 터치 핸들러 제거
        if (monitorFrame && window.innerWidth <= 480) {
            let rafId = null;
            const onScroll = () => {
                // ✅ 모바일: 확대 상태일 때는 스크롤 이벤트 무시
                if (window.innerWidth <= 480) {
                    const zoomedImages = document.querySelectorAll('.guide-image.zoomed');
                    if (zoomedImages.length > 0) {
                        // 확대 상태: 스크롤 동기화 중단
                        return;
                    }
                }
                
                if (rafId) return;
                rafId = requestAnimationFrame(() => {
                    rafId = null;
                    const w = monitorFrame.getBoundingClientRect().width;
                    if (!w) return;
                    
                    // ✅ 정확한 슬라이드 인덱스 계산 (중간 영역이 보이지 않도록)
                    const scrollLeft = monitorFrame.scrollLeft;
                    const idx = Math.round(scrollLeft / w);
                    const clamped = Math.max(0, Math.min(totalSlides - 1, idx));
                    
                    // ✅ 스크롤 위치가 정확한 슬라이드 위치가 아니면 강제 조정
                    const targetScroll = clamped * w;
                    if (Math.abs(scrollLeft - targetScroll) > 2) {
                        // 2px 이상 오차가 있으면 정확한 위치로 조정
                        monitorFrame.scrollLeft = targetScroll;
                    }
                    
                    if (clamped !== currentIndex) {
                        // 탭/자막 동기화
                        slides.forEach(slide => slide.classList.remove('active'));
                        tabs.forEach(tab => tab.classList.remove('active'));
                        if (slides[clamped]) slides[clamped].classList.add('active');
                        if (tabs[clamped]) tabs[clamped].classList.add('active');
                        if (subtitleText) subtitleText.textContent = subtitleTexts[clamped] || "";
                        if (subtitleContainer) subtitleContainer.classList.add('show');
                        currentIndex = clamped;
                    }
                });
            };

            monitorFrame.addEventListener('scroll', onScroll, { passive: true });
            
            // ✅ 초기화: 모든 슬라이드를 강제로 보이게 설정 (인라인 스타일로 완전히 덮어씀)
            if (window.innerWidth <= 480) {
                // ✅ 모바일에서만 실행
                const slideWrapper = document.querySelector('.slide-wrapper');
                if (slideWrapper) {
                    // ✅ slide-wrapper 강제 설정
                    slideWrapper.style.cssText = `
                        display: flex !important;
                        flex-direction: row !important;
                        flex-wrap: nowrap !important;
                        width: 800% !important;
                        height: auto !important;
                        position: relative !important;
                        left: 0 !important;
                        top: 0 !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        gap: 0 !important;
                    `;
                }
                
                // ✅ 모든 슬라이드에 인라인 스타일로 완전히 덮어씀
                slides.forEach((slide, index) => {
                    slide.style.cssText = `
                        position: relative !important;
                        top: auto !important;
                        left: auto !important;
                        flex: 0 0 12.5% !important;
                        width: 12.5% !important;
                        min-width: 12.5% !important;
                        max-width: 12.5% !important;
                        height: 60vh !important;
                        min-height: 300px !important;
                        opacity: 1 !important;
                        visibility: visible !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        transition: none !important;
                    `;
                });
                
                // ✅ monitor-scroll 래퍼도 확인 (있다면)
                const monitorScroll = document.querySelector('.monitor-scroll');
                if (monitorScroll) {
                    monitorScroll.style.cssText = `
                        overflow: visible !important;
                        width: 100% !important;
                    `;
                }
                
                // ✅ 초기 위치 보정: 레이아웃 계산 후 스크롤 위치 설정
                const initScroll = () => {
                    monitorFrame.scrollLeft = 0;
                    requestAnimationFrame(() => {
                        monitorFrame.scrollLeft = 0;
                        setTimeout(() => {
                            monitorFrame.scrollLeft = 0;
                            scrollToSlide(0, 'auto');
                            requestAnimationFrame(() => {
                                monitorFrame.scrollLeft = 0;
                            });
                        }, 200);
                    });
                };
                
                // ✅ 즉시 실행 + DOMContentLoaded 후 + load 후
                initScroll();
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', initScroll);
                }
                window.addEventListener('load', initScroll);
            }
        }
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

    // ✅ 모바일(<=480px): 타겟 카드 2열 요약 + 탭 시 확장/접기
    function initMobileTargetCardToggle() {
        if (window.innerWidth > 480) return;

        const cards = document.querySelectorAll('#home .target-cards .target-card');
        if (!cards || cards.length === 0) return;

        cards.forEach((card) => {
            card.addEventListener('click', (e) => {
                // 확장 상태에서 링크 클릭은 링크 동작 우선
                if (e.target && e.target.closest && e.target.closest('a')) return;

                const willExpand = !card.classList.contains('is-expanded');
                cards.forEach((c) => c.classList.remove('is-expanded'));
                if (willExpand) card.classList.add('is-expanded');
            });
        });
    }

    initMobileTargetCardToggle();

    // ✅ 모바일(<=480px): 2번 화면(타겟 섹션) 이미지 2장을 가로 스와이프 레일로 재배치
    function initMobileTargetMediaRail() {
        if (window.innerWidth > 480) return;

        const home = document.getElementById('home');
        if (!home) return;

        const targetAudience = home.querySelector('.hero-target-audience');
        if (!targetAudience) return;

        // 이미 레일이 있으면 중복 실행 방지
        if (targetAudience.querySelector('.target-media-rail')) return;

        const featuredWrap = home.querySelector('.hero-featured-image-wrapper');
        const kweoWrap = home.querySelector('.hero-kweo-image-wrapper');
        if (!featuredWrap || !kweoWrap) return;

        const rail = document.createElement('div');
        rail.className = 'target-media-rail';

        // 타겟 카드들 아래에 배치
        const cards = targetAudience.querySelector('.target-cards');
        if (cards && cards.parentNode) {
            cards.parentNode.insertBefore(rail, cards.nextSibling);
        } else {
            targetAudience.appendChild(rail);
        }

        rail.appendChild(featuredWrap);
        rail.appendChild(kweoWrap);
    }

    initMobileTargetMediaRail();
    
    // 전역 함수 등록
    window.scrollToSection = scrollToSection;
    
    // Lucide 아이콘 초기화 안전장치
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log('🚀 RohaTax homepage initialized');
});