# 라즈베리파이 도착 후 체크리스트

순서대로 하나씩. 각 단계의 **통과 기준**을 만족해야 다음으로 넘어갑니다.

## 0. 굽기 전 설정 (SD카드 구울 때 1회)

- [ ] [Raspberry Pi Imager](https://www.raspberrypi.com/software/)로 **Raspberry Pi OS (64-bit)** 선택
- [ ] "설정을 편집"에서:
  - [ ] 사용자 이름·비밀번호 정하고 **메모**
  - [ ] 무선 LAN: 집 와이파이(2.4GHz) SSID·비밀번호, 국가 `KR`
  - [ ] **SSH 사용** 체크 (비밀번호 인증)
- [ ] 굽기 → SD카드를 Pi에 꽂고 전원

## 1. SSH 접속 확인

- [ ] Pi와 이 PC를 **같은 와이파이**에 연결
- [ ] PC 터미널에서 `ssh 사용자이름@raspberrypi.local` 접속
- [ ] 접속되면 Pi 주소(IP)를 메모 → **클로드에게 알려주면 이후 원격으로 진행**

**통과 기준:** PC에서 Pi에 ssh로 접속됨

## 2. 라이브러리 설치 (한 번)

```bash
sudo apt update && sudo apt full-upgrade -y
sudo raspi-config nonint do_i2c 0
sudo reboot
```
재부팅 후:
```bash
git clone https://github.com/anhanseok/ai-trashbin.git
cd ai-trashbin/code
python3 -m venv --system-site-packages env
source env/bin/activate
pip install -r requirements.txt
```

**통과 기준:** 설치 중 에러 없음 (에러 나면 메시지 복사 → 클로드)

## 3. 카메라 테스트

```bash
rpicam-hello -t 5000
```
**통과 기준:** 5초간 카메라 영상이 보임

## 4. 서보 테스트 (배선 후)

```bash
i2cdetect -y 1          # 표에 40 이 보여야 함
python test_servo.py
```
**통과 기준:** 회전·기울임 서보가 차례로 움직이고 가운데(90°)에서 멈춤

## 5. 센서 테스트 (초기 단계에서는 건너뜀 — 센서 추가 후)

```bash
python test_sensors.py
```
**통과 기준:** 손을 대면 초음파 거리 값이 줄고, IR 센서를 가리면 해당 칸이 "참"으로 바뀜

## 6. 데이터 수집 + 학습 (조립 완료 후)

```bash
python capture.py plastic   # 페트병 올리고 Enter 반복
python capture.py can
python capture.py general
python capture.py empty
```
- `data` 폴더를 노트북으로 옮겨 [Teachable Machine](https://teachablemachine.withgoogle.com/train/image)에서 학습
- 모델 내보내기 → TensorFlow Lite → `model_unquant.tflite`, `labels.txt`를 `code/` 폴더에 복사

**통과 기준:** 학습에 안 쓴 사진 5장 중 4장 이상 맞음

## 7. 전체 통합

```bash
python main.py
```
- 엉뚱한 칸에 가면 `main.py`의 `PAN` 각도만 조정 (클로드가 도움)

**통과 기준:** 쓰레기 20개 중 16개 이상 맞는 칸에 들어감

## 8. 자동 시작 설정 (시연용)

```bash
sudo cp trashbin.service /etc/systemd/system/
sudo systemctl enable trashbin.service
sudo reboot
```
**통과 기준:** 전원만 꽂아도 (SSH 없이) 자동으로 분류가 작동
