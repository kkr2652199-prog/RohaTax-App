import React, { useState, useEffect, useCallback } from 'react';

export const Navbar: React.FC = () => {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  
  // 초기 상태: API 응답을 기다리는 동안 기본값으로 설정
  const [userInfo, setUserInfo] = useState<{ username: string | null; isLoggedIn: boolean }>({ 
    username: null, 
    isLoggedIn: false 
  });

  // 세션 확인 함수: API 응답만 신뢰 (쿠키 검사 제거)
  const checkUserSession = useCallback(async () => {
    try {
      // API 호출로 세션 상태 확인 (서버가 최종 판단)
      const apiUrl = window.location.origin + '/api/user-info';
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        credentials: 'include', // 쿠키 자동 포함 (HttpOnly 쿠키도 서버로 전송됨)
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        cache: 'no-cache' // 캐시 방지
      });
      
      // 성공(200 OK): 서버가 로그인 상태 확인
      if (response.ok) {
        const data = await response.json();
        // 서버 응답 구조의 다양성 대응 (direct user object or wrapped in data)
        const userObj = data.user || (data.data && data.data.user);
        
        if (data.success && userObj) {
          setUserInfo({ 
            username: userObj.username || userObj.name || '사용자', 
            isLoggedIn: true 
          });
          return;
        }
      }
      
      // 실패(401/403): 서버가 명확하게 "로그인 안 됨"이라고 응답
      if (response.status === 401 || response.status === 403) {
        setUserInfo({ username: null, isLoggedIn: false });
        // 스튜디오 페이지에서만 로그인 페이지로 리다이렉트
        if (window.location.pathname.startsWith('/studio')) {
          const loginUrl = window.location.origin + '/login?next=' + encodeURIComponent(window.location.href);
          window.location.href = loginUrl;
        }
        return;
      }
      
      // 기타 오류 (500 등): 일시적 오류로 간주하고 기존 상태 유지
      console.log('API 응답 오류, 기존 상태 유지', response.status);
      // 상태 변경 없이 유지 (이전 상태 그대로)
      
    } catch (error) {
      // 네트워크 오류 등: 일시적 오류로 간주하고 기존 상태 유지
      console.log('API 호출 실패, 기존 상태 유지', error);
      // 상태 변경 없이 유지 (이전 상태 그대로)
    }
  }, []);

  useEffect(() => {
    // 컴포넌트 마운트 시 즉시 세션 확인
    checkUserSession();
    
    // 주기적으로 세션 상태 확인 (30초마다)
    const intervalId = setInterval(checkUserSession, 30000);
    
    // 페이지 포커스 시 세션 확인 (다른 페이지에서 돌아올 때)
    const handleFocus = () => {
      checkUserSession();
    };
    window.addEventListener('focus', handleFocus);
    
    // 페이지 가시성 변경 시 세션 확인 (탭 전환 시)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        checkUserSession();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // storage 이벤트 리스너 (다른 탭에서 로그인 시)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'login_status_changed') {
        checkUserSession();
      }
    };
    window.addEventListener('storage', handleStorageChange);
    
    // 로그인/로그아웃 후 페이지 이동 감지 (popstate 이벤트)
    const handlePopState = () => {
      checkUserSession();
    };
    window.addEventListener('popstate', handlePopState);
    
    // 페이지 로드 완료 후 추가 확인 (로그인 성공 후 리다이렉트 대비)
    const handleLoad = () => {
      checkUserSession();
    };
    if (document.readyState === 'complete') {
      handleLoad();
    } else {
      window.addEventListener('load', handleLoad);
    }
    
    return () => {
      clearInterval(intervalId);
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('load', handleLoad);
    };
  }, [checkUserSession]);

  const toggleUserMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsUserMenuOpen(!isUserMenuOpen);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.user-menu')) {
        setIsUserMenuOpen(false);
      }
    };

    if (isUserMenuOpen) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isUserMenuOpen]);

  return (
    <nav className="navbar" style={{
      background: 'white',
      borderBottom: '1px solid #eee',
      padding: '16px 0',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)'
    }}>
      <div className="nav-container" style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <a href="/" className="nav-logo" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '1.5rem',
          fontWeight: 800,
          color: '#111111',
          textDecoration: 'none',
          letterSpacing: '-0.5px',
          transition: 'color 0.3s ease'
        }}>
          <span className="logo-text" style={{
            fontWeight: 800,
            lineHeight: 1.2,
            background: 'linear-gradient(135deg, #1F2937 0%, #F59E0B 50%, #1F2937 100%)',
            backgroundSize: '200% 200%',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            animation: 'brandShimmer 3s ease-in-out infinite'
          }}>로하택스</span>
        </a>
        <div className="nav-menu" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '32px',
          listStyle: 'none',
          margin: 0,
          padding: 0
        }}>
          <a href="#features" className="nav-link" style={{
            color: '#333333',
            textDecoration: 'none',
            fontWeight: 500,
            fontSize: '0.95rem',
            transition: 'color 0.3s ease'
          }}>기능 소개</a>
          <a href="#testimonials" className="nav-link" style={{
            color: '#333333',
            textDecoration: 'none',
            fontWeight: 500,
            fontSize: '0.95rem',
            transition: 'color 0.3s ease'
          }}>성공 사례</a>
          <a href="/shop" className="nav-link" style={{
            color: '#333333',
            textDecoration: 'none',
            fontWeight: 500,
            fontSize: '0.95rem',
            transition: 'color 0.3s ease'
          }}>멤버십</a>
          <a href="/studio" className="nav-link" style={{
            color: '#333333',
            textDecoration: 'none',
            fontWeight: 500,
            fontSize: '0.95rem',
            transition: 'color 0.3s ease'
          }}>
            AI 블로그 스튜디오 <span style={{
              display: 'inline-block',
              marginLeft: '0.5rem',
              padding: '0.2rem 0.6rem',
              background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
              color: 'white',
              fontSize: '0.7rem',
              fontWeight: 700,
              borderRadius: '4px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>New</span>
          </a>
          <a href="#faq" className="nav-link" style={{
            color: '#333333',
            textDecoration: 'none',
            fontWeight: 500,
            fontSize: '0.95rem',
            transition: 'color 0.3s ease'
          }}>고객 지원</a>
          {userInfo.isLoggedIn ? (
            <>
              <a href="/conversion" className="nav-link signup-btn" style={{
                padding: '10px 20px',
                borderRadius: '8px',
                fontWeight: 600,
                background: '#2C5BF0',
                color: 'white',
                textDecoration: 'none',
                transition: 'all 0.3s ease'
              }}>워크스페이스</a>
              <a href="/profile/edit" className="nav-link" style={{
                color: '#333333',
                textDecoration: 'none',
                fontWeight: 500,
                fontSize: '0.95rem',
                transition: 'color 0.3s ease'
              }}>마이홈</a>
              <div className="user-menu" style={{ position: 'relative' }}>
                <div 
                  className="user-menu-trigger" 
                  onClick={toggleUserMenu}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 16px',
                    background: '#FFFFFF',
                    border: '1px solid #e5e7eb',
                    borderRadius: '999px',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    color: '#111111',
                    fontWeight: 600,
                    fontSize: '0.9rem'
                  }}
                >
                  <div className="user-avatar" style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #2C5BF0 0%, #4a7aff 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '1rem',
                    color: '#ffffff',
                    textTransform: 'uppercase'
                  }}>
                    {(userInfo.username || 'U')[0].toUpperCase()}
                  </div>
                  <span>{userInfo.username || '사용자'}님</span>
                  <span className="dropdown-arrow" style={{
                    fontSize: '0.7rem',
                    transition: 'transform 0.3s ease',
                    color: '#666666',
                    transform: isUserMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)'
                  }}>▼</span>
                </div>
                {isUserMenuOpen && (
                  <ul className="user-menu-dropdown" style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    right: 0,
                    minWidth: '200px',
                    background: '#FFFFFF',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
                    borderRadius: '12px',
                    padding: '8px',
                    listStyle: 'none',
                    margin: 0,
                    zIndex: 1001
                  }}>
                    <li>
                      <a href="/conversion" className="user-menu-dropdown-item" style={{
                        display: 'block',
                        padding: '12px 16px',
                        color: '#111111',
                        textDecoration: 'none',
                        borderRadius: '8px',
                        transition: 'all 0.2s ease',
                        fontWeight: 500,
                        fontSize: '0.9rem'
                      }}>파일 변환하기</a>
                    </li>
                    <li>
                      <a href="/profile/edit" className="user-menu-dropdown-item" style={{
                        display: 'block',
                        padding: '12px 16px',
                        color: '#111111',
                        textDecoration: 'none',
                        borderRadius: '8px',
                        transition: 'all 0.2s ease',
                        fontWeight: 500,
                        fontSize: '0.9rem'
                      }}>마이 페이지</a>
                    </li>
                    <li>
                      <a href="/logout" className="user-menu-dropdown-item logout" style={{
                        display: 'block',
                        padding: '12px 16px',
                        color: '#DC2626',
                        textDecoration: 'none',
                        borderRadius: '8px',
                        transition: 'all 0.2s ease',
                        fontWeight: 500,
                        fontSize: '0.9rem'
                      }}>로그아웃</a>
                    </li>
                  </ul>
                )}
              </div>
            </>
          ) : (
            <>
              <a 
                href="/login" 
                className="nav-link login-btn" 
                onClick={(e) => {
                  // 로그인 페이지로 이동 전에 세션 확인 준비
                  // 로그인 성공 후 돌아올 때를 대비하여 이벤트 리스너는 이미 설정됨
                }}
                style={{
                  padding: '10px 20px',
                  borderRadius: '8px',
                  fontWeight: 600,
                  color: '#2C5BF0',
                  background: 'transparent',
                  textDecoration: 'none',
                  transition: 'all 0.3s ease'
                }}
              >로그인</a>
              <a href="/register" className="nav-link signup-btn" style={{
                padding: '10px 20px',
                borderRadius: '8px',
                fontWeight: 600,
                background: '#2C5BF0',
                color: 'white',
                textDecoration: 'none',
                transition: 'all 0.3s ease'
              }}>회원가입</a>
            </>
          )}
        </div>
      </div>
      <style>{`
        @keyframes brandShimmer {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .nav-link:hover {
          color: #2C5BF0 !important;
        }
        .nav-logo:hover {
          color: #2C5BF0 !important;
        }
        .user-menu-dropdown-item:hover {
          background: #F9FAFB !important;
          color: #2C5BF0 !important;
          padding-left: 20px !important;
        }
        .signup-btn:hover {
          background: #1e4ed8 !important;
        }
      `}</style>
    </nav>
  );
};

