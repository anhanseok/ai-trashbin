-- 공개 화면(/live)용: 로그인 없이 칸 상태만 읽는 함수 (2026-11-17)
-- 테이블 권한은 그대로 두고(관리자만 읽기), 이 함수가 필요한 칸·시각만 골라서 돌려준다.
-- 사진 경로·확신도·판정 수정은 내보내지 않는다.
create or replace function public_status(p_bin text, p_since timestamptz)
returns json
language sql
stable
security definer
set search_path = public
as $$
  select json_build_object(
    'bin', (select json_build_object('name', name, 'location', location, 'last_seen_at', last_seen_at)
            from bins where id = p_bin),
    'readings', coalesce((select json_agg(r order by r.created_at desc) from (
        select compartment, detected, created_at from sensor_readings
        where bin_id = p_bin order by created_at desc limit 300) r), '[]'::json),
    'collections', coalesce((select json_agg(c order by c.created_at desc) from (
        select compartment, created_at from collections
        where bin_id = p_bin order by created_at desc limit 300) c), '[]'::json),
    'deposits', coalesce((select json_agg(d order by d.created_at desc) from (
        select predicted, dropped_into, created_at from deposits
        where bin_id = p_bin and created_at >= p_since order by created_at desc limit 1000) d), '[]'::json)
  );
$$;

revoke all on function public_status(text, timestamptz) from public;
grant execute on function public_status(text, timestamptz) to anon, authenticated;
