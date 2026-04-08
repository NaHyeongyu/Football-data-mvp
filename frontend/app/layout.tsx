import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteNav } from "@/components/site-nav";

export const metadata: Metadata = {
  title: "전북현대 유소년 데이터 관리 시스템",
  description: "전북현대 유소년팀 내부 데이터 관리 시스템 프론트엔드",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="ko">
      <body>
        <div className="shell">
          <SiteNav />
          <div className="app-main">{children}</div>
        </div>
      </body>
    </html>
  );
}
