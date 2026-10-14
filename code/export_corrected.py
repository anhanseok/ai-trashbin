"""
재학습 데이터 모으기: 관리자가 판정 수정한 투입 사진을 정답 품목 폴더로 내려받는다.
실행: python export_corrected.py           → data/corrected/<품목>/*.jpg
      python export_corrected.py --all     → 수정 안 한 투입도 판정 품목(=정답으로 간주) 폴더에 함께
그다음 data 폴더를 zip 으로 묶어 model/train_mobilenetv2.ipynb 에 올리면 같이 학습된다.
"""
import os
import sys

import config as C
from supabase import create_client


def main():
    if not (C.SUPABASE_URL and C.SUPABASE_KEY):
        sys.exit("Supabase 키가 없습니다. code/.env 를 확인하세요.")
    take_all = "--all" in sys.argv
    sb = create_client(C.SUPABASE_URL, C.SUPABASE_KEY)

    rows, start = [], 0
    while True:                                   # 1000줄씩 끊어 읽기
        q = sb.table("deposits").select("id,photo_path,predicted,corrected") \
              .eq("bin_id", C.BIN_ID).not_.is_("photo_path", "null")
        if not take_all:
            q = q.not_.is_("corrected", "null")
        page = q.order("id").range(start, start + 999).execute().data
        rows += page
        if len(page) < 1000:
            break
        start += 1000

    saved = 0
    for r in rows:
        answer = r["corrected"] or r["predicted"]
        folder = os.path.join("data", "corrected", answer)
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, f"{r['id']}.jpg")
        if os.path.exists(dest):
            continue
        try:
            open(dest, "wb").write(sb.storage.from_("photos").download(r["photo_path"]))
            saved += 1
        except Exception as e:
            print("내려받기 실패:", r["photo_path"], e)

    counts = {c: len(os.listdir(os.path.join("data", "corrected", c)))
              for c in C.BINS if os.path.isdir(os.path.join("data", "corrected", c))}
    print(f"새로 받은 사진 {saved}장, 폴더별:", counts)


if __name__ == "__main__":
    main()
