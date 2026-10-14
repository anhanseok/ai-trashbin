# ai-trashbin

- 용어는 [CONTEXT.md](CONTEXT.md)를 따른다.
- 사용자가 "기획서 작성 다시할게"라고 하면 [스펙.md](스펙.md) 맨 아래 "이어서 할 일"의 남은 일을 grilling 형식(번호 + 추천 답)으로 묻고, 답을 받으면 스펙.md에 반영한다. (1~11번 초안은 완료)
- 코드 작업 순서 (2026-10-14 기준, ① 진행 중): ① Supabase 프로젝트 생성·[supabase/schema.sql](supabase/schema.sql) 실행·관리자 계정·`code/.env` 작성(사용자) → ② 파이에 .env 복사·DB 연결 시험 → ③ `main.py`를 새 테이블에 맞게 수정(사진 업로드, 센서 변경 기록, 30초 신호) → ④ 관리자 웹(Next.js) → ⑤ Vercel 배포 → ⑥ 부품 도착 후 카메라·서보 시험, 조립, 촬영, 학습 → ⑦ 전체 연결 시험. 사용자가 "코드 이어서 할게"라고 하면 남은 첫 단계부터 안내한다.
- 라즈베리파이: 사용자 `pi`, 호스트 `raspberrypi`, 아이폰 핫스팟(172.20.10.x)에서 SSH 키로 접속. 저장소는 `~/ai-trashbin`, venv는 `code/env`, sudo는 비밀번호 없이 가능.
