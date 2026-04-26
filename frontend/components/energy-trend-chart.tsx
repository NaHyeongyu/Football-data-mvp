"use client";

import { useEffect, useId, useState } from "react";
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

type EnergyTrendPoint = {
  id: string;
  label: string;
  score: number;
};

const energyToneStyles = {
  match: {
    areaBottom: "#93c5fd",
    areaTop: "#1d4ed8",
    stroke: "#0b2545",
  },
  training: {
    areaBottom: "#f1dcb4",
    areaTop: "#be9547",
    stroke: "#976712",
  },
} as const;

export function EnergyTrendChart({
  items,
  averageScore,
  rangeLabel,
  tone,
}: {
  items: EnergyTrendPoint[];
  averageScore: number;
  rangeLabel: string;
  tone: "match" | "training";
}) {
  const gradientId = `energy-trend-${useId().replace(/:/g, "")}`;
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (items.length === 0) {
    return (
      <div className="empty-state">
        <strong>에너지 그래프 없음</strong>
        <p>그래프를 그릴 수 있는 세션이 아직 부족합니다.</p>
      </div>
    );
  }

  const toneStyle = energyToneStyles[tone];
  const chartData = items.map((item) => ({
    detail: `${rangeLabel} · 에너지 ${Math.round(item.score)}점`,
    formatted: `${item.score.toFixed(1)}점`,
    label: item.label,
    value: item.score,
  }));

  if (!isHydrated) {
    return (
      <div className={`physical-energy-trend physical-energy-trend--${tone}`}>
        <div className="physical-energy-trend__header">
          <span>{rangeLabel}</span>
          <strong>평균 {averageScore.toFixed(1)}</strong>
        </div>
        <div
          aria-hidden="true"
          className="physical-energy-trend__chart-shell physical-energy-trend__chart-shell--placeholder"
        />
        <div className="physical-energy-trend__footer">
          <span>0점</span>
          <span>에너지 점수 / 100</span>
          <span>100점</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`physical-energy-trend physical-energy-trend--${tone}`}>
      <div className="physical-energy-trend__header">
        <span>{rangeLabel}</span>
        <strong>평균 {averageScore.toFixed(1)}</strong>
      </div>

      <div className="physical-energy-trend__chart-shell">
        <ResponsiveContainer height="100%" width="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={toneStyle.areaTop} stopOpacity={0.24} />
                <stop offset="70%" stopColor={toneStyle.areaTop} stopOpacity={0.08} />
                <stop offset="100%" stopColor={toneStyle.areaBottom} stopOpacity={0.03} />
              </linearGradient>
            </defs>
            <CartesianGrid
              stroke="rgba(11, 37, 69, 0.08)"
              strokeDasharray="3 6"
              vertical={false}
            />
            <XAxis
              axisLine={false}
              dataKey="label"
              dy={8}
              tick={{ fill: "#5d718f", fontSize: 11, fontWeight: 700 }}
              tickLine={false}
            />
            <YAxis
              axisLine={false}
              domain={[0, 100]}
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
              cursor={{ stroke: "rgba(11, 37, 69, 0.16)", strokeDasharray: "4 4" }}
            />
            <ReferenceLine
              ifOverflow="extendDomain"
              stroke="rgba(11, 37, 69, 0.16)"
              strokeDasharray="4 4"
              y={averageScore}
            />
            <Area
              activeDot={{ fill: "#ffffff", r: 5, stroke: toneStyle.stroke, strokeWidth: 3 }}
              dataKey="value"
              dot={chartData.length === 1 ? { fill: "#ffffff", r: 4, stroke: toneStyle.stroke, strokeWidth: 2.5 } : false}
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

      <div className="physical-energy-trend__footer">
        <span>0점</span>
        <span>에너지 점수 / 100</span>
        <span>100점</span>
      </div>
    </div>
  );
}
