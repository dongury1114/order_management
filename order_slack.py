import requests
import json
from .utils import setup_logging

class SlackManager:
    def __init__(self, log_webhook_url, order_webhook_url):
        self.log_webhook_url = log_webhook_url
        self.order_webhook_url = order_webhook_url
        self.logger = setup_logging()

    def send_message(self, webhook_url, message):
        """Slack 메시지 전송"""
        try:
            response = requests.post(
                webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.logger.info("Slack 메시지 전송 성공")
                return True
            else:
                self.logger.error(f"Slack 메시지 전송 실패: {response.status_code}")
                self.logger.error(f"응답: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Slack 메시지 전송 중 오류: {str(e)}", exc_info=True)
            return False

    def send_order_notification(self, message):
        """주문 알림 전송"""
        return self.send_message(self.order_webhook_url, message)

    def send_log_message(self, message):
        """로그 메시지 전송"""
        return self.send_message(self.log_webhook_url, message)

    def send_startup_message(self):
        """프로그램 시작 알림 전송"""
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚀 주문 관리 프로그램 시작",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "주문 모니터링이 시작되었습니다.\n주문이 들어오면 알림을 보내드리겠습니다."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "✅ 시스템이 정상적으로 실행 중입니다."
                        }
                    ]
                }
            ]
        }
        return self.send_order_notification(message)
