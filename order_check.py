import requests
from datetime import datetime, timedelta
from .order_slack import SlackManager
from .utils import load_config


notified_order_ids = set()

class OrderManager:
    def __init__(self, token):
        self.token = token
        config = load_config()
        self.slack_manager = SlackManager(config["WEBHOOK_LOG"], config["WEBHOOK_ORDER"])
        self.query_url = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/query"
        self.list_url = 'https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/last-changed-statuses'

    def send_notification(self, message):
        self.slack_manager.send_slack_log(message)

    def get_order_details(self, product_order_ids):
        headers = {
            'Authorization': f"Bearer {self.token}",
            'content-type': "application/json"
        }
        payload = {
            "productOrderIds": product_order_ids
        }
        res_query = requests.post(self.query_url, headers=headers, json=payload)

        if res_query.ok:
            query_data = res_query.json()
            return query_data
        else:
            self.send_notification(f"주문 상세 정보를 가져오는데 실패했습니다: {res_query.text}")
            return None

    def get_new_order_list(self, retry_count=0):
        headers = {
            'Authorization': f"Bearer {self.token}",
            'content-type': "application/json"
        }
        now = datetime.now()
        before_date = now - timedelta(hours=24)  # 24 hours ago
        iosFormat = before_date.astimezone().isoformat()

        params = {
            'lastChangedFrom': iosFormat,
            'lastChangedType': 'PAYED',
        }

        try:
            res = requests.get(url=self.list_url, headers=headers, params=params)
            if res.status_code == 200:
                res_data = res.json()
                return res_data.get('data', {}).get('lastChangeStatuses', [])
            elif 'code' in res.json() and res.json()['code'] == 'GW.AUTHN' and retry_count < 3:
                self.send_notification("Refreshing token due to authorization error.")
                return self.get_new_order_list(retry_count=retry_count + 1)
            elif 'data' not in res_data:
                self.send_notification(f"새로운 주문 목록을 가져오는데 실패했습니다: {res.text}")
                return []
            return res_data['data']['lastChangeStatuses']
        except requests.RequestException as e:
            if retry_count < 3:
                return self.get_new_order_list(retry_count=retry_count + 1)
            else:
                self.send_notification(f"새로운 주문 목록을 가져오는 요청 중 예외가 발생했습니다: {e}")
                return []

    def check_new_orders(self):
            global notified_order_ids
            order_list = self.get_new_order_list()
            if order_list:
                new_order_found = False
                for order_data in order_list:
                    if order_data['productOrderId'] not in notified_order_ids:
                        new_order_found = True
                        notified_order_ids.add(order_data['productOrderId'])
                if not new_order_found:
                    return []
                product_order_ids = [order_data['productOrderId'] for order_data in order_list]
                query_data = self.get_order_details(product_order_ids)
                order_details = query_data['data']
                order_details.sort(key=lambda x: x['order']['orderDate'], reverse=True)
                return order_details
            else:
                return []