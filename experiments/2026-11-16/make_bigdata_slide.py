"""발표용 1장: '버린 쓰레기는 빅데이터로!' — 쌓이는 기록 → 가득참 예측 → 수거 계획 (확장 계획).
구현된 것(기록 수집)과 계획(예측)을 구분해서 표시. 오른쪽 화면은 '예시 화면'으로 명시.
사용법: python make_bigdata_slide.py experiments/2026-11-16"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False

D = sys.argv[1]
INK, MUTED, LINE, BLUE, BLUE_BG, GREEN, GREEN_BG, ORANGE, ORANGE_BG, CARD, RED = (
    "#16202b", "#5a6876", "#d9e0e6", "#0b6bcb", "#e4effa", "#1f7a55", "#e3f4ec", "#b5541a", "#fbf0e8", "#f5f7f9", "#d33b2f")

W, H = 16, 9
fig = plt.figure(figsize=(W, H), dpi=150, facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

def card(x, y, w, h, fc=CARD, ec=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.18", facecolor=fc,
                                edgecolor=ec or fc, lw=1.4))

def chip(x, y, text, fg, bg):
    ax.add_patch(FancyBboxPatch((x, y - 0.17), 0.13 * len(text) + 0.5, 0.34, boxstyle="round,pad=0,rounding_size=0.17",
                                facecolor=bg, lw=0))
    ax.text(x + 0.25, y, text, fontsize=12, fontweight="bold", color=fg, va="center")

def arrow(x1, x2, y):
    ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=28, color=MUTED, lw=2.4))

ax.text(0.6, 8.3, "버린 쓰레기는 빅데이터로!", fontsize=36, fontweight="bold", color=INK, va="center")
ax.text(0.6, 7.65, "투입할 때마다 쌓이는 기록으로 \"언제 찰지\"를 미리 알고, 찰 통만 골라 수거한다",
        fontsize=17, color=MUTED, va="center")

# ① 쌓이는 데이터 (구현됨)
x, y, w, h = 0.6, 2.25, 4.6, 4.75
card(x, y, w, h)
ax.text(x + 0.35, y + h - 0.45, "① 쌓이는 데이터", fontsize=20, fontweight="bold", color=INK, va="center")
chip(x + 0.35, y + h - 1.0, "지금 수집 중", GREEN, GREEN_BG)
items = [("투입 기록", "시각 · 품목 · 확신도 · 들어간 칸 · 사진"),
         ("센서 기록", "칸별 가득참 감지 시각"),
         ("수거 기록", "칸을 비운 시각"),
         ("판정 수정", "관리자가 고친 정답 → 재학습")]
for i, (t, s) in enumerate(items):
    yy = y + h - 1.75 - i * 0.78
    ax.text(x + 0.35, yy, t, fontsize=16, fontweight="bold", color=INK, va="center")
    ax.text(x + 0.35, yy - 0.33, s, fontsize=12.5, color=MUTED, va="center")
arrow(5.35, 5.95, 4.6)

# ② 예측 (계획)
x2, w2 = 6.05, 4.6
card(x2, y, w2, h)
ax.text(x2 + 0.35, y + h - 0.45, "② 가득참 예측", fontsize=20, fontweight="bold", color=INK, va="center")
chip(x2 + 0.35, y + h - 1.0, "계획 · SP3 이후", ORANGE, ORANGE_BG)
steps = [("1단계  투입 속도", "칸별 최근 시간당 투입 수로\n가득참까지 남은 시간 계산"),
         ("2단계  패턴 학습", "요일 · 시간대 · 날씨 · 행사일별\n투입량을 학습해 예측"),
         ("3단계  여러 대", "수거함마다 예측 → 찰 통만\n골라 품목별 수거 동선")]
for i, (t, s) in enumerate(steps):
    yy = y + h - 1.75 - i * 1.05
    ax.text(x2 + 0.35, yy, t, fontsize=16, fontweight="bold", color=INK, va="center")
    ax.text(x2 + 0.35, yy - 0.47, s, fontsize=12.5, color=MUTED, va="center", linespacing=1.35)
arrow(10.8, 11.4, 4.6)

# ③ 대시보드 예시 화면
x3, w3 = 11.5, 3.9
card(x3, y, w3, h, fc="#0f1720")
ax.text(x3 + 0.3, y + h - 0.45, "③ 관리자 화면", fontsize=20, fontweight="bold", color="white", va="center")
ax.text(x3 + 0.3, y + h - 0.95, "예시 화면 · 숫자는 가상", fontsize=12, color="#f2b45a", va="center", fontweight="bold")
bins = [("페트", 0.82, "약 2시간 뒤 가득참", RED), ("캔", 0.45, "약 9시간 뒤", "#3ddc97"), ("일반", 0.63, "약 5시간 뒤", "#f2b45a")]
for i, (name, fill, txt, col) in enumerate(bins):
    yy = y + h - 1.75 - i * 0.92
    ax.text(x3 + 0.3, yy + 0.12, name, fontsize=15, fontweight="bold", color="white", va="center")
    ax.add_patch(FancyBboxPatch((x3 + 1.15, yy - 0.02), 2.4, 0.28, boxstyle="round,pad=0,rounding_size=0.14", facecolor="#24313f", lw=0))
    ax.add_patch(FancyBboxPatch((x3 + 1.15, yy - 0.02), 2.4 * fill, 0.28, boxstyle="round,pad=0,rounding_size=0.14", facecolor=col, lw=0))
    ax.text(x3 + 1.15, yy - 0.32, txt, fontsize=12, color="#c9d4de", va="center")
ax.text(x3 + 0.3, y + 0.55, "→ 오늘 오후 수거: 페트 칸", fontsize=14, fontweight="bold", color="#5fb0ff", va="center")

# 아래: 왜 중요한가
ax.add_patch(FancyBboxPatch((0.6, 0.55), 14.8, 1.25, boxstyle="round,pad=0,rounding_size=0.15", facecolor=BLUE_BG, lw=0))
ax.text(0.95, 1.42, "넘치기 전에 · 헛걸음 없이", fontsize=19, fontweight="bold", color=BLUE, va="center")
ax.text(0.95, 0.95, "가득찬 '뒤'에 알리는 지금 방식에서, 찰 '때'를 미리 아는 방식으로. 쌓일수록 정확해지고, 수거함 배치·수거 주기를 정하는 정책 근거가 된다.",
        fontsize=14, color=INK, va="center")
fig.savefig(f"{D}/slide_bigdata.png", facecolor="white")
print("saved")
