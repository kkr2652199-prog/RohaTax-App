// 브라우저 콘솔에서 실행할 토큰 API 테스트 스크립트

// 1. 토큰 상태 조회 API 테스트
async function testTokenStatus() {
    try {
        const response = await fetch('/api/token-status', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        console.log('=== /api/token-status API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
            
            // timestamp 필드 확인
            if ('timestamp' in data.data) {
                console.log('\n✅ timestamp 필드가 정상적으로 포함되어 있습니다!');
                console.log(`   timestamp 값: ${data.data.timestamp}`);
            } else {
                console.log('\n❌ timestamp 필드가 누락되었습니다!');
            }
            
            // 필수 필드 확인
            const requiredFields = ['total_granted', 'total_used', 'available_tokens', 'timestamp'];
            const missingFields = requiredFields.filter(field => !(field in data.data));
            
            if (missingFields.length === 0) {
                console.log('\n✅ 모든 필수 필드가 정상적으로 포함되어 있습니다!');
            } else {
                console.log('\n❌ 누락된 필드:', missingFields);
            }
        } else {
            console.log('\n❌ API 호출 실패:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 2. 토큰 사용 API 테스트 (실제 사용은 하지 않고 요청 형식만 확인)
async function testUseToken() {
    try {
        const response = await fetch('/api/use-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ tokens: 1 })
        });
        
        const data = await response.json();
        
        console.log('\n=== /api/use-token API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
        } else {
            console.log('\n⚠️ API 응답:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 테스트 실행
console.log('🚀 토큰 API 테스트 시작...\n');
testTokenStatus().then(() => {
    console.log('\n');
    // testUseToken(); // 실제 토큰 사용을 원하지 않으면 주석 처리
});



// 1. 토큰 상태 조회 API 테스트
async function testTokenStatus() {
    try {
        const response = await fetch('/api/token-status', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        console.log('=== /api/token-status API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
            
            // timestamp 필드 확인
            if ('timestamp' in data.data) {
                console.log('\n✅ timestamp 필드가 정상적으로 포함되어 있습니다!');
                console.log(`   timestamp 값: ${data.data.timestamp}`);
            } else {
                console.log('\n❌ timestamp 필드가 누락되었습니다!');
            }
            
            // 필수 필드 확인
            const requiredFields = ['total_granted', 'total_used', 'available_tokens', 'timestamp'];
            const missingFields = requiredFields.filter(field => !(field in data.data));
            
            if (missingFields.length === 0) {
                console.log('\n✅ 모든 필수 필드가 정상적으로 포함되어 있습니다!');
            } else {
                console.log('\n❌ 누락된 필드:', missingFields);
            }
        } else {
            console.log('\n❌ API 호출 실패:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 2. 토큰 사용 API 테스트 (실제 사용은 하지 않고 요청 형식만 확인)
async function testUseToken() {
    try {
        const response = await fetch('/api/use-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ tokens: 1 })
        });
        
        const data = await response.json();
        
        console.log('\n=== /api/use-token API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
        } else {
            console.log('\n⚠️ API 응답:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 테스트 실행
console.log('🚀 토큰 API 테스트 시작...\n');
testTokenStatus().then(() => {
    console.log('\n');
    // testUseToken(); // 실제 토큰 사용을 원하지 않으면 주석 처리
});



// 1. 토큰 상태 조회 API 테스트
async function testTokenStatus() {
    try {
        const response = await fetch('/api/token-status', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        console.log('=== /api/token-status API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
            
            // timestamp 필드 확인
            if ('timestamp' in data.data) {
                console.log('\n✅ timestamp 필드가 정상적으로 포함되어 있습니다!');
                console.log(`   timestamp 값: ${data.data.timestamp}`);
            } else {
                console.log('\n❌ timestamp 필드가 누락되었습니다!');
            }
            
            // 필수 필드 확인
            const requiredFields = ['total_granted', 'total_used', 'available_tokens', 'timestamp'];
            const missingFields = requiredFields.filter(field => !(field in data.data));
            
            if (missingFields.length === 0) {
                console.log('\n✅ 모든 필수 필드가 정상적으로 포함되어 있습니다!');
            } else {
                console.log('\n❌ 누락된 필드:', missingFields);
            }
        } else {
            console.log('\n❌ API 호출 실패:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 2. 토큰 사용 API 테스트 (실제 사용은 하지 않고 요청 형식만 확인)
async function testUseToken() {
    try {
        const response = await fetch('/api/use-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ tokens: 1 })
        });
        
        const data = await response.json();
        
        console.log('\n=== /api/use-token API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
        } else {
            console.log('\n⚠️ API 응답:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 테스트 실행
console.log('🚀 토큰 API 테스트 시작...\n');
testTokenStatus().then(() => {
    console.log('\n');
    // testUseToken(); // 실제 토큰 사용을 원하지 않으면 주석 처리
});



// 1. 토큰 상태 조회 API 테스트
async function testTokenStatus() {
    try {
        const response = await fetch('/api/token-status', {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        console.log('=== /api/token-status API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
            
            // timestamp 필드 확인
            if ('timestamp' in data.data) {
                console.log('\n✅ timestamp 필드가 정상적으로 포함되어 있습니다!');
                console.log(`   timestamp 값: ${data.data.timestamp}`);
            } else {
                console.log('\n❌ timestamp 필드가 누락되었습니다!');
            }
            
            // 필수 필드 확인
            const requiredFields = ['total_granted', 'total_used', 'available_tokens', 'timestamp'];
            const missingFields = requiredFields.filter(field => !(field in data.data));
            
            if (missingFields.length === 0) {
                console.log('\n✅ 모든 필수 필드가 정상적으로 포함되어 있습니다!');
            } else {
                console.log('\n❌ 누락된 필드:', missingFields);
            }
        } else {
            console.log('\n❌ API 호출 실패:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 2. 토큰 사용 API 테스트 (실제 사용은 하지 않고 요청 형식만 확인)
async function testUseToken() {
    try {
        const response = await fetch('/api/use-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ tokens: 1 })
        });
        
        const data = await response.json();
        
        console.log('\n=== /api/use-token API 테스트 결과 ===');
        console.log('Status:', response.status);
        console.log('Response:', JSON.stringify(data, null, 2));
        
        if (data.success && data.data) {
            const fields = Object.keys(data.data);
            console.log('\n✅ 반환된 필드 목록:');
            fields.forEach((field, index) => {
                console.log(`  ${index + 1}. ${field}: ${data.data[field]}`);
            });
        } else {
            console.log('\n⚠️ API 응답:', data.message);
        }
        
        return data;
    } catch (error) {
        console.error('❌ API 호출 중 오류:', error);
        return null;
    }
}

// 테스트 실행
console.log('🚀 토큰 API 테스트 시작...\n');
testTokenStatus().then(() => {
    console.log('\n');
    // testUseToken(); // 실제 토큰 사용을 원하지 않으면 주석 처리
});


