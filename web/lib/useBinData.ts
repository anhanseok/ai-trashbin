"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { BIN_ID, startOfTodayKST, type Bin, type Collection, type Deposit, type SensorReading } from "@/lib/bin";

/** 수거함 1대의 기록을 불러오고, DB가 바뀌면(Realtime) 다시 불러온다. */
export function useBinData() {
  const supabase = useMemo(() => createClient(), []);
  const [bin, setBin] = useState<Bin | null>(null);
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [deposits, setDeposits] = useState<Deposit[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  const load = useCallback(async () => {
    const today = startOfTodayKST();
    const [b, r, c, d] = await Promise.all([
      supabase.from("bins").select("*").eq("id", BIN_ID).single(),
      supabase.from("sensor_readings").select("id,compartment,detected,created_at")
        .eq("bin_id", BIN_ID).order("created_at", { ascending: false }).limit(300),
      supabase.from("collections").select("id,compartment,created_at")
        .eq("bin_id", BIN_ID).order("created_at", { ascending: false }).limit(300),
      supabase.from("deposits").select("*")
        .eq("bin_id", BIN_ID).gte("created_at", today).order("created_at", { ascending: false }),
    ]);
    setBin(b.data);
    setReadings(r.data ?? []);
    setCollections(c.data ?? []);
    setDeposits(d.data ?? []);
    setLoaded(true);
  }, [supabase]);

  useEffect(() => {
    load();
    const channel = supabase
      .channel("bin-" + BIN_ID)
      .on("postgres_changes", { event: "*", schema: "public", table: "bins" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "deposits" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "sensor_readings" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "collections" }, load)
      .subscribe();
    const tick = setInterval(() => setNow(Date.now()), 5000); // "몇 초 전", 연결 끊김 갱신
    return () => {
      supabase.removeChannel(channel);
      clearInterval(tick);
    };
  }, [supabase, load]);

  return { supabase, bin, readings, collections, deposits, loaded, now, reload: load };
}

/** Storage의 비공개 사진 경로들을 1시간짜리 서명 URL로 바꾼다. */
export function usePhotoUrls(paths: (string | null)[]) {
  const supabase = useMemo(() => createClient(), []);
  const [urls, setUrls] = useState<Record<string, string>>({});
  const key = paths.filter(Boolean).join("|");

  useEffect(() => {
    const list = key ? key.split("|") : [];
    if (list.length === 0) return;
    supabase.storage.from("photos").createSignedUrls(list, 3600).then(({ data }) => {
      const map: Record<string, string> = {};
      data?.forEach((d) => { if (d.path && d.signedUrl) map[d.path] = d.signedUrl; });
      setUrls(map);
    });
  }, [supabase, key]);

  return urls;
}
