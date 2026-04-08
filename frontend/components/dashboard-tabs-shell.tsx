"use client";

import type { ReactNode } from "react";
import { useId, useState } from "react";

const dashboardTabs = [
  {
    key: "overview",
    label: "운영 개요",
    eyebrow: "Overview",
  },
  {
    key: "schedule",
    label: "일정·경기",
    eyebrow: "Schedule",
  },
  {
    key: "load",
    label: "훈련·부하",
    eyebrow: "Load",
  },
  {
    key: "insights",
    label: "메디컬·인사이트",
    eyebrow: "Insights",
  },
] as const;

type DashboardTabKey = (typeof dashboardTabs)[number]["key"];

type DashboardTabStat = {
  value: string;
  note: string;
};

type DashboardTabsShellProps = {
  overviewContent: ReactNode;
  scheduleContent: ReactNode;
  loadContent: ReactNode;
  insightsContent: ReactNode;
  tabStats: Record<DashboardTabKey, DashboardTabStat>;
};

export function DashboardTabsShell({
  overviewContent,
  scheduleContent,
  loadContent,
  insightsContent,
  tabStats,
}: DashboardTabsShellProps) {
  const [activeTab, setActiveTab] = useState<DashboardTabKey>("overview");
  const panelId = useId();

  return (
    <>
      <div
        aria-label="대시보드 보기 전환"
        className="physical-tab-nav physical-page-tab-nav dashboard-tab-nav"
        role="tablist"
      >
        {dashboardTabs.map((tab) => {
          const isActive = activeTab === tab.key;
          const tabId = `${panelId}-${tab.key}-tab`;
          const tabStat = tabStats[tab.key];

          return (
            <button
              aria-controls={panelId}
              aria-selected={isActive}
              className={
                isActive
                  ? "physical-tab-button dashboard-tab-button physical-tab-button--active dashboard-tab-button--active"
                  : "physical-tab-button dashboard-tab-button"
              }
              id={tabId}
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              role="tab"
              type="button"
            >
              <span className="dashboard-tab-button__eyebrow">{tab.eyebrow}</span>
              <div className="dashboard-tab-button__summary">
                <strong className="dashboard-tab-button__label">{tab.label}</strong>
                <span className="dashboard-tab-button__note">{tabStat.note}</span>
              </div>
              <strong className="dashboard-tab-button__value">{tabStat.value}</strong>
            </button>
          );
        })}
      </div>

      <div
        aria-labelledby={`${panelId}-${activeTab}-tab`}
        className="physical-tab-panel dashboard-tab-panel"
        id={panelId}
        role="tabpanel"
      >
        {activeTab === "overview"
          ? overviewContent
          : activeTab === "schedule"
            ? scheduleContent
            : activeTab === "load"
              ? loadContent
              : insightsContent}
      </div>
    </>
  );
}
