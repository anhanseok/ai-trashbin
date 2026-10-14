// 수거함 데이터 타입과 칸 상태 계산 규칙 (스펙 6번 "칸 상태 계산 규칙")
// 용어는 CONTEXT.md 기준: 칸, 품목, 투입, 확신도, 가득참, 수거 완료, 판정 수정

export const BIN_ID = process.env.NEXT_PUBLIC_BIN_ID ?? "bin-01";

export const COMPARTMENTS = ["plastic", "can", "general"] as const;
export type Compartment = (typeof COMPARTMENTS)[number];

export const LABEL: Record<Compartment, string> = { plastic: "페트", can: "캔", general: "일반" };
export const KIND: Record<Compartment, string> = {
  plastic: "재활용품",
  can: "재활용품",
  general: "일반쓰레기 · 확신 70% 미만 포함",
};

export const MIN_CONF = 0.7; // 확신도가 이보다 낮으면 일반 칸으로 (안전 로직)
export const OFFLINE_MS = 2 * 60 * 1000; // 신호가 2분 넘게 없으면 연결 끊김

export type Bin = { id: string; name: string; location: string; last_seen_at: string | null };
export type Deposit = {
  id: number;
  bin_id: string;
  created_at: string;
  photo_path: string | null;
  predicted: Compartment;
  confidence: number;
  dropped_into: Compartment;
  corrected: Compartment | null;
  corrected_at: string | null;
};
export type SensorReading = { id: number; compartment: Compartment; detected: boolean; created_at: string };
export type Collection = { id: number; compartment: Compartment; created_at: string };

export type CompartmentState = {
  status: "normal" | "full";
  needsSensorCheck: boolean; // 수거 완료 뒤에도 센서가 계속 감지 중
  fullSince: string | null;
  lastCollectedAt: string | null;
};

/**
 * 한 칸의 상태를 기록으로 계산한다.
 * - 마지막 수거 완료 뒤에 센서가 감지로 바뀐 적이 있으면 가득참
 * - 수거 완료 시점에 감지 중이었고 그 뒤로 바뀐 적이 없으면(=지금도 감지 중) 센서 확인 필요
 */
export function compartmentState(
  compartment: Compartment,
  readings: SensorReading[],
  collections: Collection[],
): CompartmentState {
  const mine = readings
    .filter((r) => r.compartment === compartment)
    .sort((a, b) => a.created_at.localeCompare(b.created_at));
  const lastCollectedAt =
    collections
      .filter((c) => c.compartment === compartment)
      .map((c) => c.created_at)
      .sort()
      .at(-1) ?? null;

  const after = lastCollectedAt ? mine.filter((r) => r.created_at > lastCollectedAt) : mine;
  const firstDetect = after.find((r) => r.detected);
  if (firstDetect) {
    return { status: "full", needsSensorCheck: false, fullSince: firstDetect.created_at, lastCollectedAt };
  }

  const before = lastCollectedAt ? mine.filter((r) => r.created_at <= lastCollectedAt) : [];
  const detectingAtCollect = before.at(-1)?.detected ?? false;
  const changedSince = after.length > 0;
  return {
    status: "normal",
    needsSensorCheck: detectingAtCollect && !changedSince,
    fullSince: null,
    lastCollectedAt,
  };
}

export function isOffline(bin: Bin | null, now: number) {
  if (!bin?.last_seen_at) return true;
  return now - new Date(bin.last_seen_at).getTime() > OFFLINE_MS;
}

// ── 시간 표시 (한국 시간) ──
const tz = { timeZone: "Asia/Seoul" } as const;
export const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString("en-GB", { ...tz, hour12: false });
export const fmtDateTime = (iso: string) =>
  new Date(iso).toLocaleString("ko-KR", { ...tz, month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false });

export function startOfTodayKST() {
  const ymd = new Date().toLocaleDateString("sv-SE", tz); // YYYY-MM-DD
  return new Date(`${ymd}T00:00:00+09:00`).toISOString();
}

export function sinceText(iso: string, now: number) {
  const min = Math.floor((now - new Date(iso).getTime()) / 60000);
  if (min < 1) return "방금";
  if (min < 60) return `${min}분째`;
  return `${Math.floor(min / 60)}시간 ${min % 60}분째`;
}

export function agoText(iso: string, now: number) {
  const sec = Math.max(0, Math.floor((now - new Date(iso).getTime()) / 1000));
  if (sec < 60) return `${sec}초 전`;
  if (sec < 3600) return `${Math.floor(sec / 60)}분 전`;
  return `${Math.floor(sec / 3600)}시간 전`;
}
