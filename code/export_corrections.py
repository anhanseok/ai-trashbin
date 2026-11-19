"""DB에 쌓인 투입 사진을 학습 폴더로 내려받는다 (관리자 확인 → 재학습 데이터).
정답 = 관리자가 고친 값(corrected), 안 고쳤으면 판정 품목(predicted).
data/<정답>/db_<id>.jpg 로 저장하고, 이미 있는 파일은 건너뛴다.

사용법 (PC, code 폴더에서):
  python export_corrections.py [시작 날짜=2026-11-16] [--only-corrected]
그다음: python train_quick.py data .  → 새 model_unquant.tflite 를 파이로 복사"""
import glob, json, os, sys, urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
env = dict(l.strip().split("=", 1) for l in open(os.path.join(HERE, ".env"), encoding="utf-8")
           if "=" in l and not l.startswith("#"))
URL, KEY = env["SUPABASE_URL"], env["SUPABASE_KEY"]
HDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

args = [a for a in sys.argv[1:] if not a.startswith("--")]
since = args[0] if args else "2026-11-16"
only_corrected = "--only-corrected" in sys.argv


def get(path):
    return urllib.request.urlopen(urllib.request.Request(f"{URL}{path}", headers=HDR)).read()


rows = json.loads(get(f"/rest/v1/deposits?select=id,predicted,corrected,photo_path"
                      f"&created_at=gte.{since}&photo_path=not.is.null&order=id"))
saved, moved, skipped = Counter(), Counter(), 0
for r in rows:
    if only_corrected and not r["corrected"]:
        continue
    label = r["corrected"] or r["predicted"]
    out = os.path.join(HERE, "data", label, f"db_{r['id']}.jpg")
    # 학습에서 일부러 뺀 사진(data_hold: 손이 찍힘 등)과 시험 사진(data_test)은 다시 받지 않는다
    if any(glob.glob(os.path.join(HERE, d, "**", f"db_{r['id']}.jpg"), recursive=True) for d in ("data_hold", "data_test")):
        continue
    # 예전에 판정 품목으로 내려받은 뒤 관리자가 고쳤으면, 틀린 폴더의 같은 사진을 지운다
    for other in os.listdir(os.path.join(HERE, "data")):
        old = os.path.join(HERE, "data", other, f"db_{r['id']}.jpg")
        if other != label and os.path.exists(old):
            os.remove(old)
            moved[f"{other}→{label}"] += 1
    if os.path.exists(out):
        skipped += 1
        continue
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "wb").write(get(f"/storage/v1/object/photos/{r['photo_path']}"))
    saved[label] += 1

print(f"{since} 이후 {len(rows)}건 중 새로 저장 {sum(saved.values())}장 {dict(saved)}, 이미 있음 {skipped}장, 고친 품목으로 옮김 {dict(moved)}")
for c in sorted(os.listdir(os.path.join(HERE, "data"))):
    print(f"  data/{c}: {len(os.listdir(os.path.join(HERE, 'data', c)))}장")
