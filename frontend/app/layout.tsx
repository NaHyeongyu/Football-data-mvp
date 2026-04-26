import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteNav } from "@/components/site-nav";

export const metadata: Metadata = {
  title: "Football Data System",
  description: "Football Data System 프론트엔드",
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
