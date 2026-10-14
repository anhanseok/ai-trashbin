"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const { error } = await createClient().auth.signInWithPassword({ email, password });
    setBusy(false);
    if (error) {
      setError("이메일 또는 비밀번호가 맞지 않습니다.");
      return;
    }
    router.replace("/");
    router.refresh();
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-xl border-2 border-gray-300 bg-white p-8">
        <h1 className="mb-1 text-xl font-bold">♻ AI 분리수거함 관제</h1>
        <p className="mb-6 text-sm text-gray-500">관리자 로그인</p>
        <label className="mb-1 block text-sm text-gray-600">이메일</label>
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2"
        />
        <label className="mb-1 block text-sm text-gray-600">비밀번호</label>
        <input
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2"
        />
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
        <button
          disabled={busy}
          className="h-11 w-full rounded-lg bg-gray-900 font-bold text-white disabled:opacity-50"
        >
          {busy ? "로그인 중…" : "로그인"}
        </button>
      </form>
    </main>
  );
}
