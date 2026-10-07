# code/ — 실행 순서

라즈베리파이 5에서 실행. 자세한 준비는 상위 폴더의 [SETUP.md](../SETUP.md) 참고.

| 파일 | 역할 | 실행 |
|---|---|---|
| `config.py` | 핀·각도·임계값 설정 (여기만 수정) | — |
| `test_servo.py` | 서보 2개 동작 확인 | `python test_servo.py` |
| `test_sensors.py` | 초음파·IR 센서 확인 | `python test_sensors.py` |
| `capture.py` | 학습 사진 수집 | `python capture.py plastic` |
| `main.py` | 전체 통합 실행 | `python main.py` |
| `trashbin.service` | 시연용 자동 시작 | SETUP.md 8번 |

## 순서

1. `test_servo.py` → 서보 OK
2. `test_sensors.py` → 센서 OK
3. `capture.py` 4개 클래스 → Teachable Machine 학습 → `model_unquant.tflite`, `labels.txt` 복사
4. `main.py` → 분류·투하 확인, `config.py`의 `PAN`/`TILT_DUMP` 조정
5. (웹) `.env` 설정 후 `main.py` → Supabase 기록 확인
6. `trashbin.service` 등록 → 자동 시작

## 주의
- venv는 `--system-site-packages` 로 생성 (picamera2·gpiozero 접근용)
- `.env`(Supabase 키)는 깃허브에 올리지 않음
- 각도는 실물 조립 후 `config.py`에서 조정
