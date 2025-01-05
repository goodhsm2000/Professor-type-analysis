# 주민번호의 마지막 검증숫자를 계산하는 함수
def calculate_verification_number(id_number):
    # 검증에 사용할 가중치 (2~9 반복)
    weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]

    # 입력된 주민번호에서 각 자리 숫자를 추출하여 리스트로 변환
    digits = [int(d) for d in id_number]

    # 12자리와 가중치를 곱한 결과의 합 계산
    total = sum(d * w for d, w in zip(digits, weights))

    # 합계를 11로 나눈 나머지
    remainder = total % 11

    # 검증숫자 계산
    verification_number = (11 - remainder) % 10

    return verification_number

# 사용자로부터 12자리 주민번호 입력 받기
id_number = input("주민번호 12자리를 입력하세요 (마지막 검증 숫자 제외): ")

# 유효성 검사: 입력이 12자리인지 확인
if len(id_number) == 12 and id_number.isdigit():
    # 검증숫자 계산
    result = calculate_verification_number(id_number)
    print(f"검증숫자는: {result}")
else:
    print("올바른 12자리 숫자를 입력해주세요.")
