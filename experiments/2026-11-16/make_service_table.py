"""실서비스 관점 표: 판단 시간별 정확도(실측 39회) + 1건 처리 시간 + 분당 처리량. 발표용으로 글씨를 크게.
처리 시간 = 판단 시간 + 투하 동작 시간. 투하 동작은 main.py drop() 의 대기 시간 합
(회전 0.8 + 기울임 1.0 + 복귀 0.7 = 2.5초, 일반 칸은 털기 3회 약 1.05초 추가)을 품목 비율로 평균.
현재 규칙(같은 판정 2번 연속)은 exp2(26회) 실측값.
사용법: python make_service_table.py experiments/2026-11-16"""
import glob, json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False

D = sys.argv[1]
EXPS = [(f"{D}/exp1_13회_30초", "페트,캔,캔,일반,일반,페트,일반,캔,일반,일반,일반,일반,일반"),
        (f"{D}/exp2_26회_10초", "캔*8,페트*2,일반*3,페트*2,일반*11")]
NAME = {"캔": "can", "페트": "plastic", "일반": "general"}
TIMES = [0.5, 1, 2, 3, 5, 10]
DROP = 0.8 + 1.0 + 0.7
SHAKE = 3 * (0.15 + 0.2)
INK, MUTED, LINE, BLUE, BLUE_BG, ORANGE, ORANGE_BG, BAR_BG = (
    "#16202b", "#5a6876", "#d9e0e6", "#0b6bcb", "#e4effa", "#b5541a", "#fbf0e8", "#edf1f5")

def answers(t):
    out = []
    for p in t.split(","):
        n, _, k = p.partition("*"); out += [NAME[n]] * (int(k) if k else 1)
    return out

trials = []
for folder, ans in EXPS:
    labels = json.load(open(f"{folder}/meta.json"))["labels"]
    for f, a in zip(sorted(glob.glob(f"{folder}/item_*.jsonl")), answers(ans)):
        trials.append(([json.loads(l) for l in open(f)], a, labels))
N = len(trials)
drop_avg = DROP + SHAKE * sum(a == "general" for _, a, _ in trials) / N

def decide(rows, labels, T):
    m = np.mean([r["p"] for r in rows if r["t"] <= T + 1e-6] or [rows[0]["p"]], axis=0)
    m[labels.index("empty")] = 0
    return labels[int(np.argmax(m))]

# 행: (이름, 정확도%, 맞힌/전체, 처리 시간, 분당)
rows = []
labels2 = json.load(open(f"{EXPS[1][0]}/meta.json"))["labels"]
cur = []
for f, a in zip(sorted(glob.glob(f"{EXPS[1][0]}/item_*.jsonl")), answers(EXPS[1][1])):
    rs = [json.loads(l) for l in open(f)]; prev = None; res = (None, rs[-1]["t"])
    for r in rs:
        p = np.array(r["p"]); lab = labels2[int(p.argmax())]
        if lab == "empty" or p.max() < 0.6: prev = None; continue
        if lab == prev: res = (lab, r["t"]); break
        prev = lab
    cur.append((res[0] == a, res[1], res[0] is None))
n2 = len(cur); kc = sum(c for c, _, _ in cur); tc = float(np.mean([t for _, t, _ in cur])); miss = sum(m for _, _, m in cur)
rows.append(("현재 규칙 (2번 연속)", 100 * kc / n2, f"{kc}/{n2}", tc + drop_avg, 60 / (tc + drop_avg)))
for T in TIMES:
    k = sum(decide(r, l, T) == a for r, a, l in trials)
    rows.append((f"{T:g}초 평균", 100 * k / N, f"{k}/{N}", T + drop_avg, 60 / (T + drop_avg)))
PICK = 1 + TIMES.index(2)

W, H = 16, 9
fig = plt.figure(figsize=(W, H), dpi=150, facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
ax.text(0.6, 8.35, "정확도만큼 시간도: 실제 쓰레기통은 기다려 주지 않는다", fontsize=30, fontweight="bold", color=INK, va="center")
ax.text(0.6, 7.8, f"정확도 실측 {N}회 · 처리 시간 = 판단 시간 + 투하 동작 {drop_avg:.1f}초 · 분당 처리량 = 60 ÷ 처리 시간",
        fontsize=15, color=MUTED, va="center")

X = [0.6, 4.2, 10.1, 12.6]          # 열 시작: 판단 방식 | 정확도 | 처리 시간 | 분당 처리량
RIGHT = 14.6
top, rh = 7.15, 0.76
heads = ["판단 방식", "분류 정확도", "1건 처리 시간", "분당 처리량"]
for x, h in zip(X, heads):
    ax.text(x + 0.2, top - 0.3, h, fontsize=19, fontweight="bold", color=MUTED, va="center")
ax.add_line(plt.Line2D([X[0], RIGHT], [top - 0.62, top - 0.62], color=INK, lw=1.6))

BAR_X, BAR_W = X[1] + 0.2, 3.3
for i, (name, acc, kn, t, per) in enumerate(rows):
    y = top - 0.62 - rh * (i + 0.5)
    hi = i == PICK; cur_row = i == 0
    if hi or cur_row:
        ax.add_patch(FancyBboxPatch((X[0] - 0.05, y - rh / 2 + 0.05), RIGHT - X[0] + 0.1, rh - 0.1,
                                    boxstyle="round,pad=0,rounding_size=0.12", facecolor=BLUE_BG if hi else ORANGE_BG, lw=0))
    col = BLUE if hi else (ORANGE if cur_row else INK)
    wt = "bold" if (hi or cur_row) else "normal"
    ax.text(X[0] + 0.2, y, name, fontsize=21, color=col, fontweight=wt, va="center")
    ax.add_patch(Rectangle((BAR_X, y - 0.17), BAR_W, 0.34, facecolor=BAR_BG, lw=0))
    ax.add_patch(Rectangle((BAR_X, y - 0.17), BAR_W * acc / 100, 0.34, facecolor=col if (hi or cur_row) else "#8fb3d9", lw=0))
    ax.text(BAR_X + BAR_W + 0.2, y, f"{acc:.0f}%", fontsize=27, fontweight="bold", color=col, va="center")
    ax.text(BAR_X + BAR_W + 1.45, y, f"({kn})", fontsize=15, color=MUTED, va="center")
    ax.text(X[2] + 0.2, y, f"{t:.1f}초", fontsize=25, fontweight=wt, color=col, va="center")
    ax.text(X[3] + 0.2, y, f"{per:.0f}건", fontsize=25, fontweight=wt, color=col, va="center")
    if i < len(rows) - 1:
        ax.add_line(plt.Line2D([X[0], RIGHT], [y - rh / 2, y - rh / 2], color=LINE, lw=1))
ax.text(RIGHT + 0.1, top - 0.62 - rh * (PICK + 0.5), "◀ 채택", fontsize=18, fontweight="bold", color=BLUE, va="center")

ax.text(0.6, 0.82, "채택: 2초 평균 · 현재 규칙보다 더 정확하고(42→54%) 더 빠르다(6.4→5.1초). 3초부터는 정확도 이득 없이 처리량만 준다",
        fontsize=17, fontweight="bold", color=BLUE, va="center")
ax.text(0.6, 0.35, f"현재 규칙은 26회 실측, 그중 {miss}회는 같은 판정이 2번 연속 나오지 않아 판단 못 함(틀림으로 계산, 걸린 시간은 기록 끝 10초)",
        fontsize=12.5, color=MUTED, va="center")
fig.savefig(f"{D}/slide_service_table.png", facecolor="white")
for r in rows: print(r[0], f"{r[1]:.0f}%", r[2], f"{r[3]:.1f}s", f"{r[4]:.0f}/min")
