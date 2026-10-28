import type { Metadata } from "next";
import { IBM_Plex_Sans_KR, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const plex = IBM_Plex_Sans_KR({ weight: ["400", "500", "700"], subsets: ["latin"], variable: "--font-plex" });
const jb = JetBrains_Mono({ weight: ["500", "700"], subsets: ["latin"], variable: "--font-jb" });

export const metadata: Metadata = {
  title: "AI 분리수거함 관제",
  description: "칸별 가득참과 투입 기록을 보는 관리자 대시보드",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className={`${plex.variable} ${jb.variable}`}>
      <body className="grid-bg min-h-screen antialiased">{children}</body>
    </html>
  );
}
