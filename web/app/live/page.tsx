"use client";

// 공개 화면: 로그인 없이 칸 상태와 오늘 투입 수만 보여 준다 (시연·시민용).
// 테이블은 관리자만 읽을 수 있어서, DB 함수 public_status 로 필요한 값만 받는다 (supabase/public_status.sql).
// 사진·확신도·판정 수정·수거 완료 버튼은 없다.
import { useCallback, useEffect, useMemo, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  BIN_ID, COMPARTMENTS, KIND, LABEL, agoText, compartmentState, fmtTime, isOffline, startOfTodayKST,
  type Bin, type Collection, type Compartment, type SensorReading,
} from "@/lib/bin";

type PublicDeposit = { predicted: Compartment; dropped_into: Compartment; created_at: string };
type Status = {
  bin: Omit<Bin, "id"> | null;
  readings: Omit<SensorReading, "id">[];
  collections: Omit<Collection, "id">[];
  deposits: PublicDeposit[];
};

const POLL_MS = 3000;

export default function LivePage() {
  const supabase = useMemo(() => createClient(), []);
  const [data, setData] = useState<Status | null>(null);
  const [error, setError] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  const load = useCallback(async () => {
    const { data, error } = await supabase.rpc("public_status", { p_bin: BIN_ID, p_since: startOfTodayKST() });
    setError(!!error);
    if (!error) setData(data as Status);
    setNow(Date.now());
  }, [supabase]);

  useEffect(() => {
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [load]);

  const bin = data?.bin ? { id: BIN_ID, ...data.bin } : null;
  const readings = (data?.readings ?? []).map((r, i) => ({ id: i, ...r }));
  const collections = (data?.collections ?? []).map((c, i) => ({ id: i, ...c }));
  const deposits = data?.deposits ?? [];
  const latest = deposits[0];
  const offline = isOffline(bin, now);
  const fresh = latest && now - new Date(latest.created_at).getTime() < 10000;

  return (
    <main className="mx-auto max-w-3xl p-4 sm:p-7">
      <header className="mb-6 flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-bold sm:text-xl">
          <span className="grid size-8 place-items-center rounded-md border border-ok/40 bg-ok/10 text-ok">♻</span>
          AI 분리수거함
        </h1>
        <a href="/login" className="text-sm text-dim hover:text-accent">관리자 로그인</a>
      </header>

      {error && !data && (
        <p className="rounded-lg border border-off/50 bg-panel px-4 py-3 text-sm text-muted">상태를 불러오지 못했습니다.</p>
      )}

      {bin && (
        <div className="mb-5 flex flex-wrap items-center gap-x-3 gap-y-2">
          <span className="text-muted">{bin.name} · {bin.location}</span>
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm ${
              offline ? "border-off/50 text-off" : "border-ok/40 bg-ok/10 text-ok"
            }`}
          >
            <span className={`size-2.5 rounded-full ${offline ? "bg-off" : "bg-ok motion-safe:animate-pulse"}`} />
            {offline ? "수거함 꺼짐" : "작동 중"}
          </span>
        </div>
      )}

      <div
        className={`mb-5 rounded-xl border px-5 py-5 transition-colors sm:px-6 ${
          fresh ? "border-accent bg-accent/10" : "border-line bg-panel"
        }`}
      >
        <div className="text-sm text-muted">방금 들어온 쓰레기</div>
        {latest ? (
          <div className="mt-1 flex flex-wrap items-baseline gap-x-3">
            <span className="text-3xl font-bold text-accent sm:text-4xl">{LABEL[latest.predicted]}</span>
            <span className="text-lg">→ {LABEL[latest.dropped_into]} 칸</span>
            <span className="font-mono text-sm tabular-nums text-dim">
              {fmtTime(latest.created_at)} · {agoText(latest.created_at, now)}
            </span>
          </div>
        ) : (
          <div className="mt-1 text-xl text-dim">{data ? "오늘은 아직 없어요" : "불러오는 중…"}</div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 sm:gap-4">
        {COMPARTMENTS.map((c) => {
          const full = compartmentState(c, readings, collections).status === "full";
          const count = deposits.filter((d) => d.dropped_into === c).length;
          return (
            <section
              key={c}
              className={`relative overflow-hidden rounded-xl border px-3 py-4 text-center sm:p-5 ${
                full ? "border-full/70 bg-full/10" : "border-line bg-panel"
              }`}
            >
              <div className={`absolute inset-x-0 top-0 h-1 ${full ? "bg-full" : "bg-ok"}`} />
              <h2 className="text-xl font-bold sm:text-2xl">{LABEL[c]}</h2>
              <div className="hidden text-[12px] text-dim sm:block">{KIND[c].split(" · ")[0]}</div>
              <div className={`mt-3 text-lg font-bold sm:text-2xl ${full ? "text-full" : "text-ok"}`}>
                {full ? "가득참" : "여유 있음"}
              </div>
              <div className="mt-3 border-t border-line pt-3 text-sm text-muted">
                오늘 <b className="font-mono text-2xl tabular-nums text-ink">{count}</b>개
              </div>
            </section>
          );
        })}
      </div>

      <p className="mt-6 text-center text-sm text-dim">
        오늘 총 <b className="font-mono tabular-nums text-muted">{deposits.length}</b>개 · 쓰레기를 넣으면 몇 초 안에 이 화면에 나타납니다
      </p>
    </main>
  );
}
