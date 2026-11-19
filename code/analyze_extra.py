"""
판단 시간 실험 기록 하나로 두 가지를 더 계산한다 (PC에서 실행, TensorFlow 필요).
 1) 확신도 기준(MIN_CONF)을 바꿔 가며: 맞는 칸 비율, 재활용 칸 오염률, 일반 칸으로 빠진 재활용품 비율
 2) 학습 사진 수가 다른 모델들로 같은 사진을 다시 판정: 판단 시간별 정확도

사용법: python analyze_extra.py <실험 폴더> <정답 목록> <판단 초> <모델이름=파일> ...
  예) python analyze_extra.py exp/20261118_28회_6초 "페트*8,캔*6,일반*14" 2 \
        95장=model_unquant_95장_1116.tflite 128장=model_unquant_128장_1117.tflite 171장=model_unquant_171장_1118.tflite
결과: <실험 폴더>/threshold.csv, models.csv
"""
import csv, glob, json, os, sys
import numpy as np
from PIL import Image
import tensorflow as tf
from analyze_experiment import parse_answers, wilson

folder, answers, T = sys.argv[1], parse_answers(sys.argv[2]), float(sys.argv[3])
models = [a.split("=", 1) for a in sys.argv[4:]]
meta = json.load(open(os.path.join(folder, "meta.json")))
LABELS = meta["labels"]
EMPTY = LABELS.index("empty")
CROP_LEFT = meta.get("crop_left", 160)
INTERVAL = meta.get("interval", 0.5)
TIMES = [0.5, 1, 2, 3, 5]


def mean_label(probs):
    """확률 평균에서 빈 받침판을 빼고 (품목, 확신도)."""
    m = np.mean(probs, axis=0).copy()
    m[EMPTY] = 0
    i = int(np.argmax(m))
    return LABELS[i], float(m[i] / max(1e-9, m.sum()))


# ---------- 1) 확신도 기준 (실험 때 모델의 기록 그대로) ----------
items = []
for n, truth in enumerate(answers, 1):
    rows = [json.loads(l) for l in open(os.path.join(folder, f"item_{n:02d}.jsonl"))]
    probs = [r["p"] for r in rows if r["t"] <= T + 1e-6]
    items.append((truth, *mean_label(probs)))

out = []
for c in np.arange(0.30, 0.96, 0.05):
    into = [("general" if conf < c else lab) for _, lab, conf in items]
    truths = [t for t, _, _ in items]
    right = sum(i == t for i, t in zip(into, truths))
    rec_in = [(i, t) for i, t in zip(into, truths) if i in ("plastic", "can")]
    contam = sum(i != t for i, t in rec_in)
    rec = [(i, t) for i, t in zip(into, truths) if t in ("plastic", "can")]
    to_gen = sum(i == "general" for i, _ in rec)
    out.append({"기준": round(c * 100), "맞는칸": right, "전체": len(into),
                "맞는칸%": round(100 * right / len(into), 1),
                "재활용칸_오염": contam, "재활용칸_투입": len(rec_in),
                "오염률%": round(100 * contam / max(1, len(rec_in)), 1),
                "일반으로_빠진_재활용품": to_gen, "재활용품": len(rec),
                "일반행%": round(100 * to_gen / max(1, len(rec)), 1)})
with open(os.path.join(folder, "threshold.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
print(f"확신도 기준 (판단 {T:g}초 평균)")
for r in out:
    print(f"  {r['기준']:3d}%  맞는 칸 {r['맞는칸%']:5.1f}%  오염 {r['재활용칸_오염']}/{r['재활용칸_투입']} ({r['오염률%']}%)  "
          f"재활용품→일반 {r['일반으로_빠진_재활용품']}/{r['재활용품']} ({r['일반행%']}%)")


# ---------- 2) 모델별 다시 판정 ----------
def prep(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size; s = min(w, h); left = min(CROP_LEFT, w - s)
    img = img.crop((left, (h - s) // 2, left + s, (h + s) // 2)).resize((224, 224))
    return np.asarray(img, dtype=np.float32)[None] / 127.5 - 1


photos = {}
for n in range(1, len(answers) + 1):
    fs = sorted(glob.glob(os.path.join(folder, f"item_{n:02d}_*.jpg")))
    photos[n] = [prep(f) for f in fs]

rows = []
for name, path in models:
    it = tf.lite.Interpreter(model_path=path); it.allocate_tensors()
    i_in, i_out = it.get_input_details()[0]["index"], it.get_output_details()[0]["index"]
    preds = {}
    for n, xs in photos.items():
        ps = []
        for x in xs:
            it.set_tensor(i_in, x); it.invoke(); ps.append(it.get_tensor(i_out)[0].astype(float))
        preds[n] = ps
    for t in TIMES:
        k = int(round(t / INTERVAL)) + 1          # 0초 사진부터 t초 사진까지
        hits = [mean_label(preds[n][:k])[0] == answers[n - 1] for n in preds]
        lo, hi = wilson(sum(hits), len(hits))
        per = {c: f"{sum(h for h, a in zip(hits, answers) if a == c)}/{answers.count(c)}" for c in ("plastic", "can", "general")}
        rows.append({"모델": name, "판단초": t, "정답": sum(hits), "전체": len(hits),
                     "정확도%": round(100 * sum(hits) / len(hits), 1), "아래%": round(lo, 1), "위%": round(hi, 1),
                     "페트": per["plastic"], "캔": per["can"], "일반": per["general"]})
with open(os.path.join(folder, "models.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print("\n모델별 정확도 (같은 사진 다시 판정)")
for r in rows:
    print(f"  {r['모델']:5s} {r['판단초']:>4}초  {r['정확도%']:5.1f}% ({r['정답']}/{r['전체']})  "
          f"[{r['아래%']}~{r['위%']}]  페트 {r['페트']} 캔 {r['캔']} 일반 {r['일반']}")
