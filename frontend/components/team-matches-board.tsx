"use client";

import { usePathname, useRouter } from "next/navigation";
import { startTransition, useDeferredValue, useState } from "react";

import type { TeamMatchListItem, TeamMatchListResponse } from "@/lib/team-api-types";

const dateFormatter = new Intl.DateTimeFormat("ko-KR", {
  year: "numeric",
  month: "short",
  day: "numeric",
});
const decimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});
const numberFormatter = new Intl.NumberFormat("ko-KR");

function resultTone(result: string) {
  if (result === "승") {
    return "table-badge table-badge--success";
  }
  if (result === "패") {
    return "table-badge table-badge--danger";
  }
  return "table-badge table-badge--warning";
}

function matchTypeTone(matchType: string) {
  if (matchType === "공식") {
    return "table-badge table-badge--official";
  }
  return "table-badge table-badge--practice";
}

function formatPercent(value: number) {
  return `${decimalFormatter.format(value)}%`;
}

function buildMatchSearchText(match: TeamMatchListItem) {
  return [
    match.opponent_team,
    match.stadium_name,
    match.match_type,
    match.result,
    match.match_id,
  ]
    .join(" ")
    .toLowerCase();
}

function summarizeRecord(matches: TeamMatchListItem[]) {
  return matches.reduce(
    (summary, match) => {
      if (match.result === "승") {
        summary.win_count += 1;
      } else if (match.result === "무") {
        summary.draw_count += 1;
      } else if (match.result === "패") {
        summary.loss_count += 1;
      }
      return summary;
    },
    { win_count: 0, draw_count: 0, loss_count: 0 },
  );
}

function MatchListTable({
  matches,
  onSelectMatch,
}: {
  matches: TeamMatchListItem[];
  onSelectMatch: (matchId: string) => void;
}) {
  return (
    <div className="table-scroll">
      <table className="data-table data-table--matches">
        <thead>
          <tr>
            <th>날짜</th>
            <th>상대</th>
            <th>구분</th>
            <th>장소</th>
            <th>결과</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((match) => (
            <tr
              key={match.match_id}
              className="match-list-row"
              role="link"
              tabIndex={0}
              onClick={() => onSelectMatch(match.match_id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectMatch(match.match_id);
                }
              }}
            >
              <td>{dateFormatter.format(new Date(match.match_date))}</td>
              <td>
                <span className="match-list-link">
                  <strong>{match.opponent_team}</strong>
                </span>
              </td>
              <td>
                <span className={matchTypeTone(match.match_type)}>{match.match_type}</span>
              </td>
              <td>{match.stadium_name}</td>
              <td>
                <span className={resultTone(match.result)}>
                  {match.result} · {match.goals_for}:{match.goals_against}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TeamMatchesBoard({ data }: { data: TeamMatchListResponse }) {
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState("");
  const [matchTypeFilter, setMatchTypeFilter] = useState<"all" | "공식" | "연습">("all");
  const [resultFilter, setResultFilter] = useState<"all" | "승" | "무" | "패">("all");

  const deferredSearchQuery = useDeferredValue(searchQuery);
  const normalizedSearchQuery = deferredSearchQuery.trim().toLowerCase();

  const filteredMatches = data.matches.filter((match) => {
    if (matchTypeFilter !== "all" && match.match_type !== matchTypeFilter) {
      return false;
    }
    if (resultFilter !== "all" && match.result !== resultFilter) {
      return false;
    }
    if (!normalizedSearchQuery) {
      return true;
    }
    return buildMatchSearchText(match).includes(normalizedSearchQuery);
  });

  const officialMatches = data.matches.filter((match) => match.match_type === "공식");
  const practiceMatches = data.matches.filter((match) => match.match_type === "연습");
  const totalRecord = summarizeRecord(data.matches);
  const officialRecord = summarizeRecord(officialMatches);
  const practiceRecord = summarizeRecord(practiceMatches);

  const matchCount = data.summary.match_count;
  const officialShare = matchCount > 0 ? (data.summary.official_match_count / matchCount) * 100 : 0;
  const practiceShare = matchCount > 0 ? (data.summary.practice_match_count / matchCount) * 100 : 0;

  return (
    <>
      <section className="matches-kpi-grid" id="matches-summary">
        <article className="matches-kpi-card matches-kpi-card--primary">
          <div className="matches-kpi-card__head">
            <div>
              <p className="panel-eyebrow">Total Matches</p>
              <h2>경기 수</h2>
            </div>
            <span className="matches-kpi-chip matches-kpi-chip--inverse">{data.selected_year} 시즌</span>
          </div>
          <div className="matches-kpi-card__single">
            <strong>{numberFormatter.format(matchCount)}</strong>
            <span>전체 경기 수</span>
          </div>
          <div className="matches-kpi-mini-record">
            <span>승 {totalRecord.win_count}</span>
            <span>무 {totalRecord.draw_count}</span>
            <span>패 {totalRecord.loss_count}</span>
          </div>
        </article>

        <article className="matches-kpi-card">
          <div className="matches-kpi-card__head">
            <div>
              <p className="panel-eyebrow">Official Matches</p>
              <h3>공식경기</h3>
            </div>
            <span className="matches-kpi-chip">{formatPercent(officialShare)}</span>
          </div>
          <div className="matches-kpi-card__single">
            <strong>{numberFormatter.format(data.summary.official_match_count)}</strong>
            <span>전체 경기 대비 비중</span>
          </div>
          <div className="matches-kpi-mini-record">
            <span>승 {officialRecord.win_count}</span>
            <span>무 {officialRecord.draw_count}</span>
            <span>패 {officialRecord.loss_count}</span>
          </div>
        </article>

        <article className="matches-kpi-card">
          <div className="matches-kpi-card__head">
            <div>
              <p className="panel-eyebrow">Practice Matches</p>
              <h3>연습경기</h3>
            </div>
            <span className="matches-kpi-chip">{formatPercent(practiceShare)}</span>
          </div>
          <div className="matches-kpi-card__single">
            <strong>{numberFormatter.format(data.summary.practice_match_count)}</strong>
            <span>전체 경기 대비 비중</span>
          </div>
          <div className="matches-kpi-mini-record">
            <span>승 {practiceRecord.win_count}</span>
            <span>무 {practiceRecord.draw_count}</span>
            <span>패 {practiceRecord.loss_count}</span>
          </div>
        </article>

      </section>

      <section className="matches-section-stack" id="matches-list">
        <section className="matches-filter-panel">
          <div className="matches-filter-panel__head">
            <div>
              <p className="panel-eyebrow">Match Filters</p>
              <h3>경기 검색 필터</h3>
            </div>
            <div className="matches-filter-panel__summary">
              <strong>{numberFormatter.format(filteredMatches.length)}</strong>
              <span>{numberFormatter.format(data.matches.length)}경기 중 조회 결과</span>
            </div>
          </div>

          <div className="matches-filter-grid">
            <label className="form-field matches-filter-field">
              <span>시즌</span>
              <select
                value={String(data.selected_year)}
                onChange={(event) => {
                  const nextYear = event.target.value;
                  startTransition(() => {
                    router.replace(`${pathname}?year=${nextYear}`);
                  });
                }}
              >
                {data.available_years.map((yearOption) => (
                  <option key={yearOption.year} value={String(yearOption.year)}>
                    {yearOption.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field form-field--search matches-filter-field">
              <span>검색</span>
              <input
                placeholder="상대팀, 장소, 경기 ID 검색"
                type="search"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />
            </label>

            <label className="form-field matches-filter-field">
              <span>경기 구분</span>
              <select value={matchTypeFilter} onChange={(event) => setMatchTypeFilter(event.target.value as "all" | "공식" | "연습")}>
                <option value="all">전체</option>
                <option value="공식">공식경기</option>
                <option value="연습">연습경기</option>
              </select>
            </label>

            <label className="form-field matches-filter-field">
              <span>결과</span>
              <select value={resultFilter} onChange={(event) => setResultFilter(event.target.value as "all" | "승" | "무" | "패")}>
                <option value="all">전체</option>
                <option value="승">승</option>
                <option value="무">무</option>
                <option value="패">패</option>
              </select>
            </label>
          </div>
        </section>

        <section className="panel matches-table-panel">
          {data.matches.length === 0 ? (
            <div className="empty-state">
              <strong>해당 연도 경기 없음</strong>
              <p>선택한 연도에는 조회 가능한 경기 데이터가 없습니다.</p>
            </div>
          ) : filteredMatches.length === 0 ? (
            <div className="empty-state">
              <strong>조건에 맞는 경기가 없습니다</strong>
              <p>검색어나 필터 조건을 조정해서 다시 조회해보세요.</p>
            </div>
          ) : (
            <MatchListTable matches={filteredMatches} onSelectMatch={(matchId) => router.push(`/matches/${matchId}`)} />
          )}
        </section>
      </section>
    </>
  );
}
