"""쓰레기 투입 수요 예측 (임시 데이터 시연용).

실제 운영 데이터가 아직 적어서, 캠퍼스 수거함 1대를 가정한 임시 투입 기록 900건(11/1~11/19)을 만들고
칸별 하루 투입 수를 예측해 11/20~11/30 수요와 가득참 예상일을 낸다.

모델 4개를 같은 조건(11/1~11/12 학습 → 11/13~11/19 7일 채점)으로 비교하고,
오차(MAE)가 가장 작은 모델로 전체 기간을 다시 학습해 예측한다.

사용법 (PC, code 폴더):  python forecast_demo.py
결과:   ../web/lib/forecast-data.json  (웹 /forecast 페이지가 읽음)
        ../experiments/2026-11-19-forecast/synthetic_deposits.csv  (임시 데이터 원본)
"""
import json
import os
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import PoissonRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "..", "web", "lib", "forecast-data.json")
OUT_DIR = os.path.join(HERE, "..", "experiments", "2026-11-19-forecast")

COMPS = ["plastic", "can", "general"]
N_RECORDS = 900
HIST_START, HIST_END = date(2026, 11, 1), date(2026, 11, 19)      # 임시 기록 기간
FC_START, FC_END = date(2026, 11, 20), date(2026, 11, 30)          # 예측 기간
TEST_DAYS = 7                                                       # 채점용 마지막 7일
CAPACITY = {"plastic": 120, "can": 150, "general": 100}            # 칸 하나에 들어가는 개수 (가정)

rng = np.random.default_rng(1119)


# ── 1. 임시 데이터 900건 ──────────────────────────────────────────────
# 캠퍼스 수거함 가정: 평일 > 주말, 금요일·축제 전후 캔 증가, 점심·저녁 시간대에 몰림, 완만한 증가 추세
def day_weight(d: date) -> float:
    dow = d.weekday()                       # 0=월
    base = [1.15, 1.1, 1.1, 1.05, 1.25, 0.55, 0.45][dow]
    trend = 1 + 0.012 * (d - HIST_START).days
    return base * trend


def comp_share(d: date) -> np.ndarray:
    dow = d.weekday()
    s = np.array([0.32, 0.22, 0.46])         # 페트·캔·일반
    if dow == 4:                             # 금요일 저녁 캔 음료 증가
        s = s + np.array([0.0, 0.08, -0.08])
    if dow >= 5:                             # 주말엔 일반쓰레기 비중 증가
        s = s + np.array([-0.03, -0.03, 0.06])
    return s / s.sum()


HOURS = np.arange(8, 22)
HOUR_W = np.array([2, 4, 5, 6, 12, 13, 7, 6, 7, 8, 11, 9, 6, 4], float)
HOUR_W /= HOUR_W.sum()

days = pd.date_range(HIST_START, HIST_END).date
w = np.array([day_weight(d) for d in days])
per_day = rng.multinomial(N_RECORDS, w / w.sum())     # 정확히 900건이 되게 나눔

rows = []
for d, n in zip(days, per_day):
    comps = rng.choice(3, size=n, p=comp_share(d))
    hours = rng.choice(HOURS, size=n, p=HOUR_W)
    for c, h in zip(comps, hours):
        t = datetime(d.year, d.month, d.day, int(h), int(rng.integers(0, 60)), int(rng.integers(0, 60)))
        rows.append({"created_at": t.isoformat(), "compartment": COMPS[c]})
deposits = pd.DataFrame(rows).sort_values("created_at").reset_index(drop=True)
assert len(deposits) == N_RECORDS

os.makedirs(OUT_DIR, exist_ok=True)
deposits.to_csv(os.path.join(OUT_DIR, "synthetic_deposits.csv"), index=False, encoding="utf-8")

# 칸별 하루 투입 수
deposits["date"] = pd.to_datetime(deposits["created_at"]).dt.date
daily = (deposits.groupby(["date", "compartment"]).size().unstack(fill_value=0)
         .reindex(index=days, columns=COMPS, fill_value=0))


# ── 2. 특징: 요일(원-핫) + 경과 일수(추세) ─────────────────────────────
def features(ds) -> np.ndarray:
    ds = list(ds)
    dow = np.zeros((len(ds), 7))
    for i, d in enumerate(ds):
        dow[i, d.weekday()] = 1
    t = np.array([[(d - HIST_START).days / 30] for d in ds])
    return np.hstack([dow, t])


# ── 3. 모델 4개 ───────────────────────────────────────────────────────
def m_moving_avg(train: pd.Series, ds):
    return np.full(len(ds), train.iloc[-7:].mean())


def m_same_weekday(train: pd.Series, ds):
    out = []
    for d in ds:
        same = [v for td, v in train.items() if td.weekday() == d.weekday()]
        out.append(np.mean(same[-2:]))
    return np.array(out)


def m_poisson(train: pd.Series, ds):
    m = PoissonRegressor(alpha=0.05, max_iter=1000).fit(features(train.index), train.values)
    return m.predict(features(ds))


def m_gbm(train: pd.Series, ds):
    m = HistGradientBoostingRegressor(loss="poisson", max_iter=200, learning_rate=0.05,
                                      min_samples_leaf=3, random_state=0)
    m.fit(features(train.index), train.values)
    return m.predict(features(ds))


MODELS = [
    ("moving_avg", "최근 7일 평균", "직전 7일 평균을 그대로 이어감 (기준선)", m_moving_avg),
    ("same_weekday", "같은 요일 평균", "최근 2주 같은 요일 값의 평균", m_same_weekday),
    ("poisson", "포아송 회귀", "요일 + 추세로 '하루 개수'를 예측하는 회귀. 개수 데이터 전용", m_poisson),
    ("gbm", "그래디언트 부스팅", "결정나무 여러 개를 쌓는 모델 (포아송 손실)", m_gbm),
]

train_days, test_days = days[:-TEST_DAYS], days[-TEST_DAYS:]
scores = []
for key, name, desc, fn in MODELS:
    err = []
    for c in COMPS:
        tr = daily.loc[list(train_days), c]
        pred = fn(tr, test_days)
        err.append(np.abs(pred - daily.loc[list(test_days), c].values))
    err = np.concatenate(err)
    actual_total = daily.loc[list(test_days)].values.sum()
    scores.append({"key": key, "name": name, "desc": desc,
                   "mae": round(float(err.mean()), 2),                       # 칸·하루당 평균 오차(개)
                   "wape": round(float(err.sum() / actual_total * 100), 1)})  # 전체 대비 오차율(%)
best = min(scores, key=lambda s: s["mae"])
best_fn = next(fn for key, _, _, fn in MODELS if key == best["key"])

# ── 4. 고른 모델로 전체 기간 다시 학습 → 11/20~11/30 예측 ───────────────
fc_days = pd.date_range(FC_START, FC_END).date
fc = {c: np.clip(best_fn(daily[c], fc_days), 0, None) for c in COMPS}

series = []
for d in days:
    row = {"date": d.isoformat(), "kind": "actual"}
    for c in COMPS:
        row[c] = int(daily.loc[d, c])
    row["total"] = int(daily.loc[d].sum())
    series.append(row)
for i, d in enumerate(fc_days):
    lam = sum(fc[c][i] for c in COMPS)
    row = {"date": d.isoformat(), "kind": "forecast"}
    for c in COMPS:
        row[c] = round(float(fc[c][i]), 1)
    row["total"] = round(float(lam), 1)
    row["lo"], row["hi"] = int(poisson.ppf(0.1, lam)), int(poisson.ppf(0.9, lam))   # 80% 예측 구간
    series.append(row)

# 칸별: 예측 합계, 가득참 예상일 (11/20 아침에 비웠다고 가정하고 누적)
comps_out = []
for c in COMPS:
    cum, full_on = 0.0, None
    for i, d in enumerate(fc_days):
        cum += fc[c][i]
        if full_on is None and cum >= CAPACITY[c]:
            full_on = d.isoformat()
    total = float(fc[c].sum())
    comps_out.append({"key": c, "forecast_total": round(total, 1),
                      "per_day": round(total / len(fc_days), 1),
                      "capacity": CAPACITY[c], "full_on": full_on})

# 시간대별 비중 (임시 데이터 전체)
hourly = deposits.assign(h=pd.to_datetime(deposits["created_at"]).dt.hour).groupby("h").size()
hourly_out = [{"hour": int(h), "share": round(float(hourly.get(h, 0) / N_RECORDS * 100), 1)} for h in HOURS]

out = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "note": "임시 데이터(시뮬레이션) — 실제 운영 기록 아님",
    "records": N_RECORDS,
    "history": [HIST_START.isoformat(), HIST_END.isoformat()],
    "forecast_range": [FC_START.isoformat(), FC_END.isoformat()],
    "train_end": train_days[-1].isoformat(),
    "test_range": [test_days[0].isoformat(), test_days[-1].isoformat()],
    "best": best["key"],
    "models": scores,
    "series": series,
    "compartments": comps_out,
    "hourly": hourly_out,
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("모델 비교 (11/13~11/19, 칸·하루당 평균 오차):")
for s in scores:
    print(f"  {s['name']:<10} MAE {s['mae']:5.2f}개  WAPE {s['wape']:5.1f}%{'  ← 선택' if s is best else ''}")
for c in comps_out:
    print(f"  {c['key']:<8} 11/20~30 예측 {c['forecast_total']:6.1f}개, 가득참 예상 {c['full_on']}")
print("저장:", os.path.normpath(OUT_JSON))
