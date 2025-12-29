/**
 * 로.하 TAX 동영상 플레이어
 * YouTube 스타일 커스텀 비디오 플레이어
 */

(function() {
    'use strict';
    
    // DOM 로드 완료 후 초기화
    document.addEventListener('DOMContentLoaded', function() {
        initVideoPlayer();
    });
    
    function initVideoPlayer() {
        const playerContainer = document.querySelector('.roha-video-player');
        if (!playerContainer) {
            console.log('비디오 플레이어 컨테이너를 찾을 수 없습니다.');
            return;
        }

        const video = document.getElementById('rohaVideo');
        if (!video) {
            console.log('비디오 요소를 찾을 수 없습니다.');
            return;
        }

        // 이미 초기화된 경우 중복 초기화 방지
        if (video.dataset.initialized === 'true') {
            console.log('비디오 플레이어가 이미 초기화되었습니다.');
            return;
        }
        
        console.log('비디오 플레이어 초기화 시작');
        video.dataset.initialized = 'true';
        
        // 요소 참조
        const videoContainer = playerContainer.querySelector('.video-container');
        const playOverlayBtn = playerContainer.querySelector('.play-overlay-btn');
        const videoOverlay = playerContainer.querySelector('.video-overlay');
        const videoControlBar = playerContainer.querySelector('.video-control-bar');
        const videoLoading = playerContainer.querySelector('.video-loading');
        const videoPlaceholder = playerContainer.querySelector('.video-placeholder');
        
        // 새로운 컨트롤 바 요소들 (안전한 참조)
        const playPauseBtn = playerContainer.querySelector('.play-pause-btn');
        const playIcon = playPauseBtn ? playPauseBtn.querySelector('.play-icon') : null;
        const pauseIcon = playPauseBtn ? playPauseBtn.querySelector('.pause-icon') : null;
        const volumeBtn = playerContainer.querySelector('.volume-btn');
        const volumeIcon = volumeBtn ? volumeBtn.querySelector('.volume-icon') : null;
        const volumeMuteIcon = volumeBtn ? volumeBtn.querySelector('.volume-mute-icon') : null;
        const volumeSlider = playerContainer.querySelector('.volume-slider');
        const fullscreenBtn = playerContainer.querySelector('.fullscreen-btn');
        const fullscreenIcon = fullscreenBtn ? fullscreenBtn.querySelector('.fullscreen-icon') : null;
        const fullscreenExitIcon = fullscreenBtn ? fullscreenBtn.querySelector('.fullscreen-exit-icon') : null;
        
        // 진행 바 요소들 (안전한 참조)
        const progressBar = playerContainer.querySelector('.progress-bar');
        const progressFilled = playerContainer.querySelector('.progress-filled');
        const progressHandle = playerContainer.querySelector('.progress-handle');
        const currentTimeDisplay = playerContainer.querySelector('.current-time');
        const durationDisplay = playerContainer.querySelector('.duration-time');
        
        // 상태 변수
        let isPlaying = false;
        let isMuted = false;
        let currentSpeed = 1;
        let hideControlsTimeout = null;
        
        // ==================== 초기화 ====================
        
        console.log('비디오 플레이어 초기화 시작');
        console.log('비디오 요소:', video);
        console.log('비디오 소스 (src):', video.src);
        console.log('비디오 소스 (currentSrc):', video.currentSrc);
        console.log('비디오 readyState:', video.readyState);
        
        // 비디오 소스 확인 및 강제 로드
        const sourceElement = video.querySelector('source');
        if (sourceElement) {
            console.log('source 태그 발견:', sourceElement.src);
        }
        
        // 비디오가 아직 로드되지 않았으면 명시적으로 로드
        if (video.readyState === 0) {
            console.log('비디오 readyState가 0이므로 load() 호출');
            video.load();
        }
        
        // 비디오 메타데이터 로드 시
        video.addEventListener('loadedmetadata', function() {
            console.log('비디오 메타데이터 로드 완료');
            console.log('비디오 길이:', video.duration);
            console.log('비디오 크기:', video.videoWidth, 'x', video.videoHeight);
            console.log('비디오 currentSrc:', video.currentSrc);
            
            if (durationDisplay) {
                durationDisplay.textContent = formatTime(video.duration);
            }
            // 플레이스홀더 숨기기
            if (videoPlaceholder) {
                videoPlaceholder.style.display = 'none';
            }
        });
        
        // 비디오 로딩 중
        video.addEventListener('waiting', function() {
            console.log('비디오 로딩 중...');
            if (videoLoading) {
                videoLoading.style.display = 'block';
            }
        });
        
        // 비디오 재생 가능
        video.addEventListener('canplay', function() {
            console.log('비디오 재생 가능');
            if (videoLoading) {
                videoLoading.style.display = 'none';
            }
        });
        
        // 비디오 재생 시작
        video.addEventListener('playing', function() {
            console.log('비디오 재생 중');
            if (videoLoading) {
                videoLoading.style.display = 'none';
            }
        });
        
        // 비디오 에러 처리
        video.addEventListener('error', function(e) {
            console.error('비디오 로드 오류:', e);
            if (videoLoading) {
                videoLoading.style.display = 'none';
            }
            
            // 플레이스홀더 표시
            if (videoPlaceholder) {
                videoPlaceholder.style.display = 'flex';
                if (videoOverlay) {
                    videoOverlay.style.display = 'none';
                }
            }
            
            // 에러 메시지 표시 (옵션)
            if (video.error) {
                console.log('Error code:', video.error.code);
                console.log('Error message:', video.error.message);
                console.log('Video source:', video.src);
                console.log('Video currentSrc:', video.currentSrc);
                
                // 에러 코드별 상세 정보
                switch(video.error.code) {
                    case 1:
                        console.log('MEDIA_ERR_ABORTED: 사용자가 중단');
                        break;
                    case 2:
                        console.log('MEDIA_ERR_NETWORK: 네트워크 오류');
                        break;
                    case 3:
                        console.log('MEDIA_ERR_DECODE: 디코딩 오류');
                        break;
                    case 4:
                        console.log('MEDIA_ERR_SRC_NOT_SUPPORTED: 지원되지 않는 형식');
                        break;
                }
            }
        });
        
        // ==================== 재생/일시정지 ====================
        
        function togglePlayPause() {
            console.log('재생/일시정지 토글 호출');
            console.log('현재 상태 - paused:', video.paused, 'ended:', video.ended, 'readyState:', video.readyState);
            console.log('비디오 currentSrc:', video.currentSrc);
            
            // 비디오 소스가 없으면 로드 시도
            if (!video.currentSrc && !video.src) {
                console.log('비디오 소스가 없음, 로드 시도');
                const sourceElement = video.querySelector('source');
                if (sourceElement && sourceElement.src) {
                    console.log('source 태그에서 소스 발견:', sourceElement.src);
                    video.load();
                }
            }
            
            if (video.paused || video.ended) {
                // 비디오가 아직 준비되지 않은 경우 canplay 이벤트를 기다림
                if (video.readyState < 1) {
                    console.log('비디오 메타데이터 로드 대기 중...');
                    video.addEventListener('loadedmetadata', function onMetadataLoaded() {
                        video.removeEventListener('loadedmetadata', onMetadataLoaded);
                        console.log('메타데이터 로드 완료, 재생 시도');
                        attemptPlay();
                    }, { once: true });
                    // 메타데이터 로드를 위해 load() 호출
                    if (!video.currentSrc) {
                        video.load();
                    }
                    return;
                }
                
                // 메타데이터는 있지만 재생 가능한 데이터가 부족한 경우
                if (video.readyState < 2) {
                    console.log('비디오 재생 데이터 로드 대기 중...');
                    video.addEventListener('canplay', function onCanPlay() {
                        video.removeEventListener('canplay', onCanPlay);
                        console.log('재생 가능, 재생 시도');
                        attemptPlay();
                    }, { once: true });
                    return;
                }
                
                attemptPlay();
            } else {
                console.log('비디오 일시정지');
                video.pause();
            }
        }
        
        function attemptPlay() {
            console.log('비디오 재생 시작');
            const playPromise = video.play();
            
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log('비디오 재생 성공');
                }).catch(error => {
                    console.error('비디오 재생 실패:', error);
                    // 재생 실패 시 상태 초기화
                    isPlaying = false;
                    if (playIcon) playIcon.style.display = 'block';
                    if (pauseIcon) pauseIcon.style.display = 'none';
                });
            }
        }
        
        video.addEventListener('play', function() {
            console.log('비디오 play 이벤트 발생');
            isPlaying = true;
            if (playIcon) playIcon.style.display = 'none';
            if (pauseIcon) pauseIcon.style.display = 'block';
            if (videoOverlay) videoOverlay.classList.add('hidden');
        });
        
        video.addEventListener('pause', function() {
            console.log('비디오 pause 이벤트 발생');
            isPlaying = false;
            if (playIcon) playIcon.style.display = 'block';
            if (pauseIcon) pauseIcon.style.display = 'none';
            if (video.currentTime > 0 && videoOverlay) {
                videoOverlay.classList.remove('hidden');
            }
        });
        
        video.addEventListener('ended', function() {
            console.log('비디오 ended 이벤트 발생');
            isPlaying = false;
            if (playIcon) playIcon.style.display = 'block';
            if (pauseIcon) pauseIcon.style.display = 'none';
            if (videoOverlay) videoOverlay.classList.remove('hidden');
            video.currentTime = 0; // 비디오 종료 시 처음으로
            if (progressFilled) progressFilled.style.width = '0%';
            if (progressHandle) progressHandle.style.left = '0%';
            if (currentTimeDisplay) currentTimeDisplay.textContent = formatTime(0);
        });
        
        // 재생 버튼 클릭 (안전한 이벤트 바인딩)
        // 기존 이벤트 리스너 제거 후 새로 등록
        if (playOverlayBtn) {
            playOverlayBtn.removeEventListener('click', togglePlayPause);
            playOverlayBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('오버레이 재생 버튼 클릭됨');
                togglePlayPause();
            });
        }
        if (playPauseBtn) {
            playPauseBtn.removeEventListener('click', togglePlayPause);
            playPauseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('컨트롤 바 재생/일시정지 버튼 클릭됨');
                togglePlayPause();
            });
        }
        
        // 비디오 클릭 이벤트 (오버레이 버튼과 중복 방지)
        video.addEventListener('click', function(e) {
            // 오버레이 버튼 클릭이 아닌 경우에만 처리
            if (e.target === video) {
                e.preventDefault();
                togglePlayPause();
            }
        });
        
        // ==================== 진행 바 ====================
        
        // 시간 업데이트
        video.addEventListener('timeupdate', function() {
            if (progressFilled && progressHandle && currentTimeDisplay && video.duration > 0) {
                const percent = (video.currentTime / video.duration) * 100;
                progressFilled.style.width = percent + '%';
                progressHandle.style.left = percent + '%';
                currentTimeDisplay.textContent = formatTime(video.currentTime);
            }
        });
        
        // 진행 바 클릭 (안전한 이벤트 바인딩)
        if (progressBar) {
            progressBar.addEventListener('click', function(e) {
                if (video.duration > 0) {
                    const rect = progressBar.getBoundingClientRect();
                    const percent = (e.clientX - rect.left) / rect.width;
                    const newTime = percent * video.duration;
                    video.currentTime = Math.max(0, Math.min(video.duration, newTime));
                }
            });
        }
        
        // 진행 바 드래그 (안전한 이벤트 바인딩)
        let isDragging = false;
        
        if (progressBar) {
            progressBar.addEventListener('mousedown', function(e) {
                isDragging = true;
                updateProgress(e);
            });
        }
        
        document.addEventListener('mousemove', function(e) {
            if (isDragging && progressBar) {
                updateProgress(e);
            }
        });
        
        document.addEventListener('mouseup', function() {
            isDragging = false;
        });
        
        function updateProgress(e) {
            if (!progressBar || video.duration <= 0) return;
            const rect = progressBar.getBoundingClientRect();
            let percent = (e.clientX - rect.left) / rect.width;
            percent = Math.max(0, Math.min(1, percent));
            const newTime = percent * video.duration;
            video.currentTime = Math.max(0, Math.min(video.duration, newTime));
        }
        
        // ==================== 볼륨 ====================
        
        if (volumeBtn) {
            volumeBtn.addEventListener('click', function() {
                console.log('볼륨 버튼 클릭됨');
                if (video.muted || video.volume === 0) {
                    video.muted = false;
                    video.volume = volumeSlider ? volumeSlider.value / 100 : 1; // 슬라이더 값 사용
                    if (volumeSlider) volumeSlider.value = video.volume * 100;
                    if (volumeIcon) volumeIcon.style.display = 'block';
                    if (volumeMuteIcon) volumeMuteIcon.style.display = 'none';
                    console.log('음소거 해제됨, 볼륨:', video.volume);
                } else {
                    video.muted = true;
                    if (volumeIcon) volumeIcon.style.display = 'none';
                    if (volumeMuteIcon) volumeMuteIcon.style.display = 'block';
                    console.log('음소거됨');
                }
            });
        }
        
        // 볼륨 슬라이더 이벤트
        if (volumeSlider) {
            volumeSlider.addEventListener('input', function() {
                const volume = this.value / 100;
                video.volume = volume;
                video.muted = volume === 0;
                
                // 아이콘 업데이트
                if (volume === 0) {
                    if (volumeIcon) volumeIcon.style.display = 'none';
                    if (volumeMuteIcon) volumeMuteIcon.style.display = 'block';
                } else {
                    if (volumeIcon) volumeIcon.style.display = 'block';
                    if (volumeMuteIcon) volumeMuteIcon.style.display = 'none';
                }
                
                console.log('볼륨 변경됨:', volume);
            });
            
            // 초기 볼륨 설정
            volumeSlider.value = video.volume * 100;
        }
        
        // ==================== 재생 속도 (새로운 컨트롤 바에서는 제거됨) ====================
        
        // ==================== 전체 화면 ====================
        
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', function() {
                console.log('전체화면 버튼 클릭됨');
                if (!document.fullscreenElement) {
                    // 전체 화면 진입
                    console.log('전체화면 진입 시도');
                    if (videoContainer.requestFullscreen) {
                        videoContainer.requestFullscreen();
                    } else if (videoContainer.webkitRequestFullscreen) {
                        videoContainer.webkitRequestFullscreen();
                    } else if (videoContainer.mozRequestFullScreen) {
                        videoContainer.mozRequestFullScreen();
                    } else if (videoContainer.msRequestFullscreen) {
                        videoContainer.msRequestFullscreen();
                    }
                } else {
                    // 전체 화면 종료
                    console.log('전체화면 종료 시도');
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    } else if (document.mozCancelFullScreen) {
                        document.mozCancelFullScreen();
                    } else if (document.msExitFullscreen) {
                        document.msExitFullscreen();
                    }
                }
            });
        }
        
        // 전체 화면 상태 변경 감지
        document.addEventListener('fullscreenchange', function() {
            updateFullscreenButton();
            handleFullscreenChange();
        });
        document.addEventListener('webkitfullscreenchange', function() {
            updateFullscreenButton();
            handleFullscreenChange();
        });
        document.addEventListener('mozfullscreenchange', function() {
            updateFullscreenButton();
            handleFullscreenChange();
        });
        document.addEventListener('MSFullscreenChange', function() {
            updateFullscreenButton();
            handleFullscreenChange();
        });
        
        function updateFullscreenButton() {
            if (document.fullscreenElement || document.webkitFullscreenElement || 
                document.mozFullScreenElement || document.msFullscreenElement) {
                if (fullscreenIcon) fullscreenIcon.style.display = 'none';
                if (fullscreenExitIcon) fullscreenExitIcon.style.display = 'block';
                playerContainer.classList.add('fullscreen');
            } else {
                if (fullscreenIcon) fullscreenIcon.style.display = 'block';
                if (fullscreenExitIcon) fullscreenExitIcon.style.display = 'none';
                playerContainer.classList.remove('fullscreen');
            }
        }
        
        function handleFullscreenChange() {
            const isFullscreen = document.fullscreenElement || document.webkitFullscreenElement || 
                                document.mozFullScreenElement || document.msFullscreenElement;
            
            if (isFullscreen) {
                // 전체화면 진입 시 하단에 안내 메시지 표시
                showFullscreenGuide();
            } else {
                // 전체화면 종료 시 안내 메시지 제거
                hideFullscreenGuide();
            }
        }
        
        function showFullscreenGuide() {
            // 기존 안내 메시지가 있으면 제거
            hideFullscreenGuide();
            
            // 하단 안내 메시지 생성
            const guide = document.createElement('div');
            guide.id = 'fullscreen-guide';
            guide.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                z-index: 10000;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                animation: fadeInUp 0.3s ease-out;
            `;
            guide.textContent = '전체 화면을 종료하려면 Esc 키를 누르세요';
            
            // CSS 애니메이션 추가
            if (!document.querySelector('#fullscreen-guide-styles')) {
                const style = document.createElement('style');
                style.id = 'fullscreen-guide-styles';
                style.textContent = `
                    @keyframes fadeInUp {
                        from {
                            opacity: 0;
                            transform: translateX(-50%) translateY(20px);
                        }
                        to {
                            opacity: 1;
                            transform: translateX(-50%) translateY(0);
                        }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(guide);
            
            // 3초 후 자동으로 사라지게 하기
            setTimeout(() => {
                if (guide.parentNode) {
                    guide.style.animation = 'fadeInUp 0.3s ease-out reverse';
                    setTimeout(() => {
                        if (guide.parentNode) {
                            guide.remove();
                        }
                    }, 300);
                }
            }, 3000);
        }
        
        function hideFullscreenGuide() {
            const guide = document.getElementById('fullscreen-guide');
            if (guide) {
                guide.remove();
            }
        }
        
        // ==================== 컨트롤 자동 숨김 (새로운 컨트롤 바에서는 항상 표시) ====================
        
        // 새로운 컨트롤 바는 항상 표시되므로 자동 숨김 기능 제거
        
        // ==================== 키보드 단축키 ====================
        
        document.addEventListener('keydown', function(e) {
            // 비디오 플레이어가 활성화되어 있을 때만
            if (document.activeElement === video || 
                (videoContainer && videoContainer.contains(document.activeElement))) {
                
                switch(e.key) {
                    case ' ': // 스페이스바: 재생/일시정지
                    case 'k':
                        e.preventDefault();
                        togglePlayPause();
                        break;
                    case 'f': // F: 전체 화면
                        e.preventDefault();
                        if (fullscreenBtn) fullscreenBtn.click();
                        break;
                    case 'm': // M: 음소거
                        e.preventDefault();
                        if (volumeBtn) volumeBtn.click();
                        break;
                    case 'ArrowLeft': // 왼쪽 화살표: 5초 뒤로
                        e.preventDefault();
                        video.currentTime = Math.max(0, video.currentTime - 5);
                        break;
                    case 'ArrowRight': // 오른쪽 화살표: 5초 앞으로
                        e.preventDefault();
                        video.currentTime = Math.min(video.duration, video.currentTime + 5);
                        break;
                    case 'ArrowUp': // 위 화살표: 볼륨 증가
                        e.preventDefault();
                        video.volume = Math.min(1, video.volume + 0.1);
                        break;
                    case 'ArrowDown': // 아래 화살표: 볼륨 감소
                        e.preventDefault();
                        video.volume = Math.max(0, video.volume - 0.1);
                        break;
                }
                // 새로운 컨트롤 바는 항상 표시되므로 showControls() 호출 제거
            }
        });
        
        // ==================== 유틸리티 함수 ====================
        
        function formatTime(seconds) {
            if (isNaN(seconds)) return '0:00';
            
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            if (hours > 0) {
                return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            } else {
                return `${mins}:${secs.toString().padStart(2, '0')}`;
            }
        }
        
        // ==================== 초기 상태 설정 ====================
        
        // 초기 볼륨 설정
        video.volume = 1;
        
        // 초기 재생 속도
        video.playbackRate = 1;
        
        // 초기 컨트롤 상태 설정
        if (videoOverlay) {
            videoOverlay.style.display = 'flex';
        }
        
        // 새로운 컨트롤 바는 항상 표시되므로 초기 표시 설정 불필요
        
        console.log('로.하 TAX 비디오 플레이어 초기화 완료');
        console.log('비디오 상태:', {
            paused: video.paused,
            ended: video.ended,
            readyState: video.readyState,
            duration: video.duration,
            currentTime: video.currentTime
        });
    }
})();

