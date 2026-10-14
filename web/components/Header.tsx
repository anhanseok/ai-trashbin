"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const TABS = [
  { href: "/", label: "대시보드" },
  { href: "/log", label: "투입 기록" },
];

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
    <header className="flex h-[60px] items-center gap-6 border-b-2 border-gray-200 bg-white px-4 sm:gap-8 sm:px-7">
      <div className="whitespace-nowrap text-lg font-bold sm:text-xl">♻ AI 분리수거함 관제</div>
      <nav className="flex h-full gap-4 sm:gap-5">
        {TABS.map((t) => (
          <Link
            key={t.href}
            href={t.href}
            className={`flex items-center border-b-[3px] text-[15px] ${
              path === t.href ? "border-gray-900 font-bold text-gray-900" : "border-transparent text-gray-400"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </nav>
      <div className="ml-auto hidden text-sm text-gray-500 md:block">
        관리자 <b className="text-gray-900">{email}</b>
      </div>
      <button onClick={logout} className="ml-auto text-sm text-gray-500 hover:text-gray-900 md:ml-0">
        로그아웃
      </button>
    </header>
  );
}
