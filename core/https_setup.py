"""
HTTPS 설정 및 SSL 인증서 관리
- Let's Encrypt 자동 인증서 발급
- SSL/TLS 설정
- HTTPS 리다이렉트
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SSLManager:
    """SSL 인증서 관리 클래스"""
    
    def __init__(self, domain: str, email: str):
        self.domain = domain
        self.email = email
        self.cert_dir = Path("ssl_certs")
        self.cert_file = self.cert_dir / f"{domain}.crt"
        self.key_file = self.cert_dir / f"{domain}.key"
        self.chain_file = self.cert_dir / f"{domain}.chain.crt"
        
        # 인증서 디렉토리 생성
        self.cert_dir.mkdir(exist_ok=True)
    
    def generate_self_signed_cert(self) -> bool:
        """자체 서명 인증서 생성 (개발용)"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
            
            # 개인키 생성
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # 인증서 정보
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "KR"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Seoul"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Seoul"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "1Tax App"),
                x509.NameAttribute(NameOID.COMMON_NAME, self.domain),
            ])
            
            # 인증서 생성
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(self.domain),
                    x509.DNSName(f"*.{self.domain}"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # 파일 저장
            with open(self.cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(self.key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            logger.info(f"✅ 자체 서명 인증서 생성 완료: {self.domain}")
            return True
            
        except ImportError:
            logger.error("cryptography 라이브러리가 설치되지 않았습니다. pip install cryptography")
            return False
        except Exception as e:
            logger.error(f"자체 서명 인증서 생성 실패: {e}")
            return False
    
    def setup_letsencrypt(self) -> bool:
        """Let's Encrypt 인증서 설정 (프로덕션용)"""
        try:
            import certbot.main
            
            # Certbot 인수 설정
            args = [
                'certonly',
                '--standalone',
                '--non-interactive',
                '--agree-tos',
                '--email', self.email,
                '--domains', self.domain,
                '--cert-path', str(self.cert_file),
                '--key-path', str(self.key_file),
                '--fullchain-path', str(self.chain_file)
            ]
            
            # 인증서 발급
            certbot.main.main(args)
            
            logger.info(f"✅ Let's Encrypt 인증서 발급 완료: {self.domain}")
            return True
            
        except ImportError:
            logger.error("certbot가 설치되지 않았습니다. pip install certbot")
            return False
        except Exception as e:
            logger.error(f"Let's Encrypt 인증서 발급 실패: {e}")
            return False
    
    def check_certificate_validity(self) -> Dict[str, Any]:
        """인증서 유효성 확인"""
        if not self.cert_file.exists():
            return {'valid': False, 'error': '인증서 파일이 존재하지 않습니다'}
        
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization
            
            with open(self.cert_file, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # 유효 기간 확인
            now = datetime.datetime.utcnow()
            not_valid_after = cert.not_valid_after.replace(tzinfo=None)
            days_until_expiry = (not_valid_after - now).days
            
            return {
                'valid': True,
                'subject': cert.subject.rfc4514_string(),
                'issuer': cert.issuer.rfc4514_string(),
                'not_valid_after': not_valid_after.isoformat(),
                'days_until_expiry': days_until_expiry,
                'is_expiring_soon': days_until_expiry < 30
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def renew_certificate(self) -> bool:
        """인증서 갱신"""
        try:
            import certbot.main
            
            args = [
                'renew',
                '--non-interactive',
                '--cert-name', self.domain
            ]
            
            certbot.main.main(args)
            
            logger.info(f"✅ 인증서 갱신 완료: {self.domain}")
            return True
            
        except Exception as e:
            logger.error(f"인증서 갱신 실패: {e}")
            return False

class HTTPSConfig:
    """HTTPS 설정 관리"""
    
    def __init__(self, domain: str, email: str, environment: str = 'development'):
        self.domain = domain
        self.email = email
        self.environment = environment
        self.ssl_manager = SSLManager(domain, email)
    
    def setup_https(self) -> Dict[str, Any]:
        """HTTPS 설정"""
        config = {
            'ssl_context': None,
            'redirect_http_to_https': False,
            'hsts_enabled': False,
            'certificate_info': None
        }
        
        if self.environment == 'production':
            # 프로덕션: Let's Encrypt 사용
            if self.ssl_manager.setup_letsencrypt():
                config['ssl_context'] = (str(self.ssl_manager.cert_file), str(self.ssl_manager.key_file))
                config['redirect_http_to_https'] = True
                config['hsts_enabled'] = True
                config['certificate_info'] = self.ssl_manager.check_certificate_validity()
        else:
            # 개발/스테이징: 자체 서명 인증서 사용
            if self.ssl_manager.generate_self_signed_cert():
                config['ssl_context'] = (str(self.ssl_manager.cert_file), str(self.ssl_manager.key_file))
                config['redirect_http_to_https'] = False
                config['hsts_enabled'] = False
                config['certificate_info'] = self.ssl_manager.check_certificate_validity()
        
        return config
    
    def get_ssl_context(self):
        """SSL 컨텍스트 반환"""
        import ssl
        
        if self.ssl_manager.cert_file.exists() and self.ssl_manager.key_file.exists():
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(str(self.ssl_manager.cert_file), str(self.ssl_manager.key_file))
            return context
        return None
    
    def setup_https_redirect(self, app):
        """HTTP to HTTPS 리다이렉트 설정"""
        @app.before_request
        def force_https():
            if not request.is_secure and self.environment == 'production':
                return redirect(request.url.replace('http://', 'https://'), code=301)

# 환경 변수에서 설정 로드
def get_https_config() -> Optional[HTTPSConfig]:
    """HTTPS 설정 로드"""
    domain = os.getenv('DOMAIN')
    email = os.getenv('ADMIN_EMAIL')
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if domain and email:
        return HTTPSConfig(domain, email, environment)
    return None
