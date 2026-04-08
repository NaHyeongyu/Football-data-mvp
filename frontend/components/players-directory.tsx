"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useDeferredValue, useMemo, useState } from "react";

import type { MedicalRiskItem, PlayerSeasonSummaryItem } from "@/lib/data-types";

type PlayersDirectoryProps = {
  latestSeasonYear: number;
  medicalAvailability: MedicalRiskItem[];
  seasonSummaries: PlayerSeasonSummaryItem[];
};

function injuryTone(status: string) {
  if (status === "부상") {
    return "status-pill status-pill--danger";
  }
  if (status === "관리") {
    return "status-pill status-pill--warning";
  }
  return "status-pill status-pill--success";
}

function getInjuryStatus(medical?: MedicalRiskItem) {
  if (!medical) {
    return "정상";
  }
  if (medical.latest_match_availability === "불가") {
    return "부상";
  }
  if (medical.latest_match_availability === "조건부") {
    return "관리";
  }
  return "정상";
}

function getReturnCountdown(dateValue?: string | null) {
  if (!dateValue) {
    return null;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const target = new Date(dateValue);
  target.setHours(0, 0, 0, 0);

  if (Number.isNaN(target.getTime())) {
    return null;
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

function normalizeValue(value: string) {
  return value.trim().toLowerCase();
}

function formatUnderAge(ageToday: number) {
  const underAge = Math.max(1, Math.ceil(ageToday));
  return `U-${underAge}`;
}

export function PlayersDirectory({
  latestSeasonYear,
  medicalAvailability,
  seasonSummaries,
}: PlayersDirectoryProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [seasonFilter, setSeasonFilter] = useState(String(latestSeasonYear));
  const [positionFilter, setPositionFilter] = useState("all");
  const [injuryFilter, setInjuryFilter] = useState("all");
  const deferredQuery = useDeferredValue(searchQuery);

  const medicalMap = useMemo(
    () => new Map(medicalAvailability.map((item) => [item.player_id, item])),
    [medicalAvailability],
  );

  const seasonOptions = Array.from(
    new Set(seasonSummaries.map((item) => item.season_year)),
  ).sort((left, right) => right - left);

  const selectedSeasonYear = Number(seasonFilter);

  const seasonalRoster = seasonSummaries
    .filter((item) => item.season_year === selectedSeasonYear)
    .map((item) => ({
      injuryStatus: getInjuryStatus(medicalMap.get(item.player_id)),
      medical: medicalMap.get(item.player_id),
      summary: item,
    }));

  const rosterCounts = seasonalRoster.reduce(
    (counts, player) => {
      counts.total += 1;

      if (player.injuryStatus === "부상") {
        counts.injured += 1;
      } else if (player.injuryStatus === "관리") {
        counts.managed += 1;
      } else {
        counts.normal += 1;
      }

      return counts;
    },
    {
      injured: 0,
      managed: 0,
      normal: 0,
      total: 0,
    },
  );

  const positionOptions = Array.from(
    new Set(seasonalRoster.map(({ summary }) => summary.registered_position)),
  ).sort((left, right) => left.localeCompare(right, "ko"));

  const filteredPlayers = seasonalRoster.filter(({ injuryStatus, summary, medical }) => {
    const normalizedQuery = normalizeValue(deferredQuery);
    const matchesQuery =
      normalizedQuery.length === 0 ||
      [
        summary.player_name,
        summary.player_id,
        summary.registered_position,
        summary.primary_role,
        summary.position_group,
        injuryStatus,
        medical?.latest_injury_name ?? "",
      ]
        .map(normalizeValue)
        .some((value) => value.includes(normalizedQuery));

    const matchesPosition =
      positionFilter === "all" || summary.registered_position === positionFilter;
    const matchesInjury = injuryFilter === "all" || injuryStatus === injuryFilter;

    return matchesQuery && matchesPosition && matchesInjury;
  });

  return (
    <>
      <section className="stat-grid">
        <article className="metric-card metric-card--roster-primary">
          <p>시즌 전체 선수 수</p>
          <strong>{rosterCounts.total.toLocaleString("ko-KR")}명</strong>
          <span>{selectedSeasonYear} 시즌 등록 로스터</span>
        </article>
        <article className="metric-card">
          <p>정상 선수</p>
          <strong>{rosterCounts.normal.toLocaleString("ko-KR")}명</strong>
          <span>
            전체 로스터의{" "}
            {rosterCounts.total === 0 ? "0.0" : ((rosterCounts.normal / rosterCounts.total) * 100).toFixed(1)}
            %
          </span>
        </article>
        <article className="metric-card">
          <p>관리 선수</p>
          <strong>{rosterCounts.managed.toLocaleString("ko-KR")}명</strong>
          <span>
            전체 로스터의{" "}
            {rosterCounts.total === 0 ? "0.0" : ((rosterCounts.managed / rosterCounts.total) * 100).toFixed(1)}
            %
          </span>
        </article>
        <article className="metric-card">
          <p>부상 선수</p>
          <strong>{rosterCounts.injured.toLocaleString("ko-KR")}명</strong>
          <span>
            전체 로스터의{" "}
            {rosterCounts.total === 0 ? "0.0" : ((rosterCounts.injured / rosterCounts.total) * 100).toFixed(1)}
            %
          </span>
        </article>
      </section>

      <section className="directory-filter-panel">
        <div className="directory-filter-panel__header">
          <div>
            <h2>선수 검색 필터</h2>
          </div>
        </div>

        <div className="directory-toolbar">
          <div className="directory-filter-row">
            <label className="form-field">
              <span>Season</span>
              <select
                aria-label="Filter roster by season"
                onChange={(event) => setSeasonFilter(event.target.value)}
                value={seasonFilter}
              >
                {seasonOptions.map((seasonYear) => (
                  <option key={seasonYear} value={seasonYear}>
                    {seasonYear} 시즌
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field form-field--search form-field--wide">
              <span>Search</span>
              <input
                aria-label="Search players"
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="선수명 / 포지션 / 역할 검색"
                type="search"
                value={searchQuery}
              />
            </label>

            <label className="form-field">
              <span>Position</span>
              <select
                aria-label="Filter players by position"
                onChange={(event) => setPositionFilter(event.target.value)}
                value={positionFilter}
              >
                <option value="all">전체 포지션</option>
                {positionOptions.map((position) => (
                  <option key={position} value={position}>
                    {position}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field">
              <span>Injury</span>
              <select
                aria-label="Filter players by injury status"
                onChange={(event) => setInjuryFilter(event.target.value)}
                value={injuryFilter}
              >
                <option value="all">전체 상태</option>
                <option value="정상">정상</option>
                <option value="관리">관리</option>
                <option value="부상">부상</option>
              </select>
            </label>
          </div>
        </div>
      </section>

      <section className="panel panel--tight directory-list-panel" id="player-list">
        <div className="panel-header panel-header--compact">
          <div>
            <p className="panel-eyebrow">Roster List</p>
            <h2>{selectedSeasonYear} 시즌 선수 리스트</h2>
          </div>
          <span className="count-badge">{filteredPlayers.length}명 표시</span>
        </div>

        <div className="table-scroll">
          <table className="data-table data-table--matches data-table--players">
            <colgroup>
              <col style={{ width: "18%" }} />
              <col style={{ width: "11%" }} />
              <col style={{ width: "9%" }} />
              <col style={{ width: "13%" }} />
              <col style={{ width: "16%" }} />
              <col style={{ width: "11%" }} />
              <col style={{ width: "22%" }} />
            </colgroup>
            <thead>
              <tr>
                <th className="cell-center">선수</th>
                <th className="cell-center">포지션</th>
                <th className="cell-center">나이</th>
                <th className="cell-center">출전 경기</th>
                <th className="cell-center">출전 시간</th>
                <th className="cell-center">최근 폼</th>
                <th className="cell-center">부상 상태</th>
              </tr>
            </thead>
            <tbody>
              {filteredPlayers.length > 0 ? (
                filteredPlayers.map(({ injuryStatus, summary, medical }) => {
                  const returnCountdown =
                    injuryStatus === "부상"
                      ? getReturnCountdown(medical?.latest_return_to_play_date)
                      : null;
                  const playerDetailHref = `/players/${summary.player_id}`;

                  return (
                    <tr
                      key={`${summary.player_id}-${summary.season_id}`}
                      className="player-list-row"
                      role="link"
                      tabIndex={0}
                      onClick={() => router.push(playerDetailHref)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          router.push(playerDetailHref);
                        }
                      }}
                    >
                      <td className="cell-center">
                        <Link
                          className="table-action-link table-action-link--player"
                          href={playerDetailHref}
                          onClick={(event) => event.stopPropagation()}
                        >
                          <strong className="table-strong">{summary.player_name}</strong>
                        </Link>
                      </td>
                      <td className="cell-center">
                        <span className="table-chip">{summary.registered_position}</span>
                      </td>
                      <td className="cell-center">
                        <span className="table-chip table-chip--muted">
                          {formatUnderAge(summary.age_today)}
                        </span>
                      </td>
                      <td className="cell-center">
                        <span className="table-metric">{summary.appearances}</span>
                        <span className="table-unit">경기</span>
                      </td>
                      <td className="cell-center">
                        <span className="table-metric">
                          {summary.minutes.toLocaleString("ko-KR")}
                        </span>
                        <span className="table-unit">분</span>
                      </td>
                      <td className="cell-center">
                        <span className="table-score">
                          {summary.recent_form_score.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <div className="injury-cell">
                          <span className={injuryTone(injuryStatus)}>{injuryStatus}</span>
                          {returnCountdown ? (
                            <span className="injury-cell__eta">{returnCountdown}</span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td className="table-empty" colSpan={7}>
                    현재 검색 조건에 맞는 선수가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
