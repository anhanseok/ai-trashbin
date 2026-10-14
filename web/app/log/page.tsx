"use client";

import { useState } from "react";
import Header from "@/components/Header";
import Photo from "@/components/Photo";
import {
  COMPARTMENTS, LABEL, MIN_CONF, fmtTime, startOfTodayKST, type Compartment, type Deposit,
} from "@/lib/bin";
import { useBinData, usePhotoUrls } from "@/lib/useBinData";

type Filter = "all" | Compartment;

export default function LogPage() {
  const { supabase, readings, collections, deposits, loaded } = useBinData();
  const [filter, setFilter] = useState<Filter>("all");
  const shown = filter === "all" ? deposits : deposits.filter((d) => d.dropped_into === filter);
  const photos = usePhotoUrls(shown.slice(0, 50).map((d) => d.photo_path));

  const today = startOfTodayKST();
  const counts = Object.fromEntries(
    COMPARTMENTS.map((c) => [c, deposits.filter((d) => d.dropped_into === c).length]),
  ) as Record<Compartment, number>;
  const max = Math.max(1, ...Object.values(counts));
  const lowConf = deposits.filter((d) => d.confidence < MIN_CONF).length;
  const fullEvents = readings.filter((r) => r.detected && r.created_at >= today).length;
  const collected = collections.filter((c) => c.created_at >= today).length;
  const corrected = deposits.filter((d) => d.corrected).length;
  // 실제 정확도: 관리자가 다른 품목으로 고치지 않은 투입의 비율 (기획서 7-4)
  const wrong = deposits.filter((d) => d.corrected && d.corrected !== d.predicted).length;
  const accuracy = deposits.length > 0 ? ((deposits.length - wrong) / deposits.length) * 100 : null;

  async function correct(d: Deposit, value: string) {
    const corrected = value === "" ? null : (value as Compartment);
    const { error } = await supabase
      .from("deposits")
      .update({ corrected, corrected_at: corrected ? new Date().toISOString() : null })
      .eq("id", d.id);
    if (error) alert("수정하지 못했습니다: " + error.message);
  }

  return (
    <>
      <Header />
      <main className="mx-auto grid max-w-6xl gap-5 p-4 sm:p-7 lg:grid-cols-[1fr_360px]">
        <section className="rounded-xl border-2 border-gray-300 bg-white p-5 sm:px-6">
          <h2 className="mb-3.5 text-lg font-bold">오늘 투입 기록</h2>
          <div className="mb-3.5 flex flex-wrap gap-2 text-sm">
            {(["all", ...COMPARTMENTS] as Filter[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-full border px-3 py-1 ${
                  filter === f ? "border-gray-900 bg-gray-900 text-white" : "border-gray-300"
                }`}
              >
                {f === "all" ? "전체" : LABEL[f]}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] border-collapse text-[15px]">
              <thead>
                <tr className="border-b border-gray-200 text-left text-[13px] text-gray-400">
                  <th className="py-1.5 font-normal">사진</th>
                  <th className="font-normal">시각</th>
                  <th className="font-normal">판정 품목</th>
                  <th className="font-normal">확신도</th>
                  <th className="font-normal">들어간 칸</th>
                  <th className="font-normal">관리자 확인</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((d) => (
                  <tr key={d.id} className="border-b border-gray-100">
                    <td className="py-2">
                      <Photo url={d.photo_path ? photos[d.photo_path] : undefined} className="h-12 w-[72px]" />
                    </td>
                    <td>{fmtTime(d.created_at)}</td>
                    <td>
                      <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-sm font-bold">{LABEL[d.predicted]}</span>
                    </td>
                    <td>{Math.round(d.confidence * 100)}%</td>
                    <td>
                      {LABEL[d.dropped_into]}
                      {d.confidence < MIN_CONF && <span className="text-[13px] text-amber-700"> · 확신 부족</span>}
                    </td>
                    <td>
                      <select
                        value={d.corrected ?? ""}
                        onChange={(e) => correct(d, e.target.value)}
                        className={`rounded-md border px-2 py-1 text-[13px] ${
                          d.corrected ? "border-amber-600 text-amber-700" : "border-blue-700 text-blue-700"
                        }`}
                      >
                        <option value="">{d.corrected ? "수정 취소" : "맞음 (수정 ▾)"}</option>
                        {COMPARTMENTS.map((c) => (
                          <option key={c} value={c}>→ {LABEL[c]}로 수정</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {loaded && shown.length === 0 && <p className="py-10 text-center text-gray-400">기록이 없습니다</p>}
          </div>
        </section>

        <section className="self-start rounded-xl border-2 border-gray-300 bg-white p-5 sm:px-6">
          <h2 className="mb-3.5 text-lg font-bold">오늘 품목별 투입량</h2>
          <div className="flex h-[200px] items-end gap-6 border-b-2 border-gray-300 px-2">
            {COMPARTMENTS.map((c) => (
              <div key={c} className="flex flex-1 flex-col items-center justify-end gap-1.5 text-sm">
                {counts[c]}
                <div className="w-full rounded-t bg-slate-400" style={{ height: `${(counts[c] / max) * 170}px` }} />
              </div>
            ))}
          </div>
          <div className="flex gap-6 px-2 pt-2 text-[15px] font-bold">
            {COMPARTMENTS.map((c) => (
              <span key={c} className="flex-1 text-center">{LABEL[c]}</span>
            ))}
          </div>
          <div className="mt-5 space-y-1 text-sm text-gray-700">
            <p>총 투입 <b className="text-lg text-gray-900">{deposits.length}</b>개</p>
            <p>
              확신 부족으로 일반 처리 <b className="text-lg text-gray-900">{lowConf}</b>개
              {deposits.length > 0 && ` (${((lowConf / deposits.length) * 100).toFixed(1)}%)`}
            </p>
            <p>
              오늘 가득참 발생 <b className="text-lg text-gray-900">{fullEvents}</b>회 · 수거 완료{" "}
              <b className="text-lg text-gray-900">{collected}</b>회
            </p>
            <p>관리자가 수정한 판정 <b className="text-lg text-gray-900">{corrected}</b>개 → 재학습 데이터</p>
            <p>
              실제 정확도{" "}
              <b className={`text-lg ${accuracy !== null && accuracy < 85 ? "text-red-600" : "text-gray-900"}`}>
                {accuracy === null ? "-" : `${accuracy.toFixed(1)}%`}
              </b>{" "}
              <span className="text-gray-400">(목표 85%)</span>
            </p>
          </div>
        </section>
      </main>
    </>
  );
}
