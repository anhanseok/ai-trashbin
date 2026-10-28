"use client";

import { useState } from "react";
import Header from "@/components/Header";
import { createClient } from "@/lib/supabase/client";

export default function AccountPage() {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) return setMessage({ ok: false, text: "8자 이상으로 정해 주세요." });
    if (password !== confirm) return setMessage({ ok: false, text: "두 비밀번호가 다릅니다." });
    setBusy(true);
    const { error } = await createClient().auth.updateUser({ password });
    setBusy(false);
    if (error) return setMessage({ ok: false, text: "바꾸지 못했습니다: " + error.message });
    setPassword("");
    setConfirm("");
    setMessage({ ok: true, text: "비밀번호를 바꿨습니다. 다음 로그인부터 새 비밀번호를 쓰세요." });
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-md p-4 sm:p-7">
        <form onSubmit={submit} className="rounded-xl border border-line bg-panel p-6">
          <h1 className="mb-5 text-lg font-bold">비밀번호 변경</h1>
          <label className="mb-1 block text-sm text-muted">새 비밀번호 (8자 이상)</label>
          <input type="password" autoComplete="new-password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-4 w-full rounded-md border border-line bg-panel-2 px-3 py-2 text-ink outline-none focus:border-accent" />
          <label className="mb-1 block text-sm text-muted">새 비밀번호 확인</label>
          <input type="password" autoComplete="new-password" value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="mb-4 w-full rounded-md border border-line bg-panel-2 px-3 py-2 text-ink outline-none focus:border-accent" />
          {message && (
            <p className={`mb-4 text-sm ${message.ok ? "text-ok" : "text-full"}`}>{message.text}</p>
          )}
          <button disabled={busy} className="h-11 w-full rounded-lg bg-accent font-bold text-bg transition-colors hover:bg-accent/85 disabled:opacity-50">
            {busy ? "바꾸는 중…" : "비밀번호 바꾸기"}
          </button>
        </form>
      </main>
    </>
  );
}
