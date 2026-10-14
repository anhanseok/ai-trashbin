"""
카메라·서보 없이 웹 연동을 시험하는 가짜 수거함. main.py 와 같은 cloud.py 로 보낸다.
실행: python fake_bin.py [투입 횟수=5] [간격 초=5]
      python fake_bin.py 0   → 연결 신호만 계속 보냄 (부품 오기 전 heartbeat.service 가 이렇게 실행)
- 연결 신호를 보내 웹에 "연결됨"이 뜬다
- 무작위 품목·확신도로 투입을 보낸다 (확신도 70% 미만이면 일반 칸, main.py 와 같은 규칙)
- 마지막에 페트 칸을 가득참으로 만든다 (PIN_IR 을 쓰지 않아도 웹 표시를 볼 수 있게)
Ctrl+C 로 끝내면 연결 신호가 멈추고, 2분 뒤 웹에 "연결 끊김"이 뜬다.
"""
import random
import sys
import time

from PIL import Image, ImageDraw

import config as C
from cloud import Cloud
from logic import choose_compartment

COLOR = {"plastic": (120, 180, 230), "can": (200, 200, 200), "general": (190, 160, 120)}


def fake_photo(label, conf):
    img = Image.new("RGB", (640, 480), COLOR[label])
    d = ImageDraw.Draw(img)
    d.rectangle((220, 140, 420, 340), outline=(0, 0, 0), width=4)
    d.text((240, 230), f"FAKE {label} {conf:.0%}", fill=(0, 0, 0))
    return img


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    gap = float(sys.argv[2]) if len(sys.argv) > 2 else 5
    cloud = Cloud()
    if not cloud.sb:
        sys.exit("Supabase 키가 없습니다. code/.env 를 확인하세요.")

    for n in range(count):
        label = random.choice(list(C.BINS))
        conf = random.uniform(0.55, 0.99)
        into = choose_compartment(label, conf)
        cloud.deposit(fake_photo(label, conf), label, conf, into)
        print(f"[{n + 1}/{count}] 투입: {label} {conf:.0%} → {into} 칸")
        time.sleep(gap)

    if count > 0:                             # 0 이면 연결 신호만 보냄 (heartbeat.service)
        cloud.sensor("plastic", True)
        print("페트 칸 가득참 신호 보냄. 웹에서 빨간색으로 바뀌는지 확인하세요.")
    cloud.flush()
    print("연결 신호를 계속 보냅니다. Ctrl+C 로 끝내세요.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n종료")


if __name__ == "__main__":
    main()
