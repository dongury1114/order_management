import os
import json
import time
from datetime import datetime
from order_management import OrderManager
from order_management.notifications import SystemMessageTemplate
from order_management.utils import load_config, setup_logging

def main():
    logger = setup_logging()
    logger.info("프로그램 시작")
    
    try:
        # 설정 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'config.json')
        
        config = load_config(config_path)
        if not config:
            logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
            return

        # OrderManager 초기화 (30분 주기로 토큰 갱신)
        order_manager = OrderManager(
            client_id=config['CLIENT_ID'],
            client_secret=config['CLIENT_SECRET'],
            token_refresh_minutes=30  # 30분으로 변경
        )
        
        # 시작 알림 전송
        startup_message = SystemMessageTemplate.create_startup_message()
        order_manager.slack_manager.send_order_notification(startup_message)
        logger.info("시작 알림 전송 완료")

        # 주문 모니터링 루프
        while True:
            try:
                order_manager.process_new_orders()
            except Exception as e:
                logger.error(f"주문 처리 중 오류 발생: {str(e)}", exc_info=True)

            time.sleep(10)

    except KeyboardInterrupt:
        logger.info("프로그램 종료")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
