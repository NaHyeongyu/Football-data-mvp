import type {
  CoachFocusItem,
  ManagementBoardItem,
  MarketLeader,
  MedicalRiskItem,
  PositionDepthItem,
  RecentMatchItem,
  ScoutShortlistItem,
  SeasonTrendItem,
} from "@/lib/data-types";
import {
  formatAgentStoryline,
  formatCoachAction,
  formatCompactDate,
  formatDevelopmentFocus,
  formatDominantFoot,
  formatManagementAction,
  formatPositionGroup,
  formatRiskBand,
  formatScoutNote,
  formatScoutPriority,
} from "@/lib/dashboard-formatters";

type ScoreListItem = {
  id: string;
  title: string;
  subtitle: string;
  score: number;
  meta: string;
  note: string;
  status: string;
  tags?: string[];
};

function scoreWidth(score: number) {
  return `${Math.max(6, Math.min(100, score))}%`;
}

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

function depthTone(availabilityPct: number) {
  if (availabilityPct < 50) {
    return "depth-card depth-card--risk";
  }
  if (availabilityPct < 100) {
    return "depth-card depth-card--watch";
  }
  return "depth-card";
}

function EmptyCollection({
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

export function SeasonTrendChart({ items }: { items: SeasonTrendItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyCollection
        title="시즌 데이터 없음"
        description="시즌 성과 추이를 계산할 수 있는 데이터가 아직 없습니다."
      />
    );
  }

  const maxPoints = Math.max(...items.map((item) => item.points), 1);
  const latestSeasonId = items[items.length - 1]?.season_id;

  return (
    <div className="trend-list">
      {items.map((item) => {
        const isLatest = item.season_id === latestSeasonId;

        return (
          <div
            className={isLatest ? "trend-item trend-item--highlight" : "trend-item"}
            key={item.season_id}
          >
            <div className="trend-item__topline">
              <span className="metric-inline-badge">{item.season_year} 시즌</span>
              {isLatest ? (
                <span className="metric-inline-badge metric-inline-badge--strong">
                  현재 운영 기준
                </span>
              ) : null}
            </div>

            <div className="trend-item__head">
              <div>
                <strong>{item.season_id}</strong>
                <span>
                  {item.wins}승 {item.draws}무 {item.losses}패
                </span>
              </div>
              <div className="trend-item__meta">
                <strong>{item.points} pts</strong>
                <span>승률 {item.win_rate_pct.toFixed(1)}%</span>
              </div>
            </div>

            <div className="bar-track" aria-hidden="true">
              <div
                className="bar-fill"
                style={{ width: `${(item.points / maxPoints) * 100}%` }}
              />
            </div>

            <div className="trend-chip-row">
              <span className="meta-chip">승점/경기 {item.points_per_match.toFixed(2)}</span>
              <span className="meta-chip">득점 {item.goals_for_per_match.toFixed(2)}/경기</span>
              <span className="meta-chip">실점 {item.goals_against_per_match.toFixed(2)}/경기</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function PositionDepthGrid({ items }: { items: PositionDepthItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyCollection
        title="포지션 뎁스 없음"
        description="포지션별 구성 데이터를 아직 불러오지 못했습니다."
      />
    );
  }

  return (
    <div className="depth-grid">
      {items.map((item) => (
        <article className={depthTone(item.availability_pct)} key={item.registered_position}>
          <div className="depth-card__head">
            <div>
              <p>{formatPositionGroup(item.position_group)}</p>
              <strong>{item.registered_position}</strong>
            </div>
            <span className="metric-inline-badge metric-inline-badge--neutral">
              {item.players}명 운영
            </span>
          </div>

          <div className="depth-card__metric">
            <span>가용 비율</span>
            <strong>{item.availability_pct.toFixed(0)}%</strong>
          </div>
          <div className="bar-track" aria-hidden="true">
            <div
              className="bar-fill bar-fill--soft"
              style={{ width: scoreWidth(item.availability_pct) }}
            />
          </div>

          <div className="meta-chip-row">
            <span className="meta-chip">
              스카우트 적합도 {item.average_scout_fit_score.toFixed(1)}
            </span>
            <span className="meta-chip">
              리스크 {item.average_management_risk_score.toFixed(1)}
            </span>
          </div>

          <div className="depth-card__foot">
            <span>평균 연령 {item.average_age.toFixed(1)}세</span>
            <span>누적 출전 {item.total_minutes.toLocaleString("ko-KR")}분</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function ScoreList({
  items,
  scoreLabel,
  emptyTitle,
  emptyDescription,
}: {
  items: ScoreListItem[];
  scoreLabel: string;
  emptyTitle: string;
  emptyDescription: string;
}) {
  if (items.length === 0) {
    return <EmptyCollection description={emptyDescription} title={emptyTitle} />;
  }

  return (
    <div className="score-list">
      {items.map((item, index) => (
        <article className="score-card" key={item.id}>
          <div className="score-card__topline">
            <span className="rank-pill">{String(index + 1).padStart(2, "0")}</span>
            <span className={availabilityTone(item.status)}>{item.status}</span>
          </div>

          <div className="score-card__head">
            <div>
              <strong>{item.title}</strong>
              <span>{item.subtitle}</span>
            </div>
          </div>

          <div className="score-card__score">
            <span>{scoreLabel}</span>
            <strong>{item.score.toFixed(1)}</strong>
          </div>
          <div className="bar-track" aria-hidden="true">
            <div className="bar-fill" style={{ width: scoreWidth(item.score) }} />
          </div>

          {item.tags?.length ? (
            <div className="meta-chip-row">
              {item.tags.map((tag) => (
                <span className="meta-chip" key={tag}>
                  {tag}
                </span>
              ))}
            </div>
          ) : null}

          <div className="score-card__meta">{item.meta}</div>
          <p className="score-card__note">{item.note}</p>
        </article>
      ))}
    </div>
  );
}

export function MarketLeadersList({ items }: { items: MarketLeader[] }) {
  const list = items.map((item) => ({
    id: item.player_id,
    title: item.player_name,
    subtitle: `${item.registered_position} · ${item.grade}학년 · ${item.age_today.toFixed(1)}세`,
    score: item.market_value_score,
    meta: `출전 점유 ${item.minutes_share_pct.toFixed(1)}% · 공격 관여 ${item.goal_contrib_p90.toFixed(2)} · 성장 ${item.growth_score.toFixed(1)}`,
    note: formatAgentStoryline(item.agent_storyline),
    status: item.latest_match_availability,
    tags: [
      formatPositionGroup(item.position_group),
      `${item.primary_role} 역할`,
      formatDominantFoot(item.dominant_foot),
    ],
  }));

  return (
    <ScoreList
      emptyDescription="시장가치 리더보드 데이터를 아직 불러오지 못했습니다."
      emptyTitle="리더보드 없음"
      items={list}
      scoreLabel="시장가치 지수"
    />
  );
}

export function ScoutShortlistList({
  items,
}: {
  items: ScoutShortlistItem[];
}) {
  const list = items.map((item) => ({
    id: item.player_id,
    title: item.player_name,
    subtitle: `${item.registered_position} · ${formatPositionGroup(item.position_group)} · ${item.age_today.toFixed(1)}세`,
    score: item.scout_fit_score,
    meta: `퍼포먼스 ${item.performance_score.toFixed(1)} · 피지컬 ${item.athletic_profile_score.toFixed(1)} · 성장 ${item.growth_score.toFixed(1)}`,
    note: formatScoutNote(item.scout_note),
    status: item.latest_match_availability,
    tags: [formatScoutPriority(item.scout_priority), `${item.primary_role} 프로필`],
  }));

  return (
    <ScoreList
      emptyDescription="스카우트 추적 대상을 아직 계산하지 못했습니다."
      emptyTitle="추적 대상 없음"
      items={list}
      scoreLabel="스카우트 적합도"
    />
  );
}

export function CoachFocusList({ items }: { items: CoachFocusItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyCollection
        title="코칭 포커스 없음"
        description="코칭 우선 개입 대상 데이터가 아직 없습니다."
      />
    );
  }

  return (
    <div className="focus-list">
      {items.map((item, index) => (
        <article className="focus-card" key={item.player_id}>
          <div className="score-card__topline">
            <span className="rank-pill">{String(index + 1).padStart(2, "0")}</span>
            <span className={availabilityTone(item.latest_match_availability)}>
              {item.latest_match_availability}
            </span>
          </div>

          <div className="score-card__head">
            <div>
              <strong>{item.player_name}</strong>
              <span>
                {item.registered_position} · 최근 폼 {item.recent_form_score.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="focus-card__summary">
            <div className="focus-stat">
              <span>준비도</span>
              <strong>{item.coach_readiness_score.toFixed(1)}</strong>
            </div>
            <div className="focus-stat">
              <span>출전 점유</span>
              <strong>{item.minutes_share_pct.toFixed(1)}%</strong>
            </div>
            <div className="focus-stat">
              <span>스타트 비율</span>
              <strong>{item.start_rate_pct.toFixed(1)}%</strong>
            </div>
          </div>

          <div className="focus-chip-row">
            <span className="focus-chip">
              {formatDevelopmentFocus(item.development_focus_1)}
            </span>
            <span className="focus-chip">
              {formatDevelopmentFocus(item.development_focus_2)}
            </span>
          </div>

          <div className="meta-chip-row">
            <span className="meta-chip">부하 {item.player_load_p90.toFixed(1)}</span>
            <span className="meta-chip">총 거리 {item.distance_total_p90.toFixed(2)}km</span>
            <span className="meta-chip">고속 거리 {item.high_speed_m_p90.toFixed(0)}m</span>
          </div>

          <p className="score-card__note">{formatCoachAction(item.coach_action)}</p>
        </article>
      ))}
    </div>
  );
}

export function ManagementBoardList({
  items,
}: {
  items: ManagementBoardItem[];
}) {
  if (items.length === 0) {
    return (
      <EmptyCollection
        title="운영 보드 없음"
        description="운영 의사결정 후보 데이터가 아직 없습니다."
      />
    );
  }

  return (
    <div className="score-list">
      {items.map((item, index) => (
        <article className="score-card" key={item.player_id}>
          <div className="score-card__topline">
            <span className="rank-pill">{String(index + 1).padStart(2, "0")}</span>
            <div className="badge-pair">
              <span className={riskTone(item.risk_band)}>{formatRiskBand(item.risk_band)}</span>
              <span className={availabilityTone(item.latest_match_availability)}>
                {item.latest_match_availability}
              </span>
            </div>
          </div>

          <div className="score-card__head">
            <div>
              <strong>{item.player_name}</strong>
              <span>{item.registered_position} · {item.grade}학년 운영 자원</span>
            </div>
          </div>

          <div className="double-score">
            <div>
              <span>가치</span>
              <strong>{item.management_value_score.toFixed(1)}</strong>
            </div>
            <div>
              <span>리스크</span>
              <strong>{item.management_risk_score.toFixed(1)}</strong>
            </div>
          </div>

          <div className="meta-chip-row">
            <span className="meta-chip">퍼포먼스 {item.performance_score.toFixed(1)}</span>
            <span className="meta-chip">성장 {item.growth_score.toFixed(1)}</span>
            <span className="meta-chip">지원 부하 {item.support_load_score.toFixed(1)}</span>
          </div>

          <p className="score-card__note">
            {formatManagementAction(item.management_action)}
          </p>
        </article>
      ))}
    </div>
  );
}

export function RiskWatchList({ items }: { items: MedicalRiskItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyCollection
        title="리스크 데이터 없음"
        description="의무 리스크 워치리스트를 아직 불러오지 못했습니다."
      />
    );
  }

  return (
    <div className="risk-list">
      {items.map((item, index) => (
        <article className="risk-card" key={item.player_id}>
          <div className="score-card__topline">
            <span className="rank-pill">{String(index + 1).padStart(2, "0")}</span>
            <span className={availabilityTone(item.latest_match_availability)}>
              {item.latest_match_availability}
            </span>
          </div>

          <div className="score-card__head">
            <div>
              <strong>{item.player_name}</strong>
              <span>
                {item.registered_position} · {item.latest_status_type} · 최근 기록{" "}
                {item.latest_record_date ? formatCompactDate(item.latest_record_date) : "기록 없음"}
              </span>
            </div>
          </div>

          <div className="double-score">
            <div>
              <span>리스크</span>
              <strong>{item.availability_risk_score.toFixed(1)}</strong>
            </div>
            <div>
              <span>결장일</span>
              <strong>{item.total_days_missed}일</strong>
            </div>
          </div>

          <div className="meta-chip-row">
            <span className="meta-chip">
              재활 단계 {item.latest_rehab_stage ?? "미기록"}
            </span>
            <span className="meta-chip">
              훈련 {item.latest_training_participation ?? "미기록"}
            </span>
          </div>

          <p className="score-card__note">
            {item.latest_injury_name ?? "상세 부상명 없음"} · 복귀 예정{" "}
            {item.latest_return_to_play_date
              ? formatCompactDate(item.latest_return_to_play_date)
              : "미정"}
          </p>
        </article>
      ))}
    </div>
  );
}

export function RecentMatchesTable({
  items,
}: {
  items: RecentMatchItem[];
}) {
  if (items.length === 0) {
    return (
      <EmptyCollection
        title="최근 경기 없음"
        description="최근 경기 데이터를 아직 읽어오지 못했습니다."
      />
    );
  }

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>일자</th>
            <th>상대</th>
            <th>장소</th>
            <th>결과</th>
            <th>스코어</th>
            <th>핵심 선수</th>
            <th>영향 점수</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.match_id}>
              <td>
                <span className="table-date">{formatCompactDate(item.match_date)}</span>
                <span className="table-subtext">
                  {item.season_id} · {item.match_no}R
                </span>
              </td>
              <td>
                <strong className="table-strong">{item.opponent}</strong>
                <span className="table-subtext">{item.team_name}</span>
              </td>
              <td>
                <span className={venueTone(item.venue)}>{item.venue}</span>
              </td>
              <td>
                <span className={resultTone(item.result)}>{item.result}</span>
              </td>
              <td>
                <strong className="table-strong">{item.score}</strong>
              </td>
              <td>
                <strong className="table-strong">{item.key_player ?? "미기록"}</strong>
                <span className="table-subtext">
                  {item.key_player_role ?? "역할 미기록"} · {item.key_player_goals ?? 0}G{" "}
                  {item.key_player_assists ?? 0}A
                </span>
              </td>
              <td>
                <span className="impact-pill">
                  {(item.key_player_impact_score ?? 0).toFixed(1)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
