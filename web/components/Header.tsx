"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const TABS = [
  { href: "/", label: "대시보드" },
  { href: "/log", label: "투입 기록" },
];

function Clock() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!now) return null;
  return (
    <span className="hidden font-mono text-sm tabular-nums text-muted lg:inline">
      {now.toLocaleTimeString("en-GB", { timeZone: "Asia/Seoul", hour12: false })}
    </span>
  );
}

export default function Header() {
  const path = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState("");

  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => setEmail(data.user?.email ?? ""));
  }, []);

  async function logout() {
    await createClient().auth.signOut();
    router.replace("/login");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-10 border-b border-line bg-bg/90 backdrop-blur">
      <div className="mx-auto flex h-[60px] max-w-6xl items-center gap-4 px-4 sm:gap-8 sm:px-7">
        <Link href="/" className="flex items-center gap-2 whitespace-nowrap font-bold">
          <span className="grid size-8 place-items-center rounded-md border border-ok/40 bg-ok/10 text-ok">♻</span>
          <span className="hidden text-[17px] sm:inline">
            AI 분리수거함 <span className="text-muted">관제</span>
          </span>
        </Link>
        <nav className="flex h-full gap-4 sm:gap-6">
          {TABS.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className={`flex items-center whitespace-nowrap border-b-2 text-[15px] transition-colors ${
                path === t.href
                  ? "border-accent font-bold text-ink"
                  : "border-transparent text-muted hover:text-ink"
              }`}
            >
              {t.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-4">
          <Clock />
          <Link href="/account" className="hidden text-sm text-muted hover:text-ink md:block">
            관리자 <b className="font-medium text-ink">{email}</b>
          </Link>
          <Link href="/account" className="whitespace-nowrap text-sm text-muted hover:text-ink md:hidden">
            설정
          </Link>
          <button
            onClick={logout}
            className="whitespace-nowrap rounded-md border border-line px-3 py-1.5 text-sm text-muted hover:border-muted hover:text-ink"
          >
            로그아웃
          </button>
        </div>
      </div>
    </header>
  );
}
