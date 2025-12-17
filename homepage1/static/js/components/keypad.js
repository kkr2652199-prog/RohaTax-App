/**
 * 3D Keypad Navigation Component
 * Refined for RohaTax App
 * - Removed Tweakpane dependencies
 * - Added page navigation logic
 * - Simplified configuration
 */

(function() {
  'use strict';

  // Configuration (simplified - only essential animation variables)
  const config = {
    travel: 15, // Animation travel distance
    soundEnabled: true
  };

  // Audio context for click sound
  let audioContext = null;
  let clickSoundBuffer = null;

  /**
   * Initialize audio context and load click sound
   */
  function initAudio() {
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      createClickSound();
    } catch (e) {
      console.warn('Audio context not supported:', e);
      config.soundEnabled = false;
    }
  }

  /**
   * Create a simple click sound using Web Audio API
   */
  function createClickSound() {
    if (!audioContext) return;

    const sampleRate = audioContext.sampleRate;
    const duration = 0.1; // 100ms
    const frequency = 800; // Hz
    const buffer = audioContext.createBuffer(1, sampleRate * duration, sampleRate);
    const data = buffer.getChannelData(0);

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      // Simple sine wave with decay
      data[i] = Math.sin(2 * Math.PI * frequency * t) * Math.exp(-t * 10);
    }

    clickSoundBuffer = buffer;
  }

  /**
   * Play click sound
   */
  function playClickSound() {
    if (!config.soundEnabled || !audioContext || !clickSoundBuffer) return;

    try {
      const source = audioContext.createBufferSource();
      source.buffer = clickSoundBuffer;
      source.connect(audioContext.destination);
      source.start(0);
    } catch (e) {
      console.warn('Failed to play click sound:', e);
    }
  }

  /**
   * Handle key button click
   */
  function handleKeyClick(e) {
    const key = e.currentTarget;
    
    // Add pressed class for animation
    key.classList.add('pressed');
    setTimeout(() => {
      key.classList.remove('pressed');
    }, 300);

    // Play click sound
    playClickSound();

    // Handle navigation
    const link = key.getAttribute('data-link');
    if (link) {
      // Small delay for visual feedback before navigation
      setTimeout(() => {
        window.location.href = link;
      }, 150);
    }
    // Note: 'back' button uses onclick attribute in HTML, so it's handled automatically
  }

  /**
   * Initialize keypad component
   */
  function initKeypad() {
    // Initialize audio
    initAudio();

    // Get all key buttons
    const keys = document.querySelectorAll('.key');
    
    if (keys.length === 0) {
      console.warn('No keypad buttons found');
      return;
    }

    // Add click event listeners
    keys.forEach(key => {
      key.addEventListener('click', handleKeyClick);
      
      // Add keyboard accessibility
      key.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          key.click();
        }
      });
    });

    console.log('✅ 3D Keypad initialized:', keys.length, 'buttons');
  }

  // Initialize with retry logic (for React apps where HTML is injected dynamically)
  function initKeypadWithRetry(maxRetries = 10, delay = 200) {
    let retries = 0;
    
    function tryInit() {
      const keys = document.querySelectorAll('.key');
      if (keys.length > 0) {
        initKeypad();
        return;
      }
      
      if (retries < maxRetries) {
        retries++;
        setTimeout(tryInit, delay);
      } else {
        console.warn('3D Keypad: Failed to find buttons after', maxRetries, 'retries');
      }
    }
    
    // Start trying immediately
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', tryInit);
    } else {
      tryInit();
    }
  }

  // Start initialization
  initKeypadWithRetry();

  // Export for manual initialization if needed
  window.KeypadController = {
    init: initKeypad,
    playSound: playClickSound
  };

})();

