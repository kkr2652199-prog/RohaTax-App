/**
 * 눈송이 배경 조절 컨트롤
 */

(function() {
    'use strict';

    const toggleBtn = document.getElementById('snowflakeToggle');
    const controlPanel = document.getElementById('snowflakePanel');
    const zoomSlider = document.getElementById('zoomSlider');
    const opacitySlider = document.getElementById('opacitySlider');
    const zoomValue = document.getElementById('zoomValue');
    const opacityValue = document.getElementById('opacityValue');
    const canvas = document.getElementById('snowflakeCanvas');

    if (!toggleBtn || !controlPanel || !zoomSlider || !opacitySlider) {
        return;
    }

    // 로컬 스토리지에서 설정값 불러오기
    const savedZoom = localStorage.getItem('snowflakeZoom');
    const savedOpacity = localStorage.getItem('snowflakeOpacity');
    
    if (savedZoom) {
        zoomSlider.value = savedZoom;
        zoomValue.textContent = parseFloat(savedZoom).toFixed(1);
    }
    
    if (savedOpacity) {
        const opacityPercent = Math.round(parseFloat(savedOpacity) * 100);
        opacitySlider.value = opacityPercent;
        opacityValue.textContent = opacityPercent;
    }

    // 패널 토글
    toggleBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        const isVisible = controlPanel.style.display !== 'none';
        controlPanel.style.display = isVisible ? 'none' : 'block';
    });

    // 외부 클릭 시 패널 닫기
    document.addEventListener('click', function(e) {
        if (!controlPanel.contains(e.target) && !toggleBtn.contains(e.target)) {
            controlPanel.style.display = 'none';
        }
    });

    // 배율 조절
    zoomSlider.addEventListener('input', function(e) {
        const zoom = parseFloat(e.target.value);
        zoomValue.textContent = zoom.toFixed(1);
        
        if (window.snowflakeBackground) {
            window.snowflakeBackground.setZoom(zoom);
        }
    });

    // 투명도 조절
    opacitySlider.addEventListener('input', function(e) {
        const opacityPercent = parseInt(e.target.value);
        const opacity = opacityPercent / 100;
        opacityValue.textContent = opacityPercent;
        
        if (window.snowflakeBackground) {
            window.snowflakeBackground.setOpacity(opacity);
        }
        
        // 캔버스 투명도도 조절 (시각적 피드백)
        if (canvas) {
            canvas.style.opacity = opacity;
        }
    });

    // 초기 투명도 적용
    if (canvas && savedOpacity) {
        canvas.style.opacity = savedOpacity;
    }
})();

