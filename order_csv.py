import csv
from datetime import datetime

class CSVManager:
    def __init__(self, filename='order.csv'):
        self.filename = filename
    
    def is_order_id_in_csv(self, order_id):
        # 주어진 주문 ID가 이미 CSV 파일에 있는지 확인합니다.
        try:
            with open(self.filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and row[0] == order_id:
                        return True
        except FileNotFoundError:
            return False  # 파일이 없는 경우 False 반환

        return False

    def write_order_to_csv(self, order_details):

        for order_detail in order_details:
            order_id = str(order_detail['productOrder']['productOrderId'])
            
            # 주문 ID가 이미 CSV에 있다면, 기록하지 않습니다.
            if self.is_order_id_in_csv(order_id):
                return

            # 파일 존재 여부 체크 및 없을 경우 새 파일 생성
            try:
                with open(self.filename, 'r', encoding='utf-8') as csvfile:
                    pass
            except FileNotFoundError:
                with open(self.filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['주문ID', '주문일자', '주문자 이름', '주문자 전화번호', '상품명', '상품 옵션'])

            with open(self.filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['주문ID', '주문일자', '주문자 이름', '주문자 전화번호', '상품명', '상품 옵션']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # 주문 정보 추출
                order_date = order_detail['order']['orderDate']
                orderer_name = order_detail['order']['ordererName']
                orderer_tel = order_detail['order']['ordererTel']
                product_name = order_detail['productOrder']['productName']
                product_option = order_detail['productOrder']['productOption']

                # 주문일자를 datetime 객체로 변환
                datetime_obj = datetime.strptime(order_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                formatted_order_date = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                # CSV 파일에 기록
                writer.writerow({
                    '주문ID': order_id,
                    '주문일자': formatted_order_date,
                    '주문자 이름': orderer_name,
                    '주문자 전화번호': orderer_tel,
                    '상품명': product_name,
                    '상품 옵션': product_option
            })

# ##############################################################################
# # 사용 예시
# order_manager = OrderCSVManager()
# order_detail = {
#     'order': {
#         'orderDate': '2021-01-01',
#         'ordererName': '홍길동',
#         'ordererTel': '010-1234-5678',
#     },
#     'productOrder': {
#         'productOrderId': '123456',
#         'productName': '테스트 상품',
#         'productOption': '옵션1',
#     }
# }

# order_manager.write_order_to_csv(order_detail)
# ##############################################################################
