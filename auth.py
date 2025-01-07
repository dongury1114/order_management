# auth.py
import time
import bcrypt
import pybase64
import requests
import json
from datetime import datetime, timedelta
from .utils import setup_logging
from .notifications import SystemMessageTemplate

class TokenManager:
    def __init__(self, client_id, client_secret, token_refresh_minutes=30, slack_manager=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.current_token = None
        self.expires_in = None
        self.token_expires_at = None
        self.token_refresh_minutes = token_refresh_minutes
        self.slack_manager = slack_manager
        self.logger = setup_logging()
        self.token_url = "https://api.commerce.naver.com/external/v1/oauth2/token"
        self.logger.info(f"TokenManager 초기화 완료 (갱신 주기: {token_refresh_minutes}분)")

    def is_token_valid(self):
        """토큰 유효성 검사"""
        if not self.current_token or not self.token_expires_at:
            return False
        # 설정된 갱신 주기에 따라 토큰 유효성 검사
        return datetime.now() < (self.token_expires_at - timedelta(minutes=self.token_refresh_minutes))

    def get_valid_token(self):
        """유효한 토큰 반환"""
        try:
            current_time = datetime.now()
            
            # 토큰이 없거나 만료 시간이 없는 경우
            if not self.current_token or not self.token_expires_at:
                self.logger.info("초기 토큰 발급 필요")
                if self.refresh_token():
                    return self.current_token
                return None

            # 토큰 갱신 주기에 따른 갱신 필요 여부 확인
            minutes_since_last_refresh = (current_time - (self.token_expires_at - timedelta(seconds=self.expires_in))).total_seconds() / 60
            
            if minutes_since_last_refresh >= self.token_refresh_minutes:
                self.logger.info(f"토큰 갱신 필요 (마지막 갱신으로부터 {minutes_since_last_refresh:.1f}분 경과)")
                if self.refresh_token():
                    return self.current_token
                return None
                
            # 토큰이 아직 유효한 경우
            self.logger.debug(f"토큰 유효함 (만료까지 {(self.token_expires_at - current_time).total_seconds() / 60:.1f}분 남음)")
            return self.current_token
            
        except Exception as e:
            self.logger.error(f"토큰 검증 중 오류 발생: {str(e)}", exc_info=True)
            return None

    def refresh_token(self):
        """토큰 갱신"""
        try:
            self.logger.info("토큰 갱신 시작")
            
            secret_sign, timestamp = self.get_secret_sign()
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "client_id": self.client_id,
                "timestamp": timestamp,
                "grant_type": "client_credentials",
                "client_secret_sign": secret_sign,
                "type": "SELF"
            }
            
            response = requests.post(self.token_url, headers=headers, data=data)
            self.logger.info(f"토큰 갱신 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                if 'access_token' in token_data:
                    self.current_token = token_data['access_token']
                    self.expires_in = token_data.get('expires_in', 10800)
                    self.token_expires_at = datetime.now() + timedelta(seconds=self.expires_in)
                    
                    self.logger.info(f"토큰 갱신 성공 (만료시간: {self.token_expires_at})")
                    
                    # Slack 알림 전송 (성공)
                    if self.slack_manager:
                        self.logger.info("토큰 갱신 Slack 알림 전송")
                        message = SystemMessageTemplate.create_token_refresh_message(success=True)
                        self.slack_manager.send_log_message(message)
                        self.logger.info("토큰 갱신 Slack 알림 전송 완료")
                    
                    return True
            
            # 실패 처리
            error_message = f"상태 코드: {response.status_code}, 응답: {response.text}"
            self.logger.error(f"토큰 갱신 실패: {error_message}")
            
            # Slack 알림 전송 (실패)
            if self.slack_manager:
                self.logger.info("토큰 갱신 실패 Slack 알림 전송")
                message = SystemMessageTemplate.create_token_refresh_message(
                    success=False, 
                    error_message=error_message
                )
                self.slack_manager.send_log_message(message)
                self.logger.info("토큰 갱신 실패 Slack 알림 전송 완료")
            
            return False
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"토큰 갱신 중 오외 발생: {error_message}", exc_info=True)
            
            # Slack 알림 전송 (예외)
            if self.slack_manager:
                self.logger.info("토큰 갱신 예외 Slack 알림 전송")
                message = SystemMessageTemplate.create_token_refresh_message(
                    success=False, 
                    error_message=f"예외 발생: {error_message}"
                )
                self.slack_manager.send_log_message(message)
                self.logger.info("토큰 갱신 예외 Slack 알림 전송 완료")
            
            return False

    def update_token(self):
        """토큰 갱신 (이전 코드와의 호환성을 위한 메서드)"""
        return self.refresh_token()

    def get_secret_sign(self):
        """시크릿 서명 생성"""
        try:
            timestamp = int(time.time() * 1000)
            password = f"{self.client_id}_{timestamp}"
            
            hashed = bcrypt.hashpw(
                password.encode('utf-8'), 
                self.client_secret.encode('utf-8')
            )
            
            secret_sign = pybase64.standard_b64encode(hashed).decode('utf-8')
            
            self.logger.debug(f"시크릿 서명 생성: timestamp={timestamp}")
            return secret_sign, timestamp
            
        except Exception as e:
            self.logger.error(f"시크릿 서명 생성 실패: {str(e)}", exc_info=True)
            raise