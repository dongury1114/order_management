
import bcrypt
import pybase64
import json
import time
import requests
from datetime import datetime, timedelta
from order_management.utils import load_config

class TokenManager:
    def __init__(self, clientId, clientSecret):
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.current_token = None
        self.expires_in = 0

    def get_secret_sign(self):
        # timestamp 생성
        timestamp = int((time.time() - 290) * 1000) 
        password = self.clientId + "_" + str(timestamp)
        # bcrypt 해싱
        hashed = bcrypt.hashpw(password.encode('utf-8'), self.clientSecret.encode('utf-8'))
        # base64 인코딩
        return pybase64.standard_b64encode(hashed).decode('utf-8'), timestamp

    def get_token(self):
        url = "https://api.commerce.naver.com/external/v1/oauth2/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        secret_sign, timestamp = self.get_secret_sign()
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.clientId,
            "timestamp": timestamp,
            "client_secret_sign": secret_sign,
            "type": "SELF"
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # 오류가 있는 경우 예외를 발생시킵니다.
            token_data = response.json()
            if 'access_token' not in token_data:
                raise ValueError("access_token이 응답에 포함되어 있지 않습니다.")
            return token_data
        except requests.RequestException as e:
            print(f"토큰 갱신 실패: {e}")
            # 여기서 Slack으로 로그를 보낼 수 있습니다.
            return None

    def token_is_valid(self):
        return self.expires_in > 1800

    def update_token(self):
        token = self.get_token()
        if token is not None:
            self.current_token = token['access_token']
            self.expires_in = token['expires_in']

    def run(self):
        while True:
            if not self.token_is_valid():
                self.update_token()
            print(f"Current Token: {self.current_token}")
            print(f"Expires in: {self.expires_in} seconds")
            time.sleep(60)

