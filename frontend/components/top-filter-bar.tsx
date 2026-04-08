"use client";

import type { ChangeEvent } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

type FilterChip = {
  label: string;
  value: string;
};

type ShortcutLink = {
  label: string;
  href: string;
};

type TopFilterBarProps = {
  eyebrow: string;
  title: string;
  description: string;
  leftFilters: FilterChip[];
  rightFilters: FilterChip[];
  searchPlaceholder: string;
  profileName: string;
  profileRole: string;
  sectionLinks?: ShortcutLink[];
  searchValue?: string;
  onSearchChange?: (value: string) => void;
};

const workspaceLinks: ShortcutLink[] = [
  { label: "Dashboard", href: "/" },
  { label: "Players", href: "/players" },
  { label: "Matches", href: "/matches" },
  { label: "Calendar", href: "/calendar" },
  { label: "Physical", href: "/physical" },
  { label: "Injury / AT", href: "/injury" },
];

export function TopFilterBar({
  eyebrow,
  title,
  description,
  leftFilters,
  rightFilters,
  searchPlaceholder,
  profileName,
  profileRole,
  sectionLinks = [],
  searchValue,
  onSearchChange,
}: TopFilterBarProps) {
  const pathname = usePathname();

  return (
    <section className="top-filter-bar">
      <div className="top-filter-bar__main">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="description">{description}</p>
        </div>

        <div className="filter-chip-row">
          {leftFilters.map((filter) => (
            <div className="filter-chip" key={`${filter.label}-${filter.value}`}>
              <span>{filter.label}</span>
              <strong>{filter.value}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="top-filter-bar__actions">
        <label className="search-field">
          <span>Search</span>
          <input
            aria-label="Search dashboard"
            {...(typeof searchValue === "string"
              ? {
                  value: searchValue,
                  onChange: (event: ChangeEvent<HTMLInputElement>) =>
                    onSearchChange?.(event.target.value),
                }
              : {
                  defaultValue: "",
                })}
            placeholder={searchPlaceholder}
            type="search"
          />
        </label>

        {rightFilters.map((filter) => (
          <div
            className="filter-chip filter-chip--compact"
            key={`${filter.label}-${filter.value}`}
          >
            <span>{filter.label}</span>
            <strong>{filter.value}</strong>
          </div>
        ))}

        <div className="profile-pill">
          <span>{profileRole}</span>
          <strong>{profileName}</strong>
        </div>
      </div>

      <div className="top-filter-bar__footer">
        <div className="top-link-block">
          <span className="top-link-block__label">Quick Pages</span>
          <div className="top-link-row">
            {workspaceLinks.map((link) => {
              const isActive = pathname === link.href;

              return (
                <Link
                  className={
                    isActive ? "top-link-pill top-link-pill--active" : "top-link-pill"
                  }
                  href={link.href}
                  key={link.href}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>

        {sectionLinks.length > 0 ? (
          <div className="top-link-block">
            <span className="top-link-block__label">On This Page</span>
            <div className="top-link-row">
              {sectionLinks.map((link) => (
                <Link className="top-link-pill top-link-pill--soft" href={link.href} key={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
