import type { ReactNode } from "react";

import {
  formatAgentStoryline,
  formatCoachAction,
  formatCompactDate,
  formatDevelopmentFocus,
  formatDominantFoot,
  formatFieldLabel,
  formatGrowthBand,
  formatManagementAction,
  formatMetricValue,
  formatPositionGroup,
  formatRiskBand,
  formatScoutNote,
  formatScoutPriority,
} from "@/lib/dashboard-formatters";

type RowRecord = Record<string, unknown>;

type DatasetSectionProps<T extends RowRecord> = {
  id: string;
  eyebrow: string;
  title: string;
  description: string;
  items: T[];
  rowKey: (item: T, index: number) => string;
  columnOrder?: string[];
};

type SectionLink = {
  id: string;
  label: string;
};

function availabilityTone(status: string) {
  if (status === "불가") {
    return "status-pill status-pill--danger";
  }
  if (status === "조건부") {
    return "status-pill status-pill--warning";
  }
  return "status-pill status-pill--success";
}

function riskTone(riskBand: string) {
  if (riskBand === "red_flag") {
    return "metric-inline-badge metric-inline-badge--danger";
  }
  if (riskBand === "managed") {
    return "metric-inline-badge metric-inline-badge--warning";
  }
  return "metric-inline-badge metric-inline-badge--neutral";
}

function scoutPriorityTone(priority: string) {
  if (priority === "priority_shortlist") {
    return "metric-inline-badge metric-inline-badge--strong";
  }
  if (priority === "strong_follow") {
    return "metric-inline-badge";
  }
  return "metric-inline-badge metric-inline-badge--neutral";
}

function growthBandTone(band: string) {
  if (band === "accelerating") {
    return "metric-inline-badge metric-inline-badge--strong";
  }
  if (band === "monitor") {
    return "metric-inline-badge metric-inline-badge--warning";
  }
  return "metric-inline-badge";
}

function resultTone(result: string) {
  if (result === "패") {
    return "table-badge table-badge--danger";
  }
  if (result === "무") {
    return "table-badge table-badge--warning";
  }
  return "table-badge table-badge--success";
}

function venueTone(venue: string) {
  return venue === "홈"
    ? "table-badge table-badge--neutral"
    : "table-badge table-badge--soft";
}

function compactCell(text: string) {
  return <span className="table-note">{text}</span>;
}

function renderCell(key: string, value: unknown): ReactNode {
  if (value === null || value === undefined || value === "") {
    return <span className="table-muted">-</span>;
  }

  if (typeof value === "number") {
    if (key === "key_player_impact_score") {
      return <span className="impact-pill">{formatMetricValue(key, value)}</span>;
    }
    return formatMetricValue(key, value);
  }

  const text = String(value);

  if (key.includes("date")) {
    return formatCompactDate(text);
  }

  switch (key) {
    case "player_name":
    case "key_player":
    case "opponent":
    case "team_name":
      return <strong className="table-strong">{text}</strong>;
    case "player_id":
    case "match_id":
    case "season_id":
    case "first_season_id":
    case "latest_season_id":
      return <span className="table-code">{text}</span>;
    case "latest_match_availability":
      return <span className={availabilityTone(text)}>{text}</span>;
    case "risk_band":
      return <span className={riskTone(text)}>{formatRiskBand(text)}</span>;
    case "scout_priority":
      return (
        <span className={scoutPriorityTone(text)}>{formatScoutPriority(text)}</span>
      );
    case "growth_band":
      return <span className={growthBandTone(text)}>{formatGrowthBand(text)}</span>;
    case "position_group":
      return (
        <span className="metric-inline-badge metric-inline-badge--neutral">
          {formatPositionGroup(text)}
        </span>
      );
    case "dominant_foot":
      return formatDominantFoot(text);
    case "development_focus_1":
    case "development_focus_2":
      return <span className="focus-chip focus-chip--small">{formatDevelopmentFocus(text)}</span>;
    case "latest_status_type":
    case "latest_training_participation":
      return <span className="metric-inline-badge metric-inline-badge--neutral">{text}</span>;
    case "result":
      return <span className={resultTone(text)}>{text}</span>;
    case "venue":
      return <span className={venueTone(text)}>{text}</span>;
    case "agent_storyline":
      return compactCell(formatAgentStoryline(text));
    case "scout_note":
      return compactCell(formatScoutNote(text));
    case "coach_action":
      return compactCell(formatCoachAction(text));
    case "management_action":
      return compactCell(formatManagementAction(text));
    case "score":
      return <strong className="table-strong">{text}</strong>;
    default:
      return text;
  }
}

export function SectionIndex({ items }: { items: SectionLink[] }) {
  return (
    <nav className="section-index" aria-label="Dashboard Sections">
      {items.map((item) => (
        <a className="section-index__link" href={`#${item.id}`} key={item.id}>
          {item.label}
        </a>
      ))}
    </nav>
  );
}

export function DatasetSection<T extends RowRecord>({
  id,
  eyebrow,
  title,
  description,
  items,
  rowKey,
  columnOrder,
}: DatasetSectionProps<T>) {
  const columns =
    columnOrder ?? (items.length > 0 ? Object.keys(items[0] as RowRecord) : []);

  return (
    <section className="panel panel--tight" id={id}>
      <div className="dataset-header">
        <div>
          <p className="panel-eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        <div className="dataset-toolbar">
          <span className="count-badge">{items.length.toLocaleString("ko-KR")} rows</span>
          <p className="panel-note">{description}</p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <strong>표시할 데이터 없음</strong>
          <p>현재 섹션에 표시할 데이터가 없습니다.</p>
        </div>
      ) : (
        <div className="table-scroll table-scroll--wide">
          <table className="data-table data-table--dense">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{formatFieldLabel(column)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={rowKey(item, index)}>
                  {columns.map((column) => (
                    <td key={column}>{renderCell(column, item[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
