# AI 자동 분류 쓰레기통

카메라로 쓰레기를 보고 AI가 분류해, 서보모터로 받침판을 돌리고 기울여 4칸 중 맞는 칸에 떨어뜨리는 장치. (학교 과제)

## 구조

```
초음파 감지 → 촬영 → AI 분류(플라스틱/캔/종이/일반) → 회전+기울임 서보 → 해당 칸 낙하 → 원위치
```

- **두뇌:** 라즈베리파이 5 (보유)
- **AI:** Teachable Machine(MobileNet 전이학습) → `.tflite` 모델을 Pi에서 추론
- **구동:** PCA9685 드라이버 + 서보 2개 (회전 45°/135°, 기울임 40°/140°)로 2×2 4칸 처리
- **감지:** 초음파 센서 HC-SR04

## 설계서 (그림·배선도·코드·7일 일정)

https://claude.ai/artifact/KeB9UdGiyKLhXWbqM8xq9U

## 예산

10만 원 이하. 상세 부품표는 설계서 3번 참고.

## 구매 계획

- **알리 (여분 넉넉히, Choice 상품):** 서보 MG996R 4개, PCA9685 2개, HC-SR04 3개, Pi5 카메라 케이블 2개, 저항·점퍼선 세트
- **국내 (디바이스마트/엘레파츠):** 카메라 모듈 3, 5V 3A 어댑터 — 비싸거나 안전 관련이라 불량 시 교환이 빨라야 함

## 외관

직접 제작 대신 기성 4칸(2×2) 분리수거함 위에 장치를 얹는 방향. (2칸+서보 1개 축소안도 가능)

## 참고 자료

- SmartSort (GitHub): https://github.com/dapsanz/SmartSort
- Fab Academy AI sorter: https://fabacademy.org/2022/labs/kamakura/students/atsufumi-suzuki/Final%20Project/1.AI-sorter.html
- CircuitDigest 자동 분리수거 (Hackster): https://www.hackster.io/CircuitDigest/smart-automatic-waste-segregation-system-using-arduino-uno-q-2f8dca

## 다음 할 일

- [ ] 쿠팡에서 2×2 구조 4칸 분리수거함 찾기
- [ ] 알리/국내 부품 주문
- [ ] 1일차: OS 설치 + 카메라 테스트
