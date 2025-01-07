from datetime import datetime
import logging

class OrderMessageTemplate:
    @staticmethod
    def create_order_message(order):
        """주문 알림 메시지 생성"""
        try:
            # 주문자 정보 가져오기
            orderer = order.get('orderer', {})
            orderer_name = orderer.get('name', 'N/A')
            orderer_tel = orderer.get('tel', 'N/A')
            
            # 상품 옵션 정보 가져오기
            options = order.get('productOption', 'N/A')
            
            # 주문 시간 포맷팅
            order_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            message = (
                f"주문일자: {order_time}\n"
                f"주문자: {orderer_name} \n"
                f"전화번호: ({orderer_tel})\n"
                f"상품명: {order.get('productName', 'N/A')}\n"
                f"옵션: {options}"
            )
            
            return {
                "text": message
            }
            
        except Exception as e:
            logging.error(f"주문 메시지 생성 중 오류: {str(e)}")
            return {
                "text": "🚨 주문 알림 생성 중 오류가 발생했습니다."
            }

class SystemMessageTemplate:
    @staticmethod
    def create_startup_message():
        """시스템 시작 메시지 생성"""
        return {
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

    @staticmethod
    def create_token_refresh_message(success, error_message=None):
        """토큰 갱신 알림 메시지 생성"""
        if success:
            return {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔄 *토큰 갱신 완료*\n토큰이 성공적으로 갱신되었습니다."
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"갱신 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
        else:
            return {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "⚠️ *토큰 갱신 실패*\n토큰 갱신 중 오류가 발생했습니다."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"오류 메시지: {error_message}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"발생 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            } 