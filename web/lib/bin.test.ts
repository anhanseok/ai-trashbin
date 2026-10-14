import { describe, expect, it } from "vitest";
import { compartmentState, isOffline, type Collection, type SensorReading } from "./bin";

let id = 0;
const r = (compartment: SensorReading["compartment"], detected: boolean, at: string): SensorReading =>
  ({ id: ++id, compartment, detected, created_at: `2026-10-15T${at}:00+00:00` });
const c = (compartment: Collection["compartment"], at: string): Collection =>
  ({ id: ++id, compartment, created_at: `2026-10-15T${at}:00+00:00` });

describe("칸 상태 계산 (스펙 6번 규칙)", () => {
  it("기록이 없으면 정상", () => {
    expect(compartmentState("can", [], [])).toMatchObject({ status: "normal", needsSensorCheck: false, lastCollectedAt: null });
  });

  it("센서가 감지로 바뀌면 가득참, 그 시각부터", () => {
    const s = compartmentState("plastic", [r("plastic", false, "01:00"), r("plastic", true, "02:00")], []);
    expect(s.status).toBe("full");
    expect(s.fullSince).toContain("T02:00");
  });

  it("가득참은 센서가 다시 꺼져도 수거 완료 전까지 유지", () => {
    const s = compartmentState("plastic", [r("plastic", true, "02:00"), r("plastic", false, "02:05")], []);
    expect(s.status).toBe("full");
  });

  it("수거 완료 뒤 센서가 꺼져 있으면 정상", () => {
    const s = compartmentState("plastic",
      [r("plastic", true, "02:00"), r("plastic", false, "02:30")], [c("plastic", "03:00")]);
    expect(s).toMatchObject({ status: "normal", needsSensorCheck: false });
    expect(s.lastCollectedAt).toContain("T03:00");
  });

  it("수거 완료 때 감지 중이었고 그 뒤 변화가 없으면 센서 확인 필요", () => {
    const s = compartmentState("can", [r("can", true, "02:00")], [c("can", "03:00")]);
    expect(s).toMatchObject({ status: "normal", needsSensorCheck: true });
  });

  it("센서 확인 필요 상태에서 꺼졌다가 다시 감지되면 가득참", () => {
    const s = compartmentState("can",
      [r("can", true, "02:00"), r("can", false, "03:10"), r("can", true, "04:00")], [c("can", "03:00")]);
    expect(s.status).toBe("full");
    expect(s.fullSince).toContain("T04:00");
  });

  it("다른 칸 기록은 섞이지 않음", () => {
    const s = compartmentState("general", [r("plastic", true, "02:00")], [c("can", "03:00")]);
    expect(s).toMatchObject({ status: "normal", needsSensorCheck: false, lastCollectedAt: null });
  });
});

describe("연결 끊김", () => {
  const bin = (last: string | null) => ({ id: "bin-01", name: "", location: "", last_seen_at: last });
  const now = new Date("2026-10-15T10:00:00Z").getTime();
  it("신호가 2분 안이면 연결됨", () => expect(isOffline(bin("2026-10-15T09:58:30Z"), now)).toBe(false));
  it("2분 넘으면 끊김", () => expect(isOffline(bin("2026-10-15T09:57:59Z"), now)).toBe(true));
  it("신호 기록이 없으면 끊김", () => expect(isOffline(bin(null), now)).toBe(true));
});
