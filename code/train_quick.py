"""학습 사진(data/<클래스>/)으로 MobileNetV2 전이학습 → model_unquant.tflite, labels.txt (PC, TensorFlow 필요)
사용법: python train_quick.py data .   (결과를 현재 폴더에 저장 → 파이 code/ 로 복사)
2026-11-16 첫 모델: 사진 95장(캔 36, 페트 21, 일반 10, 빈 28), 20에포크
main.py 와 같은 전처리: 640x480 에서 왼쪽 CROP_LEFT 부터 480x480 정사각형 → 224x224 → x/127.5-1"""
import os, sys, random
import numpy as np
from PIL import Image
import tensorflow as tf

DATA = sys.argv[1]
OUT = sys.argv[2]
CROP_LEFT = 160
CLASSES = ["can", "empty", "general", "plastic"]
random.seed(0); np.random.seed(0); tf.random.set_seed(0)

def load(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size; s = min(w, h); left = min(CROP_LEFT, w - s)
    img = img.crop((left, (h - s) // 2, left + s, (h + s) // 2)).resize((224, 224))
    return np.asarray(img, dtype=np.float32) / 127.5 - 1

items = []
for i, c in enumerate(CLASSES):
    for f in sorted(os.listdir(os.path.join(DATA, c))):
        if f.endswith(".jpg"):
            items.append((os.path.join(DATA, c, f), i))
random.shuffle(items)
# 클래스별 15% 검증용 (대략적인 확인용, 같은 물건이 섞여 있어 실제보다 높게 나올 수 있음)
val, train = [], []
for i in range(len(CLASSES)):
    cls = [x for x in items if x[1] == i]
    k = max(1, round(len(cls) * 0.15))
    val += cls[:k]; train += cls[k:]
Xtr = np.stack([load(p) for p, _ in train]); ytr = np.array([y for _, y in train])
Xva = np.stack([load(p) for p, _ in val]); yva = np.array([y for _, y in val])
print("train", np.bincount(ytr, minlength=4), "val", np.bincount(yva, minlength=4))

counts = np.bincount(ytr, minlength=4)
cw = {i: len(ytr) / (4 * max(1, n)) for i, n in enumerate(counts)}

aug = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal_and_vertical"),
    tf.keras.layers.RandomRotation(0.08),
    tf.keras.layers.RandomContrast(0.2),
])
wtr = np.array([cw[int(y)] for y in ytr], dtype=np.float32)
ds = tf.data.Dataset.from_tensor_slices((Xtr, ytr.astype(np.int32), wtr)).shuffle(len(ytr)).batch(16) \
    .map(lambda x, y, w: (tf.clip_by_value(aug(x, training=True), -1, 1), y, w))

base = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights="imagenet", pooling="avg")
base.trainable = False
inp = tf.keras.Input((224, 224, 3))
x = base(inp, training=False)
x = tf.keras.layers.Dropout(0.2)(x)
outp = tf.keras.layers.Dense(4, activation="softmax")(x)
model = tf.keras.Model(inp, outp)
model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
model.fit(ds, epochs=20, validation_data=(Xva, yva.astype(np.int32)), verbose=2)

p = model.predict(Xva, verbose=0).argmax(1)
print("검증 정확도", float((p == yva).mean()), f"({(p == yva).sum()}/{len(yva)})")
for t, q, (path, _) in zip(yva, p, val):
    if t != q:
        print("  틀림:", os.path.basename(os.path.dirname(path)), os.path.basename(path), "→", CLASSES[q])

os.makedirs(OUT, exist_ok=True)
tfl = tf.lite.TFLiteConverter.from_keras_model(model).convert()
open(os.path.join(OUT, "model_unquant.tflite"), "wb").write(tfl)
open(os.path.join(OUT, "labels.txt"), "w", encoding="utf-8").write("".join(f"{i} {c}\n" for i, c in enumerate(CLASSES)))
print("저장", OUT, len(tfl) // 1024, "KB")
