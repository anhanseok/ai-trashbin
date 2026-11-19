"""재학습 한 번에: 관리자가 웹에서 확인한 사진 받기 → 학습 → 이전 모델과 채점 → 더 좋으면 파이에 올리기.

정답은 관리자가 정한다. 웹 투입 기록에서 "맞음"을 고르거나 품목을 고친 사진만 쓰고,
아무도 확인하지 않은 사진(AI 판정 그대로)은 쓰지 않는다.

사용법 (PC, code 폴더):
  python retrain.py                 기본 (11/16 이후 확인한 사진)
  python retrain.py --no-deploy     학습·채점만 하고 파이에는 안 올림
  python retrain.py --force         채점이 낮아도 올림

채점: data_test/<품목>/ 의 시험 사진(학습에 안 씀)으로 이전·새 모델을 똑같이 채점한다.
새 모델 정확도가 이전 이상일 때만 올린다. 파이의 이전 모델은 model_prev.tflite 로 남긴다.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
TEST = os.path.join(HERE, "data_test")
CUR = os.path.join(HERE, "model_unquant.tflite")
PI_HOSTS = ["172.20.10.5", "192.168.0.4"]
CROP_LEFT = 160
SINCE = "2026-11-16"
args = sys.argv[1:]


def step(n, msg):
    print(f"\n[{n}/4] {msg}", flush=True)


def run(cmd, **kw):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", TF_CPP_MIN_LOG_LEVEL="2")
    return subprocess.run(cmd, cwd=HERE, env=env, text=True, encoding="utf-8", errors="replace", **kw)


def load(path):  # train_quick.py, main.py 와 같은 전처리
    img = Image.open(path).convert("RGB")
    w, h = img.size; s = min(w, h); left = min(CROP_LEFT, w - s)
    img = img.crop((left, (h - s) // 2, left + s, (h + s) // 2)).resize((224, 224))
    return np.asarray(img, dtype=np.float32)[None] / 127.5 - 1


def score(model_path, labels):
    import tensorflow as tf
    it = tf.lite.Interpreter(model_path=model_path)
    it.allocate_tensors()
    i, o = it.get_input_details()[0], it.get_output_details()[0]
    ok = n = 0
    for c in labels:
        for f in glob.glob(os.path.join(TEST, c, "*.jpg")):
            it.set_tensor(i["index"], load(f)); it.invoke()
            ok += labels[int(it.get_tensor(o["index"])[0].argmax())] == c
            n += 1
    return ok / n * 100 if n else None, n


def find_pi():
    for h in PI_HOSTS:
        r = run(["ssh", "-o", "ConnectTimeout=4", "-o", "BatchMode=yes", f"pi@{h}", "true"], capture_output=True)
        if r.returncode == 0:
            return h
    return None


# 1) 관리자가 확인한 사진 받기
step(1, "웹에서 관리자가 확인한 사진 받기")
r = run([PY, "export_corrections.py", SINCE, "--only-corrected"])
if r.returncode:
    sys.exit("사진을 받지 못했습니다 (인터넷·Supabase 확인)")
counts = {c: len(os.listdir(os.path.join(HERE, "data", c))) for c in sorted(os.listdir(os.path.join(HERE, "data")))}
total = sum(counts.values())

# 2) 학습
step(2, f"학습 (사진 {total}장, 3~5분)")
out = tempfile.mkdtemp(prefix="retrain_")
r = run([PY, "train_quick.py", "data", out], capture_output=True)
new = os.path.join(out, "model_unquant.tflite")
if r.returncode or not os.path.exists(new):
    print(r.stdout[-2000:], r.stderr[-2000:])
    sys.exit("학습 실패")
labels = [ln.strip().split(" ", 1)[-1] for ln in open(os.path.join(out, "labels.txt"), encoding="utf-8")]

# 3) 채점
step(3, "이전 모델과 채점 비교 (시험 사진은 학습에 안 씀)")
old_acc, n = score(CUR, labels)
new_acc, _ = score(new, labels)
if n == 0:
    sys.exit("data_test 에 시험 사진이 없습니다")
print(f"  시험 사진 {n}장  이전 {old_acc:.1f}%  →  새 모델 {new_acc:.1f}%")
better = new_acc >= old_acc
if not better and "--force" not in args:
    print("  새 모델이 더 낮아서 올리지 않습니다. (그래도 올리려면 --force)")
    sys.exit(0)

# 4) 저장·파이에 올리기
step(4, "저장하고 파이에 올리기")
stamp = datetime.now().strftime("%m%d_%H%M")
shutil.copy(new, os.path.join(HERE, f"model_unquant_{total}_{stamp}.tflite"))  # 기록용
shutil.copy(new, CUR)
print(f"  PC: model_unquant.tflite 교체 (백업 model_unquant_{total}_{stamp}.tflite)")
if "--no-deploy" in args:
    sys.exit(0)
pi = find_pi()
if not pi:
    sys.exit("  파이를 찾지 못했습니다. 파이와 핫스팟을 켠 뒤 다시 실행하세요. (PC 모델은 이미 바뀜)")
remote = "ai-trashbin/code"
cmds = [
    ["ssh", f"pi@{pi}", f"cp {remote}/model_unquant.tflite {remote}/model_prev.tflite"],
    ["scp", "-q", CUR, f"pi@{pi}:{remote}/model_unquant.tflite"],
    ["ssh", f"pi@{pi}", "sudo systemctl restart trashbin.service && sleep 8 && systemctl is-active trashbin.service"],
]
for c in cmds:
    r = run(c, capture_output=True)
    if r.returncode:
        sys.exit(f"  파이에 올리다 실패: {r.stderr.strip()}")
print(f"  파이({pi}): 새 모델로 자동 분류 다시 시작 (이전 모델은 model_prev.tflite)")
print(f"\n완료: 정확도 {old_acc:.1f}% → {new_acc:.1f}%")
