import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 폰트 설정
font_path = 'C:\\Windows\\Fonts\\MalangmalangB.ttf'  # 경로 확인
if not os.path.exists(font_path):
    raise FileNotFoundError(f"폰트 파일을 찾을 수 없습니다: {font_path}")

fontprop = fm.FontProperties(fname=font_path, size=12)
plt.rc('font', family=fontprop.get_name())  # 폰트 적용
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 데이터 정의
data = {
    "HS(소융)": [12.29, 13.08],
    "SW(소융)": [13.11, 10.76],
    "SB(컴공)": [14.26, 13.91],
    "SG(컴공)": [12.78, 13.61],
    "YH(전자)": [11.54, 12.47],
    "JK(전자)": [21.52, 14.27],
    "JH(우주)": [13.61, 15.259],
    "JS(화공)": [8.44, 9.87],
    "HW(산경공)": [14.84, 17.81],
    "CH(교양)": [18.58, 16.83]
}

# 평균 계산
averages = {key: sum(values) / len(values) for key, values in data.items()}

# 평균 값 출력
print("교수님별 문장 당 평균 단어수:")
for professor, avg in averages.items():
    print(f"{professor}: {avg:.2f}")

# 색상 설정
colors = []
for professor in averages.keys():
    if professor == "JK(전자)" or professor == "CH(교양)" or professor == "HW(산경공)":
        colors.append('red')
    elif professor == "JS(화공)":
        colors.append('blue')
    else:
        colors.append('skyblue')

# 막대 그래프 생성
plt.figure(figsize=(12, 8))
bars = plt.bar(averages.keys(), averages.values(), color=colors, edgecolor='black')

# 그래프 위에 숫자 표시
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2, 
        yval + 0.5,  # 바 위의 숫자 위치 (조정 가능)
        f'{yval:.2f}', 
        ha='center', va='bottom', fontsize=10, fontproperties=fontprop
    )

# 그래프 꾸미기
plt.title('교수님별 문장 당 평균 단어수 비교', fontsize=16, fontproperties=fontprop)
plt.xlabel('교수님', fontsize=12, fontproperties=fontprop)
plt.ylabel('평균 값', fontsize=12, fontproperties=fontprop)
plt.xticks(rotation=45, fontsize=10, fontproperties=fontprop)
plt.tight_layout()

# 그래프 표시
plt.show()
