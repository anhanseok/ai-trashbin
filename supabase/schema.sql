-- AI 분리수거함 수거 관제 DB
-- Supabase 대시보드 → SQL Editor 에 통째로 붙여 넣고 Run.
-- 용어는 CONTEXT.md 기준. 칸 상태(정상/가득참/센서 확인 필요/연결 끊김)는 저장하지 않고 웹이 기록으로 계산한다.

-- ── 수거함 ──
create table bins (
  id           text primary key,                 -- 예: 'bin-01'
  name         text not null,                    -- 예: '수거함 #01'
  location     text not null,                    -- 예: '강남대 정문 버스정류장'
  last_seen_at timestamptz                       -- 수거함이 30초마다 갱신하는 연결 신호
);

-- 칸 이름 = 모델 라벨 (plastic=페트, can=캔, general=일반)
create domain compartment as text check (value in ('plastic', 'can', 'general'));

-- ── 투입: 쓰레기 하나가 들어와 칸에 담기기까지의 한 번 ──
create table deposits (
  id            bigint generated always as identity primary key,
  bin_id        text not null references bins(id),
  created_at    timestamptz not null default now(),
  photo_path    text,                            -- Storage 'photos' 버킷 안 경로
  predicted     compartment not null,            -- AI 판정 품목
  confidence    real not null check (confidence between 0 and 1),  -- 확신도
  dropped_into  compartment not null,            -- 실제로 들어간 칸 (확신도 70% 미만이면 general)
  corrected     compartment,                     -- 판정 수정: 관리자가 바로잡은 품목 (null = 수정 안 함)
  corrected_at  timestamptz
);
create index on deposits (bin_id, created_at desc);

-- ── 센서 기록: 칸의 IR 센서 값이 바뀔 때만 한 줄 ──
create table sensor_readings (
  id          bigint generated always as identity primary key,
  bin_id      text not null references bins(id),
  compartment compartment not null,
  detected    boolean not null,                  -- true = 칸 높이 80% 지점까지 참
  created_at  timestamptz not null default now()
);
create index on sensor_readings (bin_id, compartment, created_at desc);

-- ── 수거 기록: 관리자가 수거 완료를 누를 때마다 한 줄 ──
create table collections (
  id          bigint generated always as identity primary key,
  bin_id      text not null references bins(id),
  compartment compartment not null,
  created_at  timestamptz not null default now(),
  collected_by uuid default auth.uid()           -- 누른 관리자
);
create index on collections (bin_id, compartment, created_at desc);

-- ── 권한 ──
-- 수거함(파이)은 service_role 키를 쓰므로 RLS 를 거치지 않는다.
-- 웹은 로그인한 관리자(authenticated)만 읽고, 수거 완료와 판정 수정만 할 수 있다.
alter table bins            enable row level security;
alter table deposits        enable row level security;
alter table sensor_readings enable row level security;
alter table collections     enable row level security;

create policy "관리자 읽기" on bins            for select to authenticated using (true);
create policy "관리자 읽기" on deposits        for select to authenticated using (true);
create policy "관리자 읽기" on sensor_readings for select to authenticated using (true);
create policy "관리자 읽기" on collections     for select to authenticated using (true);
create policy "수거 완료"   on collections     for insert to authenticated with check (true);
create policy "판정 수정"   on deposits        for update to authenticated using (true) with check (true);

-- 판정 수정 때 관리자가 바꿀 수 있는 열을 corrected, corrected_at 으로 제한
revoke update on deposits from authenticated;
grant update (corrected, corrected_at) on deposits to authenticated;

-- ── 실시간 전달 (새로고침 없이 웹에 반영) ──
alter publication supabase_realtime add table bins, deposits, sensor_readings, collections;

-- ── 투입 사진 저장소 (비공개, 로그인한 관리자만 볼 수 있음) ──
insert into storage.buckets (id, name, public) values ('photos', 'photos', false);
create policy "관리자 사진 읽기" on storage.objects for select to authenticated using (bucket_id = 'photos');

-- ── 시험용 수거함 1대 ──
insert into bins (id, name, location) values ('bin-01', '수거함 #01', '강남대 정문 버스정류장');
