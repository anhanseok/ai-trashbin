"""11-18 실험 발표용 그래프 3장 (슬라이드 11·12번 그래프 자리 크기 5.35×2.25인치).
숫자는 code/exp/20261118_28회_6초 의 result.csv · threshold.csv · models.csv 실측값."""
import csv, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, '..', '..', 'code', 'exp', '20261118_28회_6초')
for f in ('malgun.ttf', 'malgunbd.ttf'):
    fm.fontManager.addfont('C:/Windows/Fonts/' + f)
plt.rcParams['font.family'] = 'Malgun Gothic'
BLUE, GRAY, DARK, MUTE, RED, LIGHT = '#0066CC', '#C7C7CC', '#1D1D1F', '#6E6E73', '#D03030', '#7FB2E5'
W, H = 5.35, 2.25


def style(ax):
    ax.set_facecolor('none')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRAY)
    ax.tick_params(colors=DARK, labelsize=9, length=0, pad=4)
    ax.grid(axis='y', color='#E5E5EA', lw=0.8)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(os.path.join(HERE, name), dpi=300, transparent=True, bbox_inches='tight', pad_inches=0.04)
    plt.close(fig)


# 1) 판단 시간 ↔ 정확도 (실험 때 기록한 확률, 171장 모델)
t = [0.5, 1, 2, 3, 5]
acc = [75.0, 85.7, 89.3, 85.7, 82.1]
lo = [57, 69, 73, 69, 64]
hi = [87, 94, 96, 94, 92]
fig, ax = plt.subplots(figsize=(W, H))
style(ax)
ax.fill_between(t, lo, hi, color=LIGHT, alpha=0.25, lw=0)
ax.plot(t, acc, color=BLUE, lw=2.2, marker='o', ms=5, zorder=3)
ax.axhline(75.0, color=MUTE, lw=1, ls='--')
ax.text(3.4, 72.5, '예전 규칙(같은 판정 2번 연속) 75%', fontsize=8, color=MUTE, va='top')
ax.scatter([2], [89.3], s=140, facecolor='none', edgecolor=RED, lw=1.8, zorder=4)
ax.annotate('2초 89.3%', xy=(2, 89.3), xytext=(2.35, 97), fontsize=10, fontweight='bold', color=RED)
ax.set_xticks(t)
ax.set_xticklabels(['0.5초', '1초', '2초', '3초', '5초'])
ax.set_ylim(50, 102)
ax.set_xlim(0.3, 5.9)
ax.set_ylabel('정확도 (%)', fontsize=9, color=MUTE)
ax.set_title('판단 시간별 정확도 · 28회 (띠: 95% 신뢰구간)', fontsize=9.5, color=MUTE, loc='left', pad=6)
save(fig, 'fig_time.png')

# 2) 확신도 기준 ↔ 재활용 칸 오염률 · 일반 칸으로 빠진 재활용품
rows = list(csv.DictReader(open(os.path.join(EXP, 'threshold.csv'), encoding='utf-8-sig')))
c = [int(r['기준']) for r in rows]
contam = [float(r['오염률%']) for r in rows]
togen = [float(r['일반행%']) for r in rows]
fig, ax = plt.subplots(figsize=(W, H))
style(ax)
ax.plot(c, contam, color=RED, lw=2.2, marker='o', ms=4, label='재활용 칸 오염률')
ax.plot(c, togen, color=BLUE, lw=2.2, marker='o', ms=4, label='일반 칸으로 빠진 재활용품')
ax.axvline(65, color=DARK, lw=1, ls='--')
ax.text(66, 66, '65%\n오염 10%\n일반행 29%', fontsize=8.5, color=DARK, fontweight='bold', va='top')
ax.axvline(70, color=GRAY, lw=1, ls=':')
ax.text(71, 30, '이전 70%', fontsize=8, color=MUTE)
ax.set_xlabel('확신도 기준 (%) · 이보다 낮으면 일반 칸', fontsize=9, color=MUTE)
ax.set_ylabel('%', fontsize=9, color=MUTE)
ax.set_ylim(-3, 75)
ax.legend(fontsize=8.5, frameon=False, loc='upper left')
ax.set_title('확신도 기준별 · 2초 평균 판정 28회', fontsize=9.5, color=MUTE, loc='left', pad=6)
save(fig, 'fig_threshold.png')

# 3) 학습 사진 수 ↔ 정확도 (같은 28회 사진을 모델 3개로 다시 판정, 2초 평균)
rows = [r for r in csv.DictReader(open(os.path.join(EXP, 'models.csv'), encoding='utf-8-sig')) if float(r['판단초']) == 2]
names = [r['모델'] for r in rows]
vals = [float(r['정확도%']) for r in rows]
fig, ax = plt.subplots(figsize=(W, H))
style(ax)
bars = ax.bar(names, vals, color=[GRAY, LIGHT, BLUE], width=0.55)
for b, v, r in zip(bars, vals, rows):
    ax.text(b.get_x() + b.get_width() / 2, v + 2, f'{v:.1f}%', ha='center', fontsize=12, fontweight='bold',
            color=BLUE if r is rows[-1] else DARK)
    ax.text(b.get_x() + b.get_width() / 2, 6, f"일반 {r['일반']}", ha='center', fontsize=8,
            color='white' if r is rows[-1] else DARK)
ax.set_ylim(0, 105)
ax.set_ylabel('정확도 (%)', fontsize=9, color=MUTE)
ax.set_title('학습 사진 수별 정확도 · 같은 28회 사진, 2초 평균', fontsize=9.5, color=MUTE, loc='left', pad=6)
save(fig, 'fig_models.png')
print('saved')
