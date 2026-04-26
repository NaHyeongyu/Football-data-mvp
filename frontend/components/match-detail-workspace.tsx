"use client";

import Link from "next/link";
import { useState } from "react";

import type { TeamMatchDetailPlayerStat, TeamMatchDetailResponse } from "@/lib/team-api-types";

const decimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});

const compactFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});

const dateFormatter = new Intl.DateTimeFormat("ko-KR", {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const matchDetailViews = [
  { key: "summary", label: "요약" },
  { key: "match", label: "경기 데이터" },
  { key: "gps", label: "GPS 데이터" },
] as const;

type MatchDetailViewKey = (typeof matchDetailViews)[number]["key"];
type MatchStatSortKey =
  | "jersey_number"
  | "name"
  | "role"
  | "position"
  | "minutes_played"
  | "goals"
  | "assists"
  | "shots"
  | "shots_on_target"
  | "key_passes"
  | "pass_accuracy"
  | "duel_win_rate"
  | "recoveries"
  | "interceptions"
  | "mistakes"
  | "yellow_cards"
  | "red_cards"
  | "match_score";
type MatchStatSortDirection = "asc" | "desc";

const matchStatDefaultDirection: Record<MatchStatSortKey, MatchStatSortDirection> = {
  jersey_number: "asc",
  name: "asc",
  role: "asc",
  position: "asc",
  minutes_played: "desc",
  goals: "desc",
  assists: "desc",
  shots: "desc",
  shots_on_target: "desc",
  key_passes: "desc",
  pass_accuracy: "desc",
  duel_win_rate: "desc",
  recoveries: "desc",
  interceptions: "desc",
  mistakes: "desc",
  yellow_cards: "desc",
  red_cards: "desc",
  match_score: "desc",
};

function resultTone(result: string) {
  if (result === "승") {
    return "table-badge table-badge--success";
  }
  if (result === "패") {
    return "table-badge table-badge--danger";
  }
  return "table-badge table-badge--warning";
}

function formatRate(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }
  return `${decimalFormatter.format(value * 100)}%`;
}

function formatValue(value: number | null | undefined, unit?: string) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }
  return `${compactFormatter.format(value)}${unit ?? ""}`;
}

function formatInteger(value: number | null | undefined, unit?: string) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }
  return `${Math.round(value)}${unit ?? ""}`;
}

function roleKey(player: TeamMatchDetailPlayerStat) {
  if (player.start_position) {
    return "starter" as const;
  }
  if (player.substitute_in != null || player.minutes_played > 0) {
    return "substitute" as const;
  }
  return "squad" as const;
}

function roleLabel(player: TeamMatchDetailPlayerStat) {
  const key = roleKey(player);
  if (key === "starter") {
    return "선발";
  }
  if (key === "substitute") {
    return "교체";
  }
  return "엔트리";
}

function roleToneClass(player: TeamMatchDetailPlayerStat) {
  const key = roleKey(player);
  if (key === "starter") {
    return "match-detail-role-pill match-detail-role-pill--starter";
  }
  if (key === "substitute") {
    return "match-detail-role-pill match-detail-role-pill--substitute";
  }
  return "match-detail-role-pill match-detail-role-pill--squad";
}

function roleSortValue(player: TeamMatchDetailPlayerStat) {
  const key = roleKey(player);
  if (key === "starter") {
    return 0;
  }
  if (key === "substitute") {
    return 1;
  }
  return 2;
}

function sortSquadPlayers(players: TeamMatchDetailPlayerStat[]) {
  return [...players].sort((left, right) => {
    const roleOrder = { starter: 0, substitute: 1, squad: 2 } as const;
    const leftRole = roleOrder[roleKey(left)];
    const rightRole = roleOrder[roleKey(right)];

    if (leftRole !== rightRole) {
      return leftRole - rightRole;
    }
    if ((left.jersey_number ?? 0) !== (right.jersey_number ?? 0)) {
      return (left.jersey_number ?? 0) - (right.jersey_number ?? 0);
    }
    return left.name.localeCompare(right.name);
  });
}

function duelRate(player: TeamMatchDetailPlayerStat) {
  if (player.duel_win_rate == null || Number.isNaN(player.duel_win_rate)) {
    return "-";
  }
  return formatRate(player.duel_win_rate);
}

function findTopScorer(players: TeamMatchDetailPlayerStat[]) {
  const sorted = [...players]
    .filter((player) => player.match_score != null)
    .sort((left, right) => (right.match_score ?? 0) - (left.match_score ?? 0));
  return sorted[0] ?? null;
}

function findDistanceLeader(players: TeamMatchDetailPlayerStat[]) {
  const sorted = [...players]
    .filter((player) => player.total_distance != null)
    .sort((left, right) => (right.total_distance ?? 0) - (left.total_distance ?? 0));
  return sorted[0] ?? null;
}

function findSprintLeader(players: TeamMatchDetailPlayerStat[]) {
  const sorted = [...players]
    .filter((player) => player.sprint_count != null)
    .sort((left, right) => (right.sprint_count ?? 0) - (left.sprint_count ?? 0));
  return sorted[0] ?? null;
}

function findPositiveStatLeader(
  players: TeamMatchDetailPlayerStat[],
  key: "recoveries" | "interceptions" | "shots_on_target",
) {
  const sorted = [...players]
    .filter((player) => player[key] > 0)
    .sort((left, right) => right[key] - left[key] || right.minutes_played - left.minutes_played);
  return sorted[0] ?? null;
}

function compareNullableNumber(left: number | null | undefined, right: number | null | undefined) {
  const leftMissing = left == null || Number.isNaN(left);
  const rightMissing = right == null || Number.isNaN(right);

  if (leftMissing && rightMissing) {
    return 0;
  }
  if (leftMissing) {
    return 1;
  }
  if (rightMissing) {
    return -1;
  }
  return left - right;
}

function compareText(left: string, right: string) {
  return left.localeCompare(right, "ko");
}

function compareMatchPlayers(left: TeamMatchDetailPlayerStat, right: TeamMatchDetailPlayerStat, key: MatchStatSortKey) {
  switch (key) {
    case "name":
      return compareText(left.name, right.name);
    case "role":
      return roleSortValue(left) - roleSortValue(right);
    case "position":
      return compareText(left.position, right.position);
    case "pass_accuracy":
      return compareNullableNumber(left.pass_accuracy, right.pass_accuracy);
    case "duel_win_rate":
      return compareNullableNumber(left.duel_win_rate, right.duel_win_rate);
    case "match_score":
      return compareNullableNumber(left.match_score, right.match_score);
    default:
      return Number(left[key]) - Number(right[key]);
  }
}

function sortMatchPlayers(
  players: TeamMatchDetailPlayerStat[],
  sortKey: MatchStatSortKey,
  direction: MatchStatSortDirection,
) {
  return [...players].sort((left, right) => {
    const comparison = compareMatchPlayers(left, right, sortKey);
    if (comparison !== 0) {
      return direction === "asc" ? comparison : -comparison;
    }

    return (
      compareNullableNumber(right.match_score, left.match_score) ||
      (left.jersey_number ?? 0) - (right.jersey_number ?? 0) ||
      compareText(left.name, right.name)
    );
  });
}

function sortIndicator(sortKey: MatchStatSortKey, activeKey: MatchStatSortKey, direction: MatchStatSortDirection) {
  if (sortKey !== activeKey) {
    return "↕";
  }
  return direction === "desc" ? "↓" : "↑";
}

function ScoreInfoHint({
  align = "center",
  context = "match",
}: {
  align?: "center" | "start";
  context?: "match" | "gps";
}) {
  const isGpsContext = context === "gps";

  return (
    <span className={align === "start" ? "score-info-hint score-info-hint--start" : "score-info-hint"}>
      <button
        aria-label={isGpsContext ? "GPS 탭 점수 안내" : "경기 점수 계산 기준"}
        className="score-info-hint__button"
        type="button"
      >
        ?
      </button>
      <span className="score-info-hint__panel">
        <strong>{isGpsContext ? "GPS 탭 점수 안내" : "경기 점수 기준"}</strong>
        {isGpsContext ? (
          <span>이 열은 GPS 전용 점수가 아니라, 같은 경기의 종합 경기 점수를 함께 보여주는 값입니다.</span>
        ) : null}
        <span>출전시간, 골·도움, 유효슈팅, 키패스, 패스 성공률, 경합 승률, 이동거리/분, 스프린트/90을 반영합니다.</span>
        <span>실수, 경고, 퇴장은 차감되며 최종 점수는 0~100점으로 제한됩니다.</span>
      </span>
    </span>
  );
}

function MatchStatsTable({ players }: { players: TeamMatchDetailPlayerStat[] }) {
  const [sortKey, setSortKey] = useState<MatchStatSortKey>("match_score");
  const [sortDirection, setSortDirection] = useState<MatchStatSortDirection>("desc");

  const sortedPlayers = sortMatchPlayers(players, sortKey, sortDirection);

  function handleSort(nextKey: MatchStatSortKey) {
    if (nextKey === sortKey) {
      setSortDirection((current) => (current === "desc" ? "asc" : "desc"));
      return;
    }

    setSortKey(nextKey);
    setSortDirection(matchStatDefaultDirection[nextKey]);
  }

  function renderSortHeader(label: string, columnKey: MatchStatSortKey) {
    const active = sortKey === columnKey;

    return (
      <button
        className={active ? "match-detail-sort-header match-detail-sort-header--active" : "match-detail-sort-header"}
        onClick={() => handleSort(columnKey)}
        type="button"
      >
        <span>{label}</span>
        <em>{sortIndicator(columnKey, sortKey, sortDirection)}</em>
      </button>
    );
  }

  return (
    <div className="table-scroll table-scroll--match-detail">
      <table className="data-table data-table--match-detail-stats">
        <thead>
          <tr>
            <th>{renderSortHeader("No.", "jersey_number")}</th>
            <th>{renderSortHeader("선수", "name")}</th>
            <th>{renderSortHeader("역할", "role")}</th>
            <th>{renderSortHeader("포지션", "position")}</th>
            <th>{renderSortHeader("출전", "minutes_played")}</th>
            <th>{renderSortHeader("골", "goals")}</th>
            <th>{renderSortHeader("도움", "assists")}</th>
            <th>{renderSortHeader("슈팅", "shots")}</th>
            <th>{renderSortHeader("유효슈팅", "shots_on_target")}</th>
            <th>{renderSortHeader("키패스", "key_passes")}</th>
            <th>{renderSortHeader("패스 성공률", "pass_accuracy")}</th>
            <th>{renderSortHeader("경합 승률", "duel_win_rate")}</th>
            <th>{renderSortHeader("리커버리", "recoveries")}</th>
            <th>{renderSortHeader("인터셉트", "interceptions")}</th>
            <th>{renderSortHeader("실수", "mistakes")}</th>
            <th>{renderSortHeader("경고", "yellow_cards")}</th>
            <th>{renderSortHeader("퇴장", "red_cards")}</th>
            <th>
              <div className="match-detail-sort-header-group">
                {renderSortHeader("점수", "match_score")}
                <ScoreInfoHint />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedPlayers.map((player) => (
            <tr key={player.match_player_id}>
              <td>{player.jersey_number}</td>
              <td>
                <div className="match-detail-player-cell">
                  <Link className="table-action-link" href={`/players/${player.player_id}`}>
                    {player.name}
                  </Link>
                </div>
              </td>
              <td>
                <span className={roleToneClass(player)}>{roleLabel(player)}</span>
              </td>
              <td>{player.position}</td>
              <td>{formatInteger(player.minutes_played, "분")}</td>
              <td>{player.goals}</td>
              <td>{player.assists}</td>
              <td>{player.shots}</td>
              <td>{player.shots_on_target}</td>
              <td>{player.key_passes}</td>
              <td>{formatRate(player.pass_accuracy)}</td>
              <td>{duelRate(player)}</td>
              <td>{formatInteger(player.recoveries)}</td>
              <td>{formatInteger(player.interceptions)}</td>
              <td>{formatInteger(player.mistakes)}</td>
              <td>{player.yellow_cards}</td>
              <td>{player.red_cards}</td>
              <td>{player.match_score != null ? formatValue(player.match_score) : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GpsTable({ players }: { players: TeamMatchDetailPlayerStat[] }) {
  return (
    <div className="table-scroll table-scroll--match-detail">
      <table className="data-table data-table--match-detail-gps">
        <thead>
          <tr>
            <th>No.</th>
            <th>선수</th>
            <th>역할</th>
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
                <span>경기 점수</span>
                <ScoreInfoHint context="gps" />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {players.map((player) => (
            <tr key={player.match_player_id}>
              <td>{player.jersey_number}</td>
              <td>
                <div className="match-detail-player-cell">
                  <Link className="table-action-link" href={`/players/${player.player_id}`}>
                    {player.name}
                  </Link>
                  <span>{player.position}</span>
                </div>
              </td>
              <td>
                <span className={roleToneClass(player)}>{roleLabel(player)}</span>
              </td>
              <td>{formatInteger(player.play_time_min ?? player.minutes_played, "분")}</td>
              <td>{formatValue(player.total_distance, " km")}</td>
              <td>{formatValue(player.avg_speed, " km/h")}</td>
              <td>{formatValue(player.max_speed, " km/h")}</td>
              <td>{formatInteger(player.sprint_count, "회")}</td>
              <td>{formatValue(player.sprint_distance, " m")}</td>
              <td>{formatInteger(player.accel_count, "회")}</td>
              <td>{formatInteger(player.decel_count, "회")}</td>
              <td>{formatInteger(player.hi_accel_count, "회")}</td>
              <td>{formatInteger(player.hi_decel_count, "회")}</td>
              <td>{formatInteger(player.cod_count, "회")}</td>
              <td>{formatValue(player.distance_0_15_min, " km")}</td>
              <td>{formatValue(player.distance_15_30_min, " km")}</td>
              <td>{formatValue(player.distance_30_45_min, " km")}</td>
              <td>{formatValue(player.distance_45_60_min, " km")}</td>
              <td>{formatValue(player.distance_60_75_min, " km")}</td>
              <td>{formatValue(player.distance_75_90_min, " km")}</td>
              <td>{formatValue(player.distance_speed_0_5, " km")}</td>
              <td>{formatValue(player.distance_speed_5_10, " km")}</td>
              <td>{formatValue(player.distance_speed_10_15, " km")}</td>
              <td>{formatValue(player.distance_speed_15_20, " km")}</td>
              <td>{formatValue(player.distance_speed_20_25, " km")}</td>
              <td>{formatValue(player.distance_speed_25_plus, " km")}</td>
              <td>{player.match_score != null ? formatValue(player.match_score) : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SummaryPanel({
  data,
  starterCount,
  substituteCount,
  squadOnlyCount,
  topScorer,
  distanceLeader,
  sprintLeader,
}: {
  data: TeamMatchDetailResponse;
  starterCount: number;
  substituteCount: number;
  squadOnlyCount: number;
  topScorer: TeamMatchDetailPlayerStat | null;
  distanceLeader: TeamMatchDetailPlayerStat | null;
  sprintLeader: TeamMatchDetailPlayerStat | null;
}) {
  const keyPassLeader = data.leaders.find((leader) => leader.metric_key === "key_passes") ?? null;
  const recoveryLeader = findPositiveStatLeader(data.players, "recoveries");
  const interceptionLeader = findPositiveStatLeader(data.players, "interceptions");

  const summaryCards = [
    {
      eyebrow: "Attack",
      title: "공격 생산",
      note: `팀 득점 ${data.match.goals_for}골`,
      items: [
        { label: "득점", value: formatInteger(data.match.goals_for, "골") },
        { label: "슈팅", value: formatInteger(data.team_stats.shots, "회") },
        { label: "유효슈팅", value: formatInteger(data.team_stats.shots_on_target, "회") },
        { label: "키패스", value: formatInteger(data.team_stats.key_passes, "회") },
      ],
    },
    {
      eyebrow: "Build-up",
      title: "패스 연결",
      note: `크로스 성공 ${data.team_stats.crosses_succeeded} / ${data.team_stats.crosses_attempted}`,
      items: [
        { label: "패스 성공률", value: formatRate(data.team_stats.pass_accuracy) },
        { label: "점유율", value: formatValue(data.match.possession_for, "%") },
        { label: "크로스 성공률", value: formatRate(data.team_stats.cross_accuracy) },
        { label: "도움", value: formatInteger(data.team_stats.assists, "개") },
      ],
    },
    {
      eyebrow: "Defence",
      title: "경합 · 수비",
      note: `실수 ${formatInteger(data.team_stats.mistakes, "회")}`,
      items: [
        { label: "경합 승률", value: formatRate(data.team_stats.duel_win_rate) },
        { label: "리커버리", value: formatInteger(data.team_stats.recoveries, "회") },
        { label: "인터셉트", value: formatInteger(data.team_stats.interceptions, "회") },
        { label: "실수", value: formatInteger(data.team_stats.mistakes, "회") },
      ],
    },
    {
      eyebrow: "Operations",
      title: "운영 · GPS",
      note: `선발 ${starterCount}명 · 교체 ${substituteCount}명 · 엔트리 ${squadOnlyCount}명 · 평균 최고속도 ${formatValue(data.summary.average_max_speed, " km/h")}`,
      items: [
        { label: "출전 인원", value: formatInteger(data.summary.player_count, "명") },
        { label: "평균 출전", value: formatValue(data.summary.average_minutes, "분") },
        { label: "총 뛴 거리", value: formatValue(data.summary.total_distance, " km") },
        { label: "총 스프린트 횟수", value: formatInteger(data.summary.total_sprint_count, "회") },
      ],
    },
  ];

  return (
    <div className="match-detail-tab-panel">
      <section className="match-detail-content-grid">
        <section className="panel panel--tight match-detail-brief-panel">
          <div className="panel-header match-detail-section-head">
            <div>
              <p className="panel-eyebrow">Match Brief</p>
              <h2>경기 핵심 내용</h2>
            </div>
          </div>

          <div className="match-detail-summary-board">
            {summaryCards.map((card) => (
              <article className="match-detail-summary-card" key={card.title}>
                <div className="match-detail-summary-card__head">
                  <span>{card.eyebrow}</span>
                  <h3>{card.title}</h3>
                </div>

                <div className="match-detail-summary-card__grid">
                  {card.items.map((item) => (
                    <div className="match-detail-summary-card__metric" key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </div>
                  ))}
                </div>

                <p className="match-detail-summary-card__note">{card.note}</p>
              </article>
            ))}
          </div>
        </section>

        <aside className="panel panel--tight match-detail-side-panel">
          <div className="panel-header match-detail-section-head">
            <div>
              <p className="panel-eyebrow">Top Metrics</p>
              <h2>지표별 상위 선수</h2>
            </div>
          </div>

          <div className="match-detail-insight-list">
            <article className="match-detail-insight-row">
              <span>최고 경기 점수</span>
              <strong>{topScorer ? `${topScorer.name} ${formatValue(topScorer.match_score)}` : "-"}</strong>
            </article>
            <article className="match-detail-insight-row">
              <span>최대 이동거리</span>
              <strong>{distanceLeader ? `${distanceLeader.name} ${formatValue(distanceLeader.total_distance, " km")}` : "-"}</strong>
            </article>
            <article className="match-detail-insight-row">
              <span>최다 스프린트</span>
              <strong>{sprintLeader ? `${sprintLeader.name} ${formatInteger(sprintLeader.sprint_count, "회")}` : "-"}</strong>
            </article>
            <article className="match-detail-insight-row">
              <span>최다 키패스</span>
              <strong>{keyPassLeader ? `${keyPassLeader.name} ${formatValue(keyPassLeader.value, "회")}` : "-"}</strong>
            </article>
            <article className="match-detail-insight-row">
              <span>최다 리커버리</span>
              <strong>{recoveryLeader ? `${recoveryLeader.name} ${formatInteger(recoveryLeader.recoveries, "회")}` : "-"}</strong>
            </article>
            <article className="match-detail-insight-row">
              <span>최다 인터셉트</span>
              <strong>{interceptionLeader ? `${interceptionLeader.name} ${formatInteger(interceptionLeader.interceptions, "회")}` : "-"}</strong>
            </article>
          </div>
        </aside>
      </section>

    </div>
  );
}

function MatchDataPanel({ data, players }: { data: TeamMatchDetailResponse; players: TeamMatchDetailPlayerStat[] }) {
  const matchCards = [
    { label: "슈팅", value: formatInteger(data.team_stats.shots, "회") },
    { label: "유효슈팅", value: formatInteger(data.team_stats.shots_on_target, "회") },
    { label: "키패스", value: formatInteger(data.team_stats.key_passes, "회") },
    { label: "패스 성공률", value: formatRate(data.team_stats.pass_accuracy) },
    { label: "경합 승률", value: formatRate(data.team_stats.duel_win_rate) },
    { label: "리커버리", value: formatInteger(data.team_stats.recoveries, "회") },
    { label: "인터셉트", value: formatInteger(data.team_stats.interceptions, "회") },
    { label: "실수", value: formatInteger(data.team_stats.mistakes, "회") },
  ];

  return (
    <div className="match-detail-tab-panel">
      <section className="panel panel--tight">
        <div className="panel-header match-detail-section-head">
          <div>
            <p className="panel-eyebrow">Match Data</p>
            <h2>경기 데이터</h2>
          </div>
        </div>

        <div className="match-detail-data-grid">
          {matchCards.map((card) => (
            <article className="match-detail-data-card" key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="panel panel--tight">
        <div className="panel-header match-detail-section-head">
          <div>
            <p className="panel-eyebrow">Player Match Stats</p>
            <h2>선수별 경기 기록</h2>
          </div>
        </div>

        <MatchStatsTable players={players} />
      </section>
    </div>
  );
}

function GpsDataPanel({
  data,
  players,
}: {
  data: TeamMatchDetailResponse;
  players: TeamMatchDetailPlayerStat[];
}) {
  const totalSprintDistance = players.reduce((sum, player) => sum + (player.sprint_distance ?? 0), 0);
  const totalAccelCount = players.reduce((sum, player) => sum + (player.accel_count ?? 0), 0);
  const totalDecelCount = players.reduce((sum, player) => sum + (player.decel_count ?? 0), 0);
  const totalHiAccelCount = players.reduce((sum, player) => sum + (player.hi_accel_count ?? 0), 0);
  const totalHiDecelCount = players.reduce((sum, player) => sum + (player.hi_decel_count ?? 0), 0);
  const totalCodCount = players.reduce((sum, player) => sum + (player.cod_count ?? 0), 0);
  const avgSpeedValues = players.map((player) => player.avg_speed).filter((value): value is number => value != null);
  const averageAvgSpeed =
    avgSpeedValues.length > 0
      ? avgSpeedValues.reduce((sum, value) => sum + value, 0) / avgSpeedValues.length
      : null;

  const gpsCards = [
    { label: "총 뛴 거리", value: formatValue(data.summary.total_distance, " km") },
    { label: "총 스프린트 횟수", value: formatInteger(data.summary.total_sprint_count, "회") },
    { label: "총 스프린트 거리", value: formatValue(totalSprintDistance, " m") },
    { label: "평균 속도", value: formatValue(averageAvgSpeed, " km/h") },
    { label: "평균 최고속도", value: formatValue(data.summary.average_max_speed, " km/h") },
    { label: "총 가속", value: formatInteger(totalAccelCount, "회") },
    { label: "총 감속", value: formatInteger(totalDecelCount, "회") },
    { label: "고강도 가속", value: formatInteger(totalHiAccelCount, "회") },
    { label: "고강도 감속", value: formatInteger(totalHiDecelCount, "회") },
    { label: "방향전환", value: formatInteger(totalCodCount, "회") },
  ];

  return (
    <div className="match-detail-tab-panel">
      <section className="panel panel--tight">
        <div className="panel-header match-detail-section-head">
          <div>
            <p className="panel-eyebrow">GPS Overview</p>
            <h2>GPS 데이터</h2>
          </div>
        </div>

        <div className="match-detail-data-grid match-detail-data-grid--gps">
          {gpsCards.map((card) => (
            <article className="match-detail-data-card" key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="panel panel--tight">
        <div className="panel-header match-detail-section-head">
          <div>
            <p className="panel-eyebrow">Player GPS</p>
            <h2>선수별 GPS 기록</h2>
          </div>
        </div>

        <GpsTable players={players} />
      </section>
    </div>
  );
}

export function MatchDetailWorkspace({ data }: { data: TeamMatchDetailResponse }) {
  const [activeView, setActiveView] = useState<MatchDetailViewKey>("summary");
  const matchYear = new Date(data.match.match_date).getFullYear();
  const squadPlayers = sortSquadPlayers(data.players);

  const starterCount = squadPlayers.filter((player) => roleKey(player) === "starter").length;
  const substituteCount = squadPlayers.filter((player) => roleKey(player) === "substitute").length;
  const squadOnlyCount = squadPlayers.filter((player) => roleKey(player) === "squad").length;

  const topScorer = findTopScorer(squadPlayers);
  const distanceLeader = findDistanceLeader(squadPlayers);
  const sprintLeader = findSprintLeader(squadPlayers);

  const metricStrip = [
    { label: "팀 경기 점수", value: formatValue(data.summary.team_average_match_score) },
    { label: "점유율", value: formatValue(data.match.possession_for, "%") },
    { label: "출전 인원", value: formatInteger(data.summary.player_count, "명") },
    { label: "평균 출전 시간", value: formatValue(data.summary.average_minutes, "분") },
    { label: "총 스프린트", value: formatInteger(data.summary.total_sprint_count, "회") },
  ];

  return (
    <main className="page match-detail-workspace">
      <section className="match-detail-header-card">
        <div className="match-detail-commandbar">
          <Link className="secondary-button match-detail-back-link" href={`/matches?year=${matchYear}`}>
            경기 목록으로
          </Link>
          <div className="match-detail-commandbar__meta">
            <span className="match-detail-commandbar__id">{data.match.match_id}</span>
            <span className="meta-chip">{data.match.match_type}</span>
            <span className={resultTone(data.match.result)}>
              {data.match.result} · {data.match.goals_for}:{data.match.goals_against}
            </span>
          </div>
        </div>

        <div className="match-detail-header-main">
          <div className="match-detail-header-main__title">
            <p className="panel-eyebrow">Match Detail</p>
            <h1>{data.match.opponent_team}</h1>
            <div className="match-detail-header-main__meta">
              <span>{dateFormatter.format(new Date(data.match.match_date))}</span>
              <span>{data.match.stadium_name}</span>
              <span>{data.match.match_type}</span>
            </div>
          </div>

          <div className="match-detail-score-panel">
            <span className="match-detail-score-panel__label">{data.match.result}</span>
            <strong>
              {data.match.goals_for}
              <em>:</em>
              {data.match.goals_against}
            </strong>
            <p>Football Data System vs {data.match.opponent_team}</p>
          </div>
        </div>

        <div className="match-detail-metric-strip">
          {metricStrip.map((metric) => (
            <article className="match-detail-metric" key={metric.label}>
              <span className={metric.label === "팀 경기 점수" ? "match-detail-metric__label match-detail-metric__label--with-help" : "match-detail-metric__label"}>
                {metric.label}
                {metric.label === "팀 경기 점수" ? <ScoreInfoHint align="start" /> : null}
              </span>
              <strong>{metric.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <nav className="match-detail-tab-nav" aria-label="Match detail views">
        {matchDetailViews.map((view) => (
          <button
            aria-pressed={view.key === activeView}
            className={view.key === activeView ? "match-detail-tab match-detail-tab--active" : "match-detail-tab"}
            key={view.key}
            onClick={() => setActiveView(view.key)}
            type="button"
          >
            <strong>{view.label}</strong>
          </button>
        ))}
      </nav>

      {activeView === "summary" ? (
        <SummaryPanel
          data={data}
          distanceLeader={distanceLeader}
          sprintLeader={sprintLeader}
          squadOnlyCount={squadOnlyCount}
          starterCount={starterCount}
          substituteCount={substituteCount}
          topScorer={topScorer}
        />
      ) : null}

      {activeView === "match" ? <MatchDataPanel data={data} players={squadPlayers} /> : null}

      {activeView === "gps" ? <GpsDataPanel data={data} players={squadPlayers} /> : null}
    </main>
  );
}
