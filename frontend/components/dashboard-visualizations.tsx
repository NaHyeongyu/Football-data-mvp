"use client";

import { useId } from "react";
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
  ChartValuePoint,
  PositionSnapshotItem,
  SeasonTrendItem,
  TeamMatchTrendItem,
} from "@/lib/data-types";
import { formatCompactDate, formatPositionGroup } from "@/lib/dashboard-formatters";

function EmptyVisualization({
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

function formatSigned(value: number, digits = 1) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}`;
}

const dashboardToneStyles = {
  brand: {
    areaTop: "#1e4330",
    areaBottom: "#afc3b5",
    stroke: "#1a3929",
  },
  success: {
    areaTop: "#2e7d4f",
    areaBottom: "#afc3b5",
    stroke: "#2e7d4f",
  },
  danger: {
    areaTop: "#c94c4c",
    areaBottom: "#f2cfcf",
    stroke: "#c94c4c",
  },
} as const;

export function CompactSparkBars({
  items,
  tone = "brand",
}: {
  items: ChartValuePoint[];
  tone?: "brand" | "soft" | "danger";
}) {
  if (items.length === 0) {
    return null;
  }

  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className={`spark-bars spark-bars--${tone}`} aria-hidden="true">
      {items.map((item) => (
        <span
          className="spark-bars__bar"
          key={`${item.label}-${item.value}`}
          style={{ height: `${Math.max(14, (item.value / max) * 100)}%` }}
          title={`${item.label}: ${item.value.toFixed(1)}`}
        />
      ))}
    </div>
  );
}

export function SeasonPerformanceVisual({
  items,
}: {
  items: SeasonTrendItem[];
}) {
  const gradientId = `season-points-${useId().replace(/:/g, "")}`;

  if (items.length === 0) {
    return (
      <EmptyVisualization
        title="시즌 성과 없음"
        description="시즌 단위 성과 시각화에 필요한 원장이 없습니다."
      />
    );
  }

  const ordered = [...items].sort((left, right) => left.season_year - right.season_year);
  const latest = ordered[ordered.length - 1];
  const previous = ordered[ordered.length - 2];
  const pointDelta = previous ? latest.points - previous.points : 0;
  const winRateDelta = previous ? latest.win_rate_pct - previous.win_rate_pct : 0;
  const chartData = ordered.map((item) => ({
    detail: `${item.season_id} · 승률 ${item.win_rate_pct.toFixed(1)}%`,
    formatted: `${item.points} pts`,
    label: String(item.season_year),
    value: item.points,
  }));
  const averagePoints =
    ordered.reduce((sum, item) => sum + item.points, 0) / Math.max(ordered.length, 1);

  return (
    <div className="visual-card visual-card--chart">
      <div className="visual-card__header">
        <div>
          <p className="visual-card__eyebrow">Python Output</p>
          <strong>{latest.points} pts</strong>
          <span>
            {latest.season_id} 기준 승률 {latest.win_rate_pct.toFixed(1)}%
          </span>
        </div>
        <div className="visual-delta">
          <span>전 시즌 대비</span>
          <strong>{formatSigned(pointDelta, 0)} pts</strong>
        </div>
      </div>

      <div className="trend-chart-shell">
        <ResponsiveContainer height="100%" width="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#1e4330" stopOpacity={0.24} />
                <stop offset="70%" stopColor="#4e7a67" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#afc3b5" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid
              stroke="rgba(26, 57, 41, 0.08)"
              strokeDasharray="3 6"
              vertical={false}
            />
            <XAxis
              axisLine={false}
              dataKey="label"
              dy={8}
              tick={{ fill: "#5f7467", fontSize: 11, fontWeight: 700 }}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              domain={["dataMin - 3", "dataMax + 3"]}
              tick={false}
              tickLine={false}
              width={0}
            />
            <Tooltip
              content={({ active, payload }) => {
                const tooltipPoint = payload?.[0]?.payload as
                  | {
                      detail: string;
                      formatted: string;
                      label: string;
                    }
                  | undefined;

                if (!active || tooltipPoint == null) {
                  return null;
                }

                return (
                  <div className="trend-tooltip">
                    <strong>
                      {tooltipPoint.label} · {tooltipPoint.formatted}
                    </strong>
                    <span>{tooltipPoint.detail}</span>
                  </div>
                );
              }}
              cursor={{ stroke: "rgba(26, 57, 41, 0.16)", strokeDasharray: "4 4" }}
            />
            <ReferenceLine
              ifOverflow="extendDomain"
              stroke="rgba(26, 57, 41, 0.16)"
              strokeDasharray="4 4"
              y={averagePoints}
            />
            <Area
              activeDot={{ fill: "#ffffff", r: 5, stroke: "#1a3929", strokeWidth: 3 }}
              dataKey="value"
              dot={chartData.length === 1 ? { fill: "#ffffff", r: 4, stroke: "#1a3929", strokeWidth: 2.5 } : false}
              fill={`url(#${gradientId})`}
              fillOpacity={1}
              stroke="#1a3929"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              type="monotone"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="visual-stat-row">
        <article className="visual-stat">
          <span>승점/경기</span>
          <strong>{latest.points_per_match.toFixed(2)}</strong>
          <small>{previous ? formatSigned(latest.points_per_match - previous.points_per_match, 2) : "0.00"}</small>
        </article>
        <article className="visual-stat">
          <span>득점/경기</span>
          <strong>{latest.goals_for_per_match.toFixed(2)}</strong>
          <small>{latest.goals_for} goals</small>
        </article>
        <article className="visual-stat">
          <span>실점/경기</span>
          <strong>{latest.goals_against_per_match.toFixed(2)}</strong>
          <small>{latest.goals_against} conceded</small>
        </article>
        <article className="visual-stat">
          <span>승률 변화</span>
          <strong>{formatSigned(winRateDelta, 1)}%</strong>
          <small>{latest.win_rate_pct.toFixed(1)}%</small>
        </article>
      </div>
    </div>
  );
}

function MetricStrip({
  title,
  subtitle,
  items,
  tone,
  valueKey,
  formatter,
}: {
  title: string;
  subtitle: string;
  items: TeamMatchTrendItem[];
  tone: "primary" | "success" | "danger";
  valueKey: "distance_total_p90" | "sprint_count_p90" | "player_load_p90";
  formatter: (value: number) => string;
}) {
  const gradientId = `metric-strip-${useId().replace(/:/g, "")}`;
  const latest = items[items.length - 1];
  const toneStyle =
    tone === "primary"
      ? dashboardToneStyles.brand
      : tone === "success"
        ? dashboardToneStyles.success
        : dashboardToneStyles.danger;
  const chartData = items.map((item) => ({
    detail: `${item.opponent} · ${formatCompactDate(item.match_date)}`,
    formatted: formatter(item[valueKey]),
    label: item.match_label,
    value: item[valueKey],
  }));

  return (
    <article className={`metric-strip metric-strip--${tone}`}>
      <div className="metric-strip__header">
        <div>
          <p>{title}</p>
          <strong>{formatter(latest[valueKey])}</strong>
        </div>
        <span>{subtitle}</span>
      </div>

      <div className="metric-strip__chart-shell">
        <ResponsiveContainer height="100%" width="100%">
          <AreaChart data={chartData} margin={{ top: 6, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={toneStyle.areaTop} stopOpacity={0.24} />
                <stop offset="100%" stopColor={toneStyle.areaBottom} stopOpacity={0.04} />
              </linearGradient>
            </defs>
            <CartesianGrid
              stroke="rgba(26, 57, 41, 0.08)"
              strokeDasharray="3 6"
              vertical={false}
            />
            <XAxis hide dataKey="label" />
            <YAxis hide domain={["dataMin - 2", "dataMax + 2"]} />
            <Tooltip
              content={({ active, payload }) => {
                const tooltipPoint = payload?.[0]?.payload as
                  | {
                      detail: string;
                      formatted: string;
                      label: string;
                    }
                  | undefined;

                if (!active || tooltipPoint == null) {
                  return null;
                }

                return (
                  <div className="trend-tooltip">
                    <strong>
                      {tooltipPoint.label} · {tooltipPoint.formatted}
                    </strong>
                    <span>{tooltipPoint.detail}</span>
                  </div>
                );
              }}
              cursor={{ stroke: "rgba(26, 57, 41, 0.14)", strokeDasharray: "4 4" }}
            />
            <Area
              activeDot={{ fill: "#ffffff", r: 4, stroke: toneStyle.stroke, strokeWidth: 2.5 }}
              dataKey="value"
              dot={chartData.length === 1 ? { fill: "#ffffff", r: 3.5, stroke: toneStyle.stroke, strokeWidth: 2 } : false}
              fill={`url(#${gradientId})`}
              fillOpacity={1}
              stroke={toneStyle.stroke}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              type="monotone"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="metric-strip__footer">
        <span>{items[0].match_label}</span>
        <span>{latest.match_label}</span>
      </div>
    </article>
  );
}

export function MatchLoadVisual({
  items,
}: {
  items: TeamMatchTrendItem[];
}) {
  if (items.length === 0) {
    return (
      <EmptyVisualization
        title="매치 로드 데이터 없음"
        description="경기별 로드 시각화에 필요한 원장이 없습니다."
      />
    );
  }

  const recentWindow = items.slice(-6);
  const latest = recentWindow[recentWindow.length - 1];

  return (
    <div className="visual-stack">
      <div className="visual-stack__summary">
        <div>
          <p className="visual-card__eyebrow">Latest Match</p>
          <strong>
            {latest.match_label} vs {latest.opponent}
          </strong>
          <span>
            {formatCompactDate(latest.match_date)} · {latest.active_players}명 가동 · 결과 {latest.result}
          </span>
        </div>
      </div>

      <div className="metric-strip-grid">
        <MetricStrip
          formatter={(value) => `${value.toFixed(2)} km`}
          items={recentWindow}
          subtitle="distance / 90"
          title="총 이동거리"
          tone="primary"
          valueKey="distance_total_p90"
        />
        <MetricStrip
          formatter={(value) => `${value.toFixed(1)}`}
          items={recentWindow}
          subtitle="sprint count / 90"
          title="스프린트 수"
          tone="success"
          valueKey="sprint_count_p90"
        />
        <MetricStrip
          formatter={(value) => `${value.toFixed(1)}`}
          items={recentWindow}
          subtitle="player load / 90"
          title="Player Load"
          tone="danger"
          valueKey="player_load_p90"
        />
      </div>
    </div>
  );
}

function metricBarWidth(value: number, max: number) {
  if (max <= 0) {
    return "8%";
  }
  return `${Math.max(8, (value / max) * 100)}%`;
}

export function PositionSnapshotVisual({
  items,
}: {
  items: PositionSnapshotItem[];
}) {
  if (items.length === 0) {
    return (
      <EmptyVisualization
        title="포지션 비교 없음"
        description="포지션별 비교 시각화에 필요한 원장이 없습니다."
      />
    );
  }

  const maxMinutes = Math.max(...items.map((item) => item.avg_minutes_share_pct), 1);
  const maxLoad = Math.max(...items.map((item) => item.avg_player_load_p90), 1);
  const maxForm = Math.max(...items.map((item) => item.avg_recent_form_score), 1);

  return (
    <div className="position-visual">
      {items.map((item) => (
        <article className="position-visual__row" key={item.registered_position}>
          <div className="position-visual__head">
            <div>
              <strong>{item.registered_position}</strong>
              <span>{formatPositionGroup(item.position_group)}</span>
            </div>
            <span className="metric-inline-badge metric-inline-badge--neutral">
              {item.players}명
            </span>
          </div>

          <div className="position-visual__bars">
            <div className="position-visual__metric">
              <span>출전 점유</span>
              <div className="position-visual__track">
                <div
                  className="position-visual__fill position-visual__fill--minutes"
                  style={{ width: metricBarWidth(item.avg_minutes_share_pct, maxMinutes) }}
                />
              </div>
              <strong>{item.avg_minutes_share_pct.toFixed(1)}%</strong>
            </div>
            <div className="position-visual__metric">
              <span>Load / 90</span>
              <div className="position-visual__track">
                <div
                  className="position-visual__fill position-visual__fill--load"
                  style={{ width: metricBarWidth(item.avg_player_load_p90, maxLoad) }}
                />
              </div>
              <strong>{item.avg_player_load_p90.toFixed(1)}</strong>
            </div>
            <div className="position-visual__metric">
              <span>Recent Form</span>
              <div className="position-visual__track">
                <div
                  className="position-visual__fill position-visual__fill--form"
                  style={{ width: metricBarWidth(item.avg_recent_form_score, maxForm) }}
                />
              </div>
              <strong>{item.avg_recent_form_score.toFixed(1)}</strong>
            </div>
          </div>

          <div className="meta-chip-row">
            <span className="meta-chip">Sprint/90 {item.avg_sprint_count_p90.toFixed(1)}</span>
            <span className="meta-chip">Growth {item.avg_growth_score.toFixed(1)}</span>
            <span className="meta-chip">Risk {item.avg_availability_risk_score.toFixed(1)}</span>
          </div>
        </article>
      ))}
    </div>
  );
}
