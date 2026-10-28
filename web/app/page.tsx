"use client";

import Link from "next/link";
import { useState } from "react";
import Header from "@/components/Header";
import Photo from "@/components/Photo";
import {
  BIN_ID, COMPARTMENTS, KIND, LABEL, agoText, compartmentState, fmtDateTime, fmtTime, isOffline, sinceText,
  type Compartment,
} from "@/lib/bin";
import { useBinData, usePhotoUrls } from "@/lib/useBinData";

function Stat({ label, value, tone = "text-ink" }: { label: string; value: React.ReactNode; tone?: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel px-5 py-4">
      <div className="text-[13px] text-muted">{label}</div>
      <div className={`mt-1 font-mono text-3xl font-bold tabular-nums ${tone}`}>{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const { supabase, bin, readings, collections, deposits, loaded, now } = useBinData();
  const [busy, setBusy] = useState<Compartment | null>(null);
  const latest = deposits[0];
  const photos = usePhotoUrls([latest?.photo_path ?? null]);
  const offline = isOffline(bin, now);
  const states = Object.fromEntries(
    COMPARTMENTS.map((c) => [c, compartmentState(c, readings, collections)]),
  ) as Record<Compartment, ReturnType<typeof compartmentState>>;
  const fullCount = COMPARTMENTS.filter((c) => states[c].status === "full").length;

  async function collect(c: Compartment) {
    if (!confirm(`${LABEL[c]} 칸을 비웠나요? 수거 완료로 기록합니다.`)) return;
    setBusy(c);
    const { error } = await supabase.from("collections").insert({ bin_id: BIN_ID, compartment: c });
    setBusy(null);
    if (error) alert("기록하지 못했습니다: " + error.message);
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-6xl p-4 sm:p-7">
        <div className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-2">
          <h1 className="text-xl font-bold sm:text-2xl">
            {bin ? `${bin.name} · ${bin.location}` : loaded ? "수거함을 찾을 수 없음" : "불러오는 중…"}
          </h1>
          {bin && (
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm ${
                offline ? "border-off/50 text-off" : "border-ok/40 bg-ok/10 text-ok"
              }`}
            >
              <span className="relative flex size-2.5">
                {!offline && (
                  <span className="absolute inline-flex size-full rounded-full bg-ok opacity-60 motion-safe:animate-ping" />
                )}
                <span className={`relative inline-flex size-2.5 rounded-full ${offline ? "bg-off" : "bg-ok"}`} />
              </span>
              {offline ? "연결 끊김" : "연결됨"}
              {bin.last_seen_at && <span className="text-muted">· 마지막 신호 {agoText(bin.last_seen_at, now)}</span>}
            </span>
          )}
        </div>

        {offline && bin && (
          <div className="mb-5 rounded-lg border border-off/50 bg-panel px-4 py-3 text-sm text-muted">
            <b className="text-ink">⚠ 수거함 신호가 2분 넘게 없습니다.</b> 전원이나 인터넷을 확인하세요. 아래 칸 상태는 마지막 기록
            기준입니다.
          </div>
        )}

        <div className="mb-5 grid grid-cols-3 gap-3 sm:gap-5">
          <Stat label="오늘 투입" value={<>{deposits.length}<span className="ml-1 text-base text-muted">개</span></>} />
          <Stat
            label="가득찬 칸"
            value={<>{fullCount}<span className="ml-1 text-base text-muted">/ 3</span></>}
            tone={fullCount > 0 ? "text-full" : "text-ok"}
          />
          <Stat
            label="마지막 투입"
            value={latest ? fmtTime(latest.created_at).slice(0, 5) : "--:--"}
            tone={latest ? "text-ink" : "text-dim"}
          />
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {COMPARTMENTS.map((c) => {
            const s = states[c];
            const full = s.status === "full";
            const count = deposits.filter((d) => d.dropped_into === c).length;
            const sensor = readings
              .filter((r) => r.compartment === c)
              .reduce<(typeof readings)[number] | null>((a, r) => (!a || r.created_at > a.created_at ? r : a), null);
            return (
              <section
                key={c}
                className={`relative flex min-h-[300px] flex-col overflow-hidden rounded-xl border p-6 ${
                  full
                    ? "border-full/70 bg-full/10 shadow-[0_0_32px_-8px_var(--color-full)]"
                    : "border-line bg-panel"
                }`}
              >
                <div className={`absolute inset-x-0 top-0 h-1 ${full ? "bg-full" : s.needsSensorCheck ? "bg-warn" : "bg-ok"}`} />
                <div className="flex items-baseline justify-between">
                  <h2 className="text-[22px] font-bold">{LABEL[c]}</h2>
                  <span className="text-[13px] text-dim">{KIND[c]}</span>
                </div>
                <div
                  className={`mb-1 mt-5 flex items-center gap-2.5 text-3xl font-bold ${full ? "text-full" : "text-ok"}`}
                >
                  <span className={`size-3 rounded-full ${full ? "bg-full motion-safe:animate-pulse" : "bg-ok"}`} />
                  {full ? "가득참" : "정상"}
                </div>
                <div className="mb-5 text-sm text-muted">
                  {full && s.fullSince
                    ? `${fmtDateTime(s.fullSince)}부터 (${sinceText(s.fullSince, now)})`
                    : s.lastCollectedAt
                      ? `마지막 수거 ${fmtDateTime(s.lastCollectedAt)}`
                      : "수거 기록 없음"}
                </div>
                <div className="flex items-baseline gap-1.5 border-t border-line pt-4 text-sm text-muted">
                  오늘 투입 <b className="font-mono text-2xl tabular-nums text-ink">{count}</b>개
                </div>
                <div className="mt-2 flex items-center gap-2 text-[13px] text-muted">
                  <span
                    className={`size-2 rounded-full ${!sensor ? "bg-dim" : sensor.detected ? "bg-full" : "bg-ok"}`}
                  />
                  IR 센서{" "}
                  <b className={!sensor ? "font-medium text-dim" : sensor.detected ? "text-full" : "text-ok"}>
                    {!sensor ? "기록 없음" : sensor.detected ? "감지 중" : "비어있음"}
                  </b>
                  {sensor && <span className="text-dim">· {agoText(sensor.created_at, now)} 바뀜</span>}
                </div>
                {s.needsSensorCheck && (
                  <div className="mt-3 rounded-md border border-warn/50 bg-warn/10 px-3 py-2 text-[13px] text-warn">
                    ⚠ 센서 확인 필요: 수거 완료 후에도 센서가 감지 중입니다. 덜 비웠거나 센서가 가려졌을 수 있습니다.
                  </div>
                )}
                <button
                  onClick={() => collect(c)}
                  disabled={busy === c}
                  className={`mt-auto h-12 rounded-lg text-[17px] font-bold transition-colors disabled:opacity-50 ${
                    full
                      ? "bg-full text-white hover:bg-full/85"
                      : "border border-line text-muted hover:border-muted hover:text-ink"
                  }`}
                >
                  {busy === c ? "기록 중…" : "수거 완료"}
                </button>
              </section>
            );
          })}
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-4 rounded-xl border border-line bg-panel px-6 py-4 text-[15px]">
          <b className="text-muted">방금 들어온 쓰레기</b>
          {latest ? (
            <>
              <Photo url={latest.photo_path ? photos[latest.photo_path] : undefined} className="h-12 w-16" />
              <span className="rounded-full border border-accent/40 bg-accent/10 px-2.5 py-0.5 font-bold text-accent">
                {LABEL[latest.predicted]}
              </span>
              <span>
                확신도 <b className="font-mono tabular-nums">{Math.round(latest.confidence * 100)}%</b>
              </span>
              <span className="font-mono tabular-nums text-dim">{fmtTime(latest.created_at)}</span>
            </>
          ) : (
            <span className="text-dim">오늘 들어온 쓰레기가 없습니다</span>
          )}
          <Link href="/log" className="ml-auto text-accent hover:underline">
            투입 기록 전체 보기 →
          </Link>
        </div>
      </main>
    </>
  );
}
