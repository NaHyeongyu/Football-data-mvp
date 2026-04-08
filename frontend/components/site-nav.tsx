"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/calendar", label: "Calendar", sublabel: "캘린더" },
  { href: "/players", label: "Players", sublabel: "선수" },
  { href: "/matches", label: "Matches", sublabel: "경기" },
  { href: "/training", label: "Training", sublabel: "훈련" },
  { href: "/physical", label: "Physical", sublabel: "피지컬" },
  { href: "/injury", label: "Injury", sublabel: "부상" },
  { href: "/assistant", label: "Assistant", sublabel: "질의" },
];

function isNavLinkActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SiteNav() {
  const pathname = usePathname();

  return (
    <aside className="site-sidebar" aria-label="Primary Sidebar">
      <div className="site-sidebar__inner">
        <Link className="brand" href="/calendar">
          <span className="brand__mark" aria-hidden="true">
            <Image
              alt=""
              height={38}
              priority
              src="/jeonbuk.svg"
              width={38}
            />
          </span>
          <span className="brand__copy">
            <span className="brand__meta">JEONBUK HYUNDAI</span>
            <span className="brand__title">유소년 데이터 관리 시스템</span>
          </span>
        </Link>

        <div className="site-sidebar__menu">
          <span className="site-sidebar__eyebrow">Menu</span>
          <nav className="nav-links" aria-label="Primary">
            {links.map((link) => {
              const isActive = isNavLinkActive(pathname, link.href);

              return (
                <Link
                  className={isActive ? "nav-link nav-link--active" : "nav-link"}
                  href={link.href}
                  key={link.href}
                >
                  <span className="nav-link__label">{link.label}</span>
                  <span className="nav-link__meta">{link.sublabel}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </aside>
  );
}
