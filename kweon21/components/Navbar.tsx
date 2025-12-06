import React, { useState, useEffect, useCallback } from 'react';

// Tailwind 무력화용 인라인 스타일 정의 (CSS 우선순위 1000점)
const styles = {
  navbar: {
    background: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)' as any,
    borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
    position: 'sticky' as 'sticky',
    top: 0,
    zIndex: 50,
    width: '100%',
    height: '60px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
    transition: 'all 0.3s ease'
  },
  userCapsule: {
    border: '1px solid #e0e0e0',
    borderRadius: '30px',
    padding: '6px 14px 6px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    cursor: 'pointer',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    transition: 'all 0.2s ease',
    whiteSpace: 'nowrap',
    minHeight: '36px'
  },
  dropdownArrow: {
    fontSize: '0.7rem',
    transition: 'transform 0.3s ease',
    color: '#6b7280',
    marginLeft: '4px',
    flexShrink: 0,
    paddingRight: '4px'
  },
  dropdown: {
    position: 'absolute' as 'absolute',
    top: 'calc(100% + 20px)',
    right: 0,
    width: '340px',
    backgroundColor: '#ffffff',
    background: '#ffffff',
    backgroundImage: 'none',
    backgroundClip: 'padding-box',
    backgroundOrigin: 'padding-box',
    backgroundAttachment: 'scroll',
    backgroundRepeat: 'repeat',
    backgroundSize: 'auto',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05)',
    borderRadius: '16px',
    padding: '25px',
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
    zIndex: 1001,
    listStyle: 'none' as 'none',
    margin: 0,
    marginTop: '8px',
    opacity: 0,
    visibility: 'hidden' as 'hidden',
    transform: 'translateY(-10px) scale(0.95)',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    backdropFilter: 'none',
    WebkitBackdropFilter: 'none' as any,
    mixBlendMode: 'normal' as 'normal'
  },
  dropdownActive: {
    opacity: 1,
    visibility: 'visible' as 'visible',
    transform: 'translateY(0) scale(1)',
    backgroundColor: '#ffffff',
    background: '#ffffff',
    backgroundImage: 'none',
    mixBlendMode: 'normal' as 'normal'
  },
  menuItem: {
    display: 'flex',
    flexDirection: 'column' as 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '24px 16px',
    color: '#1d1d1f',
    textDecoration: 'none',
    borderRadius: '12px',
    background: '#f5f5f7',
    border: 'none',
    boxShadow: '0 4px 0 #d1d1d6',
    transition: 'all 0.1s cubic-bezier(0.4, 0, 0.2, 1)',
    fontWeight: 600,
    fontSize: '0.85rem',
    textAlign: 'center' as 'center',
    cursor: 'pointer',
    position: 'relative' as 'relative',
    minHeight: '100px',
    minWidth: '90px',
    gap: '8px'
  },
  menuItemHover: {
    background: '#e8e8ed',
    boxShadow: '0 6px 0 #c1c1c6',
    transform: 'translateY(-2px)'
  },
  menuItemActive: {
    transform: 'translateY(4px)',
    boxShadow: '0 0 0 #d1d1d6',
    background: '#e0e0e5'
  },
  keycapIcon: {
    fontSize: '2rem',
    lineHeight: 1,
    marginBottom: '4px',
    display: 'block',
    textAlign: 'center' as 'center',
    width: '100%'
  },
  keycapText: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#1d1d1f',
    lineHeight: 1.2,
    display: 'block',
    textAlign: 'center' as 'center',
    width: '100%',
    whiteSpace: 'nowrap'
  },
  logoutItem: {
    background: '#fee2e2',
    boxShadow: '0 4px 0 #fca5a5',
    color: '#dc2626',
    gridColumn: 'span 3',
    marginTop: '4px',
    paddingTop: '20px',
    borderTop: '2px solid #fee2e2'
  },
  logoutItemHover: {
    background: '#fecaca',
    boxShadow: '0 6px 0 #f87171',
    color: '#b91c1c'
  },
  logoutItemActive: {
    transform: 'translateY(4px)',
    boxShadow: '0 0 0 #fca5a5',
    background: '#fca5a5'
  }
};

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
    <nav className="navbar" style={styles.navbar}>
      <div className="nav-container">
        <a href="/" className="nav-logo">
          <span className="logo-text">로하택스</span>
        </a>
        <div className="nav-menu">
          <a href="#features" className="nav-link">기능 소개</a>
          <a href="#testimonials" className="nav-link">성공 사례</a>
          <a href="/shop" className="nav-link">멤버십</a>
          <a href="/studio" className="nav-link">
            AI 블로그 스튜디오 <span className="beta-badge">New</span>
          </a>
          <a href="#faq" className="nav-link">고객 지원</a>
          {userInfo.isLoggedIn ? (
            <>
              <a href="/conversion" className="nav-link">워크스페이스</a>
              <a href="/profile/edit" className="nav-link">마이홈</a>
              <div className="user-menu" style={{ position: 'relative' }}>
                <div 
                  className="user-menu-trigger"
                  style={styles.userCapsule}
                  onClick={toggleUserMenu}
                  role="button"
                  tabIndex={0}
                  aria-expanded={isUserMenuOpen ? 'true' : 'false'}
                  aria-haspopup="true"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      toggleUserMenu(e);
                    }
                  }}
                >
                  <div className="user-avatar">
                    {(userInfo.username || 'U')[0].toUpperCase()}
                  </div>
                  <span>{userInfo.username || '사용자'}님</span>
                  <span 
                    className={`dropdown-arrow ${isUserMenuOpen ? 'active' : ''}`}
                    style={styles.dropdownArrow}
                  >▼</span>
                </div>
                <div 
                  className={`user-menu-dropdown ${isUserMenuOpen ? 'active' : ''}`}
                  style={{
                    ...styles.dropdown,
                    ...(isUserMenuOpen ? styles.dropdownActive : {}),
                    backgroundColor: isUserMenuOpen ? '#ffffff' : 'transparent',
                    background: isUserMenuOpen ? '#ffffff' : 'transparent',
                    backgroundImage: 'none',
                    backgroundClip: 'padding-box',
                    backgroundOrigin: 'padding-box',
                    backgroundAttachment: 'scroll',
                    backgroundRepeat: 'repeat',
                    backgroundSize: 'auto',
                    opacity: isUserMenuOpen ? 1 : 0,
                    visibility: isUserMenuOpen ? 'visible' : 'hidden',
                    mixBlendMode: 'normal',
                    // Tailwind 무력화를 위한 강제 스타일
                    color: '#000000',
                    border: 'none',
                    outline: 'none'
                  } as React.CSSProperties}
                >
                  <a 
                    href="/" 
                    className="user-menu-dropdown-item"
                    style={styles.menuItem}
                    onMouseEnter={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = '#f5f5f7'; e.currentTarget.style.boxShadow = '0 4px 0 #d1d1d6'; e.currentTarget.style.transform = 'translateY(0)'; }}
                    onMouseDown={(e) => { Object.assign(e.currentTarget.style, styles.menuItemActive); }}
                    onMouseUp={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                  >
                    <span className="keycap-icon" style={styles.keycapIcon}>🏠</span>
                    <span className="keycap-text" style={styles.keycapText}>홈</span>
                  </a>
                  <a 
                    href="/shop" 
                    className="user-menu-dropdown-item"
                    style={styles.menuItem}
                    onMouseEnter={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = '#f5f5f7'; e.currentTarget.style.boxShadow = '0 4px 0 #d1d1d6'; e.currentTarget.style.transform = 'translateY(0)'; }}
                    onMouseDown={(e) => { Object.assign(e.currentTarget.style, styles.menuItemActive); }}
                    onMouseUp={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                  >
                    <span className="keycap-icon" style={styles.keycapIcon}>🛍️</span>
                    <span className="keycap-text" style={styles.keycapText}>상점</span>
                  </a>
                  <a 
                    href="/studio" 
                    className="user-menu-dropdown-item"
                    style={styles.menuItem}
                    onMouseEnter={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = '#f5f5f7'; e.currentTarget.style.boxShadow = '0 4px 0 #d1d1d6'; e.currentTarget.style.transform = 'translateY(0)'; }}
                    onMouseDown={(e) => { Object.assign(e.currentTarget.style, styles.menuItemActive); }}
                    onMouseUp={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                  >
                    <span className="keycap-icon" style={styles.keycapIcon}>📝</span>
                    <span className="keycap-text" style={styles.keycapText}>스튜디오</span>
                  </a>
                  <a 
                    href="/conversion" 
                    className="user-menu-dropdown-item"
                    style={styles.menuItem}
                    onMouseEnter={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = '#f5f5f7'; e.currentTarget.style.boxShadow = '0 4px 0 #d1d1d6'; e.currentTarget.style.transform = 'translateY(0)'; }}
                    onMouseDown={(e) => { Object.assign(e.currentTarget.style, styles.menuItemActive); }}
                    onMouseUp={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                  >
                    <span className="keycap-icon" style={styles.keycapIcon}>⚡</span>
                    <span className="keycap-text" style={styles.keycapText}>변환</span>
                  </a>
                  <a 
                    href="/profile/edit" 
                    className="user-menu-dropdown-item"
                    style={styles.menuItem}
                    onMouseEnter={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = '#f5f5f7'; e.currentTarget.style.boxShadow = '0 4px 0 #d1d1d6'; e.currentTarget.style.transform = 'translateY(0)'; }}
                    onMouseDown={(e) => { Object.assign(e.currentTarget.style, styles.menuItemActive); }}
                    onMouseUp={(e) => { Object.assign(e.currentTarget.style, styles.menuItemHover); }}
                  >
                    <span className="keycap-icon" style={styles.keycapIcon}>👤</span>
                    <span className="keycap-text" style={styles.keycapText}>마이홈</span>
                  </a>
                  <a 
                    href="/logout" 
                    className="user-menu-dropdown-item logout"
                    style={{ ...styles.menuItem, ...styles.logoutItem }}
                    onMouseEnter={(e) => { Object.assign(e.currentTarget.style, styles.logoutItemHover); }}
                    onMouseLeave={(e) => { Object.assign(e.currentTarget.style, { ...styles.menuItem, ...styles.logoutItem }); }}
                    onMouseDown={(e) => { Object.assign(e.currentTarget.style, styles.logoutItemActive); }}
                    onMouseUp={(e) => { Object.assign(e.currentTarget.style, styles.logoutItemHover); }}
                  >
                    <span className="keycap-icon" style={styles.keycapIcon}>🚪</span>
                    <span className="keycap-text" style={styles.keycapText}>로그아웃</span>
                  </a>
                </div>
              </div>
            </>
          ) : (
            <>
              <a href="/login" className="nav-link login-btn">로그인</a>
              <a href="/register" className="nav-link signup-btn">회원가입</a>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};
