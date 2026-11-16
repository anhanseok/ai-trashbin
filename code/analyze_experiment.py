"""
experiment.py 결과로 "판단 시간 ↔ 정확도" 표와 그래프를 만든다 (PC에서 실행).

사용법:  python analyze_experiment.py <실험 폴더> <정답 목록>
         정답 목록: 넣은 순서대로 쉼표로. "이름*개수" 로 묶어 써도 된다.
         예) 캔*10,페트*10,일반*10   또는   페트,캔,캔,일반
         이름: 캔/can, 페트/플라스틱/plastic, 일반/general
결과:    <실험 폴더>/result.csv     판단 시간별 정확도·95% 신뢰구간·측정별 ○✕
         <실험 폴더>/tradeoff.png   판단 시간 ↔ 정확도 (오차 막대, 최적점)
         <실험 폴더>/settle.png     판정이 굳는 시점 분포
         <실험 폴더>/rules.png      판단 규칙 비교 (걸린 시간 ↔ 정확도)
판정 규칙: t초까지 찍힌 사진들의 확률 평균에서 빈 받침판을 뺀 가장 높은 품목.
최적점: 정확도가 최고값의 2%p 이내에 처음 들어오는 가장 짧은 시간.
"""
import csv, glob, json, math, os, sys
import numpy as np

TIMES = [0.5, 1, 2, 3, 5, 7, 10, 20, 30]
NAME = {"캔": "can", "can": "can", "페트": "plastic", "플라스틱": "plastic", "plastic": "plastic",
        "일반": "general", "general": "general"}
KO = {"can": "캔", "plastic": "페트", "general": "일반"}
DETECT_CONF = 0.60   # main.py 의 현재 규칙 (같은 판정 2번 연속, 확신 60% 이상)


def parse_answers(text):
    out = []
    for part in text.split(","):
        part = part.strip()
        name, _, n = part.partition("*")
        out += [NAME[name.strip()]] * (int(n) if n else 1)
    return out


def wilson(k, n, z=1.96):
    """정확도의 95% 신뢰구간 (윌슨 구간). 반환: (아래, 위) %"""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * max(0, c - h), 100 * min(1, c + h)


def decide(rows, labels, T):
    use = [r["p"] for r in rows if r["t"] <= T + 1e-6] or [rows[0]["p"]]
    mean = np.mean(use, axis=0)
    mean[labels.index("empty")] = 0
    return labels[int(np.argmax(mean))], float(mean.max() / max(1e-9, mean.sum()))


def settle_time(rows, labels):
    """누적 평균 판정이 마지막으로 바뀐 시각."""
    P = np.array([r["p"] for r in rows])
    cum = np.cumsum(P, axis=0)
    cum[:, labels.index("empty")] = 0
    dec = cum.argmax(1)
    last = 0.0
    for i in range(1, len(dec)):
        if dec[i] != dec[i - 1]:
            last = rows[i]["t"]
    return last


def current_rule(rows, labels):
    """main.py 규칙: 빈 받침판이 아닌 같은 판정이 확신 60% 이상으로 2번 연속 → (판정, 걸린 시간)."""
    prev = None
    for r in rows:
        p = np.array(r["p"])
        lab = labels[int(np.argmax(p))]
        if lab == "empty" or p.max() < DETECT_CONF:
            prev = None
            continue
        if lab == prev:
            return lab, r["t"]
        prev = lab
    return None, rows[-1]["t"]


def main():
    folder, answers = sys.argv[1], parse_answers(sys.argv[2])
    meta = json.load(open(os.path.join(folder, "meta.json")))
    labels = meta["labels"]
    files = sorted(glob.glob(os.path.join(folder, "item_*.jsonl")))
    if len(files) != len(answers):
        sys.exit(f"측정 기록 {len(files)}개, 정답 {len(answers)}개: 개수가 다릅니다")
    items = [[json.loads(l) for l in open(f)] for f in files]
    times = [T for T in TIMES if T <= meta["record_sec"] + 1e-6]
    n = len(answers)

    acc, lo, hi, conf, per_item = [], [], [], [], []
    for T in times:
        res = [decide(rows, labels, T) for rows in items]
        ok = [lab == ans for (lab, _), ans in zip(res, answers)]
        k = sum(ok)
        acc.append(100 * k / n); a, b = wilson(k, n); lo.append(a); hi.append(b)
        conf.append(100 * np.mean([c for _, c in res])); per_item.append(ok)
    best = max(acc)
    kbest = next(i for i, a in enumerate(acc) if a >= best - 2)

    settles = [settle_time(rows, labels) for rows in items]
    cur = [current_rule(rows, labels) for rows in items]
    cur_acc = 100 * sum(l == a for (l, _), a in zip(cur, answers)) / n
    cur_lat = float(np.mean([t for _, t in cur]))

    # 품목별 정확도 (최적점 기준)
    by_cls = {}
    for ok, ans in zip(per_item[kbest], answers):
        by_cls.setdefault(ans, []).append(ok)

    with open(os.path.join(folder, "result.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["판단 시간(초)"] + times)
        w.writerow(["정확도(%)"] + [f"{a:.1f}" for a in acc])
        w.writerow(["95% 신뢰구간 아래(%)"] + [f"{a:.1f}" for a in lo])
        w.writerow(["95% 신뢰구간 위(%)"] + [f"{a:.1f}" for a in hi])
        w.writerow(["맞힌 개수"] + [f"{sum(o)}/{len(o)}" for o in per_item])
        w.writerow(["평균 확신도(%)"] + [f"{c:.1f}" for c in conf])
        w.writerow([])
        w.writerow(["현재 규칙(2번 연속)", f"정확도 {cur_acc:.1f}%", f"평균 {cur_lat:.2f}초"])
        w.writerow(["판정이 굳는 시점(초)", f"중앙값 {np.median(settles):.1f}", f"90% {np.percentile(settles, 90):.1f}",
                    f"최대 {max(settles):.1f}"])
        w.writerow([])
        w.writerow(["측정", "정답", "굳는 시점(초)"] + times)
        for i, ans in enumerate(answers):
            w.writerow([f"{i+1}", KO[ans], f"{settles[i]:.1f}"] + ["○" if per_item[j][i] else "✕" for j in range(len(times))])

    print("판단 시간 :", "  ".join(f"{t:>6g}s" for t in times))
    print("정확도    :", "  ".join(f"{a:6.1f}%" for a in acc))
    print("95% 구간  :", "  ".join(f"{a:3.0f}~{b:3.0f}" for a, b in zip(lo, hi)))
    print(f"최적점: {times[kbest]:g}초 (정확도 {acc[kbest]:.1f}%, 최고 {best:.1f}%)")
    print("최적점 품목별:", ", ".join(f"{KO[c]} {100*sum(v)/len(v):.0f}% ({sum(v)}/{len(v)})" for c, v in by_cls.items()))
    missed = sum(l is None for l, _ in cur)
    print(f"현재 규칙(2번 연속): 정확도 {cur_acc:.1f}%, 평균 {cur_lat:.2f}초"
          + (f" (기록 시간 안에 판단 못 함 {missed}회 → 틀린 것으로, 걸린 시간은 기록 끝으로 계산)" if missed else ""))
    print(f"판정이 굳는 시점: 중앙값 {np.median(settles):.1f}초, 90%는 {np.percentile(settles, 90):.1f}초 안, 최대 {max(settles):.1f}초")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False
    BLUE, ORANGE = "#0b6bcb", "#e0661c"

    # 1) 판단 시간 ↔ 정확도
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
    ax.axvspan(times[0] * 0.8, times[kbest], color="#f4d6d2", alpha=.5, lw=0)
    if kbest + 1 < len(times):
        ax.axvspan(times[kbest + 1], times[-1] * 1.15, color="#dbe6f3", alpha=.5, lw=0)
    ax.errorbar(times, acc, yerr=[np.array(acc) - lo, np.array(hi) - acc], fmt="-o", color=BLUE,
                ecolor="#8fb8e3", elinewidth=2, capsize=4, lw=2.6, ms=7, zorder=3, label="정확도 (95% 신뢰구간)")
    for t, a in zip(times, acc):
        ax.text(t, a + 2, f"{a:.0f}%", ha="center", fontsize=9.5, color=BLUE)
    ax.plot(times[kbest], acc[kbest], marker="*", ms=24, color=ORANGE, zorder=4)
    ax.annotate(f"최적점 {times[kbest]:g}초\n정확도 {acc[kbest]:.0f}% (최고 {best:.0f}%)",
                xy=(times[kbest], acc[kbest]), xytext=(times[kbest] * 1.8, max(5, acc[kbest] - 30)), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.6))
    ax.axhline(best - 2, color="#888", ls="--", lw=1)
    ax.set_xscale("log"); ax.set_xticks(times); ax.set_xticklabels([f"{t:g}" for t in times])
    ax.set_xlim(times[0] * 0.8, times[-1] * 1.15); ax.set_ylim(0, 105)
    ax.set_xlabel("판단 시간 (초)  ·  로그 눈금", fontsize=12); ax.set_ylabel("분류 정확도 (%)", fontsize=12)
    ax.set_title(f"판단 시간과 정확도의 트레이드오프 (실측 {n}회)", fontsize=15, fontweight="bold", loc="left")
    ax.legend(loc="lower right"); ax.grid(alpha=.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(folder, "tradeoff.png")); plt.close(fig)

    # 2) 판정이 굳는 시점 분포
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
    bins = [0, 0.25] + [t for t in times if t > 0.25] + [meta["record_sec"] + 0.01]
    bins = sorted(set(bins))
    ax.hist(settles, bins=bins, color=BLUE, edgecolor="white")
    p90 = np.percentile(settles, 90)
    ax.axvline(p90, color=ORANGE, lw=2, ls="--")
    ax.text(p90, ax.get_ylim()[1] * 0.92, f"  90%가 {p90:.1f}초 안에 굳음", color=ORANGE, fontsize=11)
    ax.set_xlabel("판정이 마지막으로 바뀐 시점 (초)", fontsize=12); ax.set_ylabel("측정 횟수", fontsize=12)
    ax.set_title(f"AI 판정이 굳는 시점 (실측 {n}회)", fontsize=15, fontweight="bold", loc="left")
    ax.grid(alpha=.3, axis="y")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(folder, "settle.png")); plt.close(fig)

    # 3) 판단 규칙 비교
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.plot(times, acc, "-o", color=BLUE, lw=2, ms=6, label="t초 평균으로 판단")
    ax.plot(cur_lat, cur_acc, "s", color="#555", ms=11, label="현재 규칙: 같은 판정 2번 연속")
    ax.annotate(f"현재 규칙\n{cur_lat:.1f}초 · {cur_acc:.0f}%", xy=(cur_lat, cur_acc),
                xytext=(cur_lat * 1.6, max(5, cur_acc - 25)), fontsize=10.5,
                arrowprops=dict(arrowstyle="->", color="#555"))
    ax.plot(times[kbest], acc[kbest], marker="*", ms=22, color=ORANGE, label=f"최적점 {times[kbest]:g}초 평균")
    ax.set_xscale("log"); ax.set_xticks(times); ax.set_xticklabels([f"{t:g}" for t in times])
    ax.set_ylim(0, 105); ax.set_xlabel("판단까지 걸린 시간 (초)", fontsize=12); ax.set_ylabel("정확도 (%)", fontsize=12)
    ax.set_title("판단 규칙 비교: 빠르기와 정확도", fontsize=15, fontweight="bold", loc="left")
    ax.legend(loc="lower right"); ax.grid(alpha=.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(folder, "rules.png")); plt.close(fig)
    print("저장:", folder, "(result.csv, tradeoff.png, settle.png, rules.png)")


if __name__ == "__main__":
    main()
