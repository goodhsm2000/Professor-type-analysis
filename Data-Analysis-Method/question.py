import re
import matplotlib.pyplot as plt
import glob
import os

def analyze_sentences(filename, output_dir):
    # 1) 파일 읽기
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    # 2) 정규표현식을 사용해 문장 단위로 추출
    # [^.?!]+ : '.'나 '?' 또는 '!'가 나오기 전까지의 문자열
    # [.?!]   : 문장의 끝을 의미하는 마침표/물음표/느낌표
    sentences = re.findall(r'[^.?!]+[.?!]', text)

    # 3) 의문문(?), 평서문(.) 카운팅
    question_count = 0
    statement_count = 0

    for s in sentences:
        s = s.strip()
        if s.endswith('?'):
            if len(s) > 6:  # 글자 수가 6개 초과인 의문문만 카운트
                question_count += 1
            else:
                continue  # 조건을 만족하지 않으면 문장 제외
        elif s.endswith('.'):
            statement_count += 1

    # 총 문장 수 (조건을 만족하는 의문문과 평서문만 포함)
    total_sentences = question_count + statement_count

    # 비율 계산 (총 문장 수가 0이 아닐 때만)
    if total_sentences > 0:
        question_ratio = question_count / total_sentences * 100
        statement_ratio = statement_count / total_sentences * 100
    else:
        question_ratio = 0
        statement_ratio = 0

    # 4) 결과 텍스트 출력
    print("=" * 45)
    print(f"파일 이름: {filename}")
    print("=" * 45)
    print(f"전체 문장 수       : {total_sentences}")
    print(f"의문문(?로 끝남) 수 : {question_count}")
    print(f"평서문(.으로 끝남) 수 : {statement_count}")
    print("-" * 45)
    print(f"의문문 비율         : {question_ratio:.2f}%")
    print(f"평서문 비율         : {statement_ratio:.2f}%")
    print("=" * 45)

    # 5) 원 그래프로 시각화 (matplotlib)
    #    - labels: 파이차트에서 표시될 항목의 이름
    #    - counts: 각 항목의 값
    labels = ['Questions (?)', 'Statements (.)']
    counts = [question_count, statement_count]

    # 파이차트 생성
    fig, ax = plt.subplots()
    # autopct='%1.1f%%': 각 파이가 차지하는 비율을 소수점 1자리까지 표시
    # startangle=140: 그래프 시작 각도
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')  # 파이차트를 원형으로 보이게 설정
    plt.title('Question vs. Statement Distribution')

    # 그래프 저장
    base_filename = os.path.splitext(os.path.basename(filename))[0]
    output_path = os.path.join(output_dir, f"{base_filename}.png")
    plt.savefig(output_path)
    plt.close()  # 메모리 절약을 위해 현재 figure 닫기

    print(f"그래프가 저장되었습니다: {output_path}\n")

def main(input_dir, output_dir):
    # 입력 디렉토리에서 모든 .txt 파일 찾기
    pattern = os.path.join(input_dir, '*.txt')
    txt_files = glob.glob(pattern)

    if not txt_files:
        print(f"'{input_dir}' 디렉토리에 .txt 파일이 없습니다.")
        return

    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 각 파일에 대해 분석 실행
    for file in txt_files:
        analyze_sentences(file, output_dir)

if __name__ == "__main__":
    # 분석할 .txt 파일들이 있는 디렉토리 경로
    # 예: 현재 디렉토리
    input_directory = './'  # 원하는 경로로 변경 가능

    # 그래프 이미지를 저장할 디렉토리 경로
    output_directory = './output_graphs'  # 원하는 경로로 변경 가능

    main(input_directory, output_directory)


