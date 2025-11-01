// Conversion Page JavaScript
// Refactored from conversion.html

document.addEventListener('DOMContentLoaded', function() {
        // 버튼 상태 제어 컴포넌트
        function setButtonState(btn, {disabled, text, opacity = '1', title = ''}) {
            if (!btn) return;
            btn.disabled = !!disabled;
            if (text !== undefined) btn.textContent = text;
            btn.style.opacity = opacity;
            if (title) btn.title = title;
        }

        // 변환 시작 버튼 상태 업데이트 (모든 탭에서 허용하여 서버 측 지침 에러 확인 가능)
        function updateConversionButton() {
            const startBtn = document.getElementById('start-conversion-btn');
            if (startBtn) {
                const title = '로하VIP 회원님 첨부파일 변환 서비스';
                // 항상 활성화하여 변환 시작 가능
                setButtonState(startBtn, { disabled: false, text: '변환시작', opacity: '1', title });
            }

            // VIP 버튼은 항상 활성화 유지
            const vipBtn = document.getElementById('get-user-info-btn');
            setButtonState(vipBtn, { disabled: false, opacity: '1' });
        }
        
        // 페이지 로드 시 초기화
        // 토큰 상태 로드
            loadTokenStatus();
            
            // 달력 초기화
            initializeCalendar();
            
            // 변환 시작 버튼 상태 업데이트
            updateConversionButton();

            // 변환 시작 버튼 이벤트 바인딩
            const startBtn = document.getElementById('start-conversion-btn');
            if (startBtn) {
                startBtn.addEventListener('click', startConversion);
            }
            
            // VIP 정보 가져오기 버튼 이벤트 바인딩
            const vipBtn = document.getElementById('get-user-info-btn');
            if (vipBtn) {
                // 여러 이벤트 타입으로 바인딩
                vipBtn.addEventListener('click', function(e) {
                    console.log('🎯 VIP 버튼 클릭 이벤트 발생!', e);
                    getUserInfo();
                });
                
                vipBtn.addEventListener('mousedown', function(e) {
                    console.log('🎯 VIP 버튼 마우스다운 이벤트 발생!', e);
                });
                
                vipBtn.addEventListener('mouseup', function(e) {
                    console.log('🎯 VIP 버튼 마우스업 이벤트 발생!', e);
                });
                
                // 버튼 상태 확인
                console.log('✅ VIP 버튼 이벤트 리스너 바인딩 완료');
                console.log('🔍 VIP 버튼 상태:', {
                    disabled: vipBtn.disabled,
                    style: vipBtn.style.cssText,
                    computedStyle: window.getComputedStyle(vipBtn).pointerEvents
                });
            } else {
                console.error('❌ VIP 버튼을 찾을 수 없습니다');
            }

            // VIP 안내 토스트 표시 로직
            initVipToast();

            // 토큰 상태 로드
            async function loadTokenStatus() {
            console.log('🔍 토큰 상태 로드 시작...');
            console.log('🔍 현재 쿠키:', document.cookie);
            
            try {
                const response = await fetch('/api/token-status', {
                    method: 'GET',
                    credentials: 'same-origin',  // 쿠키 포함하여 요청
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                console.log('🔍 토큰 상태 응답:', response.status, response.statusText);

                // 비로그인 상태 처리: VIP 버튼에 로그인 유도 및 리다이렉트 바인딩
                if (response.status === 401) {
                    const vipBtn = document.getElementById('get-user-info-btn');
                    if (vipBtn) {
                        vipBtn.innerHTML = '로그인이 필요합니다';
                        vipBtn.title = '클릭하면 로그인 페이지로 이동합니다';
                        vipBtn.disabled = false;
                        vipBtn.onclick = () => { window.location.href = '/login'; };
                    }
                    // 기본값 표시
                    document.getElementById('total-granted').textContent = '0';
                    document.getElementById('total-used').textContent = '0';
                    document.getElementById('available-tokens').textContent = '0';
                    return; // JSON 파싱 없이 종료
                }
                
                const data = await response.json();
                console.log('🔍 토큰 상태 데이터:', data);
                
                if (data.success) {
                    const tokenData = data.data;
                    console.log('✅ 토큰 상태 로드 성공:', tokenData);
                    document.getElementById('total-granted').textContent = tokenData.total_granted;
                    document.getElementById('total-used').textContent = tokenData.total_used;
                    document.getElementById('available-tokens').textContent = tokenData.available_tokens;
                } else {
                    console.error('❌ 토큰 상태 로드 실패:', data.message);
                    // 기본값 설정
                    document.getElementById('total-granted').textContent = '0';
                    document.getElementById('total-used').textContent = '0';
                    document.getElementById('available-tokens').textContent = '0';
                }
            } catch (error) {
                console.error('❌ 토큰 상태 로드 오류:', error);
                // 기본값 설정
                document.getElementById('total-granted').textContent = '0';
                document.getElementById('total-used').textContent = '0';
                document.getElementById('available-tokens').textContent = '0';
            }
        }
        
        // 변환 시작: 파일 업로드 + 공급받는자 정보 추출 + 템플릿 기입
        async function startConversion() {
            const startBtn = document.getElementById('start-conversion-btn');
            const templateSelect = document.getElementById('templateSelect');
            const fileNameInput = document.getElementById('taxFileName');
            const selectedDateDisplay = document.getElementById('selectedDateDisplay');
            const logEl = document.getElementById('status-log');
            const progress = document.getElementById('progress-bar');
            const steps = [
                document.querySelector('.step-1'),
                document.querySelector('.step-2'),
                document.querySelector('.step-3'),
                document.querySelector('.step-4'),
                document.querySelector('.step-5')
            ];
            const downloadLink = document.getElementById('download-link');

            const templateId = templateSelect?.value || 'hometax_official';
            const fileName = fileNameInput?.value?.trim();
            const issueText = selectedDateDisplay?.textContent?.trim();

            if (!issueText || issueText.includes('선택')) {
                alert('전자세금일자를 먼저 선택하세요.');
                return;
            }
            if (!fileName) {
                alert('전자세금계산서 파일명을 입력하세요.');
                return;
            }

            // 파일 업로드 확인
            const fileInput = document.getElementById('fileInput');
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                alert('로하VIP 회원님 첨부파일을 업로드해주세요.');
                return;
            }

            // 초기화
            function setStep(idx, text, pct) {
                steps.forEach((s, i) => {
                    s.style.background = i === idx ? 'linear-gradient(135deg,#ecfeff,#cffafe)' : '#fff';
                    s.style.borderColor = i <= idx ? '#06b6d4' : 'var(--border)';
                    s.style.color = i === idx ? '#0e7490' : 'inherit';
                });
                // 애니메이션 레이어를 지우지 않도록 상태 텍스트만 갱신
                const statusText = document.getElementById('status-text');
                if (statusText) statusText.textContent = text;
                if (progress) progress.style.width = pct + '%';
            }

            // 로딩 상태
            startBtn.disabled = true;
            const originalText = startBtn.textContent;
            startBtn.textContent = '처리 중...';
            setStep(0, '📁 파일 업로드 중입니다', 10);
            // 데이터 스트림 애니메이션 시작
            const stream = document.querySelector('#status-log .data-stream-visual');
            if (stream) { stream.classList.add('active'); stream.style.display = 'block'; }

            try {
                // 1) 파일 업로드 및 파싱
                await new Promise(r => setTimeout(r, 150));
                setStep(1, '🔍 공급받는자 정보 추출 중입니다', 35);

                // FormData 생성
                const formData = new FormData();
                formData.append('template_id', templateId);
                formData.append('issue_date', issueText);
                formData.append('file_name', fileName);
                formData.append('file', fileInput.files[0]);
                formData.append('industry_type', 'delivery'); // 항상 배달대행으로 고정
                formData.append('guidelines', JSON.stringify({
                    name: '로하VIP 회원님 첨부파일 변환 서비스',
                    description: '모든 사용자 대상 통합 변환 서비스',
                    status: 'ready'
                }));
                formData.append('csrf_token', document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '');

                // 골드 회원 전용: 선택된 고객이 있으면 함께 전송
                if (window.__selectedGoldCustomer && window.__selectedGoldCustomer.id) {
                    formData.append('selectedCustomerId', String(window.__selectedGoldCustomer.id));
                }

                // 네트워크 일시 오류(재시작/재로딩 타이밍) 흡수를 위한 1회 자동 재시도
                async function retryFetch(url, options, retries = 1, delayMs = 400) {
                    for (let attempt = 0; attempt <= retries; attempt++) {
                        try {
                            return await fetch(url, options);
                        } catch (e) {
                            // 브라우저 네트워크 레벨 오류만 재시도
                            if (attempt < retries && (e && e.name === 'TypeError')) {
                                await new Promise(r => setTimeout(r, delayMs));
                                continue;
                            }
                            throw e;
                        }
                    }
                }

                const res = await retryFetch('/api/convert/start', {
                    method: 'POST',
                    body: formData
                }, 1, 500);

                // 서버가 HTML(500 에러 페이지) 또는 빈 응답을 돌려주는 경우를 대비해 안전 파싱
                let data;
                try {
                    const ct = res.headers.get('content-type') || '';
                    if (ct.includes('application/json')) {
                        data = await res.json();
                    } else {
                        const text = await res.text();
                        // JSON 형태 문자열인지 한 번 더 확인
                        try {
                            data = JSON.parse(text);
                        } catch (_) {
                            throw new Error(text || '서버에서 알 수 없는 응답이 반환되었습니다');
                        }
                    }
                } catch (parseErr) {
                    console.error('응답 파싱 실패:', parseErr);
                    alert((parseErr && parseErr.message ? parseErr.message : '요청 처리 중 오류가 발생했습니다.')
                          .toString()
                          .slice(0, 300));
                    if (stream) { stream.classList.remove('active'); stream.style.display = 'none'; }
                    return;
                }

                if (!res.ok || !data.success) {
                    // 토큰 부족 알림인 경우 모달 표시
                    if (data && data.data && data.data.shortage !== undefined) {
                        TokenAlertModal.show({
                            template_count: data.data.template_count || 0,
                            required_tokens: data.data.required_tokens || 0,
                            available_tokens: data.data.available_tokens || 0,
                            shortage: data.data.shortage || 0
                        });
                    } else {
                        // 기타 오류: 서버 메시지 또는 HTTP 상태 텍스트 노출
                        const serverMsg = (data && (data.message || data.error)) || res.statusText || '변환 시작 실패';
                        alert(String(serverMsg).slice(0, 300));
                    }
                    if (stream) { stream.classList.remove('active'); stream.style.display = 'none'; }
                    return;
                }

                // 2) 금액 정보 추출
                setStep(2, '💰 금액 정보 추출 중입니다', 60);
                await new Promise(r => setTimeout(r, 150));

                // 3) 홈텍스 템플릿 기입
                setStep(3, '📝 홈텍스 템플릿에 데이터 기입 중입니다', 82);
                await new Promise(r => setTimeout(r, 120));

                // 토큰 상태 반영
                loadTokenStatus();

                // 4) 완료
                setStep(4, '✅ 변환 완료! 다운로드 준비되었습니다', 100);
                if (downloadLink) {
                    downloadLink.style.opacity = '1';
                    downloadLink.style.pointerEvents = 'auto';
                    const modeSel = document.getElementById('downloadMode');
                    const mode = modeSel ? (modeSel.value || 'manual') : 'manual';
                    
                    // 결과 파일 개수에 따라 기본 파일명 결정 (1개면 단일 파일명, 여러 개면 ZIP)
                    const filesArr = (data && data.data && data.data.conversion_result && Array.isArray(data.data.conversion_result.files)) ? data.data.conversion_result.files : [];
                    
                    // 사용자 입력 파일명을 쿼리 파라미터로 전달 (백엔드 대비용)
                    const userFileInput = document.getElementById('taxFileName');
                    let userFileName = (userFileInput && userFileInput.value && userFileInput.value.trim()) || '';
                    if (userFileName) {
                        // Windows 금지 문자 제거
                        userFileName = userFileName.replace(/[\\/:*?"<>|]/g, '').trim();
                        if (filesArr.length > 1) {
                            if (!/\.(zip)$/i.test(userFileName)) userFileName += '.zip';
                        } else {
                            if (!/\.(xlsx|xlsm|xls)$/i.test(userFileName)) userFileName += '.xlsx';
                        }
                    }
                    const filenameParam = userFileName ? `&filename=${encodeURIComponent(userFileName)}` : '';
                    const dlUrl = (data.data.download_url || '/api/convert/download') + `?mode=${encodeURIComponent(mode)}${filenameParam}&_=` + Date.now();
                    
                    // 다운로드 링크가 보이도록 자동 스크롤 (smooth 스크롤)
                    setTimeout(() => {
                        downloadLink.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 300);

                    // 결과 파일 개수에 따라 기본 파일명 결정 (1개면 단일 파일명, 여러 개면 ZIP)
                    let dlName = filesArr.length > 1 ? '홈텍스_일괄등록_파일들.zip' : '홈텍스_일괄등록.xlsx';
                    if (filesArr.length === 1) {
                        const onlyPath = filesArr[0] || '';
                        dlName = (onlyPath.split(/\\|\//).pop()) || '홈텍스_일괄등록.xlsx';
                    }

                    // 사용자가 입력한 파일명 우선 적용 (여러 파일이면 .zip, 단일이면 .xlsx 권장)
                    if (userFileName) {
                        dlName = userFileName;
                    }

                    downloadLink.setAttribute('href', dlUrl);
                    downloadLink.setAttribute('download', dlName);
                    downloadLink.setAttribute('title', dlName);
                    // 다운로드 클릭 후 페이지 리셋(새로고침)로 초기 상태로 복원
                    try {
                        downloadLink.addEventListener('click', function onDl(){
                            // 다운로드 시작 여유를 주고 새로고침
                            setTimeout(() => { window.location.reload(); }, 800);
                            // 한 번만 동작하도록 제거
                            downloadLink.removeEventListener('click', onDl);
                        });
                    } catch(_) {}

                    // 변환 결과 표시 (상세한 결과 화면)
                    if (data.data.conversion_result) {
                        const result = data.data.conversion_result;
                        const extractionSummary = result.extraction_summary || {};
                        const files = result.files || [];
                        
                        // 파일 정보 생성
                        let fileInfo = '';
                        if (files.length === 1) {
                            const fileName = files[0].split(/\\|\//).pop() || '홈텍스_일괄등록.xlsx';
                            fileInfo = `
                                <div style="margin: 8px 0; padding: 8px; background: #ecfdf5; border-radius: 6px; border-left: 3px solid #10b981;">
                                    <strong>📄 생성된 파일:</strong> ${fileName}
                                </div>
                            `;
                        } else if (files.length > 1) {
                            fileInfo = `
                                <div style="margin: 8px 0; padding: 8px; background: #fef3c7; border-radius: 6px; border-left: 3px solid #f59e0b;">
                                    <strong>📦 생성된 파일:</strong> ${files.length}개 (ZIP으로 다운로드)
                                </div>
                            `;
                        }
                        
                        logEl.innerHTML = `
                            <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; border-left: 5px solid #06b6d4; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                                    <span style="font-size: 1.5rem; margin-right: 8px;">🎉</span>
                                    <strong style="font-size: 1.1rem; color: #0e7490;">변환 완료!</strong>
                                </div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                                    <div style="padding: 10px; background: white; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                        <div style="font-size: 1.5rem; color: #059669; font-weight: bold;">${result.total_recipients || 0}</div>
                                        <div style="font-size: 0.9rem; color: #6b7280;">총 공급받는자</div>
                                    </div>
                                    <div style="padding: 10px; background: white; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                        <div style="font-size: 1.5rem; color: #dc2626; font-weight: bold;">${Math.round((extractionSummary.extraction_rate || 0) * 100)}%</div>
                                        <div style="font-size: 0.9rem; color: #6b7280;">추출 성공률</div>
                                    </div>
                                </div>
                                
                                ${fileInfo}
                                
                                <div style="margin-top: 12px; padding: 10px; background: rgba(255,255,255,0.7); border-radius: 8px;">
                                    <div style="font-size: 0.9rem; color: #374151; margin-bottom: 6px;">
                                        <strong>📊 상세 통계:</strong>
                                    </div>
                                    <div style="font-size: 0.85rem; color: #6b7280; line-height: 1.4;">
                                        • 성공적으로 추출된 공급받는자: ${result.total_recipients || 0}건<br>
                                        • 추출 실패: ${extractionSummary.failed_extractions || 0}건<br>
                                        • 처리된 행 수: ${extractionSummary.total_rows_processed || 0}행<br>
                                        • 생성된 파일 수: ${files.length}개
                                    </div>
                                </div>
                                
                                <!-- 🎯 로.하 TAX 자동 수정 시스템 강조 -->
                                ${data.data.detailed_stats ? `
                                <div style="margin-top: 12px; padding: 12px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 8px; border: 2px solid #f59e0b;">
                                    <div style="font-size: 0.9rem; color: #92400e; font-weight: 700; margin-bottom: 8px;">
                                        🎯 로.하 TAX 자동 수정 시스템
                                    </div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                                        <div style="padding: 8px; background: white; border-radius: 6px; border-left: 4px solid #f59e0b;">
                                            <div style="font-size: 0.85rem; color: #92400e; font-weight: 600;">
                                                이메일 자동 수정: ${(() => {
                                                    const count = data.data.detailed_stats.email_auto_fixed_count || 0;
                                                    if (count === 0) return '0건';
                                                    if (count === 1) return '1건';
                                                    if (count === 2) return '2건';
                                                    if (count === 3) return '3건';
                                                    return `그외 ${count}건`;
                                                })()}
                                            </div>
                                            ${(() => {
                                                const s = data.data.detailed_stats;
                                                const c = s.email_auto_fixed_count || 0;
                                                const fromV = s.email_auto_fixed_sample_from;
                                                const toV = s.email_auto_fixed_sample_to;
                                                if (c > 0 && fromV && toV) {
                                                    return `<div style=\"font-size: 0.75rem; color: #a16207; margin-top: 2px;\">(예시) ${fromV} → ${toV}</div>`;
                                                }
                                                return '';
                                            })()}
                                        </div>
                                        <div style="padding: 8px; background: white; border-radius: 6px; border-left: 4px solid #f59e0b;">
                                            <div style="font-size: 0.85rem; color: #92400e; font-weight: 600;">
                                                사업자번호 자동 수정: ${(() => {
                                                    const count = data.data.detailed_stats.business_number_auto_fixed_count || 0;
                                                    if (count === 0) return '0건';
                                                    if (count === 1) return '1건';
                                                    if (count === 2) return '2건';
                                                    if (count === 3) return '3건';
                                                    return `그외 ${count}건`;
                                                })()}
                                            </div>
                                            ${(() => {
                                                const s = data.data.detailed_stats;
                                                const c = s.business_number_auto_fixed_count || 0;
                                                const fromV = s.business_auto_fixed_sample_from;
                                                const toV = s.business_auto_fixed_sample_to;
                                                if (c > 0 && fromV && toV) {
                                                    return `<div style=\"font-size: 0.75rem; color: #a16207; margin-top: 2px;\">(예시) ${fromV} → ${toV}</div>`;
                                                }
                                                return '';
                                            })()}
                                        </div>
                                    </div>
                                    <div style="font-size: 0.8rem; color: #92400e; font-weight: 500;">
                                        💡 로.하 TAX가 VIP 회원님의 실수를 자동으로 감지하고 수정해드렸습니다!
                                    </div>
                                </div>
                                ` : ''}
                                
                                <!-- 세액 관련 통계 제거 (사용자 요청) -->
                                <!-- 💰 세액 분석 결과는 제거됨 -->
                                
                                <!-- 성능 통계 -->
                                ${data.data.detailed_stats ? `
                                <div style="margin-top: 12px; padding: 10px; background: rgba(255,255,255,0.7); border-radius: 8px;">
                                    <div style="font-size: 0.9rem; color: #374151; margin-bottom: 6px;">
                                        <strong>⚡ 처리 성능 분석:</strong>
                                    </div>
                                    <div style="font-size: 0.85rem; color: #6b7280; line-height: 1.4;">
                                        • 처리 소요 시간: ${data.data.detailed_stats.processing_time || 0}초<br>
                                        • 초당 처리 건수: ${data.data.detailed_stats.per_second || 0}건/초<br>
                                        • 완벽한 데이터 품질: ${data.data.detailed_stats.perfect_info_count || 0}건
                                    </div>
                                </div>
                                ` : ''}
                                
                                <div style="margin-top: 12px; padding: 8px; background: rgba(6, 182, 212, 0.1); border-radius: 6px; text-align: center;">
                                    <span style="font-size: 0.9rem; color: #0e7490; font-weight: 500;">
                                        💡 변환된 파일이 준비되었습니다. 아래 "다운로드" 버튼을 클릭해 저장하세요.
                                    </span>
                                </div>
                            </div>
                        `;
                    }
                }
                    // 안전 가드: 응답에서 다운로드 URL/파일명 추출 (없으면 기본값)
                    const dlUrl = (data && data.data && typeof data.data.download_url === 'string' && data.data.download_url) ? data.data.download_url : '#';
                    const dlName = (data && data.data && typeof data.data.download_filename === 'string' && data.data.download_filename) ? data.data.download_filename : '세금계산서.xlsx';

                    // 자동 다운로드를 비활성화하고, 사용자가 다운로드 링크를 클릭하도록 유도
                    if (stream) { stream.classList.remove('active'); stream.style.display = 'none'; }

                // 향후 구현 예정 기능:
                // 1. 실제 파일 생성 및 다운로드 기능 구현
                // 2. 파일 변환 상태 실시간 모니터링
                // 3. 변환 결과 미리보기 기능
                // 4. 변환 히스토리 저장 및 관리
                // 5. 사용자별 변환 설정 저장
            } catch (e) {
                console.error('변환 요청 실패:', e);
                const msg = (e && e.message ? e.message : e);
                alert(String(msg).slice(0, 300));
                if (stream) { stream.classList.remove('active'); stream.style.display = 'none'; }
            } finally {
                startBtn.disabled = false;
                startBtn.textContent = originalText;
            }
        }

        // VIP 토스트 초기화: VIP일 때만 1회 노출
        async function initVipToast(){
            try{
                // url 강제 노출 플래그
                const forceVip = new URLSearchParams(location.search).get('vip') === '1';
                if (!forceVip && sessionStorage.getItem('vipToastSeen') === '1') return;
                const res = await fetch('/api/user-info',{method:'GET',credentials:'same-origin',headers:{'Content-Type':'application/json'}});
                if (!res.ok) return;
                const data = await res.json();
                if (!data.success) return;
                const user = data.data && data.data.user;
                if (!forceVip && (!user || (user.plan_type||'').toLowerCase() !== 'vip')) return;
                const toast = document.getElementById('vip-toast');
                const btn = document.getElementById('vipToastConfirm');
                if (toast){ toast.style.display='block'; }
                if (btn){
                    btn.addEventListener('click', function(){
                        if (!forceVip) sessionStorage.setItem('vipToastSeen','1');
                        if (toast) toast.style.display='none';
                    });
                }
            }catch(e){ console.warn('VIP 토스트 초기화 실패', e); }
        }

        // 파일명 입력 수동 수정 감지
        (function(){
            const nameInput = document.getElementById('taxFileName');
            if (nameInput){
                nameInput.addEventListener('input', function(){
                    this.dataset.userEdited = '1';
                });
            }
        })();

        // 파일 선택 이벤트 처리
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            const label = document.querySelector('.file-input-label');
            
            if (file) {
                // 파일이 선택된 경우
                label.innerHTML = `
                    <div class="file-input-icon">✅</div>
                    <div class="file-input-text">${file.name}</div>
                    <div class="file-input-hint">파일 크기: ${(file.size / 1024 / 1024).toFixed(2)}MB</div>
                `;
                label.style.borderColor = '#10b981';
                label.style.background = 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)';
                

                // 업로드 헤더 대조(✓/?/✗) 자동 갱신: 1행 헤더 추출 후 전달
                try{
                    if (typeof updateVipHeaderComparison === 'function'){
                        const name = (file.name || '').toLowerCase();
                        if (name.endsWith('.csv')){
                            const reader = new FileReader();
                            reader.onload = function(ev){
                                try{
                                    const text = ev.target && ev.target.result ? String(ev.target.result) : '';
                                    const firstLine = (text.split(/\r?\n/)[0] || '').trim();
                                    const headers = firstLine ? firstLine.split(',').map(s=>s.trim()) : [];
                                    if (headers.length){ updateVipHeaderComparison(headers); }
                                }catch(_){/* noop */}
                            };
                            reader.readAsText(file);
                        } else if (name.endsWith('.xlsx') || name.endsWith('.xls')){
                            // XLSX 라이브러리가 로드되어 있을 때만 사용
                            if (window.XLSX){
                                const r = new FileReader();
                                r.onload = function(ev){
                                    try{
                                        const data = new Uint8Array(ev.target.result);
                                        const wb = XLSX.read(data, {type:'array'});
                                        const firstSheet = wb.SheetNames && wb.SheetNames[0];
                                        if (!firstSheet) return;
                                        const ws = wb.Sheets[firstSheet];
                                        const range = XLSX.utils.decode_range(ws['!ref']);
                                        const headers = [];
                                        for (let C = range.s.c; C <= range.e.c; C++){
                                            const cellAddress = XLSX.utils.encode_cell({r: range.s.r, c: C});
                                            const cell = ws[cellAddress];
                                            headers.push(cell ? String(cell.v).trim() : '');
                                        }
                                        if (headers.length){ updateVipHeaderComparison(headers); }
                                    }catch(_){/* noop */}
                                };
                                r.readAsArrayBuffer(file);
                            }
                        }
                    }
                }catch(_){/* noop */}
            } else {
                // 파일이 선택되지 않은 경우 원래 상태로 복원
                label.innerHTML = `
                    <div class="file-input-icon">📄</div>
                    <div class="file-input-text">파일 선택하기</div>
                    <div class="file-input-hint">클릭하여 파일을 선택하거나 드래그하여 놓으세요</div>
                `;
                label.style.borderColor = '';
                label.style.background = '';
            }
        });
        
        // 드래그 앤 드롭 기능
        const fileLabel = document.querySelector('.file-input-label');
        
        fileLabel.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = '#5865f2';
            this.style.background = 'linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%)';
        });
        
        fileLabel.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.background = '';
        });
        
        fileLabel.addEventListener('drop', function(e) {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('fileInput').files = files;
                // 파일 선택 이벤트 트리거 (자동 감지 포함)
                document.getElementById('fileInput').dispatchEvent(new Event('change'));
            }
        });
        
        // 달력 토글 함수
        function toggleCalendar() {
            const wrapper = document.getElementById('calendarWrapper');
            const footer = document.getElementById('calendarFooter');
            const icon = document.getElementById('calendarToggleIcon');
            
            if (wrapper.style.display === 'none') {
                // 달력 펼치기
                wrapper.style.display = 'block';
                footer.style.display = 'block';
                icon.classList.add('expanded');
                
                // 달력이 아직 렌더링되지 않았다면 렌더링
                if (!window.calendarInitialized) {
                    initializeCalendar();
                }
            } else {
                // 달력 접기
                wrapper.style.display = 'none';
                footer.style.display = 'none';
                icon.classList.remove('expanded');
            }
        }
        
        // 달력 초기화
        function initializeCalendar() {
            window.calendarInitialized = true;
            const currentDate = new Date();
            window.calendarState = {
                currentYear: currentDate.getFullYear(),
                currentMonth: currentDate.getMonth(),
                selectedDate: null
            };
            
            renderCalendar();
        }
        
        // 달력 렌더링
        function renderCalendar() {
            const { currentYear, currentMonth } = window.calendarState;
            const calendarGrid = document.getElementById('calendarGrid');
            const monthYear = document.getElementById('monthYear');
            
            // 월/년 표시 업데이트
            const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', 
                              '7월', '8월', '9월', '10월', '11월', '12월'];
            monthYear.textContent = `${currentYear}년 ${monthNames[currentMonth]}`;
            
            // 달력 그리드 생성
            const firstDay = new Date(currentYear, currentMonth, 1);
            const lastDay = new Date(currentYear, currentMonth + 1, 0);
            const startDate = new Date(firstDay);
            startDate.setDate(startDate.getDate() - firstDay.getDay());
            
            const dayHeaders = ['일', '월', '화', '수', '목', '금', '토'];
            let calendarHTML = '';
            
            // 요일 헤더
            dayHeaders.forEach(day => {
                calendarHTML += `<div class="calendar-day-header">${day}</div>`;
            });
            
            // 날짜 생성 (6주)
            for (let week = 0; week < 6; week++) {
                for (let day = 0; day < 7; day++) {
                    const date = new Date(startDate);
                    date.setDate(startDate.getDate() + (week * 7) + day);
                    
                    const dayNumber = date.getDate();
                    const isCurrentMonth = date.getMonth() === currentMonth;
                    const isToday = isTodayDate(date);
                    const isSelected = window.calendarState.selectedDate && 
                                     isSameDate(date, window.calendarState.selectedDate);
                    
                    let className = 'calendar-day';
                    if (!isCurrentMonth) className += ' other-month';
                    if (isToday) className += ' today';
                    if (isSelected) className += ' selected';
                    
                    calendarHTML += `
                        <div class="${className}" 
                             onclick="selectDate(${date.getFullYear()}, ${date.getMonth()}, ${dayNumber})"
                             data-year="${date.getFullYear()}"
                             data-month="${date.getMonth()}"
                             data-day="${dayNumber}">
                            ${dayNumber}
                        </div>
                    `;
                }
            }
            
            calendarGrid.innerHTML = calendarHTML;
        }
        
        // 월 변경
        function changeMonth(direction) {
            window.calendarState.currentMonth += direction;
            
            if (window.calendarState.currentMonth < 0) {
                window.calendarState.currentMonth = 11;
                window.calendarState.currentYear--;
            } else if (window.calendarState.currentMonth > 11) {
                window.calendarState.currentMonth = 0;
                window.calendarState.currentYear++;
            }
            
            renderCalendar();
        }
        
        // 날짜 선택
        function selectDate(year, month, day) {
            window.calendarState.selectedDate = new Date(year, month, day);
            
            // 선택된 날짜 표시 업데이트 (새로운 형식: 25년10월01일)
            const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', 
                              '7월', '8월', '9월', '10월', '11월', '12월'];
            const selectedDateDisplay = document.getElementById('selectedDateDisplay');
            const selectedDateText = document.getElementById('selectedDateText');
            
            // 년도 2자리로 변환 (2025 -> 25)
            const shortYear = year.toString().slice(-2);
            
            // 표시 형식: 25년10월01일
            selectedDateDisplay.textContent = `${shortYear}년${monthNames[month]}${String(day).padStart(2, '0')}일`;
            selectedDateText.textContent = `${shortYear}년 ${monthNames[month]} ${String(day).padStart(2, '0')}일 전자세금계산서 발행일`;
            
            // 파일명 자동 업데이트 (기입 형식: 251001)
            const taxFileName = document.getElementById('taxFileName');
            const formattedDate = `${shortYear}${String(month + 1).padStart(2, '0')}${String(day).padStart(2, '0')}`;
            // 사용자가 직접 수정한 경우 덮어쓰지 않음
            const userEdited = taxFileName && taxFileName.dataset && taxFileName.dataset.userEdited === '1';
            const autoPattern = /^세금계산서_\d{6}\.xlsx$/;
            if (taxFileName && (!userEdited && (!taxFileName.value || autoPattern.test(taxFileName.value)))) {
                taxFileName.value = `세금계산서_${formattedDate}.xlsx`;
            }
            
            // 달력 다시 렌더링
            renderCalendar();
            
            // 날짜 선택 후 달력 자동 접기
            setTimeout(() => {
                toggleCalendar();
            }, 300);
        }
        
        // 오늘 날짜 확인
        function isTodayDate(date) {
            const today = new Date();
            return date.getFullYear() === today.getFullYear() &&
                   date.getMonth() === today.getMonth() &&
                   date.getDate() === today.getDate();
        }
        
        // 같은 날짜 확인
        function isSameDate(date1, date2) {
            return date1.getFullYear() === date2.getFullYear() &&
                   date1.getMonth() === date2.getMonth() &&
                   date1.getDate() === date2.getDate();
        }
        
        // 토큰 사용 함수 (변환 작업 시 호출)
        async function useToken(tokens = 1) {
            try {
                const response = await fetch('/api/use-token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
                    },
                    body: JSON.stringify({ tokens: tokens })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // 토큰 상태 새로고침
                    loadTokenStatus();
                    return true;
                } else {
                    alert('토큰 사용 실패: ' + data.message);
                    return false;
                }
            } catch (error) {
                console.error('토큰 사용 오류:', error);
                alert('토큰 사용 중 오류가 발생했습니다.');
                return false;
            }
        }
        
        // VIP 유저정보 가져오기 함수 (최고급 퀄리티)
        async function getUserInfo() {
            console.log('🚀 VIP 정보 가져오기 함수 시작');
            const btn = document.getElementById('get-user-info-btn');
            const userInfoBox = document.getElementById('user-info-box');
            const userInfoContent = document.getElementById('user-info-content');
            
            console.log('🔍 버튼 요소:', btn);
            console.log('🔍 사용자 정보 박스:', userInfoBox);
            
            // 버튼 로딩 상태 (최고급 애니메이션)
            btn.innerHTML = `
                <div class="btn-content">
                    <div class="btn-icon" style="animation: spin 1s linear infinite;">⏳</div>
                    <div class="btn-text">정보 로딩 중...</div>
                    <div class="btn-subtitle">잠시만 기다려주세요</div>
                </div>
            `;
            btn.disabled = true;
            
            try {
                console.log('유저정보 요청 시작...');
                
                const response = await fetch('/api/user-info', {
                    method: 'GET',
                    credentials: 'same-origin',  // 쿠키 포함하여 요청
                    headers: {
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
                        'Content-Type': 'application/json'
                    }
                });
                
                console.log('응답 상태:', response.status, response.statusText);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('응답 데이터:', data);
                
                if (data.success) {
                    const user = data.data.user;
                    
                    // 성공 애니메이션
                    btn.innerHTML = `
                        <div class="btn-content">
                            <div class="btn-icon" style="animation: bounce 0.6s ease;">✅</div>
                            <div class="btn-text">정보 로드 완료!</div>
                            <div class="btn-subtitle">클릭하여 확인하세요</div>
                        </div>
                    `;
                    
                    // 유저정보 HTML 생성 (최고급 스타일)
                    const userInfoHTML = `
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>🏢 회사명:</strong> <span style="color:#000000;font-weight:600;">${user.company_name || '-'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>👤 대표자:</strong> <span style="color:#000000;font-weight:600;">${user.representative_name || '-'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>📋 사업자번호:</strong> <span style="color:#000000;font-weight:600;">${user.business_number || '-'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>📧 이메일:</strong> <span style="color:#000000;font-weight:600;">${user.email || '-'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>📱 전화번호:</strong> <span style="color:#000000;font-weight:600;">${user.phone || '-'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>🏭 업태:</strong> <span style="color:#000000;font-weight:600;">${user.business_type || '-'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>📊 종목:</strong> <span style="color:#000000;font-weight:600;">${user.business_category || '-'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>🎫 권한:</strong> <span style="color:#fbbf24;font-weight:700;text-transform:uppercase;">${user.plan_type || 'free'}</span>
                        </div>
                        <div style="margin-bottom:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>📅 가입일:</strong> <span style="color:#84cc16;font-weight:600;">${user.created_at ? new Date(user.created_at).toLocaleDateString('ko-KR') : '-'}</span>
                        </div>
                        <div style="margin-bottom:0;padding:8px;background:rgba(255,255,255,0.1);border-radius:8px;">
                            <strong>✅ 상태:</strong> <span style="color:#10b981;font-weight:700;">${user.is_active ? '활성' : '비활성'}</span>
                        </div>
                    `;
                    
                    userInfoContent.innerHTML = userInfoHTML;
                    userInfoBox.style.display = 'block';
                    
                    // 유저정보 박스 등장 애니메이션
                    userInfoBox.style.opacity = '0';
                    userInfoBox.style.transform = 'translateY(-20px) scale(0.9)';
                    setTimeout(() => {
                        userInfoBox.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                        userInfoBox.style.opacity = '1';
                        userInfoBox.style.transform = 'translateY(0) scale(1)';
                    }, 100);
                    
                    // 빠른 사라짐 애니메이션 (즉시 트리거, 0.3초)
                    btn.classList.add('fade-out');
                    setTimeout(() => {
                        btn.style.display = 'none';
                    }, 300);
                    
                } else {
                    // 에러 상태
                    btn.innerHTML = `
                        <div class="btn-content">
                            <div class="btn-icon" style="animation: shake 0.5s ease;">❌</div>
                            <div class="btn-text">로드 실패</div>
                            <div class="btn-subtitle">다시 시도해주세요</div>
                        </div>
                    `;
                    btn.style.background = 'linear-gradient(135deg,#ef4444,#dc2626)';
                    
                    setTimeout(() => {
                        btn.innerHTML = `
                            <div class="btn-content">
                                <div class="btn-icon">👤</div>
                                <div class="btn-text">VIP 정보 가져오기</div>
                                <div class="btn-subtitle">클릭하여 사용자 정보 확인</div>
                            </div>
                        `;
                        btn.style.background = '';
                        btn.disabled = false;
                    }, 3000);
                }
            } catch (error) {
                console.error('유저정보 가져오기 오류:', error);
                
                // 에러 상태
                btn.innerHTML = `
                    <div class="btn-content">
                        <div class="btn-icon" style="animation: shake 0.5s ease;">⚠️</div>
                        <div class="btn-text">연결 오류</div>
                        <div class="btn-subtitle">네트워크를 확인해주세요</div>
                    </div>
                `;
                btn.style.background = 'linear-gradient(135deg,#f59e0b,#d97706)';
                
                setTimeout(() => {
                    btn.innerHTML = `
                        <div class="btn-content">
                            <div class="btn-icon">👤</div>
                            <div class="btn-text">VIP 정보 가져오기</div>
                            <div class="btn-subtitle">클릭하여 사용자 정보 확인</div>
                        </div>
                    `;
                    btn.style.background = '';
                    btn.disabled = false;
                }, 3000);
            }
        }
        
        
        // 추가 애니메이션 키프레임
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-10px); }
                60% { transform: translateY(-5px); }
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                20%, 40%, 60%, 80% { transform: translateX(5px); }
            }
            
        `;
        document.head.appendChild(style);

        // ===== 골드 고객 선택 UI 로직 =====
        const openBtn = document.getElementById('load-customer-btn');
        const badge = document.getElementById('supplier-badge');
        const badgeName = document.getElementById('supplier-badge-name');
        const clearBtn = document.getElementById('clear-supplier');
        let modal = document.getElementById('gold-customer-modal');
        let closeModalBtn = document.getElementById('close-gold-modal');
        let tbody = document.getElementById('gold-customer-tbody');
        let searchInput = document.getElementById('gold-search');
        let searchBtn = document.getElementById('gold-search-btn');
        let refreshBtn = document.getElementById('refresh-gold-customers');
        let confirmBtn = document.getElementById('confirm-gold-customer');

        function ensureGoldModal(){
            if (document.getElementById('gold-customer-modal')) return;
            const html = `
            <div id="gold-customer-modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:10000;padding:2rem;">
                <div style="background:white;border-radius:12px;max-width:1200px;width:100%;margin:0 auto;max-height:85vh;overflow:auto;box-shadow:0 10px 30px rgba(0,0,0,0.15);">
                    <div style="padding:1.5rem;border-bottom:2px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;">
                        <h2 style="margin:0;color:#1f2937;">골드 고객 선택</h2>
                        <button id="close-gold-modal" type="button" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">×</button>
                    </div>
                    <div style="padding:1rem 1.5rem;border-bottom:2px solid #e5e7eb;display:flex;justify-content:flex-end;gap:8px;">
                        <button class="btn btn-secondary" id="refresh-gold-customers">새로고침</button>
                    </div>
                    <div style="overflow-x:auto;max-height:60vh;">
                        <table class="table" style="width:100%;min-width:900px;border-collapse:collapse;">
                            <thead>
                                <tr style="background:linear-gradient(135deg,#f9fafb,#f3f4f6);border-bottom:2px solid #e5e7eb;">
                                    <th style="padding:12px;text-align:left;">대표자명</th>
                                    <th style="padding:12px;text-align:left;">업체명</th>
                                    <th style="padding:12px;text-align:left;">사업자등록번호</th>
                                    <th style="padding:12px;text-align:left;">주소</th>
                                    <th style="padding:12px;text-align:left;">이메일</th>
                                    <th style="padding:12px;text-align:left;">업태</th>
                                    <th style="padding:12px;text-align:left;">종목</th>
                                    <th style="padding:12px;text-align:left;">선택</th>
                                </tr>
                            </thead>
                            <tbody id="gold-customer-tbody">
                                <tr><td colspan="8" style="text-align:center;color:#6B7280;padding:2rem;">데이터가 없습니다</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>`;
            document.body.insertAdjacentHTML('beforeend', html);
            // refresh references
            modal = document.getElementById('gold-customer-modal');
            closeModalBtn = document.getElementById('close-gold-modal');
            tbody = document.getElementById('gold-customer-tbody');
            searchInput = document.getElementById('gold-search');
            searchBtn = document.getElementById('gold-search-btn');
            refreshBtn = document.getElementById('refresh-gold-customers');
            confirmBtn = document.getElementById('confirm-gold-customer');
            if (closeModalBtn){ closeModalBtn.addEventListener('click', closeModal); }
            if (searchBtn){ /* 검색 제거됨 */ }
            if (refreshBtn){ refreshBtn.addEventListener('click', ()=> loadCustomers('')); }
        }

        function openModal(){
            ensureGoldModal();
            if (!modal) return;
            try {
                console.log('🟢 골드 모달 오픈 시도');
                modal.style.display = 'block';
                modal.style.visibility = 'visible';
                modal.style.opacity = '1';
                modal.setAttribute('aria-hidden','false');
                // 배경 스크롤 방지
                document.body.style.overflow = 'hidden';
            } catch (e) {
                console.warn('모달 오픈 처리 중 오류', e);
            }
        }
        function closeModal(){
            if (modal) modal.style.display = 'none';
            // 배경 스크롤 복원
            document.body.style.overflow = '';
        }

        function escapeHtml(str){
            return String(str).replace(/[&<>"]/g, s=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[s]));
        }

        // 서버에서 고객 목록 로드
        async function loadCustomers(q=''){
            if (!tbody) return;
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#6b7280;">불러오는 중...</td></tr>';
            try{
                const url = '/api/gold/customers' + (q? ('?search='+encodeURIComponent(q)) : '');
                const res = await fetch(url,{credentials:'same-origin'});
                const data = await res.json();
                if (!data.success){
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#ef4444;">목록을 불러올 수 없습니다</td></tr>';
                    return;
                }
                const rows = (data.data||[]).map(c=>{
                    const bn = (c.business_number||'').replace(/(\d{3})(\d{2})(\d{5})/,'$1-$2-$3');
                    let bt = c.business_type || c.biz_type || c.type || '';
                    let bc = c.business_category || c.biz_category || c.category || '';
                    if ((!bt || !bc) && c.business_kind){
                        try{
                            const kind = typeof c.business_kind === 'string' ? JSON.parse(c.business_kind) : c.business_kind;
                            bt = bt || kind.업태 || kind.business_type || kind.type || '';
                            bc = bc || kind.종목 || kind.business_category || kind.category || '';
                        }catch(_){}
                    }
                    bt = bt || '-';
                    bc = bc || '-';
                    return `<tr style="transition:background .15s;" onmouseover="this.style.background='#FAFAFB'" onmouseout="this.style.background=''">
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;">${escapeHtml(c.representative_name||'')}</td>
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;">${escapeHtml(c.company_name||'')}</td>
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;">${escapeHtml(bn)}</td>
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;">${escapeHtml(c.address||'-')}</td>
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;">${escapeHtml(c.email||'-')}</td>
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;">${escapeHtml(bt)}</td>
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;">${escapeHtml(bc)}</td>
                        <td style="padding:10px; border-bottom:1px solid #F3F4F6;"><button type="button" class="btn btn-secondary" data-id="${c.id}" data-name="${escapeHtml(c.company_name||'')}">선택</button></td>
                    </tr>`;
                }).join('');
                tbody.innerHTML = rows || '<tr><td colspan="8" style="text-align:center;color:#6b7280;">데이터가 없습니다</td></tr>';

                // 선택 버튼 바인딩
                tbody.querySelectorAll('button[data-id]').forEach(btn=>{
                    btn.addEventListener('click', function(){
                        const id = Number(this.getAttribute('data-id'));
                        const name = this.getAttribute('data-name')||'';
                        window.__selectedGoldCustomer = { id, name };
                        
                        // 배지 업데이트
                        if (badge && badgeName){
                            badgeName.textContent = name;
                            badge.style.display = 'inline-flex';
                        }
                        
                        // 공급자 패널 업데이트
                        const panel = document.getElementById('current-supplier-panel');
                        const nameEl = document.getElementById('current-supplier-name');
                        const resetBtn = document.getElementById('reset-supplier-btn');
                        if (panel && nameEl && resetBtn){
                            nameEl.textContent = name;
                            resetBtn.style.display = 'inline-block';
                        }
                        
                        closeModal();
                    });
                });
            }catch(e){
                tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#ef4444;">오류가 발생했습니다</td></tr>';
            }
        }

        // 사용자 플랜 확인하여 골드 전용 버튼 표시
        fetch('/api/user-info',{method:'GET',credentials:'same-origin'})
            .then(r=>r.json()).then(d=>{
                const plan = (d && d.data && d.data.user && (d.data.user.plan_type||'').toLowerCase()) || '';
                if (plan.includes('gold')){
                    if (openBtn) openBtn.style.display='inline-block';
                    
                    // 공급자 패널 초기화: 사용자 본인 업체명 설정
                    const user = d && d.data && d.data.user;
                    const userName = (user && user.company_name) || (user && user.username) || '내 정보';
                    const panel = document.getElementById('current-supplier-panel');
                    const nameEl = document.getElementById('current-supplier-name');
                    if (panel && nameEl){
                        panel.style.display = 'block';
                        nameEl.textContent = userName;
                        window.__defaultSupplierName = userName; // 초기값 저장
                    }
                }
            }).catch(()=>{});

        if (openBtn){
            openBtn.addEventListener('click', ()=>{
                console.log('🟢 내 고객 불러오기 버튼 클릭 (direct)');
                openModal();
                loadCustomers();
            });
        }
        // 안전 가드: 이벤트 위임으로도 처리 (동적 렌더/중복 스크립트 상황 대비)
        document.addEventListener('click', function(e){
            const trigger = e.target && (e.target.id === 'load-customer-btn' ? e.target : e.target.closest && e.target.closest('#load-customer-btn'));
            if (trigger){
                console.log('🟢 내 고객 불러오기 버튼 클릭 (delegated)');
                openModal();
                loadCustomers();
            }
        });
        if (closeModalBtn){
            closeModalBtn.addEventListener('click', ()=>{
                console.log('🔴 골드 모달 닫기');
                closeModal();
            });
        }
        if (searchBtn){ /* 검색 제거됨 */ }
        if (refreshBtn){ refreshBtn.addEventListener('click', ()=> loadCustomers('')); }
        // 공급자를 본인 정보로 복원하는 공통 함수
        function resetToMyInfo(){
            // 선택된 고객 초기화
            window.__selectedGoldCustomer = null;
            // 배지 숨김
            if (badge) badge.style.display = 'none';
            // 패널 복원
            const nameEl = document.getElementById('current-supplier-name');
            const resetBtn = document.getElementById('reset-supplier-btn');
            if (nameEl && window.__defaultSupplierName){
                nameEl.textContent = window.__defaultSupplierName;
            }
            if (resetBtn){ resetBtn.style.display = 'none'; }
        }

        if (clearBtn){
            clearBtn.addEventListener('click', resetToMyInfo);
        }
        
        // "내 정보로 전환" 버튼 이벤트
        const resetSupplierBtn = document.getElementById('reset-supplier-btn');
        if (resetSupplierBtn){
            resetSupplierBtn.addEventListener('click', resetToMyInfo);
        }

        // 전역 스코프에 노출 (HTML onclick에서 호출)
        window.toggleCalendar = toggleCalendar;
        window.changeMonth = changeMonth;
        window.selectDate = selectDate;
});
