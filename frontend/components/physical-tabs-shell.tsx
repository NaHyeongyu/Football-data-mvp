"use client";

import type { ReactNode } from "react";
import { useId, useState } from "react";

const physicalTabs = [
  {
    key: "energy",
    label: "에너지 레벨",
  },
  {
    key: "tests",
    label: "피지컬 측정",
  },
] as const;

type PhysicalTabKey = (typeof physicalTabs)[number]["key"];

type PhysicalTabsShellProps = {
  energyContent: ReactNode;
  physicalContent: ReactNode;
};

export function PhysicalTabsShell({
  energyContent,
  physicalContent,
}: PhysicalTabsShellProps) {
  const [activeTab, setActiveTab] = useState<PhysicalTabKey>("energy");
  const panelId = useId();

  return (
    <>
      <div aria-label="피지컬 화면 보기 전환" className="physical-tab-nav physical-page-tab-nav" role="tablist">
        {physicalTabs.map((tab) => {
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
        {activeTab === "energy" ? energyContent : physicalContent}
      </div>
    </>
  );
}
