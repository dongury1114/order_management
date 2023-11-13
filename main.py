import time
from datetime import datetime, timedelta
from order_management import load_config, TokenManager, OrderManager, SlackManager, SMSManager, CSVManager  # 필요한 클래스와 함수를 임포트합니다.

def main():
    config = load_config()
    webhook_order_url = config["WEBHOOK_ORDER"]
    webhook_log_url = config["WEBHOOK_LOG"]

    current_token = None
    expires_in = 0

    slack_manager = SlackManager(webhook_log_url, webhook_order_url)
    token_manager = TokenManager(config["CLIENT_ID"], config["CLIENT_SECRET"])
    
    sms_manager = SMSManager()
    csv_manager = CSVManager()
    
    token_manager.update_token()  # 토큰을 가져옵니다.

    current_token = token_manager.current_token
    expires_in = token_manager.expires_in

    order_manager = OrderManager(current_token)

    if current_token is None:
        print("토큰을 가져오는 데 실패했습니다.")
        return

    print("프로그램이 시작되었습니다.")
    # sms_manager.send_sms("01053698401", "01053698401", "hello world")

    try:
        while True:
            # 토큰 만료가 임박하면 갱신합니다.
            if expires_in <= 1800:
                current_token = token_manager.update_token()
                if current_token is None:
                    slack_manager.send_slack_log("토큰 갱신 실패.")
                    continue
                print("토큰이 갱신되었습니다.")
            else:
                token_info = token_manager.get_token()
                expires_in = token_info['expires_in']
                current_token = token_info['access_token']
                print("토큰이 유효합니다." , current_token)
                print("토큰 만료까지 남은 시간: ", expires_in)

            order_details = order_manager.check_new_orders()
            if order_details:
                csv_manager.write_order_to_csv(order_details)
                slack_manager.send_order_details_notification(order_details)
            time.sleep(30)  # 30초마다 반복합니다.

    except KeyboardInterrupt:
        print("사용자에 의해 프로그램이 종료되었습니다.")
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        print(error_message)
        slack_manager.send_slack_log(error_message)

if __name__ == "__main__":
    main()
