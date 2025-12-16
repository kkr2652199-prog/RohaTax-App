// Lightweight developer overlay console for in-app progress visibility
// Usage: initConsoleMirror(); window.vipLog('message');

let overlayEl, bodyEl, isVisible = false;

function createOverlay() {
  if (overlayEl) return overlayEl;
  overlayEl = document.createElement('div');
  overlayEl.className = 'console-mirror';
  overlayEl.style.display = 'none';

  const header = document.createElement('div');
  header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:8px 10px;border-bottom:1px solid rgba(255,255,255,0.08);font-weight:600;font-size:12px;letter-spacing:.2px;';
  header.innerHTML = '<span>Dev Console</span><div style="display:flex;gap:8px;align-items:center"><button id="cm-clear" style="background:#0ea5a4;color:#fff;border:none;padding:4px 8px;border-radius:6px;cursor:pointer;font-size:11px">Clear</button><button id="cm-close" style="background:#374151;color:#e5f9ff;border:none;padding:4px 8px;border-radius:6px;cursor:pointer;font-size:11px">Hide (F9)</button></div>';

  bodyEl = document.createElement('div');
  bodyEl.style.cssText = 'padding:10px;overflow:auto;white-space:pre-wrap;word-break:break-word;font-size:12px;line-height:1.4;flex:1';

  overlayEl.appendChild(header);
  overlayEl.appendChild(bodyEl);
  document.body.appendChild(overlayEl);

  header.querySelector('#cm-close').addEventListener('click', toggle);
  header.querySelector('#cm-clear').addEventListener('click', () => { bodyEl.innerHTML = ''; });
  return overlayEl;
}

function toggle(force) {
  if (!overlayEl) createOverlay();
  if (typeof force === 'boolean') isVisible = force; else isVisible = !isVisible;
  overlayEl.style.display = isVisible ? 'flex' : 'none';
}

function logLine(level, msg) {
  if (!overlayEl) createOverlay();
  const time = new Date().toLocaleTimeString();
  const line = document.createElement('div');
  const color = level === 'error' ? '#fda4af' : level === 'warn' ? '#fde68a' : '#a7f3d0';
  line.style.cssText = `margin:2px 0;color:${color}`;
  line.textContent = `[${time}] ${msg}`;
  bodyEl.appendChild(line);
  bodyEl.scrollTop = bodyEl.scrollHeight;
}

export function initConsoleMirror() {
  createOverlay();
  // expose global helper
  window.vipLog = (msg) => logLine('info', msg);
  window.vipWarn = (msg) => logLine('warn', msg);
  window.vipError = (msg) => logLine('error', msg);

  // F9 toggle
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F9') {
      e.preventDefault();
      toggle();
    }
    if (e.key === 'F10') {
      e.preventDefault();
      toggleCursor();
    }
  });

  // auto-show when ?dev=1
  try {
    const url = new URL(location.href);
    if (url.searchParams.get('dev') === '1') toggle(true);
    if (url.searchParams.get('cursor') === '1') toggleCursor(true);
  } catch (_) {}
}

// ===== Pointer mirror (show real-time cursor for demos/dev) =====
let cursorEl, cursorVisible = false;

function ensureCursor() {
  if (cursorEl) return cursorEl;
  cursorEl = document.createElement('div');
  cursorEl.id = 'cursor-mirror';
  cursorEl.style.display = 'none';
  document.body.appendChild(cursorEl);
  window.addEventListener('mousemove', (e) => {
    if (!cursorVisible) return;
    cursorEl.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
  });
  return cursorEl;
}

function toggleCursor(force) {
  ensureCursor();
  if (typeof force === 'boolean') cursorVisible = force; else cursorVisible = !cursorVisible;
  cursorEl.style.display = cursorVisible ? 'block' : 'none';
}



