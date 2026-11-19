"""중간에 끊겨 두 폴더로 나뉜 실험 기록을 하나로 합친다 (번호를 이어 붙임).
사용법: python merge_runs.py <결과 폴더> <폴더1> <폴더2> ...
"""
import os, shutil, sys

out, srcs = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
n = 0
for src in srcs:
    items = sorted({f.split("_")[1][:2] for f in os.listdir(src) if f.startswith("item_")})
    for it in items:
        n += 1
        for f in os.listdir(src):
            if f.startswith(f"item_{it}"):
                shutil.copy(os.path.join(src, f), os.path.join(out, f.replace(f"item_{it}", f"item_{n:02d}", 1)))
    if os.path.exists(os.path.join(src, "meta.json")):
        shutil.copy(os.path.join(src, "meta.json"), os.path.join(out, "meta.json"))
print(out, n, "items")
