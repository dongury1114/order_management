import requests
from datetime import datetime, timedelta
import json
from .notifications import SlackManager, OrderMessageTemplate
from .utils import load_config, setup_logging
from .auth import TokenManager

class OrderManager:
    def __init__(self, client_id=None, client_secret=None, token_refresh_minutes=30):
        """초기화 메서드"""
        # logger를 가장 먼저 초기화
        self.logger = setup_logging()
        
        try:
            if not client_id or not client_secret:
                self.logger.error("client_id와 client_secret이 제공되지 않았습니다.")
                raise ValueError("client_id와 client_secret은 필수 값입니다.")
                
            config = load_config()
            if not config:
                self.logger.error("설정을 불러올 수 없습니다.")
                raise ValueError("설정 로드 실패")
            
            # 필수 설정 검증
            required_configs = ['WEBHOOK_LOG', 'WEBHOOK_ORDER']
            for key in required_configs:
                if key not in config:
                    self.logger.error(f"필수 설정 누락: {key}")
                    raise ValueError(f"설정에서 {key}를 찾을 수 없습니다.")
            
            # Slack 초기화
            self.slack_manager = SlackManager(config["WEBHOOK_LOG"], config["WEBHOOK_ORDER"])
            
            # API 엔드포인트 설정
            self.query_url = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/query"
            self.list_url = 'https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/last-changed-statuses'
            
            # 기타 초기화
            self.notified_order_ids = set()
            
            # TokenManager 초기화
            self.auth = TokenManager(
                client_id=client_id,
                client_secret=client_secret,
                token_refresh_minutes=token_refresh_minutes,
                slack_manager=self.slack_manager
            )
            
            self.logger.info(f"OrderManager 초기화 완료 (토큰 갱신 주기: {token_refresh_minutes}분)")
            
        except Exception as e:
            self.logger.error(f"OrderManager 초기화 중 오류 발생: {str(e)}", exc_info=True)
            raise

    def get_new_order_list(self, retry_count=0):
        """신규 주문 목록 조회"""
        try:
            current_time = datetime.now()
            from_time = current_time - timedelta(minutes=30)
            
            headers = {
                "Authorization": f"Bearer {self.auth.get_valid_token()}",
                "Content-Type": "application/json"
            }
            
            params = {
                "lastChangedFrom": from_time.strftime("%Y-%m-%dT%H:%M:%S.%f+09:00"),
                "lastChangedType": "PAYED"
            }
            
            self.logger.debug(f"주문 조회 파라미터: {params}")
            
            response = requests.get(self.list_url, headers=headers, params=params)
            
            if response.status_code == 401:
                if retry_count < 3:
                    self.logger.info(f"토큰 갱신 시도 {retry_count + 1}/3")
                    if self.auth.refresh_token():
                        return self.get_new_order_list(retry_count + 1)
                self.logger.error("토큰 갱신 실패")
                return []
                
            if response.status_code == 200:
                res_data = response.json()
                orders = res_data.get('data', {}).get('lastChangeStatuses', [])
                return orders
                
            self.logger.error(f"API 오류 응답: {response.text}")
            return []
            
        except Exception as e:
            self.logger.error(f"주문 목록 조회 중 오류 발생: {str(e)}", exc_info=True)
            return []

    def get_order_details(self, product_order_ids):
        """주문 상세 정보 조회"""
        try:
            if not product_order_ids:
                return []
                
            self.logger.info(f"주문 상세 정보 조회: {product_order_ids}")
            
            headers = {
                "Authorization": f"Bearer {self.auth.get_valid_token()}",
                "Content-Type": "application/json"
            }
            
            payload = {"productOrderIds": product_order_ids}
            
            response = requests.post(self.query_url, headers=headers, json=payload)
            self.logger.debug(f"상세 정보 조회 응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            
            self.logger.error(f"상세 정보 조회 실패: {response.text}")
            return []
            
        except Exception as e:
            self.logger.error(f"주문 상세 정보 조회 중 오류: {str(e)}", exc_info=True)
            return []

    def get_order_detail(self, product_order_id):
        """주문 상세 정보 조회"""
        try:
            token = self.auth.get_valid_token()
            if not token:
                self.logger.error("유효한 토큰이 없습니다.")
                return None

            headers = {
                "Authorization": f"Bearer {token}",
                "content-type": "application/json"
            }

            url = f"https://api.commerce.naver.com/external/v1/pay-order/seller/orders/single/{product_order_id}"
            response = requests.get(url, headers=headers)
            
            self.logger.info(f"주문 상세 조회 응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                order_detail = response.json()
                self.logger.debug(f"주문 상세 정보: {json.dumps(order_detail, ensure_ascii=False, indent=2)}")
                return order_detail
            else:
                self.logger.error(f"주문 상세 조회 실패: {response.text}")
                return None
            
        except Exception as e:
            self.logger.error(f"주문 상세 조회 중 오류: {str(e)}")
            return None

    def process_new_orders(self):
        """신규 주문 처리"""
        try:
            orders = self.get_new_order_list()
            if not orders:
                return
            
            # 처리할 주문 필터링
            new_orders = [
                order for order in orders 
                if order.get('productOrderId') not in self.notified_order_ids
            ]
            
            if not new_orders:
                return
            
            self.logger.info(f"처리할 신규 주문: {len(new_orders)}건")
            
            # 주문 상세 정보 조회
            product_order_ids = [order.get('productOrderId') for order in new_orders]
            order_details = self.get_order_details(product_order_ids)
            if not order_details:
                self.logger.error("주문 상세 정보 조회 실패")
                return
            
            # 주문별 알림 전송
            for order_data in order_details.get('data', []):
                try:
                    product_order = order_data.get('productOrder', {})
                    order_info = order_data.get('order', {})
                    
                    if not product_order:
                        continue
                    
                    product_order_id = product_order.get('productOrderId')
                    
                    # 주문 정보와 주문자 정보 결합
                    combined_order = {
                        **product_order,
                        'orderer': {
                            'name': order_info.get('ordererName'),
                            'tel': order_info.get('ordererTel'),
                            'orderDate': order_info.get('orderDate')
                        }
                    }
                    
                    # Slack 메시지 전송
                    message = OrderMessageTemplate.create_order_message(combined_order)
                    if self.slack_manager.send_order_notification(message):
                        self.logger.info(f"주문 알림 전송 성공: {product_order_id}")
                        self.notified_order_ids.add(product_order_id)
                    else:
                        self.logger.error(f"주문 알림 전송 실패: {product_order_id}")
                        
                except Exception as e:
                    self.logger.error(f"주문 처리 중 오류: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"주문 처리 중 오류 발생: {str(e)}", exc_info=True)