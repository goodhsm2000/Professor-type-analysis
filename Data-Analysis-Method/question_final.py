import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np

# 폰트 설정
font_path = 'C:\\Windows\\Fonts\\MalangmalangB.ttf'  # 경로 확인
if not os.path.exists(font_path):
    raise FileNotFoundError(f"폰트 파일을 찾을 수 없습니다: {font_path}")

fontprop = fm.FontProperties(fname=font_path, size=12)
plt.rc('font', family=fontprop.get_name())  # 폰트 적용
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 데이터 정의
data = {
    "HS(소융)": [19.7, 15.5],
    "SW(소융)": [3.0, 2.9],
    "SB(컴공)": [12.2, 12.3],
    "SG(컴공)": [15.8, 8.6],
    "YH(전자)": [13.6, 10.7],
    "JK(전자)": [8.5, 7.9],
    "JH(우주)": [10.3, 10.3],
    "JS(화공)": [28.0, 23.0],
    "HW(산경공)": [18.5, 9.6],
    "CH(교양)": [4.8, 3.2]
}

# 평균 의문문 비율 계산 및 평서문 비율 계산
avg_question_ratio = {}
for prof, ratios in data.items():
    avg = np.mean(ratios)
    avg_question_ratio[prof] = avg

avg_declarative_ratio = {prof: 100 - ratio for prof, ratio in avg_question_ratio.items()}

# 비율 정리 및 출력
print("교수님별 평서문 및 의문문 비율:")
for prof in data.keys():
    print(f"{prof} - 의문문 비율: {avg_question_ratio[prof]:.2f}%, 평서문 비율: {avg_declarative_ratio[prof]:.2f}%")

# -------------------- 원 그래프 --------------------
fig_pie, axes_pie = plt.subplots(2, 5, figsize=(20, 10))
axes_pie = axes_pie.flatten()

for idx, prof in enumerate(data.keys()):
    ratios = [avg_question_ratio[prof], avg_declarative_ratio[prof]]
    labels = ['의문문', '평서문']
    colors = ['#ff9999', '#66b3ff']
    wedges, texts, autotexts = axes_pie[idx].pie(
        ratios,
        labels=labels,
        autopct='%1.1f%%',
        colors=colors,
        startangle=140,
        textprops={'fontsize': 10}
    )
    axes_pie[idx].set_title(prof, fontproperties=fontprop, fontsize=12)

for idx in range(len(data.keys()), len(axes_pie)):
    fig_pie.delaxes(axes_pie[idx])

fig_pie.suptitle('각 교수님의 의문문 vs 평서문 비율', fontproperties=fontprop, fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# -------------------- 의문문 비율 막대 그래프 --------------------
fig_bar_q, ax_bar_q = plt.subplots(figsize=(12, 8))

question_ratios = [avg_question_ratio[prof] for prof in data.keys()]
bars_q = ax_bar_q.bar(data.keys(), question_ratios, color='#ff9999')

for bar in bars_q:
    height = bar.get_height()
    ax_bar_q.annotate(f'{height:.1f}%',
                      xy=(bar.get_x() + bar.get_width() / 2, height),
                      xytext=(0, 3),
                      textcoords="offset points",
                      ha='center', va='bottom',
                      fontproperties=fontprop,
                      fontsize=10)

ax_bar_q.set_xlabel('교수님', fontproperties=fontprop, fontsize=12)
ax_bar_q.set_ylabel('의문문 비율 (%)', fontproperties=fontprop, fontsize=12)
ax_bar_q.set_title('교수님별 의문문 비율', fontproperties=fontprop, fontsize=16)
ax_bar_q.set_xticklabels(data.keys(), rotation=45, ha='right', fontproperties=fontprop)
ax_bar_q.set_ylim(0, max(question_ratios) * 1.2)
plt.tight_layout()

# -------------------- 평서문 비율 막대 그래프 --------------------
fig_bar_d, ax_bar_d = plt.subplots(figsize=(12, 8))

declarative_ratios = [avg_declarative_ratio[prof] for prof in data.keys()]
bars_d = ax_bar_d.bar(data.keys(), declarative_ratios, color='#66b3ff')

for bar in bars_d:
    height = bar.get_height()
    ax_bar_d.annotate(f'{height:.1f}%',
                      xy=(bar.get_x() + bar.get_width() / 2, height),
                      xytext=(0, 3),
                      textcoords="offset points",
                      ha='center', va='bottom',
                      fontproperties=fontprop,
                      fontsize=10)

ax_bar_d.set_xlabel('교수님', fontproperties=fontprop, fontsize=12)
ax_bar_d.set_ylabel('평서문 비율 (%)', fontproperties=fontprop, fontsize=12)
ax_bar_d.set_title('교수님별 평서문 비율', fontproperties=fontprop, fontsize=16)
ax_bar_d.set_xticklabels(data.keys(), rotation=45, ha='right', fontproperties=fontprop)
ax_bar_d.set_ylim(60, max(declarative_ratios) * 1.05)
plt.tight_layout()

# 그래프 출력
plt.show()
