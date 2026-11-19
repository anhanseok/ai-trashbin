"""실험 기록으로 혼동행렬(판정 품목·들어간 칸) 계산. 판단 T초 평균, 확신도 기준 MIN_CONF.
사용법: python confusion.py <실험 폴더> <정답 목록> [T=2] [MIN_CONF=0.65]"""
import json, os, sys
import numpy as np
from analyze_experiment import parse_answers

folder, answers = sys.argv[1], parse_answers(sys.argv[2])
T = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
MC = float(sys.argv[4]) if len(sys.argv) > 4 else 0.65
labels = json.load(open(os.path.join(folder, "meta.json")))["labels"]
E = labels.index("empty")
C = ["plastic", "can", "general"]
pred = np.zeros((3, 3), int); bins = np.zeros((3, 3), int)
for n, truth in enumerate(answers, 1):
    rows = [json.loads(l) for l in open(os.path.join(folder, f"item_{n:02d}.jsonl"))]
    m = np.mean([r["p"] for r in rows if r["t"] <= T + 1e-6], axis=0); m[E] = 0
    lab = labels[int(np.argmax(m))]; conf = m.max() / m.sum()
    into = "general" if conf < MC else lab
    pred[C.index(truth), C.index(lab)] += 1
    bins[C.index(truth), C.index(into)] += 1
for name, M in (("판정 품목", pred), ("들어간 칸", bins)):
    print(f"[{name}] 세로 실제(페트·캔·일반) / 가로 {name}  정확도 {np.trace(M)}/{M.sum()} = {np.trace(M)/M.sum():.1%}")
    for r, c in zip(M, ("페트", "캔", "일반")):
        print(f"  {c}: {list(r)}")
