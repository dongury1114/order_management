import requests
import logging
import traceback
import json
import datetime

class SlackManager:
    def __init__(self, webhook_log_url, webhook_order_url):
        self.webhook_log_url = webhook_log_url
        self.webhook_order_url = webhook_order_url
        self.notified_order_ids = set()

    def send_slack_log(self, message):
        payload = {
            "text": message
        }
        try:
            requests.post(self.webhook_log_url, json=payload)
        except Exception as e:
            logging.error(f"Error in send_slack_log: {e}")
            logging.error(traceback.format_exc())

    def send_slack_notification(self, message):
        payload = {"text": message}
        response = requests.post(self.webhook_order_url, data=json.dumps(payload))

        if response.status_code == 200:
            print("Slack 알림이 성공적으로 전송되었습니다!")
        else:
            error_msg = "Slack 알림 전송에 실패하였습니다: " + response.text
            print(error_msg)
            self.send_slack_log(error_msg)

    # Correct usage of datetime within send_order_details_notification method
    def send_order_details_notification(self, order_details):
        total_quantity = sum(order_detail['productOrder']['quantity'] for order_detail in order_details)
        message = "*****새로운 주문 알림*****\n"
        for order_detail in order_details:
            product_order = order_detail['productOrder']
            orderer_tel = order_detail['order']['ordererTel']
            order_date = order_detail['order']['orderDate']
            orderer_name = order_detail['order']['ordererName']
            product_name = product_order["productName"]
            product_option = product_order["productOption"]
            
            # Corrected usage of datetime.datetime.strptime
            datetime_obj = datetime.datetime.strptime(order_date, "%Y-%m-%dT%H:%M:%S.%f%z")
            formatted_order_date = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

            message += f"주문일자: {formatted_order_date}, 주문자: {orderer_name}, 전화번호: {orderer_tel}, 상품명: {product_name}, 옵션: {product_option}\n"
        
        self.send_slack_notification(message)

# ##############################################################################
# # 사용 예:
# webhook_log_url = "YOUR_WEBHOOK_LOG_URL"
# webhook_order_url = "YOUR_WEBHOOK_ORDER_URL"
# slack_manager = SlackManager(webhook_log_url, webhook_order_url)

# # 로그 전송
# slack_manager.send_slack_log("This is a log message.")

# # 주문 알림 전송
# slack_manager.send_slack_notification("Order placed with ID 12345.")
# ##############################################################################