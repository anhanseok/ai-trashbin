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
        <form onSubmit={submit} className="rounded-xl border-2 border-gray-300 bg-white p-6">
          <h1 className="mb-5 text-lg font-bold">비밀번호 변경</h1>
          <label className="mb-1 block text-sm text-gray-600">새 비밀번호 (8자 이상)</label>
          <input type="password" autoComplete="new-password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2" />
          <label className="mb-1 block text-sm text-gray-600">새 비밀번호 확인</label>
          <input type="password" autoComplete="new-password" value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2" />
          {message && (
            <p className={`mb-4 text-sm ${message.ok ? "text-green-700" : "text-red-600"}`}>{message.text}</p>
          )}
          <button disabled={busy} className="h-11 w-full rounded-lg bg-gray-900 font-bold text-white disabled:opacity-50">
            {busy ? "바꾸는 중…" : "비밀번호 바꾸기"}
          </button>
        </form>
      </main>
    </>
  );
}
