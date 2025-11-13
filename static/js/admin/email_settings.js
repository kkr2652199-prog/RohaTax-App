/**
 * Admin Dashboard 이메일 인증 설정 모듈
 *
 * 이 파일은 admin.html에서 분리된 이메일 인증 설정 관련 함수를 포함합니다.
 * - 이메일 인증 설정 로드
 * - 이메일 인증 설정 UI 렌더링
 * - 이메일 인증 설정 저장
 */

/**
 * 이메일 인증 설정 로드
 * 서버에서 이메일 인증 설정 데이터를 가져와 UI를 업데이트합니다.
 * @returns {Promise<void>}
 */
async function loadEmailVerificationSettings() {
    console.log('🔧 이메일 인증 설정 로드 시작...');
    
    try {
        const response = await fetch('/admin/api/email-settings', {
            headers: {
                'X-CSRF-Token': csrfToken()
            },
        });
        console.log('📡 API 응답 상태:', response.status);
        console.log('📡 API 응답 헤더:', response.headers);
        
        const data = await response.json();
        console.log('📊 API 응답 데이터:', data);
        
        if (data.success) {
            console.log('✅ API 호출 성공, UI 렌더링 시작...');
            renderEmailVerificationSettings(data.data);
        } else {
            console.error('❌ API 호출 실패:', data.message);
            document.getElementById('emailVerificationSettings').innerHTML = 
                `<p class="muted">이메일 인증 설정을 불러올 수 없습니다: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('❌ 이메일 인증 설정 로드 실패:', error);
        document.getElementById('emailVerificationSettings').innerHTML = 
            `<p class="muted">이메일 인증 설정을 불러오는 중 오류가 발생했습니다: ${error.message}</p>`;
    }
}

/**
 * 이메일 인증 설정 UI 렌더링
 * 제공된 설정 데이터를 기반으로 이메일 인증 설정 UI를 생성합니다.
 * @param {object} data - 설정 데이터 객체 (stats, settings 포함)
 */
function renderEmailVerificationSettings(data) {
    const { stats, settings } = data;
    
    const html = `
        <div class="status-badge ${settings.email_verification_enabled === '1' ? 'enabled' : 'disabled'}">
            ${settings.email_verification_enabled === '1' ? '활성화됨' : '비활성화됨'}
        </div>
        
        <div class="email-stats">
            <div class="email-stat-item">
                <div class="email-stat-value">${stats.total_users || 0}</div>
                <div class="email-stat-label">전체 사용자</div>
            </div>
            <div class="email-stat-item">
                <div class="email-stat-value">${stats.verified_users || 0}</div>
                <div class="email-stat-label">인증 완료</div>
            </div>
            <div class="email-stat-item">
                <div class="email-stat-value">${stats.pending_users || 0}</div>
                <div class="email-stat-label">인증 대기</div>
            </div>
            <div class="email-stat-item">
                <div class="email-stat-value">${(stats.verification_rate || 0).toFixed(1)}%</div>
                <div class="email-stat-label">인증률</div>
            </div>
        </div>
        
        <form id="emailSettingsForm" class="email-settings-form">
            <div class="email-toggle">
                <div class="toggle-switch ${settings.email_verification_enabled === '1' ? 'active' : ''}" 
                     onclick="toggleEmailVerification(this)">
                    <input type="checkbox" id="emailVerificationToggle" name="email_verification_enabled" value="1" 
                           ${settings.email_verification_enabled === '1' ? 'checked' : ''}>
                </div>
                <span>이메일 인증 ${settings.email_verification_enabled === '1' ? '활성화' : '비활성화'}</span>
            </div>
            
            <div class="setting-group">
                <h4>토큰 만료 시간</h4>
                <p>인증 토큰이 유효한 시간을 설정합니다. (시간 단위)</p>
                <div class="setting-control">
                    <input type="number" name="email_verification_expiry_hours" 
                           value="${settings.email_verification_expiry_hours || '24'}" 
                           min="1" max="168" class="number-input">
                    <span>시간</span>
                </div>
            </div>
            
            <div class="setting-group">
                <h4>최대 시도 횟수</h4>
                <p>사용자가 인증 이메일을 재발송할 수 있는 최대 횟수입니다.</p>
                <div class="setting-control">
                    <input type="number" name="email_verification_max_attempts" 
                           value="${settings.email_verification_max_attempts || '3'}" 
                           min="1" max="10" class="number-input">
                    <span>회</span>
                </div>
            </div>
            
            <div class="setting-group">
                <h4>잠금 시간</h4>
                <p>최대 시도 횟수를 초과했을 때 재발송이 제한되는 시간입니다.</p>
                <div class="setting-control">
                    <input type="number" name="email_verification_lockout_hours" 
                           value="${settings.email_verification_lockout_hours || '24'}" 
                           min="1" max="168" class="number-input">
                    <span>시간</span>
                </div>
            </div>
            
            <button type="submit" class="save-button">설정 저장</button>
        </form>
    `;
    
    document.getElementById('emailVerificationSettings').innerHTML = html;
    
    // 폼 제출 이벤트 추가
    document.getElementById('emailSettingsForm').addEventListener('submit', saveEmailSettings);
}

/**
 * 이메일 인증 설정 저장
 * 폼 데이터를 서버로 전송하여 이메일 인증 설정을 저장합니다.
 * @param {Event} event - 폼 제출 이벤트
 * @returns {Promise<void>}
 */
async function saveEmailSettings(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const settings = {};
    
    // 폼 데이터 수집
    for (let [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    // [버그 수정] 체크박스가 체크되지 않으면 FormData에 포함되지 않으므로 명시적으로 처리
    // ID로 먼저 찾고, 없으면 name으로 찾기
    let emailVerificationCheckbox = document.getElementById('emailVerificationToggle');
    if (!emailVerificationCheckbox) {
        emailVerificationCheckbox = event.target.querySelector('input[name="email_verification_enabled"]');
    }
    
    if (emailVerificationCheckbox) {
        // 체크박스의 checked 상태를 명시적으로 확인하여 설정
        settings.email_verification_enabled = emailVerificationCheckbox.checked ? '1' : '0';
        console.log('🔍 이메일 인증 설정 상태:', emailVerificationCheckbox.checked ? '활성화' : '비활성화');
        console.log('🔍 체크박스 요소:', emailVerificationCheckbox);
        console.log('🔍 체크박스 checked 속성:', emailVerificationCheckbox.checked);
    } else {
        console.error('❌ 이메일 인증 체크박스를 찾을 수 없습니다!');
    }
    
    console.log('📤 전송할 설정 데이터:', settings);
    
    try {
        const response = await fetch('/admin/api/email-settings/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken()
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('이메일 인증 설정이 저장되었습니다.');
            loadEmailVerificationSettings(); // 설정 다시 로드
        } else {
            alert('설정 저장 실패: ' + result.error);
        }
    } catch (error) {
        console.error('설정 저장 오류:', error);
        alert('설정 저장 중 오류가 발생했습니다.');
    }
}

// 전역 함수로 노출 (다른 모듈에서 호출 가능하도록)
window.loadEmailVerificationSettings = loadEmailVerificationSettings;
window.renderEmailVerificationSettings = renderEmailVerificationSettings;
window.saveEmailSettings = saveEmailSettings;

