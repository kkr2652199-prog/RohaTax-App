"""
이메일 발송 유틸리티
Flask-Mail을 사용한 이메일 발송 기능
"""
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

try:
    from flask_mail import Mail, Message
    mail = Mail()
    
    # Flask-Mail 초기화 함수
    def init_mail(app):
        """Flask-Mail 초기화"""
        mail.init_app(app)
        logger.info("Flask-Mail 초기화 완료")
        
        # 이메일 설정 확인
        mail_server = app.config.get('MAIL_SERVER')
        mail_port = app.config.get('MAIL_PORT')
        mail_use_tls = app.config.get('MAIL_USE_TLS')
        mail_username = app.config.get('MAIL_USERNAME')
        
        logger.info(f"이메일 설정 - Server: {mail_server}, Port: {mail_port}, TLS: {mail_use_tls}, Username: {mail_username}")
    
    
    def send_password_reset_email(email: str, token: str, username: str) -> bool:
        """
        비밀번호 재설정 이메일 발송
        
        Args:
            email: 수신자 이메일 주소
            token: 비밀번호 재설정 토큰
            username: 사용자 이름
         
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 이메일 설정이 완료되지 않은 경우 로그만 출력
            mail_server = os.environ.get('MAIL_SERVER')
            if not mail_server:
                logger.warning("이메일 서버 설정이 없습니다. 콘솔에 토큰을 출력합니다.")
                logger.info(f"비밀번호 재설정 토큰 - 사용자: {username}, 이메일: {email}, 토큰: {token}")
                logger.info(f"재설정 URL: http://localhost:3000/reset-password/{token}")
                return False
            
            # 메일 메시지 생성
            msg = Message(
                subject='비밀번호 재설정 요청',
                recipients=[email],
                body=f"""
안녕하세요 {username}님,

비밀번호 재설정 요청이 접수되었습니다.

다음 링크를 클릭하여 새로운 비밀번호를 설정해주세요:
http://localhost:3000/reset-password/{token}

이 링크는 1시간 동안만 유효합니다.
만약 비밀번호 재설정을 요청하지 않으셨다면, 이 이메일을 무시하셔도 됩니다.

감사합니다.
RohaTax 팀
                """,
                html=f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
        .content {{ background: #f9f9f9; padding: 30px; }}
        .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 비밀번호 재설정</h1>
        </div>
        <div class="content">
            <p>안녕하세요 <strong>{username}</strong>님,</p>
            <p>비밀번호 재설정 요청이 접수되었습니다.</p>
            <p>다음 버튼을 클릭하여 새로운 비밀번호를 설정해주세요:</p>
            <a href="http://localhost:3000/reset-password/{token}" class="button">비밀번호 재설정</a>
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                또는 다음 링크를 브라우저에 복사하여 접속하세요:<br>
                <a href="http://localhost:3000/reset-password/{token}">http://localhost:3000/reset-password/{token}</a>
            </p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="font-size: 12px; color: #666;">
                ⏰ 이 링크는 1시간 동안만 유효합니다.<br>
                ⚠️ 만약 비밀번호 재설정을 요청하지 않으셨다면, 이 이메일을 무시하셔도 됩니다.
            </p>
        </div>
        <div class="footer">
            <p>© 2025 RohaTax. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
                """
            )
            
            # 이메일 발송
            mail.send(msg)
            
            logger.info(f"비밀번호 재설정 이메일 발송 완료 - 수신자: {email}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 발송 중 오류 발생: {str(e)}")
            logger.info(f"대체: 콘솔에 토큰 출력 - 수신자: {email}, 토큰: {token}")
            return False


except ImportError:
    # Flask-Mail이 설치되지 않은 경우
    logger.warning("Flask-Mail이 설치되지 않았습니다. 이메일 발송 기능을 사용할 수 없습니다.")
    
    def init_mail(app):
        """Flask-Mail이 없을 때"""
        logger.warning("Flask-Mail이 없어 이메일 발송 기능을 사용할 수 없습니다.")
    
    def send_password_reset_email(email: str, token: str, username: str) -> bool:
        """Flask-Mail이 없을 때 콘솔 출력"""
        logger.warning("이메일 발송 불가 - Flask-Mail 미설치")
        logger.info(f"비밀번호 재설정 토큰 - 수신자: {email}, 사용자: {username}, 토큰: {token}")
        logger.info(f"재설정 URL: http://localhost:3000/reset-password/{token}")
        return False

