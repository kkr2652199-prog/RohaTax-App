/**
 * Admin Dashboard 유틸리티 함수 모음
 * 
 * 이 파일은 admin.html에서 분리된 독립적인 유틸리티 함수들을 포함합니다.
 */

/**
 * 마지막 업데이트 시간을 콘솔에 출력
 * 대시보드 새로고침 시 호출되어 현재 시간을 로깅합니다.
 */
function updateLastRefreshTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ko-KR');
    console.log(`🔄 대시보드 업데이트: ${timeString}`);
}

/**
 * 파일 다운로드 기능
 * 현재는 placeholder로 구현되어 있으며, 추후 실제 다운로드 로직이 추가될 예정입니다.
 * 
 * @param {string} filename - 다운로드할 파일명
 */
function downloadFile(filename) {
    // 파일 다운로드 로직 (추후 구현)
    console.log('파일 다운로드:', filename);
}

