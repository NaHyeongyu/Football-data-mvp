"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";

import {
  formatCompactDate,
  formatDominantFoot,
} from "@/lib/dashboard-formatters";
import type {
  PlayerDetailPayload,
  PlayerInjuryRecordItem,
  PlayerMatchPerformanceItem,
  PlayerMentalNoteItem,
  PlayerPhysicalTestItem,
  PlayerSeasonSummaryItem,
  PlayersDirectoryPayload,
} from "@/lib/data-types";

type PlayerOption = {
  id: string;
  latestSeasonYear: number;
  name: string;
  position: string;
};

type PeriodOption = {
  label: string;
  value: string;
};

type ReportFocusItem = {
  label: string;
  title: string;
  value: string;
};

type ReportDataset = {
  assists: number;
  avgFormScore: number | null;
  dateRangeLabel: string;
  distancePer90: number | null;
  focusItems: ReportFocusItem[];
  goals: number;
  highSpeedPer90: number | null;
  injuries: PlayerInjuryRecordItem[];
  latestInjury: PlayerInjuryRecordItem | null;
  latestMatch: PlayerMatchPerformanceItem | null;
  latestMentalNote: PlayerMentalNoteItem | null;
  latestPhysicalTest: PlayerPhysicalTestItem | null;
  matchSummary: string;
  matches: PlayerMatchPerformanceItem[];
  maxSpeed: number | null;
  medicalSummary: string;
  mentalNotes: PlayerMentalNoteItem[];
  mentalSummary: string;
  passSuccessPct: number | null;
  periodLabel: string;
  physicalSummary: string;
  physicalTests: PlayerPhysicalTestItem[];
  playedMatches: PlayerMatchPerformanceItem[];
  playerLoadPer90: number | null;
  sprintPer90: number | null;
  totalGoalContrib: number;
  totalMinutes: number;
};

type PlayerReportWorkspaceProps = {
  detail: PlayerDetailPayload | null;
  directoryData: PlayersDirectoryPayload;
  selectedPeriod: string | null;
  selectedPlayerId: string | null;
};

const numberFormatter = new Intl.NumberFormat("ko-KR");

const recentPeriodOptions: PeriodOption[] = [
  { value: "recent:5", label: "최근 5경기" },
  { value: "recent:10", label: "최근 10경기" },
  { value: "all", label: "전체 기간" },
];

function buildPlayerOptions(summaries: PlayerSeasonSummaryItem[]) {
  const byPlayer = new Map<string, PlayerOption>();
  const sortedSummaries = [...summaries].sort(
    (left, right) =>
      right.season_year - left.season_year ||
      left.player_name.localeCompare(right.player_name, "ko"),
  );

  for (const item of sortedSummaries) {
    if (byPlayer.has(item.player_id)) {
      continue;
    }

    byPlayer.set(item.player_id, {
      id: item.player_id,
      latestSeasonYear: item.season_year,
      name: item.player_name,
      position: item.registered_position,
    });
  }

  return Array.from(byPlayer.values()).sort((left, right) =>
    left.name.localeCompare(right.name, "ko"),
  );
}

function getPlayerSeasonYears(
  summaries: PlayerSeasonSummaryItem[],
  playerId: string,
) {
  return Array.from(
    new Set(
      summaries
        .filter((item) => item.player_id === playerId)
        .map((item) => item.season_year),
    ),
  ).sort((left, right) => right - left);
}

function getDefaultPeriod(
  summaries: PlayerSeasonSummaryItem[],
  playerId: string,
) {
  const latestSeasonYear = getPlayerSeasonYears(summaries, playerId)[0];
  return latestSeasonYear ? `season:${latestSeasonYear}` : "all";
}

function buildPeriodOptions(
  summaries: PlayerSeasonSummaryItem[],
  playerId: string,
) {
  const seasonOptions = getPlayerSeasonYears(summaries, playerId).map((year) => ({
    value: `season:${year}`,
    label: `${year} 시즌`,
  }));

  return [...seasonOptions, ...recentPeriodOptions];
}

function parseSeasonPeriod(period: string) {
  if (!period.startsWith("season:")) {
    return null;
  }

  const seasonYear = Number(period.replace("season:", ""));
  return Number.isFinite(seasonYear) ? seasonYear : null;
}

function parseRecentPeriod(period: string) {
  if (!period.startsWith("recent:")) {
    return null;
  }

  const count = Number(period.replace("recent:", ""));
  return Number.isFinite(count) && count > 0 ? count : null;
}

function parseDateValue(value?: string | null) {
  if (!value) {
    return Number.NEGATIVE_INFINITY;
  }

  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
}

function sortMatchesByDate(items: PlayerMatchPerformanceItem[]) {
  return [...items].sort(
    (left, right) =>
      parseDateValue(right.match_date) - parseDateValue(left.match_date) ||
      right.match_no - left.match_no,
  );
}

function sortPhysicalTestsByDate(items: PlayerPhysicalTestItem[]) {
  return [...items].sort(
    (left, right) =>
      parseDateValue(right.test_date) - parseDateValue(left.test_date) ||
      right.test_round - left.test_round,
  );
}

function sortInjuriesByDate(items: PlayerInjuryRecordItem[]) {
  return [...items].sort(
    (left, right) => parseDateValue(right.record_date) - parseDateValue(left.record_date),
  );
}

function sortMentalNotesByDate(items: PlayerMentalNoteItem[]) {
  return [...items].sort(
    (left, right) =>
      parseDateValue(right.session_date) - parseDateValue(left.session_date) ||
      right.session_round - left.session_round,
  );
}

function firstValidNumber(...values: Array<number | null | undefined>) {
  for (const value of values) {
    if (value != null && !Number.isNaN(value)) {
      return value;
    }
  }

  return null;
}

function maxDefined(values: Array<number | null | undefined>) {
  const filtered = values.filter((value): value is number => value != null && !Number.isNaN(value));
  return filtered.length > 0 ? Math.max(...filtered) : null;
}

function averageDefined(values: Array<number | null | undefined>) {
  const filtered = values.filter((value): value is number => value != null && !Number.isNaN(value));
  if (filtered.length === 0) {
    return null;
  }

  return filtered.reduce((sum, value) => sum + value, 0) / filtered.length;
}

function computePer90(total: number, minutes: number) {
  if (minutes <= 0) {
    return null;
  }

  return (total / minutes) * 90;
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

function formatMetric(
  value: number | null | undefined,
  options?: {
    digits?: number;
    suffix?: string;
  },
) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }

  const digits = options?.digits ?? 1;
  const formatted =
    digits === 0
      ? numberFormatter.format(Math.round(value))
      : value.toLocaleString("ko-KR", {
          maximumFractionDigits: digits,
          minimumFractionDigits: digits,
        });

  return `${formatted}${options?.suffix ?? ""}`;
}

function formatFoot(value?: string | null) {
  if (!value) {
    return "-";
  }

  const normalized = value.toLowerCase();
  if (normalized === "right") {
    return "오른발";
  }
  if (normalized === "left") {
    return "왼발";
  }
  if (normalized === "both") {
    return "양발";
  }

  return formatDominantFoot(value);
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

function availabilityTone(value?: string | null) {
  if (value === "불가") {
    return "status-pill status-pill--danger";
  }
  if (value === "조건부") {
    return "status-pill status-pill--warning";
  }
  return "status-pill status-pill--success";
}

function getDateRangeLabel(matches: PlayerMatchPerformanceItem[]) {
  const dates = matches
    .map((item) => item.match_date)
    .filter((value): value is string => Boolean(value))
    .sort((left, right) => parseDateValue(left) - parseDateValue(right));

  if (dates.length === 0) {
    return "경기 날짜 기록 없음";
  }

  if (dates.length === 1) {
    return formatCompactDate(dates[0]);
  }

  return `${formatCompactDate(dates[0])} - ${formatCompactDate(dates[dates.length - 1])}`;
}

function getSelectedDateBounds(matches: PlayerMatchPerformanceItem[]) {
  const timestamps = matches
    .map((item) => parseDateValue(item.match_date))
    .filter((value) => Number.isFinite(value));

  if (timestamps.length === 0) {
    return null;
  }

  return {
    end: Math.max(...timestamps),
    start: Math.min(...timestamps),
  };
}

function isDateWithinBounds(value: string, bounds: { end: number; start: number }) {
  const timestamp = parseDateValue(value);
  return Number.isFinite(timestamp) && timestamp >= bounds.start && timestamp <= bounds.end;
}

function buildMatchSummary(report: Pick<ReportDataset, "assists" | "avgFormScore" | "goals" | "playedMatches" | "totalMinutes">) {
  if (report.playedMatches.length === 0) {
    return "선택한 기간에는 출전 경기 기록이 없습니다. 경기 표본이 쌓이면 출전 시간, 공격포인트, 폼 지표를 기준으로 요약합니다.";
  }

  return `${numberFormatter.format(report.playedMatches.length)}경기 ${numberFormatter.format(report.totalMinutes)}분 출전, ${numberFormatter.format(report.goals)}골 ${numberFormatter.format(report.assists)}도움입니다. 평균 폼 점수는 ${formatMetric(report.avgFormScore, { digits: 1 })}입니다.`;
}

function buildPhysicalSummary(report: Pick<ReportDataset, "distancePer90" | "maxSpeed" | "playerLoadPer90" | "sprintPer90">) {
  return `90분 환산 활동량 ${formatMetric(report.distancePer90, { digits: 1, suffix: "km" })}, 스프린트 ${formatMetric(report.sprintPer90, { digits: 1, suffix: "회" })}, Player Load ${formatMetric(report.playerLoadPer90, { digits: 1 })}, 최고 속도 ${formatMetric(report.maxSpeed, { digits: 1, suffix: "km/h" })}입니다.`;
}

function buildMedicalSummary(injuries: PlayerInjuryRecordItem[]) {
  if (injuries.length === 0) {
    return "선택한 기간에는 AT/부상 기록이 없습니다.";
  }

  const daysMissed = injuries.reduce((sum, item) => sum + item.days_missed, 0);
  const latest = injuries[0];
  return `${numberFormatter.format(injuries.length)}건의 AT/부상 기록이 있고 누적 결장일은 ${numberFormatter.format(daysMissed)}일입니다. 최신 기록은 ${formatCompactDate(latest.record_date)} ${latest.match_availability} 상태입니다.`;
}

function buildMentalSummary(notes: PlayerMentalNoteItem[]) {
  if (notes.length === 0) {
    return "선택한 기간에는 상담 기록이 없습니다.";
  }

  const latest = notes[0];
  return `${formatCompactDate(latest.session_date)} ${latest.counseling_type}: "${latest.player_quote}"`;
}

function buildFocusItems(
  report: Omit<ReportDataset, "focusItems">,
): ReportFocusItem[] {
  const items: ReportFocusItem[] = [];

  if (report.playedMatches.length === 0) {
    items.push({
      label: "경기",
      title: "출전 표본 확보",
      value: "기간 내 출전 경기 없음",
    });
  } else if ((report.avgFormScore ?? 0) >= 45) {
    items.push({
      label: "경기",
      title: "현재 폼 유지",
      value: `폼 ${formatMetric(report.avgFormScore, { digits: 1 })}`,
    });
  } else {
    items.push({
      label: "경기",
      title: "역할 수행 안정화",
      value: `폼 ${formatMetric(report.avgFormScore, { digits: 1 })}`,
    });
  }

  if ((report.playerLoadPer90 ?? 0) >= 440 || (report.sprintPer90 ?? 0) >= 22) {
    items.push({
      label: "부하",
      title: "고강도 부하 모니터링",
      value: `PL/90 ${formatMetric(report.playerLoadPer90, { digits: 1 })}`,
    });
  } else {
    items.push({
      label: "부하",
      title: "일반 부하 범위",
      value: `거리/90 ${formatMetric(report.distancePer90, { digits: 1, suffix: "km" })}`,
    });
  }

  if (report.latestInjury?.match_availability === "불가" || report.latestInjury?.match_availability === "조건부") {
    items.push({
      label: "메디컬",
      title: "가용성 확인 필요",
      value: report.latestInjury.match_availability,
    });
  } else {
    items.push({
      label: "메디컬",
      title: "특이 리스크 낮음",
      value: "기간 내 주요 제한 없음",
    });
  }

  if (report.latestMentalNote) {
    items.push({
      label: "상담",
      title: report.latestMentalNote.counseling_type,
      value: formatCompactDate(report.latestMentalNote.session_date),
    });
  }

  return items.slice(0, 4);
}

function createReportDataset(data: PlayerDetailPayload, period: string): ReportDataset {
  const seasonYear = parseSeasonPeriod(period);
  const recentCount = parseRecentPeriod(period);
  const sortedMatches = sortMatchesByDate(data.matchPerformance);
  const playedAllMatches = sortedMatches.filter((item) => item.minutes_played > 0);
  const periodOption =
    seasonYear != null
      ? { label: `${seasonYear} 시즌`, value: period }
      : recentCount != null
        ? { label: `최근 ${recentCount}경기`, value: period }
        : { label: "전체 기간", value: "all" };

  const matches =
    seasonYear != null
      ? sortedMatches.filter((item) => item.season_year === seasonYear)
      : recentCount != null
        ? playedAllMatches.slice(0, recentCount)
        : sortedMatches;
  const bounds = recentCount != null ? getSelectedDateBounds(matches) : null;
  const physicalTests = sortPhysicalTestsByDate(
    seasonYear != null
      ? data.physicalTests.filter((item) => item.season_year === seasonYear)
      : bounds
        ? data.physicalTests.filter((item) => isDateWithinBounds(item.test_date, bounds))
        : data.physicalTests,
  );
  const injuries = sortInjuriesByDate(
    seasonYear != null
      ? data.injuryHistory.filter((item) => item.season_year === seasonYear)
      : bounds
        ? data.injuryHistory.filter((item) => isDateWithinBounds(item.record_date, bounds))
        : data.injuryHistory,
  );
  const mentalNotes = sortMentalNotesByDate(
    seasonYear != null
      ? data.mentalNotes.filter((item) => item.season_year === seasonYear)
      : bounds
        ? data.mentalNotes.filter((item) => isDateWithinBounds(item.session_date, bounds))
        : data.mentalNotes,
  );
  const playedMatches = matches.filter((item) => item.minutes_played > 0);
  const totalMinutes = playedMatches.reduce((sum, item) => sum + item.minutes_played, 0);
  const goals = playedMatches.reduce((sum, item) => sum + item.goals, 0);
  const assists = playedMatches.reduce((sum, item) => sum + item.assists, 0);
  const totalGoalContrib = goals + assists;
  const passAttempts = playedMatches.reduce((sum, item) => sum + item.pass_attempts, 0);
  const passSuccess = playedMatches.reduce((sum, item) => sum + item.pass_success, 0);
  const totalDistance = playedMatches.reduce(
    (sum, item) => sum + (firstValidNumber(item.distance_total_km, item.total_distance) ?? 0),
    0,
  );
  const totalHighSpeed = playedMatches.reduce(
    (sum, item) => sum + (firstValidNumber(item.distance_high_speed_m, item.sprint_distance) ?? 0),
    0,
  );
  const totalSprints = playedMatches.reduce((sum, item) => sum + (item.sprint_count ?? 0), 0);
  const totalPlayerLoad = playedMatches.reduce((sum, item) => sum + (item.player_load ?? 0), 0);

  const baseReport = {
    assists,
    avgFormScore: averageDefined(playedMatches.map((item) => computeRecentMatchFormScore(item))),
    dateRangeLabel: getDateRangeLabel(matches),
    distancePer90: computePer90(totalDistance, totalMinutes),
    goals,
    highSpeedPer90: computePer90(totalHighSpeed, totalMinutes),
    injuries,
    latestInjury: injuries[0] ?? null,
    latestMatch: playedMatches[0] ?? matches[0] ?? null,
    latestMentalNote: mentalNotes[0] ?? null,
    latestPhysicalTest: physicalTests[0] ?? null,
    matches,
    maxSpeed: maxDefined(playedMatches.map((item) => firstValidNumber(item.max_speed_kmh, item.max_speed))),
    mentalNotes,
    passSuccessPct: passAttempts > 0 ? (passSuccess / passAttempts) * 100 : null,
    periodLabel: periodOption.label,
    physicalTests,
    playedMatches,
    playerLoadPer90: computePer90(totalPlayerLoad, totalMinutes),
    sprintPer90: computePer90(totalSprints, totalMinutes),
    totalGoalContrib,
    totalMinutes,
  } satisfies Omit<
    ReportDataset,
    "focusItems" | "matchSummary" | "medicalSummary" | "mentalSummary" | "physicalSummary"
  >;

  const withSummaries = {
    ...baseReport,
    matchSummary: buildMatchSummary(baseReport),
    medicalSummary: buildMedicalSummary(injuries),
    mentalSummary: buildMentalSummary(mentalNotes),
    physicalSummary: buildPhysicalSummary(baseReport),
  };

  return {
    ...withSummaries,
    focusItems: buildFocusItems(withSummaries),
  };
}

function ReportEmptyState() {
  return (
    <section className="panel report-empty-panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Report Builder</p>
          <h2>선수와 기간을 선택한 뒤 보고서를 생성하세요</h2>
        </div>
      </div>
      <p className="panel-note">
        보고서는 경기, GPS, 피지컬 테스트, AT/부상, 상담 기록을 한 화면으로 묶어 요약합니다.
      </p>
    </section>
  );
}

export function PlayerReportWorkspace({
  detail,
  directoryData,
  selectedPeriod,
  selectedPlayerId,
}: PlayerReportWorkspaceProps) {
  const router = useRouter();
  const playerOptions = useMemo(
    () => buildPlayerOptions(directoryData.playerSeasonSummary),
    [directoryData.playerSeasonSummary],
  );
  const initialPlayerId = selectedPlayerId ?? playerOptions[0]?.id ?? "";
  const [playerId, setPlayerId] = useState(initialPlayerId);
  const [period, setPeriod] = useState(
    selectedPeriod ?? (initialPlayerId ? getDefaultPeriod(directoryData.playerSeasonSummary, initialPlayerId) : "all"),
  );
  const periodOptions = useMemo(
    () => (playerId ? buildPeriodOptions(directoryData.playerSeasonSummary, playerId) : recentPeriodOptions),
    [directoryData.playerSeasonSummary, playerId],
  );
  const report = detail ? createReportDataset(detail, selectedPeriod ?? period) : null;

  function handlePlayerChange(nextPlayerId: string) {
    setPlayerId(nextPlayerId);
    setPeriod(getDefaultPeriod(directoryData.playerSeasonSummary, nextPlayerId));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!playerId) {
      return;
    }

    const params = new URLSearchParams();
    params.set("playerId", playerId);
    params.set("period", period);
    router.push(`/reports?${params.toString()}`);
  }

  return (
    <div className="player-detail-workspace report-workspace">
      <section className="directory-filter-panel report-control-panel">
        <div className="directory-filter-panel__header">
          <div>
            <h2>선수 보고서 생성</h2>
          </div>
        </div>

        <form className="directory-toolbar report-builder-form" onSubmit={handleSubmit}>
          <div className="directory-filter-row">
            <label className="form-field form-field--wide">
              <span>Player</span>
              <select
                aria-label="보고서 선수 선택"
                onChange={(event) => handlePlayerChange(event.target.value)}
                value={playerId}
              >
                {playerOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} · {item.position} · {item.latestSeasonYear}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field">
              <span>Period</span>
              <select
                aria-label="보고서 기간 선택"
                onChange={(event) => setPeriod(event.target.value)}
                value={period}
              >
                {periodOptions.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <button className="primary-button report-generate-button" disabled={!playerId} type="submit">
            보고서 생성
          </button>
        </form>
      </section>

      {!detail || !report ? (
        <ReportEmptyState />
      ) : (
        <>
          <section className="player-detail-hero report-hero">
            <div className="player-detail-hero__main">
              <div className="player-detail-hero__topbar">
                <div className="player-detail-hero__tags">
                  <span className="player-detail-tag player-detail-tag--strong">
                    {report.periodLabel}
                  </span>
                  <span className="player-detail-tag">{report.dateRangeLabel}</span>
                  <span className={availabilityTone(detail.profile.latest_match_availability)}>
                    {detail.profile.latest_match_availability ?? "가능"}
                  </span>
                </div>
                <Link className="ghost-button" href={`/players/${detail.profile.player_id}`}>
                  선수 상세
                </Link>
              </div>

              <div className="player-detail-hero__identity">
                <p className="panel-eyebrow">Player Report</p>
                <div className="player-detail-hero__title-row">
                  <h1>{detail.profile.name}</h1>
                </div>
                <p className="player-detail-hero__summary">
                  {report.matchSummary} {report.physicalSummary}
                </p>
              </div>

              <div className="player-detail-profile-inline">
                <div className="player-detail-profile-inline__item">
                  <span>Position</span>
                  <strong>{detail.profile.registered_position ?? "-"}</strong>
                </div>
                <div className="player-detail-profile-inline__item">
                  <span>Age</span>
                  <strong>{formatMetric(detail.profile.age_today, { digits: 1 })}</strong>
                </div>
                <div className="player-detail-profile-inline__item">
                  <span>Foot</span>
                  <strong>{formatFoot(detail.profile.dominant_foot)}</strong>
                </div>
                <div className="player-detail-profile-inline__item">
                  <span>Generated</span>
                  <strong>{formatCompactDate(detail.generatedOn)}</strong>
                </div>
              </div>
            </div>
          </section>

          <section className="stat-grid">
            <article className="metric-card metric-card--highlight">
              <p>출전 시간</p>
              <strong>{numberFormatter.format(report.totalMinutes)}분</strong>
              <span>{numberFormatter.format(report.playedMatches.length)}경기 출전</span>
              <div className="metric-card__meta">
                <span>평균 폼</span>
                <strong>{formatMetric(report.avgFormScore, { digits: 1 })}</strong>
              </div>
            </article>
            <article className="metric-card">
              <p>공격포인트</p>
              <strong>{numberFormatter.format(report.totalGoalContrib)}개</strong>
              <span>
                {numberFormatter.format(report.goals)}골 · {numberFormatter.format(report.assists)}도움
              </span>
              <div className="metric-card__meta">
                <span>패스 성공률</span>
                <strong>{formatMetric(report.passSuccessPct, { digits: 1, suffix: "%" })}</strong>
              </div>
            </article>
            <article className="metric-card">
              <p>GPS 부하</p>
              <strong>{formatMetric(report.playerLoadPer90, { digits: 1 })}</strong>
              <span>Player Load / 90</span>
              <div className="metric-card__meta">
                <span>거리 / 90</span>
                <strong>{formatMetric(report.distancePer90, { digits: 1, suffix: "km" })}</strong>
              </div>
            </article>
            <article className="metric-card">
              <p>메디컬 기록</p>
              <strong>{numberFormatter.format(report.injuries.length)}건</strong>
              <span>{report.latestInjury ? formatCompactDate(report.latestInjury.record_date) : "기간 내 기록 없음"}</span>
              <div className="metric-card__meta">
                <span>상담 기록</span>
                <strong>{numberFormatter.format(report.mentalNotes.length)}건</strong>
              </div>
            </article>
          </section>

          <section className="dashboard-grid dashboard-grid--triple report-summary-grid">
            <article className="focus-card">
              <div className="score-card__head">
                <div>
                  <span className="panel-eyebrow">Performance</span>
                  <strong>경기 요약</strong>
                </div>
              </div>
              <p className="score-card__note">{report.matchSummary}</p>
            </article>
            <article className="focus-card">
              <div className="score-card__head">
                <div>
                  <span className="panel-eyebrow">Physical</span>
                  <strong>피지컬 / GPS</strong>
                </div>
              </div>
              <p className="score-card__note">{report.physicalSummary}</p>
            </article>
            <article className="focus-card">
              <div className="score-card__head">
                <div>
                  <span className="panel-eyebrow">Medical</span>
                  <strong>메디컬 / 상담</strong>
                </div>
              </div>
              <p className="score-card__note">
                {report.medicalSummary} {report.mentalSummary}
              </p>
            </article>
          </section>

          <section className="dashboard-grid dashboard-grid--split">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Focus</p>
                  <h2>코칭 포커스</h2>
                </div>
              </div>
              <div className="focus-list">
                {report.focusItems.map((item) => (
                  <article className="focus-card" key={`${item.label}-${item.title}`}>
                    <div className="score-card__head">
                      <div>
                        <span>{item.label}</span>
                        <strong>{item.title}</strong>
                      </div>
                      <span className="metric-inline-badge metric-inline-badge--neutral">
                        {item.value}
                      </span>
                    </div>
                  </article>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Latest Signals</p>
                  <h2>최근 기록</h2>
                </div>
              </div>
              <div className="note-list">
                <article className="note-card">
                  <div className="detail-note-head">
                    <strong>최근 피지컬 테스트</strong>
                    <span className="metric-inline-badge metric-inline-badge--neutral">
                      {report.latestPhysicalTest ? formatCompactDate(report.latestPhysicalTest.test_date) : "-"}
                    </span>
                  </div>
                  <p>
                    체중 {formatMetric(report.latestPhysicalTest?.weight_kg, { digits: 1, suffix: "kg" })} ·
                    골격근 {formatMetric(report.latestPhysicalTest?.skeletal_muscle_kg, { digits: 1, suffix: "kg" })} ·
                    체지방 {formatMetric(report.latestPhysicalTest?.body_fat_pct, { digits: 1, suffix: "%" })}
                  </p>
                </article>
                <article className="note-card">
                  <div className="detail-note-head">
                    <strong>최근 상담</strong>
                    <span className="metric-inline-badge metric-inline-badge--neutral">
                      {report.latestMentalNote ? formatCompactDate(report.latestMentalNote.session_date) : "-"}
                    </span>
                  </div>
                  <p>{report.mentalSummary}</p>
                </article>
              </div>
            </article>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Match Log</p>
                <h2>기간 내 경기 기록</h2>
              </div>
              <p className="panel-note">선택한 기간 기준 최근 경기부터 표시합니다.</p>
            </div>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>일자</th>
                    <th>상대</th>
                    <th>결과</th>
                    <th>출전</th>
                    <th>득점 / 도움</th>
                    <th>GPS</th>
                  </tr>
                </thead>
                <tbody>
                  {report.playedMatches.length > 0 ? (
                    report.playedMatches.slice(0, 10).map((item) => (
                      <tr key={item.analysis_id}>
                        <td>{formatCompactDate(item.match_date)}</td>
                        <td>{item.opponent}</td>
                        <td>
                          <span className={resultTone(item.result)}>
                            {item.result} {item.score}
                          </span>
                        </td>
                        <td>{numberFormatter.format(item.minutes_played)}분</td>
                        <td>
                          {item.goals} / {item.assists}
                        </td>
                        <td>
                          {formatMetric(firstValidNumber(item.distance_total_km, item.total_distance), {
                            digits: 1,
                            suffix: "km",
                          })}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="table-empty" colSpan={6}>
                        선택한 기간에 출전 경기 기록이 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
