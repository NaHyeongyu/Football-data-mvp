"use client";

import type { ReactNode } from "react";
import { useId, useState } from "react";

type InjuryTabKey = "dashboard" | "players" | "history";

type InjuryTabsShellProps = {
  dashboardContent: ReactNode;
  historyContent?: ReactNode;
  historyCount?: number;
  playersContent: ReactNode;
  playerCount: number;
};

export function InjuryTabsShell({
  dashboardContent,
  historyContent,
  historyCount = 0,
  playersContent,
  playerCount,
}: InjuryTabsShellProps) {
  const [activeTab, setActiveTab] = useState<InjuryTabKey>("dashboard");
  const panelId = useId();
  const tabs = [
    {
      key: "dashboard" as const,
      label: "리스크 대시보드",
    },
    {
      key: "players" as const,
      label: `선수 리스트 (${playerCount}명)`,
    },
    ...(historyContent
      ? [
          {
            key: "history" as const,
            label: `부상 이력 (${historyCount}건)`,
          },
        ]
      : []),
  ];

  return (
    <>
      <div
        aria-label="부상 리스크 화면 보기 전환"
        className="physical-tab-nav injury-tab-nav"
        role="tablist"
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          const tabId = `${panelId}-${tab.key}-tab`;

          return (
            <button
              aria-controls={panelId}
              aria-selected={isActive}
              className={isActive ? "physical-tab-button physical-tab-button--active" : "physical-tab-button"}
              id={tabId}
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              role="tab"
              type="button"
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      <div
        aria-labelledby={`${panelId}-${activeTab}-tab`}
        className="physical-tab-panel"
        id={panelId}
        role="tabpanel"
      >
        {activeTab === "dashboard"
          ? dashboardContent
          : activeTab === "history" && historyContent
            ? historyContent
            : playersContent}
      </div>
    </>
  );
}
