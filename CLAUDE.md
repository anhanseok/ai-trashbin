# ai-trashbin

- 용어는 [CONTEXT.md](CONTEXT.md)를 따른다.
- 사용자가 "기획서 작성 다시할게"라고 하면 [스펙.md](스펙.md) 맨 아래 "이어서 할 일"의 남은 일을 grilling 형식(번호 + 추천 답)으로 묻고, 답을 받으면 스펙.md에 반영한다. (1~11번 초안은 완료)
- 코드 작업 순서 (2026-10-15 기준, ①~⑤ 완료, ⑥ 부품 대기): ① Supabase 프로젝트 생성·[supabase/schema.sql](supabase/schema.sql) 실행·관리자 계정·`code/.env` 작성(사용자) → ② 파이에 .env 복사·DB 연결 시험 → ③ `main.py`를 새 테이블에 맞게 수정(사진 업로드, 센서 변경 기록, 30초 신호) → ④ 관리자 웹(Next.js) → ⑤ Vercel 배포 → ⑥ 부품 도착 후 카메라·서보 시험, 조립, 촬영, 학습 → ⑦ 전체 연결 시험. 사용자가 "코드 이어서 할게"라고 하면 남은 첫 단계부터 안내한다.
- 라즈베리파이: 사용자 `pi`, 호스트 `raspberrypi`, SSH 키로 접속. 와이파이는 집 iptime5G(192.168.0.4, 우선)와 아이폰 핫스팟(172.20.10.x) 두 곳이 등록되어 있음. 주소가 바뀌면 MAC 2c-cf-67-09-09-bd 로 찾는다. 실제 보드는 **Raspberry Pi 4 Model B 8GB**(파이 5 아님, ElectroCookie 팬 케이스). 저장소는 `~/ai-trashbin`, venv는 `code/env`, sudo는 비밀번호 없이 가능.
- Supabase 프로젝트 ref `ojxtixdmnedotimnsfcr`(서울). 관리 API 토큰은 `.supabase-token`, 웹 키는 `web/.env.local`, 수거함 키는 `code/.env` (모두 Git 제외). 웹은 `web/`(Next.js 15, `npm run dev`).
- 배포: https://ai-trashbin.vercel.app (Vercel 프로젝트 hanseok1/ai-trashbin, 루트 `web`). master에 푸시하면 자동 배포. 관리자 계정 hanseogan@naver.com, 비밀번호는 로컬 `.admin-login`.
- 카메라·서보 없이 웹 연동 시험: 파이에서 `cd ~/ai-trashbin/code && env/bin/python fake_bin.py 5 5` (가짜 투입 + 페트 칸 가득참). 2026-10-15 시험 데이터(투입 3건, 페트 가득참)가 DB에 남아 있음 — 사용자가 화면을 본 뒤 지울 것.
