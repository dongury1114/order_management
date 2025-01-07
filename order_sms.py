# order_sms.py
import requests
import hashlib
import hmac
import base64
import json
import time
from .utils import load_config

class SMSManager:
    def __init__(self):
        config = load_config()
        self.access_key = config["ACCESS_KEY"]
        self.secret_key = config["SECRET_KEY"]
        self.api_url = config["SMS_BASE_URL"].rstrip('/') + '/' + config["SMS_API_URL"].lstrip('/')

    def _make_signature(self, timestamp):
        method = "POST"
        uri = "/" + "/".join(self.api_url.split('/')[3:])  # API URL에서 호스트를 제외한 URI 부분을 추출합니다.
        message = method + " " + uri + "\n" + timestamp + "\n" + self.access_key
        message = bytes(message, 'UTF-8')
        secret_key_bytes = bytes(self.secret_key, 'UTF-8')
        
        signature = base64.b64encode(hmac.new(secret_key_bytes, message, digestmod=hashlib.sha256).digest())
        return signature.decode('UTF-8')

    def _get_headers(self):
        timestamp = str(int((time.time()-290) * 1000))
        signature = self._make_signature(timestamp)
        
        return {
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": self.access_key,
            "x-ncp-apigw-signature-v2": signature
        }

    def send_sms(self, from_number, to_number, content):
        headers = self._get_headers()
        data = {
            "type": "SMS",
            "contentType": "COMM",
            "countryCode": "82",
            "from": from_number,
            "content": content,
            "messages": [
                {
                    "to": to_number,
                    "content": content
                }
            ]
        }

        response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
        return response.json()

# # SMSManager 클래스 인스턴스를 생성합니다.
# sms_client = SMSManager()
# from_number = "01053698401"  # 보내는 번호
# to_number = "01053698401"  # 받는 번호
# content = "hello world"  # 내용

# # SMS 전송 함수를 호출하고 응답을 출력합니다.
# response = sms_client.send_sms(from_number, to_number, content)
# print(response)
