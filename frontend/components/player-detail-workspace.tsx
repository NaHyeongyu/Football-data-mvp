"use client";

import Link from "next/link";
import { useId, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  PlayerDetailPayload,
  PlayerInjuryRecordItem,
  PlayerMatchPerformanceItem,
  PlayerMentalNoteItem,
  PlayerPhysicalTestItem,
} from "@/lib/data-types";
import {
  formatCompactDate,
  formatDominantFoot,
} from "@/lib/dashboard-formatters";

const numberFormatter = new Intl.NumberFormat("ko-KR");

const detailTabs = [
  { key: "overview", label: "개요" },
  { key: "match", label: "경기 퍼포먼스" },
  { key: "physical", label: "피지컬" },
  { key: "gps", label: "GPS" },
  { key: "injury", label: "부상 / AT" },
  { key: "mental", label: "멘탈 노트" },
  { key: "reports", label: "리포트" },
] as const;

type DetailTabKey = (typeof detailTabs)[number]["key"];

type EvaluationTrendLabel = "큰 하락" | "하락" | "보통" | "발전" | "많은 발전";

type MonthlyCoachEvaluationItem = {
  id: string;
  evaluationDate: string;
  monthLabel: string;
  matchCount: number;
  trendLabel: EvaluationTrendLabel;
  trendCode: number;
  passSuccessPct: number | null;
  duelWinPct: number | null;
  impactScore: number;
  minutesAverage: number;
  comment: string;
};

type PhysicalTrendMetricConfig = {
  key: string;
  eyebrow: string;
  title: string;
  unit?: string;
  digits?: number;
  value: (item: PlayerPhysicalTestItem) => number | null;
};

function availabilityTone(value?: string | null) {
  if (value === "불가") {
    return "table-badge table-badge--danger";
  }
  if (value === "조건부") {
    return "table-badge table-badge--warning";
  }
  if (value === "가능") {
    return "table-badge table-badge--success";
  }
  return "table-badge table-badge--neutral";
}

function resultTone(result: string) {
  if (result === "승") {
    return "table-badge table-badge--success";
  }
  if (result === "패") {
    return "table-badge table-badge--danger";
  }
  return "table-badge table-badge--neutral";
}

function isOfficialMatch(item: PlayerMatchPerformanceItem) {
  return item.match_type === "공식";
}

function injuryEventTone(record: PlayerInjuryRecordItem) {
  if (record.match_availability === "불가") {
    return "attention-item attention-item--danger";
  }
  if (record.match_availability === "조건부") {
    return "attention-item attention-item--warning";
  }
  return "attention-item attention-item--neutral";
}

function signedText(value: number, digits = 1) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}`;
}

function signedChartDelta(value: number) {
  const absolute = Math.abs(value);
  if (absolute < 1) {
    return signedText(value, 2);
  }
  if (absolute < 10) {
    return signedText(value, 1);
  }
  return signedText(value, 0);
}

function computeRecentMatchFormScore(item: PlayerMatchPerformanceItem) {
  return (
    item.minutes_played * 0.04 +
    item.goals * 20 +
    item.assists * 12 +
    item.shots_on_target * 3 +
    item.key_passes * 2 +
    (item.pass_success_pct ?? 0) * 0.01
  );
}

function computePer90(total: number, minutes: number) {
  if (minutes <= 0) {
    return 0;
  }

  return (total / minutes) * 90;
}

function computeAverageSpeedKmh(distanceKm?: number | null, minutes?: number | null) {
  if (distanceKm == null || minutes == null || minutes <= 0) {
    return null;
  }

  return distanceKm / (minutes / 60);
}

function getMatchGpsMinutes(item: PlayerMatchPerformanceItem) {
  return firstValidNumber(item.play_time_min, item.minutes_played);
}

function getMatchDistancePer90(item: PlayerMatchPerformanceItem) {
  const minutes = getMatchGpsMinutes(item);
  const distance = firstValidNumber(item.total_distance, item.distance_total_km);
  if (minutes == null || minutes <= 0 || distance == null) {
    return null;
  }

  return computePer90(distance, minutes);
}

function getMatchSprintCountPer90(item: PlayerMatchPerformanceItem) {
  const minutes = getMatchGpsMinutes(item);
  if (minutes == null || minutes <= 0 || item.sprint_count == null) {
    return null;
  }

  return computePer90(item.sprint_count, minutes);
}

function getMatchPlayerLoadPer90(item: PlayerMatchPerformanceItem) {
  const minutes = getMatchGpsMinutes(item);
  if (minutes == null || minutes <= 0 || item.player_load == null) {
    return null;
  }

  return computePer90(item.player_load, minutes);
}

function getDeltaTone(
  delta: number,
  preference: "up" | "down" | "neutral",
) {
  if (Math.abs(delta) < 0.05) {
    return "detail-delta detail-delta--neutral";
  }
  if (preference === "neutral") {
    return delta > 0
      ? "detail-delta detail-delta--positive"
      : "detail-delta detail-delta--negative";
  }
  if (preference === "up") {
    return delta > 0
      ? "detail-delta detail-delta--positive"
      : "detail-delta detail-delta--negative";
  }
  return delta < 0
    ? "detail-delta detail-delta--positive"
    : "detail-delta detail-delta--negative";
}

function buildDeltaMeta(
  current?: number | null,
  previous?: number | null,
  options?: {
    unit?: string;
    digits?: number;
    label?: string;
    preference?: "up" | "down" | "neutral";
  },
) {
  if (current == null || previous == null) {
    return null;
  }

  const delta = current - previous;
  if (Math.abs(delta) < 0.05) {
    return {
      className: "detail-delta detail-delta--neutral",
      text: `${options?.label ? `${options.label} ` : ""}변화 없음`,
    };
  }

  const digits = options?.digits ?? 1;
  return {
    className: getDeltaTone(delta, options?.preference ?? "neutral"),
    text: `${options?.label ? `${options.label} ` : ""}${signedText(delta, digits)}${options?.unit ?? ""}`,
  };
}

function formatUnderAge(value?: number | null) {
  if (value == null) {
    return "-";
  }
  return `U-${Math.max(1, Math.ceil(value))}`;
}

function formatReturnCountdown(dateValue?: string | null) {
  if (!dateValue) {
    return null;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const target = new Date(dateValue);
  target.setHours(0, 0, 0, 0);

  if (Number.isNaN(target.getTime())) {
    return formatCompactDate(dateValue);
  }

  const diffDays = Math.ceil((target.getTime() - today.getTime()) / 86400000);
  if (diffDays > 0) {
    return `예상 복귀 D-${diffDays}`;
  }
  if (diffDays === 0) {
    return "예상 복귀 D-Day";
  }
  return "복귀 일정 경과";
}

function formatValueWithUnit(
  value?: number | null,
  options?: {
    digits?: number;
    unit?: string;
  },
) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }

  const digits = options?.digits ?? 1;
  const formatted =
    digits === 0 ? numberFormatter.format(Math.round(value)) : value.toFixed(digits);

  return `${formatted}${options?.unit ?? ""}`;
}

function parseDateValue(value?: string | null) {
  if (!value) {
    return Number.NEGATIVE_INFINITY;
  }

  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
}

function averageDefined(values: Array<number | null | undefined>) {
  const filtered = values.filter((value): value is number => value != null && !Number.isNaN(value));
  if (filtered.length === 0) {
    return null;
  }
  return filtered.reduce((sum, value) => sum + value, 0) / filtered.length;
}

function firstValidNumber(...values: Array<number | null | undefined>) {
  for (const value of values) {
    if (value != null && !Number.isNaN(value)) {
      return value;
    }
  }
  return null;
}

function clampNumber(value: number, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

function roundTo(value: number, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function getEvaluationTrend(delta: number | null) {
  if (delta == null) {
    return { code: 3, label: "보통" as const };
  }
  if (delta <= -8) {
    return { code: 1, label: "큰 하락" as const };
  }
  if (delta <= -2) {
    return { code: 2, label: "하락" as const };
  }
  if (delta < 2) {
    return { code: 3, label: "보통" as const };
  }
  if (delta < 8) {
    return { code: 4, label: "발전" as const };
  }
  return { code: 5, label: "많은 발전" as const };
}

function getEvaluationTrendBadgeClass(label: EvaluationTrendLabel) {
  if (label === "많은 발전") {
    return "table-badge table-badge--official";
  }
  if (label === "발전") {
    return "table-badge table-badge--success";
  }
  if (label === "하락") {
    return "table-badge table-badge--warning";
  }
  if (label === "큰 하락") {
    return "table-badge table-badge--danger";
  }
  return "table-badge table-badge--neutral";
}

function formatEvaluationTrendCode(value: number) {
  if (value <= 1) {
    return "큰 하락";
  }
  if (value <= 2) {
    return "하락";
  }
  if (value <= 3) {
    return "보통";
  }
  if (value <= 4) {
    return "발전";
  }
  return "많은 발전";
}

function getMonthlyLabel(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return `${parsed.getFullYear()}년 ${parsed.getMonth() + 1}월`;
}

function formatCoachEvaluationTick(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return `${String(parsed.getFullYear()).slice(2)}.${String(parsed.getMonth() + 1).padStart(2, "0")}`;
}

function buildMonthlyCoachComment(
  item: MonthlyCoachEvaluationItem,
  previous?: MonthlyCoachEvaluationItem,
) {
  if (item.matchCount === 0) {
    return `${item.trendLabel}. 이달 경기 기록이 적어 코멘트는 제한적으로 남깁니다.`;
  }

  if (!previous) {
    return "보통. 첫 월간 평가입니다. 최근 경기 흐름을 기준선으로 잡습니다.";
  }

  const passDelta =
    item.passSuccessPct != null && previous.passSuccessPct != null
      ? item.passSuccessPct - previous.passSuccessPct
      : null;
  const duelDelta =
    item.duelWinPct != null && previous.duelWinPct != null ? item.duelWinPct - previous.duelWinPct : null;
  const impactDelta = item.impactScore - previous.impactScore;
  const minutesDelta = item.minutesAverage - previous.minutesAverage;

  const positiveAspects = [
    passDelta != null && passDelta >= 1.5
      ? {
          weight: Math.abs(passDelta),
          text: "최근 경기에서 패스 능력이 향상됐습니다.",
        }
      : null,
    duelDelta != null && duelDelta >= 4
      ? {
          weight: Math.abs(duelDelta),
          text: "경합 부분에서 발전이 보입니다.",
        }
      : null,
    impactDelta >= 0.2
      ? {
          weight: Math.abs(impactDelta) * 10,
          text: "경기 영향력이 좋아졌습니다.",
        }
      : null,
    minutesDelta >= 12
      ? {
          weight: Math.abs(minutesDelta),
          text: "출전 시간이 늘며 역할이 커졌습니다.",
        }
      : null,
  ].filter((value): value is { weight: number; text: string } => value != null);

  const negativeAspects = [
    passDelta != null && passDelta <= -1.5
      ? {
          weight: Math.abs(passDelta),
          text: "최근 경기에서 패스 정확도가 내려가 보완이 필요합니다.",
        }
      : null,
    duelDelta != null && duelDelta <= -4
      ? {
          weight: Math.abs(duelDelta),
          text: "경합 장면 대응 보완이 필요합니다.",
        }
      : null,
    impactDelta <= -0.2
      ? {
          weight: Math.abs(impactDelta) * 10,
          text: "경기 영향력이 줄어들었습니다.",
        }
      : null,
    minutesDelta <= -12
      ? {
          weight: Math.abs(minutesDelta),
          text: "출전 시간이 줄어 역할 유지가 과제입니다.",
        }
      : null,
  ].filter((value): value is { weight: number; text: string } => value != null);

  const base = `${item.trendLabel}.`;

  if (item.trendCode >= 4 && positiveAspects.length > 0) {
    return [base, ...positiveAspects.sort((left, right) => right.weight - left.weight).slice(0, 2).map((item) => item.text)].join(" ");
  }

  if (item.trendCode <= 2 && negativeAspects.length > 0) {
    return [base, ...negativeAspects.sort((left, right) => right.weight - left.weight).slice(0, 2).map((item) => item.text)].join(" ");
  }

  if (positiveAspects.length === 0 && negativeAspects.length === 0) {
    if (item.trendCode >= 4) {
      return `${base} 최근 경기 흐름이 전월보다 좋아졌습니다.`;
    }
    if (item.trendCode <= 2) {
      return `${base} 최근 경기에서 보완이 필요한 흐름이 보입니다.`;
    }
    return `${base} 최근 경기 흐름은 전월과 비슷합니다.`;
  }

  const mixed = [...positiveAspects, ...negativeAspects]
    .sort((left, right) => right.weight - left.weight)
    .slice(0, 1)
    .map((entry) => entry.text);

  return [base, ...mixed].join(" ");
}

function buildMonthlyCoachEvaluations(matches: PlayerMatchPerformanceItem[]): MonthlyCoachEvaluationItem[] {
  const grouped = new Map<string, PlayerMatchPerformanceItem[]>();

  matches
    .filter((item) => parseDateValue(item.match_date) > Number.NEGATIVE_INFINITY)
    .forEach((item) => {
      const parsed = new Date(item.match_date);
      const monthKey = `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, "0")}`;
      const existing = grouped.get(monthKey);
      if (existing) {
        existing.push(item);
      } else {
        grouped.set(monthKey, [item]);
      }
    });

  const historyAscending: MonthlyCoachEvaluationItem[] = [];

  Array.from(grouped.entries())
    .sort(([leftKey], [rightKey]) => leftKey.localeCompare(rightKey))
    .forEach(([monthKey, monthMatches], index) => {
      const playedMatches = monthMatches.filter((item) => item.minutes_played > 0);
      const relevantMatches = playedMatches.length > 0 ? playedMatches : monthMatches;
      const totalPassAttempts = relevantMatches.reduce((sum, item) => sum + item.pass_attempts, 0);
      const totalPassSuccess = relevantMatches.reduce((sum, item) => sum + item.pass_success, 0);
      const totalDuelsWon = relevantMatches.reduce((sum, item) => sum + item.duels_won, 0);
      const totalDuelsLost = relevantMatches.reduce((sum, item) => sum + item.duels_lost, 0);
      const totalDuels = totalDuelsWon + totalDuelsLost;
      const passSuccessPct =
        totalPassAttempts > 0
          ? roundTo((totalPassSuccess / totalPassAttempts) * 100, 1)
          : averageDefined(relevantMatches.map((item) => item.pass_success_pct));
      const duelWinPct =
        totalDuels > 0 ? roundTo((totalDuelsWon / totalDuels) * 100, 1) : null;
      const impactScore = roundTo(
        averageDefined(relevantMatches.map((item) => item.impact_score)) ?? 0,
        2,
      );
      const minutesAverage = roundTo(
        averageDefined(relevantMatches.map((item) => item.minutes_played)) ?? 0,
        0,
      );
      const evaluationDate = relevantMatches[relevantMatches.length - 1]?.match_date ?? monthMatches[monthMatches.length - 1]?.match_date ?? monthKey;
      const previous = index > 0 ? historyAscending[index - 1] : null;

      let trendDelta: number | null = null;
      if (previous) {
        const passDelta =
          passSuccessPct != null && previous.passSuccessPct != null
            ? passSuccessPct - previous.passSuccessPct
            : 0;
        const duelDelta =
          duelWinPct != null && previous.duelWinPct != null ? duelWinPct - previous.duelWinPct : 0;
        const impactDelta = impactScore - previous.impactScore;
        const minutesDelta = minutesAverage - previous.minutesAverage;
        trendDelta = roundTo(
          clampNumber(passDelta / 3, -1, 1) * 4 +
            clampNumber(duelDelta / 6, -1, 1) * 4 +
            clampNumber(impactDelta / 0.35, -1, 1) * 5 +
            clampNumber(minutesDelta / 20, -1, 1) * 3,
          2,
        );
      }

      const trend = getEvaluationTrend(trendDelta);
      const item: MonthlyCoachEvaluationItem = {
        comment: "",
        evaluationDate,
        id: `${monthKey}-${monthMatches[0]?.player_id ?? "player"}`,
        impactScore,
        matchCount: monthMatches.length,
        minutesAverage,
        monthLabel: getMonthlyLabel(evaluationDate),
        passSuccessPct,
        duelWinPct,
        trendCode: trend.code,
        trendLabel: trend.label,
      };
      item.comment = buildMonthlyCoachComment(item, previous ?? undefined);
      historyAscending.push(item);
    });

  return historyAscending.sort(
    (left, right) => parseDateValue(right.evaluationDate) - parseDateValue(left.evaluationDate),
  );
}

function EmptyPanel({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}

function MetricInfoHint({
  title,
  lines,
  align = "center",
}: {
  title: string;
  lines: string[];
  align?: "center" | "start" | "end";
}) {
  const className =
    align === "start"
      ? "score-info-hint score-info-hint--start"
      : align === "end"
        ? "score-info-hint score-info-hint--end"
        : "score-info-hint";

  return (
    <span className={className}>
      <button
        aria-label={`${title} 안내`}
        className="score-info-hint__button"
        type="button"
      >
        ?
      </button>
      <span className="score-info-hint__panel">
        <strong>{title}</strong>
        {lines.map((line) => (
          <span key={line}>{line}</span>
        ))}
      </span>
    </span>
  );
}

function TrendLinePanel<T>({
  eyebrow,
  title,
  items,
  getLabel,
  getValue,
  formatValue,
  footerLabel,
}: {
  eyebrow: string;
  title: string;
  items: T[];
  getLabel: (item: T) => string;
  getValue: (item: T) => number;
  formatValue: (value: number) => string;
  footerLabel: (item: T) => string;
}) {
  const gradientId = useId().replace(/:/g, "");

  if (items.length === 0) {
    return (
      <EmptyPanel
        title={`${title} 데이터 없음`}
        description="선택한 시즌 기준으로 표시할 기록이 없습니다."
      />
    );
  }

  const ordered = [...items].reverse();
  const chartData = ordered.map((item, index) => {
    const value = getValue(item);

    return {
      id: `${footerLabel(item)}-${index}`,
      footer: footerLabel(item),
      label: getLabel(item),
      value,
      formatted: formatValue(value),
      item,
    };
  });
  const values = chartData.map((item) => item.value);
  const latest = chartData[chartData.length - 1];
  const previous = chartData[chartData.length - 2];
  const latestValue = latest.value;
  const previousValue = previous?.value ?? latestValue;
  const maxPoint = chartData.reduce((best, current) => (current.value > best.value ? current : best));
  const minPoint = chartData.reduce((best, current) => (current.value < best.value ? current : best));
  const averageValue = values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1);

  return (
    <div className="visual-card visual-card--chart">
      <div className="visual-card__header">
        <div>
          <p className="visual-card__eyebrow">{eyebrow}</p>
          <strong>{formatValue(latestValue)}</strong>
          <span>{latest.label}</span>
        </div>
        <div className="visual-delta">
          <span>직전 기록 대비</span>
          <strong>{signedChartDelta(latestValue - previousValue)}</strong>
        </div>
      </div>

      <div className="trend-chart-shell">
        <ResponsiveContainer height="100%" width="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
          >
            <defs>
              <linearGradient id={`trend-fill-${gradientId}`} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#1d4ed8" stopOpacity={0.24} />
                <stop offset="70%" stopColor="#3b82f6" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#93c5fd" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid
              stroke="rgba(11, 37, 69, 0.08)"
              strokeDasharray="3 6"
              vertical={false}
            />
            <XAxis
              axisLine={false}
              dataKey="footer"
              dy={8}
              interval={chartData.length > 8 ? "preserveStartEnd" : 0}
              minTickGap={16}
              tick={{ fill: "#5d718f", fontSize: 11, fontWeight: 700 }}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              domain={["dataMin - 5", "dataMax + 5"]}
              tick={false}
              tickLine={false}
              width={0}
            />
            <Tooltip
              content={({ active, payload }) => {
                const tooltipPoint = payload?.[0]?.payload as
                  | {
                      footer: string;
                      label: string;
                      formatted: string;
                    }
                  | undefined;

                if (!active || tooltipPoint == null) {
                  return null;
                }

                return (
                  <div className="trend-tooltip">
                    <strong>
                      {tooltipPoint.footer} · {tooltipPoint.formatted}
                    </strong>
                    <span>{tooltipPoint.label}</span>
                  </div>
                );
              }}
              cursor={{ stroke: "rgba(11, 37, 69, 0.16)", strokeDasharray: "4 4" }}
            />
            <ReferenceLine
              ifOverflow="extendDomain"
              stroke="rgba(11, 37, 69, 0.16)"
              strokeDasharray="4 4"
              y={averageValue}
            />
            <Area
              activeDot={{ fill: "#ffffff", r: 5, stroke: "#0b2545", strokeWidth: 3 }}
              dataKey="value"
              dot={chartData.length === 1 ? { fill: "#ffffff", r: 4, stroke: "#0b2545", strokeWidth: 2.5 } : false}
              fill={`url(#trend-fill-${gradientId})`}
              fillOpacity={1}
              stroke="#0b2545"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              type="monotone"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="visual-stat-row visual-stat-row--compact">
        <div className="visual-stat visual-stat--compact">
          <span>평균</span>
          <strong>{formatValue(averageValue)}</strong>
          <small>선택 구간 {chartData.length}건</small>
        </div>
        <div className="visual-stat visual-stat--compact">
          <span>최고</span>
          <strong>{maxPoint.formatted}</strong>
          <small>{maxPoint.label}</small>
        </div>
        <div className="visual-stat visual-stat--compact">
          <span>최저</span>
          <strong>{minPoint.formatted}</strong>
          <small>{minPoint.label}</small>
        </div>
      </div>
    </div>
  );
}

function CoachEvaluationTrendPanel({
  items,
  yearRangeLabel,
}: {
  items: MonthlyCoachEvaluationItem[];
  yearRangeLabel: string;
}) {
  const gradientId = useId().replace(/:/g, "");

  if (items.length === 0) {
    return null;
  }

  const chartData = [...items].reverse().map((item, index) => ({
    id: `${item.id}-${index}`,
    comment: item.comment,
    footer: formatCoachEvaluationTick(item.evaluationDate),
    monthLabel: item.monthLabel,
    trendLabel: item.trendLabel,
    value: item.trendCode,
  }));
  const latest = chartData[chartData.length - 1];
  const previous = chartData[chartData.length - 2];
  const maxPoint = chartData.reduce((best, current) => (current.value > best.value ? current : best));
  const minPoint = chartData.reduce((best, current) => (current.value < best.value ? current : best));
  const movement =
    previous == null
      ? "첫 평가"
      : latest.value === previous.value
        ? "직전 월과 동일"
        : latest.value > previous.value
          ? `${latest.value - previous.value}단계 상승`
          : `${previous.value - latest.value}단계 하락`;

  return (
    <div className="visual-card visual-card--chart">
      <div className="visual-card__header">
        <div>
          <p className="visual-card__eyebrow">{yearRangeLabel} 평가 추이</p>
          <strong>{latest.trendLabel}</strong>
          <span>{latest.monthLabel}</span>
        </div>
        <div className="visual-delta">
          <span>직전 월 대비</span>
          <strong>{movement}</strong>
        </div>
      </div>

      <div className="trend-chart-shell">
        <ResponsiveContainer height="100%" width="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
          >
            <defs>
              <linearGradient id={`coach-evaluation-fill-${gradientId}`} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#1d4ed8" stopOpacity={0.24} />
                <stop offset="70%" stopColor="#3b82f6" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#93c5fd" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid
              stroke="rgba(11, 37, 69, 0.08)"
              strokeDasharray="3 6"
              vertical={false}
            />
            <XAxis
              axisLine={false}
              dataKey="footer"
              dy={8}
              interval={chartData.length > 10 ? "preserveStartEnd" : 0}
              minTickGap={18}
              tick={{ fill: "#5d718f", fontSize: 11, fontWeight: 700 }}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              domain={[0.75, 5.25]}
              tick={{ fill: "#5d718f", fontSize: 11, fontWeight: 700 }}
              tickFormatter={formatEvaluationTrendCode}
              tickLine={false}
              ticks={[1, 2, 3, 4, 5]}
              width={58}
            />
            <Tooltip
              content={({ active, payload }) => {
                const tooltipPoint = payload?.[0]?.payload as
                  | {
                      comment: string;
                      monthLabel: string;
                      trendLabel: string;
                    }
                  | undefined;

                if (!active || tooltipPoint == null) {
                  return null;
                }

                return (
                  <div className="trend-tooltip">
                    <strong>
                      {tooltipPoint.monthLabel} · {tooltipPoint.trendLabel}
                    </strong>
                    <span>{tooltipPoint.comment}</span>
                  </div>
                );
              }}
              cursor={{ stroke: "rgba(11, 37, 69, 0.16)", strokeDasharray: "4 4" }}
            />
            <ReferenceLine
              ifOverflow="extendDomain"
              stroke="rgba(11, 37, 69, 0.16)"
              strokeDasharray="4 4"
              y={3}
            />
            <Area
              activeDot={{ fill: "#ffffff", r: 5, stroke: "#0b2545", strokeWidth: 3 }}
              dataKey="value"
              dot={chartData.length === 1 ? { fill: "#ffffff", r: 4, stroke: "#0b2545", strokeWidth: 2.5 } : false}
              fill={`url(#coach-evaluation-fill-${gradientId})`}
              fillOpacity={1}
              stroke="#0b2545"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              type="monotone"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="visual-stat-row visual-stat-row--compact">
        <div className="visual-stat visual-stat--compact">
          <span>최근</span>
          <strong>{latest.trendLabel}</strong>
          <small>{latest.monthLabel}</small>
        </div>
        <div className="visual-stat visual-stat--compact">
          <span>최고</span>
          <strong>{maxPoint.trendLabel}</strong>
          <small>{maxPoint.monthLabel}</small>
        </div>
        <div className="visual-stat visual-stat--compact">
          <span>최저</span>
          <strong>{minPoint.trendLabel}</strong>
          <small>{minPoint.monthLabel}</small>
        </div>
      </div>
    </div>
  );
}

function renderMentalNote(item: PlayerMentalNoteItem) {
  return (
    <article className="note-card" key={item.mental_id}>
      <div className="detail-note-head">
        <strong>{item.counseling_type}</strong>
        <span className="metric-inline-badge metric-inline-badge--neutral">
          {formatCompactDate(item.session_date)}
        </span>
      </div>
      <p>"{item.player_quote}"</p>
      <span className="table-note">
        시즌 {item.season_year} · 세션 {item.session_round}
      </span>
    </article>
  );
}

function DeltaChip({
  text,
  className,
}: {
  text: string;
  className: string;
}) {
  return <span className={className}>{text}</span>;
}

export function PlayerDetailWorkspace({ data }: { data: PlayerDetailPayload }) {
  const [activeTab, setActiveTab] = useState<DetailTabKey>("overview");
  const [selectedSeason, setSelectedSeason] = useState(
    data.profile.latest_season_year ? String(data.profile.latest_season_year) : "all",
  );

  const seasonOptions = Array.from(
    new Set(
      [
        ...data.seasonSummaries.map((item) => item.season_year),
        ...data.matchPerformance.map((item) => item.season_year),
        ...data.physicalTests.map((item) => item.season_year),
        ...data.injuryHistory.map((item) => item.season_year),
        ...data.mentalNotes.map((item) => item.season_year),
      ].filter((value) => value != null),
    ),
  ).sort((left, right) => right - left);

  const selectedSeasonYear = selectedSeason === "all" ? null : Number(selectedSeason);
  const filteredSeasonSummaries =
    selectedSeasonYear == null
      ? data.seasonSummaries
      : data.seasonSummaries.filter((item) => item.season_year === selectedSeasonYear);
  const selectedSeasonSummary =
    filteredSeasonSummaries[0] ?? data.latestSeasonSummary ?? data.seasonSummaries[0] ?? null;
  const seasonMatches =
    selectedSeasonYear == null
      ? data.matchPerformance
      : data.matchPerformance.filter((item) => item.season_year === selectedSeasonYear);
  const visibleMatches = seasonMatches;
  const playedMatches = visibleMatches.filter((item) => item.minutes_played > 0);
  const overviewRecentMatches = playedMatches.slice(0, 5);
  const visiblePhysicalTests =
    selectedSeasonYear == null
      ? data.physicalTests
      : data.physicalTests.filter((item) => item.season_year === selectedSeasonYear);
  const visibleInjuryHistory =
    selectedSeasonYear == null
      ? data.injuryHistory
      : data.injuryHistory.filter((item) => item.season_year === selectedSeasonYear);
  const visibleMentalNotes =
    selectedSeasonYear == null
      ? data.mentalNotes
      : data.mentalNotes.filter((item) => item.season_year === selectedSeasonYear);
  const reportSeasonYears = Array.from(
    new Set(data.matchPerformance.map((item) => item.season_year).filter((value) => value != null)),
  ).sort((left, right) => left - right);
  const reportYearRangeLabel =
    reportSeasonYears.length === 0
      ? "기록 없음"
      : reportSeasonYears.length === 1
        ? String(reportSeasonYears[0])
        : `${reportSeasonYears[0]}~${reportSeasonYears[reportSeasonYears.length - 1]}`;
  const monthlyCoachEvaluations = buildMonthlyCoachEvaluations(data.matchPerformance);

  const latestMatch = visibleMatches[0];
  const latestPhysicalTest = visiblePhysicalTests[0];
  const previousPhysicalTest = visiblePhysicalTests[1] ?? data.physicalTests[1];
  const latestInjury = visibleInjuryHistory[0];
  const returnLabel = formatReturnCountdown(data.profile.latest_return_to_play_date);
  const totalGoals = visibleMatches.reduce((sum, item) => sum + item.goals, 0);
  const totalAssists = visibleMatches.reduce((sum, item) => sum + item.assists, 0);
  const totalPlayedMinutes = playedMatches.reduce((sum, item) => sum + item.minutes_played, 0);
  const totalGoalContrib = playedMatches.reduce((sum, item) => sum + item.goal_contrib, 0);
  const totalShots = playedMatches.reduce((sum, item) => sum + item.shots, 0);
  const totalShotsOnTarget = playedMatches.reduce((sum, item) => sum + item.shots_on_target, 0);
  const totalKeyPasses = playedMatches.reduce((sum, item) => sum + item.key_passes, 0);
  const totalPassAttempts = playedMatches.reduce((sum, item) => sum + item.pass_attempts, 0);
  const totalPassSuccess = playedMatches.reduce((sum, item) => sum + item.pass_success, 0);
  const totalDribbleAttempts = playedMatches.reduce((sum, item) => sum + item.dribble_attempts, 0);
  const totalDribbleSuccess = playedMatches.reduce((sum, item) => sum + item.dribble_success, 0);
  const totalTacklesWon = playedMatches.reduce((sum, item) => sum + item.tackles_won, 0);
  const totalInterceptions = playedMatches.reduce((sum, item) => sum + item.interceptions, 0);
  const totalClearings = playedMatches.reduce((sum, item) => sum + item.clearings, 0);
  const totalSaves = playedMatches.reduce((sum, item) => sum + item.saves, 0);
  const totalDuelsWon = playedMatches.reduce((sum, item) => sum + item.duels_won, 0);
  const totalDuelsLost = playedMatches.reduce((sum, item) => sum + item.duels_lost, 0);
  const totalYellowCards = playedMatches.reduce((sum, item) => sum + item.yellow_cards, 0);
  const totalRedCards = playedMatches.reduce((sum, item) => sum + item.red_cards, 0);
  const totalDistanceTotal = playedMatches.reduce((sum, item) => sum + (item.distance_total_km ?? 0), 0);
  const totalHighSpeedDistance = playedMatches.reduce((sum, item) => sum + (item.distance_high_speed_m ?? 0), 0);
  const totalSprintCount = playedMatches.reduce((sum, item) => sum + (item.sprint_count ?? 0), 0);
  const totalAccelerationCount = playedMatches.reduce((sum, item) => sum + (item.acceleration_count ?? 0), 0);
  const totalDecelerationCount = playedMatches.reduce((sum, item) => sum + (item.deceleration_count ?? 0), 0);
  const totalPlayerLoad = playedMatches.reduce((sum, item) => sum + (item.player_load ?? 0), 0);
  const recentAppearanceScore =
    overviewRecentMatches.reduce((sum, item) => sum + computeRecentMatchFormScore(item), 0) /
    Math.max(overviewRecentMatches.length, 1);
  const recentAppearanceMinutes = overviewRecentMatches.reduce((sum, item) => sum + item.minutes_played, 0);
  const matchPer90Metrics = [
    { key: "goals", group: "공격", label: "득점 / 90", note: "90분당 득점 생산", value: computePer90(totalGoals, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "assists", group: "공격", label: "도움 / 90", note: "90분당 도움 생산", value: computePer90(totalAssists, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "goal-contrib", group: "공격", label: "공격포인트 / 90", note: "득점과 도움 합산", value: computePer90(totalGoalContrib, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "shots", group: "공격", label: "슈팅 / 90", note: "90분당 전체 슈팅", value: computePer90(totalShots, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "shots-on-target", group: "공격", label: "유효슈팅 / 90", note: "90분당 유효 마무리", value: computePer90(totalShotsOnTarget, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "key-passes", group: "전개", label: "키패스 / 90", note: "90분당 찬스 메이킹", value: computePer90(totalKeyPasses, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "pass-attempts", group: "전개", label: "패스 시도 / 90", note: "90분당 패스 연결량", value: computePer90(totalPassAttempts, totalPlayedMinutes), digits: 1, unit: "" },
    { key: "pass-success", group: "전개", label: "패스 성공 / 90", note: "90분당 성공 패스", value: computePer90(totalPassSuccess, totalPlayedMinutes), digits: 1, unit: "" },
    { key: "dribble-attempts", group: "전개", label: "드리블 시도 / 90", note: "90분당 돌파 시도", value: computePer90(totalDribbleAttempts, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "dribble-success", group: "전개", label: "드리블 성공 / 90", note: "90분당 성공 돌파", value: computePer90(totalDribbleSuccess, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "tackles-won", group: "수비", label: "태클 / 90", note: "90분당 태클 성공", value: computePer90(totalTacklesWon, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "interceptions", group: "수비", label: "인터셉트 / 90", note: "90분당 차단 횟수", value: computePer90(totalInterceptions, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "clearings", group: "수비", label: "클리어링 / 90", note: "90분당 걷어내기", value: computePer90(totalClearings, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "saves", group: "수비", label: "세이브 / 90", note: "90분당 선방 횟수", value: computePer90(totalSaves, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "duels-won", group: "수비", label: "경합 승리 / 90", note: "90분당 경합 승리", value: computePer90(totalDuelsWon, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "duels-lost", group: "수비", label: "경합 패배 / 90", note: "90분당 경합 패배", value: computePer90(totalDuelsLost, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "distance-total", group: "활동량", label: "총거리 / 90", note: "90분당 이동 거리", value: computePer90(totalDistanceTotal, totalPlayedMinutes), digits: 2, unit: " km" },
    { key: "distance-high-speed", group: "활동량", label: "고속거리 / 90", note: "90분당 고속 주행", value: computePer90(totalHighSpeedDistance, totalPlayedMinutes), digits: 0, unit: " m" },
    { key: "sprint-count", group: "활동량", label: "스프린트 / 90", note: "90분당 스프린트", value: computePer90(totalSprintCount, totalPlayedMinutes), digits: 1, unit: "" },
    { key: "acceleration-count", group: "활동량", label: "가속 / 90", note: "90분당 가속 횟수", value: computePer90(totalAccelerationCount, totalPlayedMinutes), digits: 1, unit: "" },
    { key: "deceleration-count", group: "활동량", label: "감속 / 90", note: "90분당 감속 횟수", value: computePer90(totalDecelerationCount, totalPlayedMinutes), digits: 1, unit: "" },
    { key: "player-load", group: "활동량", label: "Player Load / 90", note: "90분당 경기 부하", value: computePer90(totalPlayerLoad, totalPlayedMinutes), digits: 1, unit: "" },
    { key: "yellow-cards", group: "리스크", label: "경고 / 90", note: "90분당 경고 빈도", value: computePer90(totalYellowCards, totalPlayedMinutes), digits: 2, unit: "" },
    { key: "red-cards", group: "리스크", label: "퇴장 / 90", note: "90분당 퇴장 빈도", value: computePer90(totalRedCards, totalPlayedMinutes), digits: 2, unit: "" },
  ];
  const matchPer90Groups = [
    {
      group: "공격",
      description: "득점, 도움, 슈팅 지표",
      items: matchPer90Metrics.filter((item) => item.group === "공격"),
    },
    {
      group: "전개",
      description: "패스와 드리블 연결 지표",
      items: matchPer90Metrics.filter((item) => item.group === "전개"),
    },
    {
      group: "수비",
      description: "수비 액션과 경합 지표",
      items: matchPer90Metrics.filter((item) => item.group === "수비"),
    },
    {
      group: "활동량",
      description: "거리, 스프린트, 부하 지표",
      items: matchPer90Metrics.filter((item) => item.group === "활동량"),
    },
    {
      group: "리스크",
      description: "카드 발생 빈도",
      items: matchPer90Metrics.filter((item) => item.group === "리스크"),
    },
  ].filter((group) => group.items.length > 0);
  const gpsMatches = visibleMatches.filter(isOfficialMatch);
  const gpsLatestMatch = gpsMatches[0] ?? null;
  const gpsTotalMinutes = gpsMatches.reduce(
    (sum, item) => sum + (firstValidNumber(item.play_time_min, item.minutes_played) ?? 0),
    0,
  );
  const gpsTotalDistance = gpsMatches.reduce(
    (sum, item) => sum + (firstValidNumber(item.total_distance, item.distance_total_km) ?? 0),
    0,
  );
  const gpsTotalSprintCount = gpsMatches.reduce((sum, item) => sum + (item.sprint_count ?? 0), 0);
  const gpsTotalPlayerLoad = gpsMatches.reduce((sum, item) => sum + (item.player_load ?? 0), 0);
  const averageGpsMaxSpeed = averageDefined(gpsMatches.map((item) => item.max_speed_kmh));
  const gpsDistancePer90 = gpsTotalMinutes > 0 ? computePer90(gpsTotalDistance, gpsTotalMinutes) : null;
  const gpsSprintCountPer90 = gpsTotalMinutes > 0 ? computePer90(gpsTotalSprintCount, gpsTotalMinutes) : null;
  const gpsPlayerLoadPer90 = gpsTotalMinutes > 0 ? computePer90(gpsTotalPlayerLoad, gpsTotalMinutes) : null;
  const matchesWithDistance = gpsMatches.filter(
    (item) => firstValidNumber(item.total_distance, item.distance_total_km) != null,
  );
  const matchesWithSprintCount = gpsMatches.filter((item) => item.sprint_count != null);
  const matchesWithMaxSpeed = gpsMatches.filter((item) => item.max_speed_kmh != null);
  const matchesWithPlayerLoad = gpsMatches.filter((item) => item.player_load != null);

  const primaryRoleDiffers =
    data.profile.primary_role != null &&
    data.profile.primary_role !== data.profile.registered_position;
  const weightDelta = buildDeltaMeta(latestPhysicalTest?.weight_kg, previousPhysicalTest?.weight_kg, {
    label: "체중",
    unit: "kg",
    digits: 1,
    preference: "neutral",
  });
  const bodyFatDelta = buildDeltaMeta(
    latestPhysicalTest?.body_fat_pct,
    previousPhysicalTest?.body_fat_pct,
    {
      label: "체지방",
      unit: "%p",
      digits: 1,
      preference: "down",
    },
  );
  const muscleDelta = buildDeltaMeta(
    latestPhysicalTest?.skeletal_muscle_kg,
    previousPhysicalTest?.skeletal_muscle_kg,
    {
      label: "골격근",
      unit: "kg",
      digits: 1,
      preference: "up",
    },
  );
  const sprintDelta = buildDeltaMeta(
    latestPhysicalTest?.sprint_30m_sec,
    previousPhysicalTest?.sprint_30m_sec,
    {
      label: "30m",
      unit: "s",
      digits: 2,
      preference: "down",
    },
  );
  const jumpDelta = buildDeltaMeta(
    latestPhysicalTest?.vertical_jump_cm,
    previousPhysicalTest?.vertical_jump_cm,
    {
      label: "점프",
      unit: "cm",
      digits: 1,
      preference: "up",
    },
  );
  const profileMeta: Array<{
    label: string;
    value: string;
  }> = [
    {
      label: "포지션",
      value: data.profile.registered_position ?? "-",
    },
    {
      label: "생년월일",
      value: data.profile.birth_date ? formatCompactDate(data.profile.birth_date) : "-",
    },
    {
      label: "신체정보",
      value: `${data.profile.height_cm ?? "-"}cm / ${data.profile.weight_kg ?? "-"}kg`,
    },
    {
      label: "주발",
      value: data.profile.dominant_foot ? formatDominantFoot(data.profile.dominant_foot) : "-",
    },
  ];
  const compareCards = [
    {
      key: "weight",
      label: "체중",
      value: formatValueWithUnit(latestPhysicalTest?.weight_kg, { digits: 1, unit: "kg" }),
      sub:
        previousPhysicalTest != null
          ? `직전 ${formatValueWithUnit(previousPhysicalTest.weight_kg, { digits: 1, unit: "kg" })} · ${formatCompactDate(previousPhysicalTest.test_date)}`
          : "직전 비교 기록 없음",
      delta: weightDelta,
    },
    {
      key: "body-fat",
      label: "체지방률",
      value: formatValueWithUnit(latestPhysicalTest?.body_fat_pct, { digits: 1, unit: "%" }),
      sub:
        previousPhysicalTest != null
          ? `직전 ${formatValueWithUnit(previousPhysicalTest.body_fat_pct, { digits: 1, unit: "%" })} · ${formatCompactDate(previousPhysicalTest.test_date)}`
          : "직전 비교 기록 없음",
      delta: bodyFatDelta,
    },
    {
      key: "muscle",
      label: "골격근량",
      value: formatValueWithUnit(latestPhysicalTest?.skeletal_muscle_kg, { digits: 1, unit: "kg" }),
      sub:
        previousPhysicalTest != null
          ? `직전 ${formatValueWithUnit(previousPhysicalTest.skeletal_muscle_kg, { digits: 1, unit: "kg" })} · ${formatCompactDate(previousPhysicalTest.test_date)}`
          : "직전 비교 기록 없음",
      delta: muscleDelta,
    },
    {
      key: "sprint",
      label: "30m 스프린트",
      value: formatValueWithUnit(latestPhysicalTest?.sprint_30m_sec, { digits: 2, unit: "s" }),
      sub:
        previousPhysicalTest != null
          ? `직전 ${formatValueWithUnit(previousPhysicalTest.sprint_30m_sec, { digits: 2, unit: "s" })} · ${formatCompactDate(previousPhysicalTest.test_date)}`
          : "직전 비교 기록 없음",
      delta: sprintDelta,
    },
    {
      key: "jump",
      label: "수직 점프",
      value: formatValueWithUnit(latestPhysicalTest?.vertical_jump_cm, { digits: 1, unit: "cm" }),
      sub:
        previousPhysicalTest != null
          ? `직전 ${formatValueWithUnit(previousPhysicalTest.vertical_jump_cm, { digits: 1, unit: "cm" })} · ${formatCompactDate(previousPhysicalTest.test_date)}`
          : "직전 비교 기록 없음",
      delta: jumpDelta,
    },
  ];
  const physicalTrendMetrics: PhysicalTrendMetricConfig[] = [
    {
      key: "height",
      eyebrow: "Height",
      title: "신장 추이",
      digits: 0,
      unit: "cm",
      value: (item) => item.height_cm,
    },
    {
      key: "weight",
      eyebrow: "Weight",
      title: "체중 추이",
      digits: 1,
      unit: "kg",
      value: (item) => item.weight_kg,
    },
    {
      key: "muscle",
      eyebrow: "Muscle",
      title: "골격근 추이",
      digits: 1,
      unit: "kg",
      value: (item) => item.skeletal_muscle_kg,
    },
    {
      key: "body-fat",
      eyebrow: "Body Fat",
      title: "체지방률 추이",
      digits: 1,
      unit: "%",
      value: (item) => item.body_fat_pct,
    },
    {
      key: "sprint-10m",
      eyebrow: "Sprint 10m",
      title: "10m 스프린트 추이",
      digits: 2,
      unit: "s",
      value: (item) => item.sprint_10m_sec,
    },
    {
      key: "sprint-30m",
      eyebrow: "Sprint 30m",
      title: "30m 스프린트 추이",
      digits: 2,
      unit: "s",
      value: (item) => item.sprint_30m_sec,
    },
    {
      key: "sprint-50m",
      eyebrow: "Sprint 50m",
      title: "50m 스프린트 추이",
      digits: 2,
      unit: "s",
      value: (item) => item.sprint_50m_sec,
    },
    {
      key: "sprint-100m",
      eyebrow: "Sprint 100m",
      title: "100m 스프린트 추이",
      digits: 2,
      unit: "s",
      value: (item) => item.sprint_100m_sec,
    },
    {
      key: "vertical-jump",
      eyebrow: "Vertical Jump",
      title: "수직 점프 추이",
      digits: 1,
      unit: "cm",
      value: (item) => item.vertical_jump_cm,
    },
    {
      key: "agility-t",
      eyebrow: "Agility T",
      title: "민첩성 추이",
      digits: 2,
      unit: "s",
      value: (item) => item.agility_t_sec,
    },
    {
      key: "shuttle-count",
      eyebrow: "Shuttle Count",
      title: "셔틀런 횟수 추이",
      digits: 0,
      unit: "회",
      value: (item) => item.shuttle_run_count,
    },
    {
      key: "shuttle-sec",
      eyebrow: "Shuttle Time",
      title: "셔틀런 시간 추이",
      digits: 2,
      unit: "s",
      value: (item) => item.shuttle_run_sec,
    },
    {
      key: "endurance",
      eyebrow: "Endurance",
      title: "지구력 추이",
      digits: 0,
      unit: "m",
      value: (item) => item.endurance_m,
    },
    {
      key: "flexibility",
      eyebrow: "Flexibility",
      title: "유연성 추이",
      digits: 1,
      unit: "cm",
      value: (item) => item.flexibility_cm,
    },
  ];

  return (
    <div className="player-detail-workspace">
      <section className="player-detail-hero">
        <div className="player-detail-hero__main">
          <div className="player-detail-hero__topbar">
            <Link className="secondary-button" href="/players">
              로스터로 돌아가기
            </Link>

            <label className="form-field player-detail-hero__season">
              <span>시즌 선택</span>
              <select
                aria-label="Filter player detail by season"
                onChange={(event) => setSelectedSeason(event.target.value)}
                value={selectedSeason}
              >
                <option value="all">전체 시즌</option>
                {seasonOptions.map((seasonYear) => (
                  <option key={seasonYear} value={seasonYear}>
                    {seasonYear} 시즌
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="player-detail-hero__header">
            <div className="player-detail-hero__identity">
              <p className="panel-eyebrow">Player Profile</p>
              <div className="player-detail-hero__title-row">
                <h1>{data.profile.name}</h1>
                <span className={availabilityTone(data.profile.latest_match_availability)}>
                  {data.profile.latest_match_availability ?? "상태 미기록"}
                </span>
              </div>
              <div className="player-detail-hero__tags">
                <span className="player-detail-tag player-detail-tag--strong">
                  {data.profile.registered_position ?? "-"}
                </span>
                {primaryRoleDiffers ? (
                  <span className="player-detail-tag">주 역할 {data.profile.primary_role}</span>
                ) : null}
                {data.profile.team_name ? (
                  <span className="player-detail-tag">{data.profile.team_name}</span>
                ) : null}
                <span className="player-detail-tag">{formatUnderAge(data.profile.age_today)}</span>
              </div>
              <div className="player-detail-profile-inline">
                {profileMeta.map((item) => (
                  <div className="player-detail-profile-inline__item" key={item.label}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="detail-tab-nav">
        {detailTabs.map((tab) => (
          <button
            className={activeTab === tab.key ? "detail-tab detail-tab--active" : "detail-tab"}
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" ? (
        <div className="detail-tab-stack">
          <section className="stat-grid">
            <article className="metric-card metric-card--highlight">
              <p>최근 폼</p>
              <strong>{recentAppearanceScore.toFixed(1)}</strong>
              <span>최근 출전 경기 기준 평균 점수</span>
              <div className="metric-card__meta">
                <span>최근 출전 경기</span>
                <strong>{numberFormatter.format(recentAppearanceMinutes)}분</strong>
              </div>
            </article>
            <article className="metric-card">
              <p>출전 시간</p>
              <strong>{numberFormatter.format(selectedSeasonSummary?.minutes ?? 0)}분</strong>
              <span>시즌 전체 누적 출전 시간</span>
              <div className="metric-card__meta">
                <span>선발 비율</span>
                <strong>{(selectedSeasonSummary?.start_rate_pct ?? 0).toFixed(1)}%</strong>
              </div>
            </article>
            <article className="metric-card">
              <p>Player Load / 90</p>
              <strong>{(selectedSeasonSummary?.player_load_p90 ?? 0).toFixed(1)}</strong>
              <span>경기 부하 지표</span>
              <div className="metric-card__meta">
                <span>활동량</span>
                <strong>{(selectedSeasonSummary?.distance_total_p90 ?? 0).toFixed(1)} km/90</strong>
              </div>
            </article>
            <article className="metric-card">
              <p>부상 결장일</p>
              <strong>{numberFormatter.format(data.reports.medical?.total_days_missed ?? 0)}일</strong>
              <span>최신 메디컬 리포트 누적 기준</span>
              <div className="metric-card__meta">
                <span>최근 부상일</span>
                <strong>{latestInjury ? formatCompactDate(latestInjury.record_date) : "기록 없음"}</strong>
              </div>
            </article>
          </section>

          <section className="dashboard-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Match Trend</p>
                  <h2>경기 폼 추이</h2>
                </div>
              </div>
              <TrendLinePanel
                eyebrow="Form Score"
                footerLabel={(item) => `R${item.match_no}`}
                formatValue={(value) => value.toFixed(1)}
                getLabel={(item) => `${item.opponent} · ${formatCompactDate(item.match_date)}`}
                getValue={(item) => computeRecentMatchFormScore(item)}
                items={playedMatches}
                title="Form Score"
              />
            </article>
          </section>

          <section className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Recent Matches</p>
                  <h2>최근 경기 기록</h2>
                </div>
              <p className="panel-note">선택한 시즌 기준 최근 경기 로그입니다.</p>
            </div>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>일자</th>
                    <th>상대</th>
                    <th>결과</th>
                    <th>포지션</th>
                    <th>출전 시간</th>
                    <th>득점 / 도움</th>
                  </tr>
                </thead>
                <tbody>
                  {playedMatches.length > 0 ? (
                    playedMatches.slice(0, 6).map((item) => (
                      <tr key={item.analysis_id}>
                        <td>{formatCompactDate(item.match_date)}</td>
                        <td>{item.opponent}</td>
                        <td>
                          <span className={resultTone(item.result)}>
                            {item.result} {item.score}
                          </span>
                        </td>
                        <td>{item.position_played}</td>
                        <td>{item.minutes_played}분</td>
                        <td>
                          {item.goals} / {item.assists}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="table-empty" colSpan={6}>
                        선택한 시즌 기준 출전 경기 기록이 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === "match" ? (
        <div className="detail-tab-stack">
          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Per 90 Summary</p>
                <h2>90분당 환산 지표</h2>
              </div>
            </div>
            {playedMatches.length > 0 ? (
              <div className="player-detail-metric-groups">
                {matchPer90Groups.map((group) => (
                  <section className="player-detail-metric-group" key={group.group}>
                    <div className="player-detail-metric-group__head">
                      <strong>{group.group}</strong>
                      <span>{group.description}</span>
                    </div>
                    <div className="player-detail-metric-group__grid">
                      {group.items.map((item) => (
                        <article className="player-detail-metric-card" key={item.key}>
                          <span>{item.label}</span>
                          <strong>{formatValueWithUnit(item.value, { digits: item.digits, unit: item.unit })}</strong>
                          <p>{item.note}</p>
                        </article>
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            ) : (
              <EmptyPanel
                title="90분당 환산 데이터 없음"
                description="출전 시간이 있는 경기 데이터가 없어 90분 환산 지표를 계산할 수 없습니다."
              />
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Full Match Log</p>
                <h2>경기별 퍼포먼스 기록</h2>
              </div>
            </div>
            {visibleMatches.length > 0 ? (
              <div className="table-scroll table-scroll--match-detail player-detail-match-log">
                <table className="data-table data-table--player-match-log match-detail-table">
                  <thead>
                    <tr>
                      <th><div className="match-detail-static-header-group"><span>R</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>상대</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>일자</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>결과</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>장소</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>출전</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>선발</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>등록 포지션</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>출전 포지션</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>분</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>전반</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>후반</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>교체 IN</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>교체 OUT</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>골</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>도움</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>공격P</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>슈팅</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>유효슈팅</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>키패스</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>패스 시도</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>패스 성공</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>패스%</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>드리블 시도</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>드리블 성공</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>드리블%</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>태클</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>인터셉트</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>클리어링</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>세이브</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>경합 승</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>경합 패</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>경고</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>퇴장</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>총거리</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>고속거리</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>최고속도</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>스프린트</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>가속</span></div></th>
                      <th><div className="match-detail-static-header-group"><span>감속</span></div></th>
                      <th>
                        <div className="match-detail-static-header-group">
                          <span>Load</span>
                          <MetricInfoHint
                            align="end"
                            lines={[
                              "가속, 감속, 방향전환 같은 움직임 강도를 합산한 외부 부하 지표입니다.",
                              "절대값보다 같은 선수의 경기 간 변화나 최근 추이를 보는 용도로 해석하는 편이 좋습니다.",
                            ]}
                            title="Player Load 안내"
                          />
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleMatches.map((item) => (
                      <tr key={item.analysis_id}>
                        <td>{item.match_no}</td>
                        <td>
                          <div className="match-detail-player-cell">
                            <strong>{item.opponent}</strong>
                            <span>{item.match_label}</span>
                          </div>
                        </td>
                        <td>{formatCompactDate(item.match_date)}</td>
                        <td>
                          <div className="match-detail-cell-stack">
                            <span className={resultTone(item.result)}>{item.result}</span>
                            <span>{item.score}</span>
                          </div>
                        </td>
                        <td>{item.venue}</td>
                        <td>{item.appearance_type}</td>
                        <td>{item.started === "Y" ? "선발" : "교체"}</td>
                        <td>{item.position}</td>
                        <td>{item.position_played}</td>
                        <td>{item.minutes_played}분</td>
                        <td>{item.first_half_minutes}분</td>
                        <td>{item.second_half_minutes}분</td>
                        <td>{item.sub_in_minute == null ? "-" : `${item.sub_in_minute}분`}</td>
                        <td>{item.sub_out_minute == null ? "-" : `${item.sub_out_minute}분`}</td>
                        <td>{item.goals}</td>
                        <td>{item.assists}</td>
                        <td>{item.goal_contrib}</td>
                        <td>{item.shots}</td>
                        <td>{item.shots_on_target}</td>
                        <td>{item.key_passes}</td>
                        <td>{item.pass_attempts}</td>
                        <td>{item.pass_success}</td>
                        <td>{formatValueWithUnit(item.pass_success_pct, { digits: 1, unit: "%" })}</td>
                        <td>{item.dribble_attempts}</td>
                        <td>{item.dribble_success}</td>
                        <td>{formatValueWithUnit(item.dribble_success_pct, { digits: 1, unit: "%" })}</td>
                        <td>{item.tackles_won}</td>
                        <td>{item.interceptions}</td>
                        <td>{item.clearings}</td>
                        <td>{item.saves}</td>
                        <td>{item.duels_won}</td>
                        <td>{item.duels_lost}</td>
                        <td>{item.yellow_cards}</td>
                        <td>{item.red_cards}</td>
                        <td>{formatValueWithUnit(item.distance_total_km, { digits: 2, unit: " km" })}</td>
                        <td>{formatValueWithUnit(item.distance_high_speed_m, { digits: 0, unit: " m" })}</td>
                        <td>{formatValueWithUnit(item.max_speed_kmh, { digits: 1, unit: " km/h" })}</td>
                        <td>{formatValueWithUnit(item.sprint_count, { digits: 0, unit: "회" })}</td>
                        <td>{formatValueWithUnit(item.acceleration_count, { digits: 0, unit: "회" })}</td>
                        <td>{formatValueWithUnit(item.deceleration_count, { digits: 0, unit: "회" })}</td>
                        <td>{formatValueWithUnit(item.player_load, { digits: 1, unit: "" })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyPanel
                title="경기별 퍼포먼스 데이터 없음"
                description="선택한 시즌 기준 경기별 퍼포먼스 데이터가 없습니다."
              />
            )}
          </section>
        </div>
      ) : null}

      {activeTab === "physical" ? (
        <div className="detail-tab-stack">
          <section className="player-detail-compare-section">
            <div className="section-head section-head--compact">
              <div>
                <p className="panel-eyebrow">Physical Comparison</p>
                <h2>직전 테스트 대비 변화</h2>
              </div>
              <p className="panel-note">
                최근 테스트와 직전 테스트를 나란히 비교해 변화 방향을 바로 확인합니다.
              </p>
            </div>
            <div className="player-detail-compare-grid">
              {compareCards.map((item) => (
                <article className="player-detail-compare-card" key={item.key}>
                  <span className="player-detail-compare-card__label">{item.label}</span>
                  <strong className="player-detail-compare-card__value">{item.value}</strong>
                  <div className="player-detail-compare-card__foot">
                    <small className="player-detail-compare-card__sub">{item.sub}</small>
                    {item.delta ? (
                      <DeltaChip className={item.delta.className} text={item.delta.text} />
                    ) : (
                      <span className="detail-delta detail-delta--neutral">비교 불가</span>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="dashboard-grid dashboard-grid--triple">
            {physicalTrendMetrics.map((metric) => {
              const metricItems = visiblePhysicalTests.filter((item) => metric.value(item) != null);

              return (
                <article className="panel" key={metric.key}>
                  <div className="panel-header">
                    <div>
                      <p className="panel-eyebrow">{metric.eyebrow}</p>
                      <h2>{metric.title}</h2>
                    </div>
                  </div>
                  <TrendLinePanel
                    eyebrow={metric.eyebrow}
                    footerLabel={(item) => `T${item.test_round}`}
                    formatValue={(value) =>
                      formatValueWithUnit(value, {
                        digits: metric.digits ?? 1,
                        unit: metric.unit ?? "",
                      })
                    }
                    getLabel={(item) => formatCompactDate(item.test_date)}
                    getValue={(item) => metric.value(item) ?? 0}
                    items={metricItems}
                    title={metric.title}
                  />
                </article>
              );
            })}
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Physical History</p>
                <h2>피지컬 테스트 기록</h2>
              </div>
              <p className="panel-note">테스트 회차별 기록입니다.</p>
            </div>
            <div className="table-scroll table-scroll--wide">
              <table className="data-table data-table--dense">
                <thead>
                  <tr>
                    <th>일자</th>
                    <th>회차</th>
                    <th>신장</th>
                    <th>체중</th>
                    <th>골격근</th>
                    <th>체지방</th>
                    <th>10m</th>
                    <th>30m</th>
                    <th>50m</th>
                    <th>100m</th>
                    <th>점프</th>
                    <th>민첩성</th>
                    <th>셔틀런</th>
                  </tr>
                </thead>
                <tbody>
                  {visiblePhysicalTests.length > 0 ? (
                    visiblePhysicalTests.map((item) => (
                      <tr key={item.physical_id}>
                        <td>{formatCompactDate(item.test_date)}</td>
                        <td>{item.test_round}</td>
                        <td>{formatValueWithUnit(item.height_cm, { digits: 0 })}</td>
                        <td>{formatValueWithUnit(item.weight_kg, { digits: 1 })}</td>
                        <td>{formatValueWithUnit(item.skeletal_muscle_kg, { digits: 1 })}</td>
                        <td>{formatValueWithUnit(item.body_fat_pct, { digits: 1, unit: "%" })}</td>
                        <td>{formatValueWithUnit(item.sprint_10m_sec, { digits: 2 })}</td>
                        <td>{formatValueWithUnit(item.sprint_30m_sec, { digits: 2 })}</td>
                        <td>{formatValueWithUnit(item.sprint_50m_sec, { digits: 2 })}</td>
                        <td>{formatValueWithUnit(item.sprint_100m_sec, { digits: 2 })}</td>
                        <td>{formatValueWithUnit(item.vertical_jump_cm, { digits: 1 })}</td>
                        <td>{formatValueWithUnit(item.agility_t_sec, { digits: 2 })}</td>
                        <td>{formatValueWithUnit(item.shuttle_run_count, { digits: 0 })}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="table-empty" colSpan={13}>
                        피지컬 테스트 기록이 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === "gps" ? (
        <div className="detail-tab-stack">
          <section className="stat-grid">
            <article className="metric-card metric-card--highlight">
              <p>평균 최고 속도</p>
              <strong>{formatValueWithUnit(averageGpsMaxSpeed, { digits: 1, unit: " km/h" })}</strong>
              <span>선택 시즌 공식경기 기준 평균 최고 속도</span>
            </article>
            <article className="metric-card">
              <p>Player Load / 90</p>
              <strong>{formatValueWithUnit(gpsPlayerLoadPer90, { digits: 1 })}</strong>
              <span>공식경기 기준 90분당 부하 지표</span>
            </article>
            <article className="metric-card">
              <p>총거리 / 90</p>
              <strong>{formatValueWithUnit(gpsDistancePer90, { digits: 2, unit: " km" })}</strong>
              <span>공식경기 기준 90분당 이동 거리</span>
            </article>
            <article className="metric-card">
              <p>스프린트 / 90</p>
              <strong>{formatValueWithUnit(gpsSprintCountPer90, { digits: 1, unit: "회" })}</strong>
              <span>공식경기 기준 90분당 스프린트 수</span>
            </article>
          </section>

          <section className="dashboard-grid dashboard-grid--split">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Activity Trend</p>
                  <h2>활동량 추이</h2>
                </div>
                <p className="panel-note">공식경기별 총거리 변화를 확인합니다.</p>
              </div>
              <TrendLinePanel
                eyebrow="Total Distance"
                footerLabel={(item) => `R${item.match_no}`}
                formatValue={(value) => `${value.toFixed(2)} km`}
                getLabel={(item) => `${item.opponent} · ${formatCompactDate(item.match_date)}`}
                getValue={(item) => firstValidNumber(item.total_distance, item.distance_total_km) ?? 0}
                items={matchesWithDistance}
                title="Total Distance"
              />
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Sprint Trend</p>
                  <h2>스프린트 횟수 추이</h2>
                </div>
                <p className="panel-note">공식경기별 스프린트 횟수를 비교합니다.</p>
              </div>
              <TrendLinePanel
                eyebrow="Sprint Count"
                footerLabel={(item) => `R${item.match_no}`}
                formatValue={(value) => `${value.toFixed(0)}회`}
                getLabel={(item) => `${item.opponent} · ${formatCompactDate(item.match_date)}`}
                getValue={(item) => item.sprint_count ?? 0}
                items={matchesWithSprintCount}
                title="Sprint Count"
              />
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">GPS Trend</p>
                  <h2>최고 속도 추이</h2>
                </div>
                <p className="panel-note">공식경기별 최고 속도 변화를 확인합니다.</p>
              </div>
              <TrendLinePanel
                eyebrow="Max Speed"
                footerLabel={(item) => `R${item.match_no}`}
                formatValue={(value) => `${value.toFixed(1)} km/h`}
                getLabel={(item) => `${item.opponent} · ${formatCompactDate(item.match_date)}`}
                getValue={(item) => item.max_speed_kmh ?? 0}
                items={matchesWithMaxSpeed}
                title="Max Speed"
              />
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Load Trend</p>
                  <h2>Player Load 추이</h2>
                </div>
                <p className="panel-note">공식경기별 부하 강도를 비교합니다.</p>
              </div>
              <TrendLinePanel
                eyebrow="Player Load"
                footerLabel={(item) => `R${item.match_no}`}
                formatValue={(value) => value.toFixed(1)}
                getLabel={(item) => `${item.opponent} · ${formatCompactDate(item.match_date)}`}
                getValue={(item) => item.player_load ?? 0}
                items={matchesWithPlayerLoad}
                title="Player Load"
              />
            </article>
          </section>

          <section className="snapshot-grid">
            <article className="snapshot-card">
              <span>최근 최고 속도</span>
              <strong>{gpsLatestMatch?.max_speed_kmh?.toFixed(1) ?? "-"} km/h</strong>
              <p>{gpsLatestMatch ? `${gpsLatestMatch.opponent} · ${formatCompactDate(gpsLatestMatch.match_date)}` : "-"}</p>
            </article>
            <article className="snapshot-card">
              <span>최근 총거리</span>
              <strong>{gpsLatestMatch?.distance_total_km?.toFixed(2) ?? "-"} km</strong>
              <p>고속 거리 {gpsLatestMatch?.distance_high_speed_m?.toFixed(0) ?? "-"} m</p>
            </article>
            <article className="snapshot-card">
              <span>최근 스프린트</span>
              <strong>{gpsLatestMatch?.sprint_count?.toFixed(0) ?? "-"}</strong>
              <p>가속 {gpsLatestMatch?.acceleration_count?.toFixed(0) ?? "-"}회</p>
            </article>
            <article className="snapshot-card">
              <span>최근 Player Load</span>
              <strong>{gpsLatestMatch?.player_load?.toFixed(1) ?? "-"}</strong>
              <p>감속 {gpsLatestMatch?.deceleration_count?.toFixed(0) ?? "-"}회</p>
            </article>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">GPS Log</p>
                <h2>경기 GPS 기록</h2>
              </div>
              <p className="panel-note">공식경기 기록만 표시합니다.</p>
            </div>
            <div className="table-scroll table-scroll--match-detail player-detail-match-log">
              <table className="data-table data-table--match-detail-gps match-detail-table">
                <thead>
                  <tr>
                    <th>No.</th>
                    <th>상대</th>
                    <th>GPS 시간</th>
                    <th>총 거리</th>
                    <th>평균속도</th>
                    <th>최고속도</th>
                    <th>스프린트</th>
                    <th>스프린트 거리</th>
                    <th>가속</th>
                    <th>감속</th>
                    <th>고강도 가속</th>
                    <th>고강도 감속</th>
                    <th>방향전환</th>
                    <th>0-15분</th>
                    <th>15-30분</th>
                    <th>30-45분</th>
                    <th>45-60분</th>
                    <th>60-75분</th>
                    <th>75-90분</th>
                    <th>0-5 km/h</th>
                    <th>5-10 km/h</th>
                    <th>10-15 km/h</th>
                    <th>15-20 km/h</th>
                    <th>20-25 km/h</th>
                    <th>25+ km/h</th>
                    <th>
                      <div className="match-detail-static-header-group">
                        <span>Load</span>
                        <MetricInfoHint
                          align="end"
                          lines={[
                            "가속, 감속, 방향전환 같은 움직임 강도를 합산한 외부 부하 지표입니다.",
                            "절대값보다 같은 선수의 경기 간 변화나 최근 추이를 보는 용도로 해석하는 편이 좋습니다.",
                          ]}
                          title="Player Load 안내"
                        />
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {gpsMatches.length > 0 ? (
                    gpsMatches.map((item) => {
                      const gpsMinutes = firstValidNumber(item.play_time_min, item.minutes_played);
                      const totalDistance = firstValidNumber(item.total_distance, item.distance_total_km);
                      const avgSpeed = firstValidNumber(
                        item.avg_speed,
                        computeAverageSpeedKmh(totalDistance, gpsMinutes),
                      );
                      const maxSpeed = firstValidNumber(item.max_speed, item.max_speed_kmh);
                      const sprintDistance = firstValidNumber(item.sprint_distance, item.distance_high_speed_m);
                      const accelCount = firstValidNumber(item.accel_count, item.acceleration_count);
                      const decelCount = firstValidNumber(item.decel_count, item.deceleration_count);

                      return (
                        <tr key={item.analysis_id}>
                          <td>{item.match_no}</td>
                          <td>
                            <div className="match-detail-player-cell">
                              <strong>{item.opponent}</strong>
                              <span>{item.position_played}</span>
                            </div>
                          </td>
                          <td>{formatValueWithUnit(gpsMinutes, { digits: 0, unit: "분" })}</td>
                          <td>{formatValueWithUnit(totalDistance, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(avgSpeed, { digits: 1, unit: " km/h" })}</td>
                          <td>{formatValueWithUnit(maxSpeed, { digits: 1, unit: " km/h" })}</td>
                          <td>{formatValueWithUnit(item.sprint_count, { digits: 0, unit: "회" })}</td>
                          <td>{formatValueWithUnit(sprintDistance, { digits: 0, unit: " m" })}</td>
                          <td>{formatValueWithUnit(accelCount, { digits: 0, unit: "회" })}</td>
                          <td>{formatValueWithUnit(decelCount, { digits: 0, unit: "회" })}</td>
                          <td>{formatValueWithUnit(item.hi_accel_count, { digits: 0, unit: "회" })}</td>
                          <td>{formatValueWithUnit(item.hi_decel_count, { digits: 0, unit: "회" })}</td>
                          <td>{formatValueWithUnit(item.cod_count, { digits: 0, unit: "회" })}</td>
                          <td>{formatValueWithUnit(item.distance_0_15_min, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_15_30_min, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_30_45_min, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_45_60_min, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_60_75_min, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_75_90_min, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_speed_0_5, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_speed_5_10, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_speed_10_15, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_speed_15_20, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_speed_20_25, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.distance_speed_25_plus, { digits: 2, unit: " km" })}</td>
                          <td>{formatValueWithUnit(item.player_load, { digits: 1, unit: "" })}</td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td className="table-empty" colSpan={26}>
                        공식경기 GPS 기록이 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === "injury" ? (
        <div className="detail-tab-stack">
          <section className="stat-grid">
            <article className="metric-card">
              <p>누적 결장일</p>
              <strong>{numberFormatter.format(data.reports.medical?.total_days_missed ?? 0)}일</strong>
              <span>메디컬 리포트 기준</span>
            </article>
            <article className="metric-card">
              <p>불가 이벤트</p>
              <strong>{numberFormatter.format(data.reports.medical?.unavailable_events ?? 0)}회</strong>
              <span>완전 이탈 기준</span>
            </article>
            <article className="metric-card">
              <p>조건부 이벤트</p>
              <strong>{numberFormatter.format(data.reports.medical?.conditional_events ?? 0)}회</strong>
              <span>제한 가동 기준</span>
            </article>
            <article className="metric-card">
              <p>예상 복귀</p>
              <strong>{returnLabel ?? "-"}</strong>
              <span>{data.profile.latest_injury_name ?? "최근 부상명 없음"}</span>
            </article>
          </section>

          <section className="dashboard-grid dashboard-grid--split">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Injury Timeline</p>
                  <h2>부상 / AT 타임라인</h2>
                </div>
                <p className="panel-note">부상, 피로, 재활 이벤트를 날짜 순으로 배치했습니다.</p>
              </div>
              <div className="timeline">
                {visibleInjuryHistory.length > 0 ? (
                  visibleInjuryHistory.map((item) => (
                    <article className="timeline-item" key={item.at_id}>
                      <strong>
                        {formatCompactDate(item.record_date)} · {item.status_type}
                      </strong>
                      <p>
                        {item.injury_name ?? item.body_part ?? "메디컬 기록"} ·{" "}
                        {item.rehab_stage ?? "재활 단계 미기록"}
                      </p>
                      <p>
                        {item.match_availability} · 결장 {item.days_missed}일
                      </p>
                    </article>
                  ))
                ) : (
                  <EmptyPanel
                    title="AT 기록 없음"
                    description="선택한 시즌 기준 부상 / AT 기록이 없습니다."
                  />
                )}
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Latest Medical Snapshot</p>
                  <h2>최신 메디컬 상태</h2>
                </div>
              </div>
              {latestInjury ? (
                <div className="attention-list">
                  <article className={injuryEventTone(latestInjury)}>
                    <div>
                      <strong>{latestInjury.injury_name ?? latestInjury.status_type}</strong>
                      <span>{latestInjury.injury_grade ?? latestInjury.rehab_stage ?? "등급 미기록"}</span>
                    </div>
                    <p>
                      {latestInjury.match_availability} · 훈련 {latestInjury.training_participation ?? "미기록"}
                    </p>
                  </article>
                  <div className="registry-list">
                    <div className="registry-row">
                      <span>최근 기록일</span>
                      <strong>{formatCompactDate(latestInjury.record_date)}</strong>
                    </div>
                    <div className="registry-row">
                      <span>예상 복귀일</span>
                      <strong>{formatCompactDate(latestInjury.return_to_play_date ?? "")}</strong>
                    </div>
                    <div className="registry-row">
                      <span>Body Part</span>
                      <strong>{latestInjury.body_part ?? "-"}</strong>
                    </div>
                  </div>
                </div>
              ) : (
                <EmptyPanel
                  title="최신 메디컬 기록 없음"
                  description="선택한 시즌에서 표시할 부상 상태가 없습니다."
                />
              )}
            </article>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Medical Records</p>
                <h2>AT 기록</h2>
              </div>
              <p className="panel-note">기록 날짜, 부상명, 재활 단계, 가용 여부를 전체 기록으로 봅니다.</p>
            </div>
            <div className="table-scroll table-scroll--wide">
              <table className="data-table data-table--dense">
                <thead>
                  <tr>
                    <th>기록일</th>
                    <th>상태</th>
                    <th>부위</th>
                    <th>부상명</th>
                    <th>등급</th>
                    <th>가용 상태</th>
                    <th>결장일</th>
                    <th>복귀일</th>
                    <th>재활 단계</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleInjuryHistory.length > 0 ? (
                    visibleInjuryHistory.map((item) => (
                      <tr key={item.at_id}>
                        <td>{formatCompactDate(item.record_date)}</td>
                        <td>{item.status_type}</td>
                        <td>{item.body_part ?? "-"}</td>
                        <td>{item.injury_name ?? "-"}</td>
                        <td>{item.injury_grade ?? "-"}</td>
                        <td>
                          <span className={availabilityTone(item.match_availability)}>
                            {item.match_availability}
                          </span>
                        </td>
                        <td>{item.days_missed}</td>
                        <td>{formatCompactDate(item.return_to_play_date ?? "")}</td>
                        <td>{item.rehab_stage ?? "-"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="table-empty" colSpan={9}>
                        메디컬 기록이 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === "mental" ? (
        <div className="detail-tab-stack">
          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Mental Notes</p>
                <h2>멘탈 / 상담 기록</h2>
              </div>
              <p className="panel-note">민감한 기록이라 과한 장식 없이 날짜와 선수 발화를 중심으로 구성했습니다.</p>
            </div>
            <div className="note-list">
              {visibleMentalNotes.length > 0 ? (
                visibleMentalNotes.map((item) => renderMentalNote(item))
              ) : (
                <EmptyPanel
                  title="멘탈 기록 없음"
                  description="선택한 시즌 기준 상담 기록이 없습니다."
                />
              )}
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === "reports" ? (
        <div className="detail-tab-stack">
          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Coach Reports</p>
                <h2>월간 지도자 평가</h2>
              </div>
              <p className="panel-note">{reportYearRangeLabel} 전체 경기 기준으로 월 1회 평가와 코멘트만 남깁니다.</p>
            </div>
            {monthlyCoachEvaluations.length > 0 ? (
              <div className="coach-evaluation-stack">
                <CoachEvaluationTrendPanel
                  items={monthlyCoachEvaluations}
                  yearRangeLabel={reportYearRangeLabel}
                />
                <div className="note-list">
                  {monthlyCoachEvaluations.map((item) => (
                    <article className="note-card coach-evaluation-card" key={item.id}>
                      <div className="coach-evaluation-card__head">
                        <div>
                          <strong>{item.monthLabel}</strong>
                          <span>
                            {formatCompactDate(item.evaluationDate)} 평가 · {numberFormatter.format(item.matchCount)}경기 기준
                          </span>
                        </div>
                        <span className={getEvaluationTrendBadgeClass(item.trendLabel)}>
                          {item.trendLabel}
                        </span>
                      </div>
                      <p>{item.comment}</p>
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyPanel
                title="월간 평가 없음"
                description="2023년부터 2025년까지 월간 지도자 평가를 만들 경기 기록이 없습니다."
              />
            )}
          </section>
        </div>
      ) : null}
    </div>
  );
}
