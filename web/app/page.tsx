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

export default function Dashboard() {
  const { supabase, bin, readings, collections, deposits, loaded, now } = useBinData();
  const [busy, setBusy] = useState<Compartment | null>(null);
  const latest = deposits[0];
  const photos = usePhotoUrls([latest?.photo_path ?? null]);
  const offline = isOffline(bin, now);

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
        <div className="mb-5 flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h1 className="text-xl font-bold sm:text-2xl">
            {bin ? `${bin.name} · ${bin.location}` : loaded ? "수거함을 찾을 수 없음" : "불러오는 중…"}
          </h1>
          {bin && (
            <span className="text-sm text-gray-500">
              <i className={`mr-1.5 inline-block size-2.5 rounded-full ${offline ? "bg-gray-400" : "bg-green-600"}`} />
              {offline ? "연결 끊김" : "연결됨"}
              {bin.last_seen_at && ` · 마지막 신호 ${agoText(bin.last_seen_at, now)}`}
            </span>
          )}
        </div>

        {offline && bin && (
          <div className="mb-5 rounded-lg border border-gray-400 bg-gray-100 px-4 py-3 text-sm">
            ⚠ 수거함 신호가 2분 넘게 없습니다. 전원이나 인터넷을 확인하세요. 아래 칸 상태는 마지막 기록 기준입니다.
          </div>
        )}

        <div className="grid gap-5 md:grid-cols-3">
          {COMPARTMENTS.map((c) => {
            const s = compartmentState(c, readings, collections);
            const full = s.status === "full";
            const count = deposits.filter((d) => d.dropped_into === c).length;
            return (
              <section
                key={c}
                className={`flex min-h-[300px] flex-col rounded-xl border-2 p-6 ${
                  full ? "border-red-600 bg-red-50" : "border-gray-300 bg-white"
                }`}
              >
                <h2 className="text-[22px] font-bold">{LABEL[c]}</h2>
                <div className="mb-4 text-[13px] text-gray-400">{KIND[c]}</div>
                <div className={`mb-2 text-3xl font-bold ${full ? "text-red-600" : "text-green-600"}`}>
                  ● {full ? "가득참" : "정상"}
                </div>
                <div className="mb-4 text-sm text-gray-500">
                  {full && s.fullSince
                    ? `${fmtDateTime(s.fullSince)}부터 (${sinceText(s.fullSince, now)})`
                    : s.lastCollectedAt
                      ? `마지막 수거 ${fmtDateTime(s.lastCollectedAt)}`
                      : "수거 기록 없음"}
                </div>
                <div className="text-sm text-gray-700">
                  오늘 투입 <b className="text-xl">{count}</b>개
                </div>
                {s.needsSensorCheck && (
                  <div className="mt-3 rounded-md border border-yellow-500 bg-yellow-50 px-3 py-2 text-[13px]">
                    ⚠ 센서 확인 필요: 수거 완료 후에도 센서가 감지 중입니다. 덜 비웠거나 센서가 가려졌을 수 있습니다.
                  </div>
                )}
                <button
                  onClick={() => collect(c)}
                  disabled={busy === c}
                  className={`mt-auto h-12 rounded-lg text-[17px] font-bold disabled:opacity-50 ${
                    full ? "bg-red-600 text-white" : "border-2 border-gray-300 bg-white text-gray-700"
                  }`}
                >
                  {busy === c ? "기록 중…" : "수거 완료"}
                </button>
              </section>
            );
          })}
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-4 rounded-xl border-2 border-gray-300 bg-white px-6 py-4 text-[15px]">
          <b>방금 들어온 쓰레기</b>
          {latest ? (
            <>
              <Photo url={latest.photo_path ? photos[latest.photo_path] : undefined} className="h-12 w-16" />
              <span className="rounded-full bg-blue-50 px-2.5 py-0.5 font-bold">{LABEL[latest.predicted]}</span>
              <span>확신도 {Math.round(latest.confidence * 100)}%</span>
              <span className="text-gray-400">{fmtTime(latest.created_at)}</span>
            </>
          ) : (
            <span className="text-gray-400">오늘 들어온 쓰레기가 없습니다</span>
          )}
          <Link href="/log" className="ml-auto text-blue-700 underline">
            투입 기록 전체 보기 →
          </Link>
        </div>
      </main>
    </>
  );
}
