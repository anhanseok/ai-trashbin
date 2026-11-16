"""두 실험(실측)을 합쳐 발표용 그림 2장(slide_result.png, slide_table.png)을 만든다. 숫자는 실측 그대로.
사용법: python make_figures.py experiments/2026-11-16
정답은 실험 사진으로 확인한 값 (exp2 의 9~16번에 딱풀·숟가락이 섞여 일반으로 계산)."""
import glob, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False

S = sys.argv[1]
EXPS = [
    (f"{S}/exp1_13회_30초", "페트,캔,캔,일반,일반,페트,일반,캔,일반,일반,일반,일반,일반"),
    (f"{S}/exp2_26회_10초", "캔*8,페트*2,일반*3,페트*2,일반*11"),
]
NAME = {"캔": "can", "페트": "plastic", "일반": "general"}
KO = {"can": "캔", "plastic": "페트", "general": "일반"}
TIMES = [0.5, 1, 2, 3, 5, 7, 10]
INK, MUTED, LINE, BLUE, ORANGE, BG = "#16202b", "#5a6876", "#d9e0e6", "#0b6bcb", "#e0661c", "#ffffff"

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

def decide(rows, labels, T):
    m = np.mean([r["p"] for r in rows if r["t"] <= T + 1e-6] or [rows[0]["p"]], axis=0)
    m[labels.index("empty")] = 0
    return labels[int(np.argmax(m))]

def settle(rows, labels):
    c = np.cumsum([r["p"] for r in rows], axis=0); c[:, labels.index("empty")] = 0
    d = c.argmax(1); last = 0.0
    for i in range(1, len(d)):
        if d[i] != d[i - 1]: last = rows[i]["t"]
    return last

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z*z/n; c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return 100*max(0, c-h), 100*min(1, c+h)

acc, lo, hi, oks = [], [], [], []
for T in TIMES:
    ok = [decide(r, l, T) == a for r, a, l in trials]
    k = sum(ok); acc.append(100*k/N); a, b = wilson(k, N); lo.append(a); hi.append(b); oks.append(ok)
settles = np.array([settle(r, l) for r, _, l in trials])
p90 = float(np.percentile(settles, 90))
T2 = TIMES.index(2)
cls = {}
for ok, (_, a, _) in zip(oks[T2], trials):
    cls.setdefault(a, []).append(ok)

# ── 그림 1: 결과 요약 (16:9) ──
fig = plt.figure(figsize=(16, 9), dpi=150, facecolor=BG)
fig.text(0.04, 0.93, "판단 시간을 늘리면 더 정확해질까?", fontsize=28, fontweight="bold", color=INK)
fig.text(0.04, 0.885, f"실물 수거함에서 직접 측정 · 2회 실험, 총 {N}회 투입 · 0.5초마다 AI 확률 기록", fontsize=15, color=MUTED)

ax = fig.add_axes([0.05, 0.16, 0.52, 0.62])
ax.fill_between(TIMES, lo, hi, color=BLUE, alpha=.12, lw=0, label="95% 신뢰구간")
ax.plot(TIMES, acc, "-o", color=BLUE, lw=3, ms=9, label="정확도 (t초까지 본 평균으로 판단)")
for t, a in zip(TIMES, acc):
    ax.text(t, a + 3, f"{a:.0f}%", ha="center", fontsize=12, color=BLUE, fontweight="bold")
ax.axvspan(2, 10.8, color="#eef3f8", zorder=0)
ax.text(4.6, 12, "2초 이후: 더 기다려도 정확도 그대로", ha="center", fontsize=13, color=MUTED)
ax.set_xscale("log"); ax.set_xticks(TIMES); ax.set_xticklabels([f"{t:g}" for t in TIMES], fontsize=12)
ax.set_xlim(0.42, 11); ax.set_ylim(0, 100); ax.tick_params(axis="y", labelsize=12)
ax.set_xlabel("판단 시간 (초)", fontsize=14, color=INK); ax.set_ylabel("분류 정확도 (%)", fontsize=14, color=INK)
ax.legend(loc="upper left", fontsize=11.5, frameon=False); ax.grid(alpha=.35, color=LINE)
for s in ("top", "right"): ax.spines[s].set_visible(False)

ax2 = fig.add_axes([0.63, 0.53, 0.33, 0.25])
bins = [0, 0.3, 0.8, 1.5, 2.5, 3.5, 5, 7, 10.5]
ax2.hist(settles, bins=bins, color=BLUE, edgecolor="white")
ax2.axvline(p90, color=ORANGE, lw=2.4, ls="--")
ax2.text(p90 + 0.15, ax2.get_ylim()[1]*0.78, f"90%가 {p90:.1f}초 안에\n판정 확정", color=ORANGE, fontsize=12, fontweight="bold")
ax2.set_title("AI 판정이 더 이상 안 바뀌는 시점", fontsize=14, color=INK, loc="left", fontweight="bold")
ax2.set_xlabel("초", fontsize=11, color=MUTED); ax2.set_ylabel("투입 횟수", fontsize=11, color=MUTED)
ax2.grid(alpha=.35, axis="y", color=LINE)
for s in ("top", "right"): ax2.spines[s].set_visible(False)

ax3 = fig.add_axes([0.63, 0.16, 0.33, 0.25])
order = ["can", "plastic", "general"]
vals = [100*sum(cls[c])/len(cls[c]) for c in order]
bars = ax3.barh([KO[c] for c in order], vals, color=[BLUE, "#6aa6e0", "#a9c8ea"])
for b, v, c in zip(bars, vals, order):
    ax3.text(v + 2, b.get_y() + b.get_height()/2, f"{v:.0f}%  ({sum(cls[c])}/{len(cls[c])})", va="center", fontsize=12, color=INK)
ax3.set_xlim(0, 115); ax3.invert_yaxis(); ax3.tick_params(labelsize=13)
ax3.set_title("품목별 정확도 (2초 판단)", fontsize=14, color=INK, loc="left", fontweight="bold")
ax3.set_xticks([]); [ax3.spines[s].set_visible(False) for s in ("top", "right", "bottom")]

box = FancyBboxPatch((0.04, 0.015), 0.92, 0.055, boxstyle="round,pad=0.006,rounding_size=0.008",
                     transform=fig.transFigure, facecolor="#f3f5f7", edgecolor="none")
fig.patches.append(box)
fig.add_artist(plt.Line2D([0.045, 0.045], [0.022, 0.063], transform=fig.transFigure, color=BLUE, lw=5))
fig.text(0.06, 0.042, "결론: 판단은 1~2초면 충분하다. 오답은 시간이 아니라 학습에 없던 물건(케이블·펜·상자 등) 때문 → 데이터를 늘려야 한다.",
         fontsize=15, color=INK, va="center", fontweight="bold")
fig.savefig(f"{S}/slide_result.png", facecolor=BG)

# ── 그림 2: 결과 표 ──
fig = plt.figure(figsize=(16, 4.2), dpi=150, facecolor=BG)
fig.text(0.04, 0.86, f"판단 시간별 정확도 (실측 {N}회)", fontsize=24, fontweight="bold", color=INK)
ax = fig.add_axes([0.04, 0.14, 0.92, 0.62]); ax.axis("off")
cols = ["판단 시간"] + [f"{t:g}초" for t in TIMES]
rows = [["정확도"] + [f"{a:.0f}%" for a in acc],
        ["맞힌 횟수"] + [f"{sum(o)}/{N}" for o in oks],
        ["95% 신뢰구간"] + [f"{a:.0f}~{b:.0f}%" for a, b in zip(lo, hi)]]
tb = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center")
tb.auto_set_font_size(False); tb.set_fontsize(15); tb.scale(1, 3.2)
for (r, c), cell in tb.get_celld().items():
    cell.set_edgecolor(LINE); cell.set_linewidth(1)
    if r == 0:
        cell.set_facecolor("#f3f5f7"); cell.set_text_props(fontweight="bold", color=INK)
    if c == 0:
        cell.set_text_props(fontweight="bold", color=INK); cell.set_facecolor("#f3f5f7")
    if c == T2 + 1 and r > 0:
        cell.set_facecolor("#e4effa"); cell.set_text_props(color=BLUE, fontweight="bold")
fig.text(0.04, 0.04, f"판정 규칙: t초까지 찍힌 사진(0.5초 간격)의 확률 평균 · 강조한 열 = 채택한 판단 시간(2초) · 판정이 굳는 시점 90%: {p90:.1f}초",
         fontsize=12, color=MUTED)
fig.savefig(f"{S}/slide_table.png", facecolor=BG)
print("N", N, "acc", [round(a, 1) for a in acc], "p90", p90, {KO[c]: f"{sum(v)}/{len(v)}" for c, v in cls.items()})
