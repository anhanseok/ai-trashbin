import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 분리수거함 관제",
  description: "칸별 가득참과 투입 기록을 보는 관리자 대시보드",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className="antialiased">{children}</body>
    </html>
  );
}
