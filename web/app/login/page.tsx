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
      <form onSubmit={submit} className="w-full max-w-sm rounded-xl border border-line bg-panel p-8 shadow-[0_0_60px_-20px_var(--color-accent)]">
        <h1 className="mb-1 flex items-center gap-2 text-xl font-bold">
          <span className="grid size-8 place-items-center rounded-md border border-ok/40 bg-ok/10 text-ok">♻</span>
          AI 분리수거함 <span className="text-muted">관제</span>
        </h1>
        <p className="mb-6 text-sm text-muted">관리자 로그인</p>
        <label className="mb-1 block text-sm text-muted">이메일</label>
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-4 w-full rounded-md border border-line bg-panel-2 px-3 py-2 text-ink outline-none focus:border-accent"
        />
        <label className="mb-1 block text-sm text-muted">비밀번호</label>
        <input
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4 w-full rounded-md border border-line bg-panel-2 px-3 py-2 text-ink outline-none focus:border-accent"
        />
        {error && <p className="mb-4 text-sm text-full">{error}</p>}
        <button
          disabled={busy}
          className="h-11 w-full rounded-lg bg-accent font-bold text-bg transition-colors hover:bg-accent/85 disabled:opacity-50"
        >
          {busy ? "로그인 중…" : "로그인"}
        </button>
      </form>
    </main>
  );
}
