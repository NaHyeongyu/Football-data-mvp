"use client";

import Link from "next/link";
import { startTransition, useState } from "react";

import { formatCompactDate } from "@/lib/dashboard-formatters";
import type {
  PhysicalTestMetricKey,
  PhysicalTestSessionRow,
  PhysicalTestSessionView,
} from "@/lib/data-types";

const oneDecimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});

const twoDecimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 2,
});

type MetricTone = "improved" | "declined" | "neutral";

const metricConfig: Record<
  PhysicalTestMetricKey,
  {
    label: string;
    averageLabel: string;
  }
> = {
  heightCm: {
    label: "신장",
    averageLabel: "신장 평균",
  },
  weightKg: {
    label: "체중",
    averageLabel: "체중 평균",
  },
  skeletalMuscleKg: {
    label: "골격근",
    averageLabel: "골격근 평균",
  },
  bodyFatPct: {
    label: "체지방",
    averageLabel: "체지방 평균",
  },
  sprint10mSec: {
    label: "10m",
    averageLabel: "10m 평균",
  },
  sprint30mSec: {
    label: "30m",
    averageLabel: "30m 평균",
  },
  sprint50mSec: {
    label: "50m",
    averageLabel: "50m 평균",
  },
  sprint100mSec: {
    label: "100m",
    averageLabel: "100m 평균",
  },
  verticalJumpCm: {
    label: "점프",
    averageLabel: "점프 평균",
  },
  agilityTSec: {
    label: "민첩",
    averageLabel: "민첩 평균",
  },
  shuttleRunCount: {
    label: "셔틀런",
    averageLabel: "셔틀런 평균",
  },
};

const tableMetricOrder: PhysicalTestMetricKey[] = [
  "heightCm",
  "weightKg",
  "sprint10mSec",
  "sprint30mSec",
  "sprint50mSec",
  "sprint100mSec",
  "verticalJumpCm",
  "agilityTSec",
  "shuttleRunCount",
  "bodyFatPct",
  "skeletalMuscleKg",
];

const summaryMetricOrder: PhysicalTestMetricKey[] = ["sprint30mSec", "verticalJumpCm", "shuttleRunCount", "bodyFatPct"];

function average(values: Array<number | null | undefined>) {
  const validValues = values.filter((value): value is number => value != null && Number.isFinite(value));
  if (validValues.length === 0) {
    return null;
  }

  return validValues.reduce((sum, value) => sum + value, 0) / validValues.length;
}

function hasMeaningfulDelta(value: number) {
  return Math.abs(value) >= 0.01;
}

function formatMetricValue(metricKey: PhysicalTestMetricKey, value: number | null) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }

  switch (metricKey) {
    case "heightCm":
      return `${Math.round(value)}cm`;
    case "weightKg":
    case "skeletalMuscleKg":
      return `${oneDecimalFormatter.format(value)}kg`;
    case "bodyFatPct":
      return `${oneDecimalFormatter.format(value)}%`;
    case "sprint10mSec":
    case "sprint30mSec":
    case "sprint50mSec":
    case "sprint100mSec":
    case "agilityTSec":
      return `${twoDecimalFormatter.format(value)}초`;
    case "shuttleRunCount":
      return `${Math.round(value).toLocaleString("ko-KR")}회`;
    case "verticalJumpCm":
      return `${oneDecimalFormatter.format(value)}cm`;
  }
}

function formatSignedValue(value: number, digits: 1 | 2) {
  const formatter = digits === 2 ? twoDecimalFormatter : oneDecimalFormatter;
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatter.format(value)}`;
}

function getDeltaPresentation(metricKey: PhysicalTestMetricKey, delta: number | null) {
  if (metricKey === "heightCm") {
    return {
      label: "프로필 기준",
      tone: "neutral" as MetricTone,
    };
  }

  if (delta === null) {
    return {
      label: "비교 없음",
      tone: "neutral" as MetricTone,
    };
  }

  if (!hasMeaningfulDelta(delta)) {
    return {
      label: "변화 없음",
      tone: "neutral" as MetricTone,
    };
  }

  switch (metricKey) {
    case "sprint10mSec":
    case "sprint30mSec":
    case "sprint50mSec":
    case "sprint100mSec":
    case "agilityTSec":
      return delta < 0
        ? {
            label: `${twoDecimalFormatter.format(Math.abs(delta))}초 단축`,
            tone: "improved" as MetricTone,
          }
        : {
            label: `${formatSignedValue(delta, 2)}초`,
            tone: "declined" as MetricTone,
          };
    case "shuttleRunCount":
      return {
        label: `${delta > 0 ? "+" : ""}${Math.round(delta).toLocaleString("ko-KR")}회`,
        tone: delta > 0 ? ("improved" as MetricTone) : ("declined" as MetricTone),
      };
    case "bodyFatPct":
      return delta < 0
        ? {
            label: `${oneDecimalFormatter.format(Math.abs(delta))}%p 감소`,
            tone: "improved" as MetricTone,
          }
        : {
            label: `${formatSignedValue(delta, 1)}%p`,
            tone: "declined" as MetricTone,
          };
    case "verticalJumpCm":
      return {
        label: `${formatSignedValue(delta, 1)}cm`,
        tone: delta > 0 ? ("improved" as MetricTone) : ("declined" as MetricTone),
      };
    case "skeletalMuscleKg":
      return {
        label: `${formatSignedValue(delta, 1)}kg`,
        tone: delta > 0 ? ("improved" as MetricTone) : ("declined" as MetricTone),
      };
    case "weightKg":
      return {
        label: `${formatSignedValue(delta, 1)}kg`,
        tone: "neutral" as MetricTone,
      };
  }
}

function getMetricSummary(rows: PhysicalTestSessionRow[], metricKey: PhysicalTestMetricKey) {
  const comparableRows = rows.filter(
    (row) => row.metrics[metricKey].current != null && row.metrics[metricKey].previous !== null,
  );
  const activeRows =
    comparableRows.length > 0
      ? comparableRows
      : rows.filter((row) => row.metrics[metricKey].current != null);
  const currentAverage = average(activeRows.map((row) => row.metrics[metricKey].current));
  const previousAverage =
    comparableRows.length > 0 ? average(comparableRows.map((row) => row.metrics[metricKey].previous ?? 0)) : null;

  return {
    currentAverage,
    previousAverage,
    comparisonCount: comparableRows.length,
    delta:
      currentAverage === null || previousAverage === null ? null : currentAverage - previousAverage,
  };
}

function renderMetricCell(row: PhysicalTestSessionRow, metricKey: PhysicalTestMetricKey) {
  const metric = row.metrics[metricKey];
  const deltaPresentation = getDeltaPresentation(metricKey, metric.delta);
  const detailLabel =
    metric.current == null
      ? "측정값 없음"
      : metricKey === "heightCm"
      ? "선수 프로필"
      : metric.previous === null
        ? "직전 측정 없음"
        : `이전 ${formatMetricValue(metricKey, metric.previous)}`;

  return (
    <div className="physical-session-metric">
      <strong>{formatMetricValue(metricKey, metric.current)}</strong>
      <span className={`physical-delta-pill physical-delta-pill--${deltaPresentation.tone}`}>
        {deltaPresentation.label}
      </span>
      <small>{detailLabel}</small>
    </div>
  );
}

export function PhysicalTestsBoard({
  sessions,
}: {
  sessions: PhysicalTestSessionView[];
}) {
  const [selectedSessionKey, setSelectedSessionKey] = useState(sessions[0]?.key ?? "");
  const selectedSession = sessions.find((session) => session.key === selectedSessionKey) ?? sessions[0] ?? null;

  if (!selectedSession) {
    return (
      <section className="panel panel--tight" id="physical-tests-board">
        <div className="empty-state">
          <strong>피지컬 측정 기록 없음</strong>
          <p>최근 시즌 측정 데이터가 연결되면 전체 선수 기록을 회차별로 바로 볼 수 있습니다.</p>
        </div>
      </section>
    );
  }

  const sortedRows = [...selectedSession.rows].sort(
    (left, right) =>
      left.registeredPosition.localeCompare(right.registeredPosition, "ko-KR") ||
      left.playerName.localeCompare(right.playerName, "ko-KR"),
  );
  const comparableCount = sortedRows.filter((row) => row.metrics.weightKg.previous !== null).length;
  const summaryMetrics = summaryMetricOrder.map((metricKey) => {
    const summary = getMetricSummary(sortedRows, metricKey);
    return {
      metricKey,
      ...summary,
      deltaPresentation: getDeltaPresentation(metricKey, summary.delta),
    };
  });

  return (
    <>
      <section className="stat-grid physical-kpi-grid" id="physical-tests">
        <article className="metric-card metric-card--highlight">
          <p>선택 회차</p>
          <strong>{`R${selectedSession.testRound}`}</strong>
          <div className="physical-kpi-comparison">
            <span className="metric-card__delta metric-card__delta--neutral">{selectedSession.playerCount}명 측정</span>
            <small>
              {formatCompactDate(selectedSession.testDate)} · 직전 비교 {comparableCount}명
            </small>
          </div>
        </article>

        {summaryMetrics.map(({ comparisonCount, currentAverage, deltaPresentation, metricKey, previousAverage }) => (
          <article className="metric-card" key={metricKey}>
            <p>{metricConfig[metricKey].averageLabel}</p>
            <strong>{formatMetricValue(metricKey, currentAverage)}</strong>
            <div className="physical-kpi-comparison">
              <span className={`metric-card__delta metric-card__delta--${deltaPresentation.tone}`}>
                {deltaPresentation.label}
              </span>
              <small>
                {previousAverage === null
                  ? "직전 평균 없음"
                  : `직전 평균 ${formatMetricValue(metricKey, previousAverage)} · ${comparisonCount}명 기준`}
              </small>
            </div>
          </article>
        ))}
      </section>

      <section className="panel panel--tight physical-session-panel" id="physical-tests-board">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Recent Test Log</p>
            <h2>최근 측정 전체 선수 기록</h2>
          </div>
        </div>

        <div className="physical-session-toolbar">
          <div className="physical-session-selector" aria-label="피지컬 측정 회차 선택">
            {sessions.map((session) => {
              const isActive = session.key === selectedSession.key;

              return (
                <button
                  aria-pressed={isActive}
                  className={
                    isActive
                      ? "physical-session-button physical-session-button--active"
                      : "physical-session-button"
                  }
                  key={session.key}
                  onClick={() => startTransition(() => setSelectedSessionKey(session.key))}
                  type="button"
                >
                  <strong>{`R${session.testRound}`}</strong>
                  <span>{formatCompactDate(session.testDate)}</span>
                  <small>{`${session.playerCount}명`}</small>
                </button>
              );
            })}
          </div>
        </div>

        <div className="table-scroll">
          <table className="data-table data-table--physical-session">
            <thead>
              <tr>
                <th>선수</th>
                {tableMetricOrder.map((metricKey) => (
                  <th key={metricKey}>{metricConfig[metricKey].label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => (
                <tr key={row.playerId}>
                  <td>
                    <div className="physical-session-player">
                      <Link className="table-action-link" href={`/players/${row.playerId}`}>
                        {row.playerName}
                      </Link>
                      <span>{row.registeredPosition}</span>
                    </div>
                  </td>
                  {tableMetricOrder.map((metricKey) => (
                    <td key={metricKey}>{renderMetricCell(row, metricKey)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
