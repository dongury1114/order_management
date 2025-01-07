# 
import requests
import hashlib
import hmac
import base64
import json
import time
from .utils import load_config

class KakaoTalkManager:
    def __init__(self):
        config = load_config()
        self.access_key = config["ACCESS_KEY"]
        self.secret_key = config["SECRET_KEY"]
        self.service_id = config["KAKAO_SERVICE_ID"]
        self.api_url = f"https://sens.apigw.ntruss.com/alimtalk/v2/services/{self.service_id}/messages"

    def _make_signature(self, timestamp):
        method = "POST"
        uri = f"/alimtalk/v2/services/{self.service_id}/messages"
        message = method + " " + uri + "\n" + timestamp + "\n" + self.access_key
        message = bytes(message, 'UTF-8')
        secret_key_bytes = bytes(self.secret_key, 'UTF-8')
        
        signature = base64.b64encode(hmac.new(secret_key_bytes, message, digestmod=hashlib.sha256).digest())
        return signature.decode('UTF-8')

    def _get_headers(self):
        timestamp = str(int(time.time() * 1000))
        signature = self._make_signature(timestamp)
        
        return {
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": self.access_key,
            "x-ncp-apigw-signature-v2": signature
        }


    def send_kakao_talk(self, to_number, template_code, template_args):
        headers = self._get_headers()
        content = (
            f"안녕하세요, {template_args['고객명']}님!\n\n"
            "네이버에서 유일하게 틴더 공식 발급 한국 코드를 유통하는 저희 미니멀 스튜디오를 믿고 구매해주셔서 감사합니다.\n\n"
            f"▶ 프로모션 코드\n{template_args['쿠폰코드']}\n\n"
            "▶ 사용 방법:\n"
            "1. www.tinder.com에 로그인합니다.\n"
            "(*전화번호 및 이메일 로그인)\n"
            "2. www.tinder.com/vip/codehere 페이지에서 코드를 등록합니다.\n"
            "(프로모션코드 등록으로 가셔도 됩니다)\n\n"
            "코드 등록 시 오류가 발생하면, 스크린샷과 함께 문의해주시면 확인 즉시 해결해드리겠습니다.\n\n"
            "구매해주셔서 감사합니다!다음에 또 필요하면 연락주세요, 부쩍 추워진 요즘 건강유의하시고 좋은하루보내세요!\n\n"
            "실례가안된다면, 번거로우실수도 있지만 리뷰 부탁드리겠습니다.\n"
            "저희 스마트스토어에 큰 힘이됩니다!\n\n"
            "감사합니다."
        )

        data = {
            "plusFriendId": "@minimalstudio",
            "templateCode": template_code,
            "messages": [
                {
                    "to": to_number,
                    "content": content,
                    "buttons": [
                        {
                            "type": "WL",
                            "name": "틴더 바로가기",
                            "linkMobile": "https://tinder.com/",
                            "linkPc": "https://tinder.com/"
                        },
                        {
                            "type": "WL",
                            "name": "미니멀 스튜디오 바로가기",
                            "linkMobile": "https://m.smartstore.naver.com/minimalstudio",
                            "linkPc": "https://smartstore.naver.com/minimalstudio"
                        }
                    ]
                }
            ]
        }

        response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
        return response.json()

# 사용 예시
kakao_manager = KakaoTalkManager()
template_args = {
    "고객명": "윤혁",
    "쿠폰코드": "12345678"
}

phone_number = "01053698401"
response = kakao_manager.send_kakao_talk(phone_number, "TindercodeReviewNoEmoji", template_args)
print(response)