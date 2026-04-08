import Link from "next/link";

import type {
  PositionAvailabilityItem,
  PositionBalanceItem,
  PositionDevelopmentItem,
  TeamMatchFormItem,
  TeamOverviewResponse,
} from "@/lib/team-api-types";

const numberFormatter = new Intl.NumberFormat("ko-KR");
const decimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});
const compactDecimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});
const dateFormatter = new Intl.DateTimeFormat("ko-KR", {
  month: "short",
  day: "numeric",
});

function formatSignedValue(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }

  const formatter =
    digits === 1
      ? decimalFormatter
      : new Intl.NumberFormat("ko-KR", {
          maximumFractionDigits: digits,
          minimumFractionDigits: digits,
        });
  const prefix = value > 0 ? "+" : "";

  return `${prefix}${formatter.format(value)}`;
}

function formatLoad(value: number) {
  return numberFormatter.format(Math.round(value));
}

function formatDistance(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }

  return `${compactDecimalFormatter.format(value)} km`;
}

function formatDeltaTone(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "dashboard-chip";
  }
  if (value > 0) {
    return "dashboard-chip dashboard-chip--good";
  }
  if (value < 0) {
    return "dashboard-chip dashboard-chip--danger";
  }
  return "dashboard-chip";
}

function formatGrowthDeltaTone(value: number | null | undefined, positiveIsGood = true) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "dashboard-chip";
  }

  const isGood = positiveIsGood ? value > 0 : value < 0;
  const isBad = positiveIsGood ? value < 0 : value > 0;

  if (isGood) {
    return "dashboard-chip dashboard-chip--good";
  }
  if (isBad) {
    return "dashboard-chip dashboard-chip--danger";
  }
  return "dashboard-chip";
}

function formatInsightLabel(label: string) {
  if (label === "availability risk") {
    return "가용 인원 주의";
  }
  if (label === "high load") {
    return "부하 높음";
  }
  if (label === "form down") {
    return "폼 하락";
  }
  return "안정적";
}

function insightTone(label: string) {
  if (label === "availability risk") {
    return "dashboard-chip dashboard-chip--danger";
  }
  if (label === "high load" || label === "form down") {
    return "dashboard-chip dashboard-chip--warning";
  }
  return "dashboard-chip dashboard-chip--good";
}

function formatGrowthLabel(label: string) {
  if (label === "rising") {
    return "상승";
  }
  if (label === "monitor") {
    return "관리 필요";
  }
  return "유지";
}

function growthTone(label: string) {
  if (label === "rising") {
    return "dashboard-chip dashboard-chip--good";
  }
  if (label === "monitor") {
    return "dashboard-chip dashboard-chip--warning";
  }
  return "dashboard-chip";
}

function availabilityRate(item: PositionAvailabilityItem) {
  if (item.roster_count <= 0) {
    return 0;
  }
  return (item.available_count / item.roster_count) * 100;
}

function matchResult(item: TeamMatchFormItem) {
  if (item.goals_for > item.goals_against) {
    return "승";
  }
  if (item.goals_for < item.goals_against) {
    return "패";
  }
  return "무";
}

function resultTone(item: TeamMatchFormItem) {
  const result = matchResult(item);

  if (result === "승") {
    return "table-badge table-badge--success";
  }
  if (result === "패") {
    return "table-badge table-badge--danger";
  }
  return "table-badge table-badge--warning";
}

function OverviewHighlight({
  title,
  item,
}: {
  title: string;
  item: TeamMatchFormItem | null;
}) {
  if (!item) {
    return (
      <article className="dashboard-match-card">
        <div className="dashboard-match-card__head">
          <span className="panel-eyebrow">{title}</span>
        </div>
        <p className="interpretation-note">경기 데이터가 아직 없습니다.</p>
      </article>
    );
  }

  return (
    <article className="dashboard-match-card">
      <div className="dashboard-match-card__head">
        <span className="panel-eyebrow">{title}</span>
        <span className={resultTone(item)}>{matchResult(item)}</span>
      </div>
      <strong>{item.opponent_team}</strong>
      <p>
        {dateFormatter.format(new Date(item.match_date))} · {item.match_type}
      </p>
      <div className="dashboard-match-card__scoreline">
        <span>
          {item.goals_for} : {item.goals_against}
        </span>
        <strong>{decimalFormatter.format(item.team_average_match_score)}</strong>
      </div>
      <div className="meta-chip-row">
        <span className="meta-chip">평균 출전 {decimalFormatter.format(item.average_minutes)}분</span>
        <span className="meta-chip">
          효율 {item.efficiency_score === null ? "-" : decimalFormatter.format(item.efficiency_score)}
        </span>
      </div>
    </article>
  );
}

function PositionBalanceCard({ item }: { item: PositionBalanceItem }) {
  return (
    <article className="dashboard-position-card">
      <div className="dashboard-position-card__head">
        <div>
          <span className="dashboard-position-card__label">Position</span>
          <strong>{item.position}</strong>
        </div>
        <span className={insightTone(item.insight_label)}>{formatInsightLabel(item.insight_label)}</span>
      </div>

      <div className="dashboard-position-card__metrics">
        <div>
          <span>최근 폼</span>
          <strong>
            {item.recent_form_score === null ? "-" : decimalFormatter.format(item.recent_form_score)}
          </strong>
        </div>
        <div>
          <span>출전 시간</span>
          <strong>{item.average_minutes === null ? "-" : `${decimalFormatter.format(item.average_minutes)}분`}</strong>
        </div>
        <div>
          <span>스프린트</span>
          <strong>
            {item.average_sprint_count === null
              ? "-"
              : decimalFormatter.format(item.average_sprint_count)}
          </strong>
        </div>
        <div>
          <span>거리</span>
          <strong>{formatDistance(item.average_total_distance)}</strong>
        </div>
      </div>

      <div className="dashboard-position-card__footer">
        <span className={formatDeltaTone(item.form_delta)}>
          폼 {formatSignedValue(item.form_delta)}
        </span>
        <span className="dashboard-chip">
          가용 {item.available_count} / 관리 {item.managed_count} / 부상 {item.injured_count}
        </span>
      </div>
    </article>
  );
}

function DevelopmentRow({ item }: { item: PositionDevelopmentItem }) {
  return (
    <article className="dashboard-development-row">
      <div className="dashboard-development-row__head">
        <div>
          <strong>{item.position}</strong>
          <span>{item.roster_count}명 로스터</span>
        </div>
        <span className={growthTone(item.growth_label)}>{formatGrowthLabel(item.growth_label)}</span>
      </div>
      <div className="dashboard-development-row__metrics">
        <span className={formatGrowthDeltaTone(item.average_body_fat_delta, false)}>
          체지방 {formatSignedValue(item.average_body_fat_delta)}%
        </span>
        <span className={formatGrowthDeltaTone(item.average_muscle_mass_delta, true)}>
          근육량 {formatSignedValue(item.average_muscle_mass_delta)}kg
        </span>
        <span className={formatDeltaTone(item.average_form_delta)}>
          폼 {formatSignedValue(item.average_form_delta)}
        </span>
      </div>
    </article>
  );
}

export function TeamOverviewDashboard({ data }: { data: TeamOverviewResponse }) {
  const latestTrendPoints = data.load.trend_points.slice(-6).reverse();
  const maxTrendLoad = Math.max(...latestTrendPoints.map((item) => item.total_load), 1);
  const availabilityCards = [
    {
      label: "정상 출전 가능",
      value: `${numberFormatter.format(data.availability.available_count)}명`,
      description: "현재 스냅샷 기준 즉시 운영 가능한 인원",
      delta: `${numberFormatter.format(data.availability.positions.length)}개 포지션 그룹 추적`,
      tone: "highlight",
    },
    {
      label: "관리 필요 인원",
      value: `${numberFormatter.format(data.availability.managed_count)}명`,
      description: "출전은 가능하지만 부하 관리가 필요한 인원",
      delta: `복귀 예정 ${numberFormatter.format(data.availability.scheduled_return_count)}명`,
      tone: "default",
    },
    {
      label: "부상 인원",
      value: `${numberFormatter.format(data.availability.injured_count)}명`,
      description: "현재 재활 또는 즉시 출전 불가 상태",
      delta: `재활 진행 ${numberFormatter.format(data.medical.current_rehab_count)}명`,
      tone: "default",
    },
    {
      label: "최근 5경기 팀 평균 점수",
      value: decimalFormatter.format(data.match_form.recent_5_match_score),
      description: "객관 경기 지표 기반 최근 팀 폼",
      delta: `이전 5경기 대비 ${formatSignedValue(data.match_form.form_delta)}`,
      tone: "highlight",
    },
    {
      label: "최근 28일 팀 총 Load",
      value: formatLoad(data.load.load_28d),
      description: "훈련과 경기 부하를 합산한 최근 28일 총량",
      delta: `급증 ${data.load.load_spike_player_count}명 / 급감 ${data.load.load_drop_player_count}명`,
      tone: "default",
    },
    {
      label: "최근 7일 평균 Sprint 노출",
      value: decimalFormatter.format(data.load.average_sprint_exposure_7d),
      description: "선수 1인 기준 평균 스프린트 노출량",
      delta: `평균 거리 ${decimalFormatter.format(data.load.average_total_distance_7d)} km`,
      tone: "default",
    },
  ] as const;

  return (
    <>
      <section className="stat-grid" id="kpi-summary">
        {availabilityCards.map((card, index) => (
          <article
            className={
              card.tone === "highlight" && index < 4
                ? "metric-card metric-card--highlight"
                : "metric-card"
            }
            key={card.label}
          >
            <p>{card.label}</p>
            <strong>{card.value}</strong>
            <span>{card.description}</span>
            <div className="metric-card__delta">{card.delta}</div>
          </article>
        ))}
      </section>

      <section className="dashboard-grid dashboard-grid--split" id="availability-board">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Team Availability</p>
              <h2>가용 인원 보드</h2>
            </div>
            <p className="panel-note">포지션별 즉시 운영 가능 인원과 관리 대상 비중을 함께 봅니다.</p>
          </div>

          <div className="dashboard-availability-list">
            {data.availability.positions.map((item) => (
              <article className="dashboard-availability-row" key={item.position}>
                <div className="dashboard-availability-row__head">
                  <div>
                    <strong>{item.position}</strong>
                    <span>{item.roster_count}명 로스터</span>
                  </div>
                  <span className="dashboard-chip">
                    가용 {item.available_count} / 관리 {item.managed_count} / 부상 {item.injured_count}
                  </span>
                </div>
                <div className="bar-track" aria-hidden="true">
                  <div
                    className="bar-fill"
                    style={{ width: `${Math.max(0, Math.min(100, availabilityRate(item)))}%` }}
                  />
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel" id="medical-overview">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Medical / Return</p>
              <h2>메디컬 개요</h2>
            </div>
            <p className="panel-note">최근 부상, 재활, 복귀 상황을 운영 관점으로 요약했습니다.</p>
          </div>

          <div className="dashboard-inline-grid">
            <div className="dashboard-summary-card">
              <span>최근 180일 부상</span>
              <strong>{data.medical.injuries_last_180d}건</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>재부상</span>
              <strong>{data.medical.reinjury_count_365d}건</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>복귀 후 14일 이내</span>
              <strong>{data.medical.returns_last_14d_count}명</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>현재 재활</span>
              <strong>{data.medical.current_rehab_count}명</strong>
            </div>
          </div>

          <div className="attention-list">
            {data.medical.injury_parts.map((item) => (
              <article className="attention-item attention-item--neutral" key={item.injury_part}>
                <div>
                  <strong>{item.injury_part}</strong>
                  <span>{item.count}건</span>
                </div>
                <p>최근 180일 기준 동일 부위 이슈 빈도를 누적 집계했습니다.</p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="dashboard-grid dashboard-grid--split" id="load-trend">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Team Load Trend</p>
              <h2>부하 추세</h2>
            </div>
            <p className="panel-note">최근 7/14/28일 부하와 최근 세션 흐름을 한 번에 봅니다.</p>
          </div>

          <div className="dashboard-inline-grid">
            <div className="dashboard-summary-card">
              <span>최근 7일</span>
              <strong>{formatLoad(data.load.load_7d)}</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>최근 14일</span>
              <strong>{formatLoad(data.load.load_14d)}</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>최근 28일</span>
              <strong>{formatLoad(data.load.load_28d)}</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>Load 비중</span>
              <strong>
                경기 {decimalFormatter.format(data.load.match_load_share_28d)}% / 훈련{" "}
                {decimalFormatter.format(data.load.training_load_share_28d)}%
              </strong>
            </div>
          </div>

          <div className="dashboard-trend-list">
            {latestTrendPoints.map((item) => (
              <article className="dashboard-trend-row" key={`${item.session_date}-${item.session_source}`}>
                <div className="dashboard-trend-row__head">
                  <div>
                    <strong>{dateFormatter.format(new Date(item.session_date))}</strong>
                    <span>{item.session_source === "match" ? "경기 세션" : "훈련 세션"}</span>
                  </div>
                  <span className="dashboard-chip">{formatLoad(item.total_load)}</span>
                </div>
                <div className="bar-track" aria-hidden="true">
                  <div
                    className="bar-fill bar-fill--soft"
                    style={{ width: `${(item.total_load / maxTrendLoad) * 100}%` }}
                  />
                </div>
                <div className="meta-chip-row">
                  <span className="meta-chip">Sprint {item.sprint_count}</span>
                  <span className="meta-chip">Distance {compactDecimalFormatter.format(item.total_distance)} km</span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel" id="match-form">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Team Match Form</p>
              <h2>팀 경기 폼</h2>
            </div>
            <p className="panel-note">최근 5경기 팀 평균 점수와 시즌 최고/최저 경기를 함께 봅니다.</p>
          </div>

          <div className="dashboard-inline-grid">
            <div className="dashboard-summary-card">
              <span>최근 5경기 평균</span>
              <strong>{decimalFormatter.format(data.match_form.recent_5_match_score)}</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>직전 5경기 평균</span>
              <strong>
                {data.match_form.previous_5_match_score === null
                  ? "-"
                  : decimalFormatter.format(data.match_form.previous_5_match_score)}
              </strong>
            </div>
            <div className="dashboard-summary-card">
              <span>변화 폭</span>
              <strong>{formatSignedValue(data.match_form.form_delta)}</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>최신 경기 점수</span>
              <strong>
                {data.match_form.latest_match_score === null
                  ? "-"
                  : decimalFormatter.format(data.match_form.latest_match_score)}
              </strong>
            </div>
          </div>

          <div className="dashboard-match-grid">
            <OverviewHighlight item={data.match_form.best_match} title="Season Best" />
            <OverviewHighlight item={data.match_form.worst_match} title="Season Low" />
          </div>
        </article>
      </section>

      <section className="dashboard-grid dashboard-grid--split" id="position-balance">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Position Balance</p>
              <h2>포지션 밸런스</h2>
            </div>
            <p className="panel-note">포지션별 최근 폼, 평균 출전 시간, 스프린트와 거리 노출을 정리했습니다.</p>
          </div>

          <div className="dashboard-position-grid">
            {data.position_balance.map((item) => (
              <PositionBalanceCard item={item} key={item.position} />
            ))}
          </div>
        </article>

        <article className="panel" id="development-trend">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Development Trend</p>
              <h2>성장 추세</h2>
            </div>
            <p className="panel-note">체성분 변화와 최근 폼 변화를 포지션 단위로 묶었습니다.</p>
          </div>

          <div className="dashboard-inline-grid">
            <div className="dashboard-summary-card">
              <span>평균 체지방 변화</span>
              <strong>{formatSignedValue(data.development.average_body_fat_delta)}%</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>평균 근육량 변화</span>
              <strong>{formatSignedValue(data.development.average_muscle_mass_delta)}kg</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>상승 선수</span>
              <strong>{data.development.rising_players_count}명</strong>
            </div>
            <div className="dashboard-summary-card">
              <span>관리 필요 선수</span>
              <strong>{data.development.falling_players_count}명</strong>
            </div>
          </div>

          <div className="dashboard-development-list">
            {data.development.positions.map((item) => (
              <DevelopmentRow item={item} key={item.position} />
            ))}
          </div>
        </article>
      </section>

      <section className="panel" id="recent-matches">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Recent Matches</p>
            <h2>최근 경기 로그</h2>
          </div>
          <Link className="ghost-button" href="/matches">
            경기 화면 열기
          </Link>
        </div>

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>날짜</th>
                <th>상대</th>
                <th>구분</th>
                <th>스코어</th>
                <th>팀 평균 점수</th>
                <th>평균 출전</th>
                <th>효율</th>
              </tr>
            </thead>
            <tbody>
              {data.match_form.recent_matches.slice(0, 8).map((item) => (
                <tr key={item.match_id}>
                  <td>{dateFormatter.format(new Date(item.match_date))}</td>
                  <td>{item.opponent_team}</td>
                  <td>
                    <span className={resultTone(item)}>
                      {item.match_type} · {matchResult(item)}
                    </span>
                  </td>
                  <td>
                    {item.goals_for} : {item.goals_against}
                  </td>
                  <td>{decimalFormatter.format(item.team_average_match_score)}</td>
                  <td>{decimalFormatter.format(item.average_minutes)}분</td>
                  <td>
                    {item.efficiency_score === null
                      ? "-"
                      : decimalFormatter.format(item.efficiency_score)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
