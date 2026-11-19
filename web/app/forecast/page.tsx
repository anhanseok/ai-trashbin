"use client";

// 쓰레기 투입 수요 예측 (임시 데이터 900건 기반 시연). 데이터는 code/forecast_demo.py 가 만든다.
import { useState } from "react";
import Header from "@/components/Header";
import { LABEL, type Compartment } from "@/lib/bin";
import data from "@/lib/forecast-data.json";

type Row = (typeof data.series)[number] & { lo?: number; hi?: number };
const series = data.series as Row[];
const DOW = ["일", "월", "화", "수", "목", "금", "토"];

const md = (iso: string) => `${Number(iso.slice(5, 7))}/${Number(iso.slice(8, 10))}`;
const dow = (iso: string) => DOW[new Date(iso + "T00:00:00+09:00").getDay()];
const n1 = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1));

function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel px-5 py-4">
      <div className="text-[13px] text-muted">{label}</div>
      <div className="mt-1 font-mono text-3xl font-bold tabular-nums text-ink">{value}</div>
      {sub && <div className="mt-1 text-[13px] text-dim">{sub}</div>}
    </div>
  );
}

// ── 하루 투입 수: 실제(실선) + 예측(점선, 80% 구간) ──
function DailyChart() {
  const [hover, setHover] = useState<number | null>(null);
  const W = 760, H = 300, L = 40, R = 12, T = 16, B = 34;
  const max = Math.ceil(Math.max(...series.map((s) => s.hi ?? s.total)) / 20) * 20;
  const x = (i: number) => L + (i * (W - L - R)) / (series.length - 1);
  const y = (v: number) => T + (1 - v / max) * (H - T - B);
  const split = series.findIndex((s) => s.kind === "forecast");
  const act = series.slice(0, split);
  const fc = series.slice(split - 1); // 마지막 실제 점에서 이어 그림
  const line = (rows: Row[], off: number) =>
    rows.map((s, i) => `${i ? "L" : "M"}${x(i + off).toFixed(1)},${y(s.total).toFixed(1)}`).join("");
  const fcRows = series.slice(split);
  const band =
    fcRows.map((s, i) => `${i ? "L" : "M"}${x(i + split).toFixed(1)},${y(s.hi!).toFixed(1)}`).join("") +
    [...fcRows].reverse().map((s, i) => `L${x(split + fcRows.length - 1 - i).toFixed(1)},${y(s.lo!).toFixed(1)}`).join("") +
    "Z";
  const ticks = Array.from({ length: max / 20 + 1 }, (_, i) => i * 20);
  const h = hover !== null ? series[hover] : null;

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="날짜별 하루 투입 수 실제와 예측">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="var(--color-line)" strokeWidth={1} />
            <text x={L - 8} y={y(t) + 4} textAnchor="end" fontSize={11} fill="var(--color-dim)">{t}</text>
          </g>
        ))}
        {/* 예측 시작선 */}
        <line x1={(x(split - 1) + x(split)) / 2} x2={(x(split - 1) + x(split)) / 2} y1={T} y2={H - B}
          stroke="var(--color-muted)" strokeDasharray="3 4" strokeWidth={1} />
        <text x={(x(split - 1) + x(split)) / 2 + 6} y={T + 10} fontSize={11} fill="var(--color-muted)">예측 →</text>
        <path d={band} fill="var(--color-accent)" opacity={0.14} />
        <path d={line(act, 0)} fill="none" stroke="var(--color-accent)" strokeWidth={2} strokeLinejoin="round" />
        <path d={line(fc, split - 1)} fill="none" stroke="var(--color-accent)" strokeWidth={2} strokeDasharray="6 5" />
        {series.map((s, i) => (
          <circle key={s.date} cx={x(i)} cy={y(s.total)} r={hover === i ? 5 : 3}
            fill={s.kind === "actual" ? "var(--color-accent)" : "var(--color-panel)"}
            stroke="var(--color-accent)" strokeWidth={2} />
        ))}
        {series.map((s, i) =>
          (i % 3 === 0 && i < series.length - 3) || i === series.length - 1 ? (
            <text key={s.date} x={x(i)} y={H - 12} textAnchor={i === series.length - 1 ? "end" : "middle"} fontSize={11} fill="var(--color-dim)">{md(s.date)}</text>
          ) : null,
        )}
        {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} stroke="var(--color-muted)" strokeWidth={1} />}
        {/* 마우스 영역 (점보다 넓게) */}
        {series.map((s, i) => (
          <rect key={s.date} x={x(i) - (W - L - R) / series.length / 2} y={T} width={(W - L - R) / series.length}
            height={H - T - B} fill="transparent" onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
            onTouchStart={() => setHover(i)} />
        ))}
      </svg>
      {h && (
        <div
          className="pointer-events-none absolute top-2 z-10 w-48 rounded-lg border border-line bg-panel-2 px-3 py-2 text-[13px] shadow-lg"
          style={hover! < series.length / 2 ? { left: `${(x(hover!) / W) * 100 + 2}%` } : { right: `${100 - (x(hover!) / W) * 100 + 2}%` }}
        >
          <div className="mb-1 font-bold text-ink">
            {md(h.date)} ({dow(h.date)}) <span className="font-normal text-muted">{h.kind === "actual" ? "기록" : "예측"}</span>
          </div>
          <div className="flex justify-between text-ink"><span>합계</span><b className="font-mono">{n1(h.total)}개</b></div>
          {h.kind === "forecast" && (
            <div className="flex justify-between text-muted"><span>80% 구간</span><span className="font-mono">{h.lo}~{h.hi}</span></div>
          )}
          {(["plastic", "can", "general"] as Compartment[]).map((c) => (
            <div key={c} className="flex justify-between text-muted"><span>{LABEL[c]}</span><span className="font-mono">{n1(h[c])}</span></div>
          ))}
        </div>
      )}
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[13px] text-muted">
        <span className="flex items-center gap-2"><span className="h-0.5 w-6 bg-accent" />기록 (11/1~11/19)</span>
        <span className="flex items-center gap-2"><span className="w-6 border-t-2 border-dashed border-accent" />예측 (11/20~11/30)</span>
        <span className="flex items-center gap-2"><span className="h-3 w-6 rounded-sm bg-accent/20" />80% 예측 구간</span>
      </div>
    </div>
  );
}

// ── 시간대별 투입 비중 ──
function HourChart() {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(...data.hourly.map((h) => h.share));
  return (
    <div>
      <div className="flex h-36 items-end gap-[2px]">
        {data.hourly.map((h, i) => (
          <div key={h.hour} className="relative flex h-full flex-1 items-end"
            onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
            <div className={`w-full rounded-t-[4px] ${hover === i ? "bg-accent" : "bg-accent/70"}`}
              style={{ height: `${(h.share / max) * 100}%` }} />
            {hover === i && (
              <div className="pointer-events-none absolute -top-9 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-md border border-line bg-panel-2 px-2 py-1 text-[12px] text-ink">
                {h.hour}시 · <b className="font-mono">{h.share}%</b>
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="mt-1 flex gap-[2px] text-center text-[11px] text-dim">
        {data.hourly.map((h) => <div key={h.hour} className="flex-1">{h.hour % 2 === 0 ? h.hour : ""}</div>)}
      </div>
    </div>
  );
}

export default function ForecastPage() {
  const fc = series.filter((s) => s.kind === "forecast");
  const total = fc.reduce((a, s) => a + s.total, 0);
  const peak = fc.reduce((a, s) => (s.total > a.total ? s : a));
  const best = data.models.find((m) => m.key === data.best)!;
  const byFull = [...data.compartments].sort((a, b) => (a.full_on ?? "9").localeCompare(b.full_on ?? "9"));
  const topHour = data.hourly.reduce((a, h) => (h.share > a.share ? h : a));

  return (
    <>
      <Header />
      <main className="mx-auto max-w-6xl p-4 sm:p-7">
        <div className="mb-2 flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h1 className="text-2xl font-bold">쓰레기 수요 예측</h1>
          <span className="text-sm text-muted">11월 하루 투입 수와 칸별 가득참 예상일</span>
        </div>
        <div className="mb-3" />

        <div className="mb-5 grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
          <Stat label="11/20~30 예상 투입" value={<>{Math.round(total)}<span className="ml-1 text-base text-muted">개</span></>}
            sub={`하루 평균 ${(total / fc.length).toFixed(0)}개`} />
          <Stat label="가장 붐빌 날" value={md(peak.date)} sub={`${dow(peak.date)}요일 · 약 ${Math.round(peak.total)}개`} />
          <Stat label="가장 먼저 찰 칸" value={LABEL[byFull[0].key as Compartment]}
            sub={byFull[0].full_on ? `${md(byFull[0].full_on)} 예상` : "기간 안에 안 참"} />
          <Stat label="예측 오차 (선택 모델)" value={<>{best.wape}<span className="ml-1 text-base text-muted">%</span></>}
            sub={`${best.name} · 칸·하루당 ±${best.mae}개`} />
        </div>

        <section className="mb-5 rounded-xl border border-line bg-panel p-5 sm:p-6">
          <h2 className="text-lg font-bold">하루 투입 수</h2>
          <p className="mb-4 text-[13px] text-muted">세 칸 합계 · 점에 마우스를 올리면 칸별 개수</p>
          <DailyChart />
        </section>

        <div className="mb-5 grid gap-5 lg:grid-cols-5">
          <section className="rounded-xl border border-line bg-panel p-5 sm:p-6 lg:col-span-3">
            <h2 className="text-lg font-bold">칸별 예측과 수거 추천</h2>
            <p className="mb-4 text-[13px] text-muted">11/20 아침에 모두 비웠다고 가정하고 예측 개수를 누적 · 칸 용량은 가정값</p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-[13px] text-muted">
                  <tr className="border-b border-line">
                    <th className="py-2 font-medium">칸</th>
                    <th className="py-2 text-right font-medium">11/20~30 예측</th>
                    <th className="py-2 text-right font-medium">하루 평균</th>
                    <th className="py-2 text-right font-medium">용량</th>
                    <th className="py-2 text-right font-medium">가득참 예상</th>
                  </tr>
                </thead>
                <tbody>
                  {data.compartments.map((c) => (
                    <tr key={c.key} className="border-b border-line/60">
                      <td className="py-2.5 font-bold">{LABEL[c.key as Compartment]}</td>
                      <td className="py-2.5 text-right font-mono tabular-nums">{Math.round(c.forecast_total)}개</td>
                      <td className="py-2.5 text-right font-mono tabular-nums">{c.per_day}개</td>
                      <td className="py-2.5 text-right font-mono tabular-nums text-muted">{c.capacity}개</td>
                      <td className="py-2.5 text-right font-mono tabular-nums">
                        {c.full_on ? `${md(c.full_on)} (${dow(c.full_on)})` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 rounded-lg border border-line bg-panel-2 px-4 py-3 text-sm text-muted">
              <b className="text-ink">수거 추천:</b>{" "}
              {byFull.filter((c) => c.full_on).map((c, i) => (
                <span key={c.key}>
                  {i > 0 && " → "}
                  <b className="text-ink">{LABEL[c.key as Compartment]}</b> {md(c.full_on!)} 전
                </span>
              ))}
              . 매일 돌지 않고 찰 날짜에 맞춰 들르면 빈 칸을 보러 가는 헛걸음이 줄어듭니다.
            </div>
          </section>

          <section className="rounded-xl border border-line bg-panel p-5 sm:p-6 lg:col-span-2">
            <h2 className="text-lg font-bold">시간대별 투입 비중</h2>
            <p className="mb-4 text-[13px] text-muted">
              가장 많은 때 {topHour.hour}시 ({topHour.share}%) · 수거는 그 전에
            </p>
            <HourChart />
          </section>
        </div>

        <section className="rounded-xl border border-line bg-panel p-5 sm:p-6">
          <h2 className="text-lg font-bold">어떤 모델을 썼나</h2>
          <p className="mb-4 text-[13px] text-muted">
            {md(data.history[0])}~{md(data.train_end)} 기록으로 학습하고 마지막 7일({md(data.test_range[0])}~
            {md(data.test_range[1])})을 맞혀 보는 방식으로 4개를 비교 · 오차가 가장 작은 모델로 전체를 다시 학습해 예측
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-[13px] text-muted">
                <tr className="border-b border-line">
                  <th className="py-2 font-medium">모델</th>
                  <th className="py-2 font-medium">방식</th>
                  <th className="py-2 text-right font-medium">평균 오차</th>
                  <th className="py-2 text-right font-medium">오차율</th>
                </tr>
              </thead>
              <tbody>
                {data.models.map((m) => (
                  <tr key={m.key} className={`border-b border-line/60 ${m.key === data.best ? "bg-accent/10" : ""}`}>
                    <td className="whitespace-nowrap py-2.5 pl-2 font-bold">
                      {m.name}
                      {m.key === data.best && <span className="ml-2 rounded bg-accent/20 px-1.5 py-0.5 text-[12px] text-accent">선택</span>}
                    </td>
                    <td className="py-2.5 text-muted">{m.desc}</td>
                    <td className="whitespace-nowrap py-2.5 text-right font-mono tabular-nums">±{m.mae}개</td>
                    <td className="whitespace-nowrap py-2.5 pr-2 text-right font-mono tabular-nums">{m.wape}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-[13px] text-dim">
            포아송 회귀를 고른 이유: 하루 투입 수처럼 0 이상의 &lsquo;개수&rsquo;를 다루는 데 맞춰진 회귀라 음수나 엉뚱한 값이
            나오지 않고, 데이터가 3주 정도로 적어도 요일·추세만으로 안정적으로 학습됩니다. 나무 모델(부스팅)은 데이터가 적어 오히려
            오차가 컸습니다. 80% 구간은 예측값을 평균으로 한 포아송 분포에서 계산했습니다.
          </p>
        </section>
      </main>
    </>
  );
}
