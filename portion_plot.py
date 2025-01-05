import matplotlib.pyplot as plt
import os
import matplotlib.font_manager as fm

font_path = 'C:\\Windows\\Fonts\\MalangmalangB.ttf'  # 경로 확인
if not os.path.exists(font_path):
    raise FileNotFoundError(f"폰트 파일을 찾을 수 없습니다: {font_path}")

fontprop = fm.FontProperties(fname=font_path, size=12)
plt.rc('font', family=fontprop.get_name())  # 폰트 적용
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 데이터 설정
# 데이터 설정
professors = ['HS (소융)', 'SW (전정대)', 'SB (컴공)', 'SG (컴공)', 'YH (컴공)', 'JK (컴공)',
              'JH (우주)', 'JS (화공)', 'HW (산경공)', 'CH (생명,교양)']

tangent_ratios = [1.393, 0, 2.2315, 1.456, 1.8325, 1.377, 0.755, 14.01, 3.2225, 10.235]

# 색상 설정
colors = ['skyblue'] * len(professors)
special_professors = ['JS (화공)', 'CH (생명,교양)']
for i, professor in enumerate(professors):
    if professor in special_professors:
        colors[i] = 'red'

# 그래프 생성
plt.figure(figsize=(10, 6))
plt.bar(professors, tangent_ratios, color=colors, edgecolor='black')

# 그래프 꾸미기
plt.title('교수님별 여담 비율 (%)', fontsize=16)
plt.xlabel('교수님', fontsize=12)
plt.ylabel('여담 비율 (%)', fontsize=12)
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 그래프 출력
plt.tight_layout()
plt.show()