import Link from "next/link";

import type {
  PositionAvailabilityItem,
  PositionBalanceItem,
  PositionDevelopmentItem,
  PlayerDevelopmentReportItem,
  PlayerDevelopmentReportResponse,
  PlayerInjuryRiskItem,
  PlayerInjuryRiskResponse,
  PlayerPerformanceReadinessItem,
  PlayerPerformanceReadinessResponse,
  TeamCalendarEvent,
  TeamCalendarResponse,
  TeamMatchFormItem,
  TeamMatchListResponse,
  TeamOverviewResponse,
  TeamTrainingListItem,
  TeamTrainingListResponse,
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
  year: "numeric",
  month: "short",
  day: "numeric",
});
const shortDateFormatter = new Intl.DateTimeFormat("ko-KR", {
  month: "numeric",
  day: "numeric",
});
const timeFormatter = new Intl.DateTimeFormat("ko-KR", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function parseDate(value: string) {
  return new Date(value.includes("T") ? value : `${value}T00:00:00`);
}

function formatDate(value: string) {
  return dateFormatter.format(parseDate(value));
}

function formatShortDate(value: string) {
  return shortDateFormatter.format(parseDate(value));
}

function formatSnapshotDate(value: string) {
  const date = parseDate(value);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${date.getFullYear()}.${month}.${day}`;
}

function formatTimeRange(startAt: string | null, endAt: string | null) {
  if (!startAt) {
    return "시간 미기록";
  }

  const start = timeFormatter.format(new Date(startAt));
  if (!endAt) {
    return start;
  }

  return `${start} - ${timeFormatter.format(new Date(endAt))}`;
}

function formatPercent(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }

  return `${decimalFormatter.format(value)}%`;
}

function formatSigned(value: number | null | undefined, digits = 1) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}`;
}

function formatMetric(value: number | null | undefined, unit = "", digits = 1) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }

  const formatted =
    digits === 0
      ? numberFormatter.format(Math.round(value))
      : digits === 1
        ? decimalFormatter.format(value)
        : compactDecimalFormatter.format(value);

  return unit ? `${formatted}${unit}` : formatted;
}

function trainingTypeLabel(trainingType: string) {
  if (trainingType === "conditioning") {
    return "컨디셔닝";
  }
  if (trainingType === "pre_match") {
    return "프리매치";
  }
  if (trainingType === "recovery") {
    return "회복";
  }
  if (trainingType === "tactical") {
    return "전술";
  }
  if (trainingType === "tactical_physical") {
    return "전술+피지컬";
  }
  if (trainingType === "technical") {
    return "기술";
  }

  return trainingType;
}

function trainingTypeTone(trainingType: string) {
  if (trainingType === "conditioning" || trainingType === "tactical_physical") {
    return "table-badge table-badge--danger";
  }
  if (trainingType === "recovery") {
    return "table-badge table-badge--success";
  }
  if (trainingType === "pre_match") {
    return "table-badge table-badge--warning";
  }
  if (trainingType === "technical") {
    return "table-badge table-badge--practice";
  }
  if (trainingType === "tactical") {
    return "table-badge table-badge--official";
  }

  return "table-badge table-badge--neutral";
}

function intensityLabel(value: string | null) {
  if (value === "high" || value === "very_high") {
    return "high";
  }
  if (value === "medium") {
    return "medium";
  }
  if (value === "low") {
    return "low";
  }

  return "not set";
}

function intensityTone(value: string | null) {
  if (value === "high" || value === "very_high") {
    return "table-badge table-badge--danger";
  }
  if (value === "medium") {
    return "table-badge table-badge--warning";
  }
  if (value === "low") {
    return "table-badge table-badge--soft";
  }

  return "table-badge table-badge--neutral";
}

function matchTone(result: string) {
  if (result === "승") {
    return "table-badge table-badge--success";
  }
  if (result === "패") {
    return "table-badge table-badge--danger";
  }

  return "table-badge table-badge--warning";
}

function riskBandLabel(riskBand: string) {
  if (riskBand === "risk") {
    return "긴급";
  }
  if (riskBand === "watch") {
    return "집중 관리";
  }

  return "안정";
}

function riskBandTone(riskBand: string) {
  if (riskBand === "risk") {
    return "dashboard-chip dashboard-chip--danger";
  }
  if (riskBand === "watch") {
    return "dashboard-chip dashboard-chip--warning";
  }

  return "dashboard-chip dashboard-chip--good";
}

function readinessBandLabel(readinessBand: string) {
  if (readinessBand === "ready") {
    return "Ready";
  }
  if (readinessBand === "managed") {
    return "Managed";
  }

  return "Watch";
}

function readinessBandTone(readinessBand: string) {
  if (readinessBand === "ready") {
    return "dashboard-chip dashboard-chip--good";
  }
  if (readinessBand === "managed") {
    return "dashboard-chip dashboard-chip--warning";
  }

  return "dashboard-chip dashboard-chip--danger";
}

function growthBandLabel(growthBand: string) {
  if (growthBand === "rising") {
    return "상승";
  }
  if (growthBand === "stable") {
    return "유지";
  }

  return "관리 필요";
}

function growthBandTone(growthBand: string) {
  if (growthBand === "rising") {
    return "dashboard-chip dashboard-chip--good";
  }
  if (growthBand === "stable") {
    return "dashboard-chip";
  }

  return "dashboard-chip dashboard-chip--warning";
}

function eventTone(event: TeamCalendarEvent) {
  if (event.event_type === "match") {
    return event.category === "공식"
      ? "table-badge table-badge--official"
      : "table-badge table-badge--practice";
  }

  return intensityTone(event.intensity_level);
}

function eventLabel(event: TeamCalendarEvent) {
  if (event.event_type === "match") {
    return event.category === "공식" ? "공식전" : "연습경기";
  }

  return intensityLabel(event.intensity_level);
}

function buildEventHref(event: TeamCalendarEvent) {
  return event.event_type === "match"
    ? `/matches/${event.event_id}`
    : `/training/${event.event_id}`;
}

function buildTrainingTypeSummary(trainings: TeamTrainingListItem[]) {
  const total = trainings.length || 1;
  const counts = new Map<string, number>();

  trainings.forEach((training) => {
    const current = counts.get(training.training_type) ?? 0;
    counts.set(training.training_type, current + 1);
  });

  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || trainingTypeLabel(left[0]).localeCompare(trainingTypeLabel(right[0]), "ko-KR"))
    .map(([trainingType, count]) => ({
      trainingType,
      label: trainingTypeLabel(trainingType),
      count,
      share: (count / total) * 100,
    }));
}

function availabilityRate(item: PositionAvailabilityItem) {
  if (item.roster_count <= 0) {
    return 0;
  }

  return (item.available_count / item.roster_count) * 100;
}

function insightLabel(value: string) {
  if (value === "availability risk") {
    return "가용 인원 주의";
  }
  if (value === "high load") {
    return "부하 높음";
  }
  if (value === "form down") {
    return "폼 하락";
  }

  return "안정";
}

function insightTone(value: string) {
  if (value === "availability risk") {
    return "dashboard-chip dashboard-chip--danger";
  }
  if (value === "high load" || value === "form down") {
    return "dashboard-chip dashboard-chip--warning";
  }

  return "dashboard-chip dashboard-chip--good";
}

function signedMetricTone(value: number | null | undefined, positiveIsGood = true) {
  if (value == null || Number.isNaN(value)) {
    return "dashboard-chip";
  }

  const isPositive = value > 0;
  const isGood = positiveIsGood ? isPositive : value < 0;
  const isBad = positiveIsGood ? value < 0 : isPositive;

  if (isGood) {
    return "dashboard-chip dashboard-chip--good";
  }
  if (isBad) {
    return "dashboard-chip dashboard-chip--danger";
  }

  return "dashboard-chip";
}

function matchResult(goalsFor: number, goalsAgainst: number) {
  if (goalsFor > goalsAgainst) {
    return "승";
  }
  if (goalsFor < goalsAgainst) {
    return "패";
  }

  return "무";
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

function SectionSpotlight({
  eyebrow,
  title,
  description,
  primaryLabel,
  primaryValue,
  stats,
  notes = [],
  tone = "forest",
}: {
  eyebrow: string;
  title: string;
  description: string;
  primaryLabel: string;
  primaryValue: string;
  stats: Array<{ label: string; value: string }>;
  notes?: string[];
  tone?: "forest" | "sand" | "sage" | "ember";
}) {
  return (
    <section className={`dashboard-spotlight dashboard-spotlight--${tone}`}>
      <div className="dashboard-spotlight__body">
        <div>
          <p className="panel-eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        <p>{description}</p>
        {notes.length > 0 ? (
          <div className="dashboard-spotlight__notes">
            {notes.map((note) => (
              <span className="dashboard-spotlight__note" key={note}>
                {note}
              </span>
            ))}
          </div>
        ) : null}
      </div>

      <div className="dashboard-spotlight__aside">
        <div className="dashboard-spotlight__value">
          <span>{primaryLabel}</span>
          <strong>{primaryValue}</strong>
        </div>

        <div className="dashboard-spotlight__stats">
          {stats.map((item) => (
            <article className="dashboard-spotlight__stat" key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function MatchHighlightCard({
  title,
  item,
}: {
  title: string;
  item: TeamMatchFormItem | null;
}) {
  if (!item) {
    return (
      <article className="dashboard-match-highlight">
        <div className="dashboard-match-highlight__head">
          <span className="panel-eyebrow">{title}</span>
        </div>
        <strong>기록 없음</strong>
        <p>표시할 경기 데이터가 없습니다.</p>
      </article>
    );
  }

  const result = matchResult(item.goals_for, item.goals_against);

  return (
    <article className="dashboard-match-highlight">
      <div className="dashboard-match-highlight__head">
        <span className="panel-eyebrow">{title}</span>
        <span className={matchTone(result)}>{result}</span>
      </div>
      <strong>{item.opponent_team}</strong>
      <p>
        {formatDate(item.match_date)} · {item.match_type}
      </p>
      <div className="dashboard-match-highlight__score">
        <span>
          {item.goals_for} : {item.goals_against}
        </span>
        <strong>{formatMetric(item.team_average_match_score)}</strong>
      </div>
      <div className="meta-chip-row">
        <span className="meta-chip">평균 출전 {formatMetric(item.average_minutes, "분")}</span>
        <span className="meta-chip">
          효율 {item.efficiency_score == null ? "-" : formatMetric(item.efficiency_score)}
        </span>
      </div>
    </article>
  );
}

function OverviewAvailabilityPanel({
  overview,
}: {
  overview: TeamOverviewResponse;
}) {
  const positions = [...overview.availability.positions].sort(
    (left, right) =>
      right.managed_count +
        right.injured_count -
        (left.managed_count + left.injured_count) ||
      left.position.localeCompare(right.position, "ko-KR"),
  );

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Availability</p>
          <h3>포지션 가용성</h3>
        </div>
        <span className="dashboard-chip">
          가용 {overview.availability.available_count}명 / 관리 {overview.availability.managed_count}명
        </span>
      </div>

      <div className="dashboard-compact-list">
        {positions.slice(0, 5).map((item) => (
          <article className="dashboard-compact-row dashboard-compact-row--warning" key={item.position}>
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>{item.position}</strong>
                <span className="dashboard-chip">{item.roster_count}명 로스터</span>
              </div>
              <div className="bar-track" aria-hidden="true">
                <div
                  className="bar-fill"
                  style={{ width: `${Math.max(8, Math.min(100, availabilityRate(item)))}%` }}
                />
              </div>
              <div className="dashboard-compact-row__meta">
                <span className="meta-chip">가용 {item.available_count}명</span>
                <span className="meta-chip">관리 {item.managed_count}명</span>
                <span className="meta-chip">부상 {item.injured_count}명</span>
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>Availability</span>
              <strong>{formatMetric(availabilityRate(item), "%")}</strong>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function OverviewFormPanel({
  overview,
}: {
  overview: TeamOverviewResponse;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Form</p>
          <h3>경기 폼 하이라이트</h3>
        </div>
        <span className={signedMetricTone(overview.match_form.form_delta)}>
          최근 변화 {formatSigned(overview.match_form.form_delta)}
        </span>
      </div>

      <div className="dashboard-mini-stat-grid">
        <article className="dashboard-mini-stat">
          <span>최근 5경기</span>
          <strong>{formatMetric(overview.match_form.recent_5_match_score)}</strong>
        </article>
        <article className="dashboard-mini-stat">
          <span>직전 5경기</span>
          <strong>
            {overview.match_form.previous_5_match_score == null
              ? "-"
              : formatMetric(overview.match_form.previous_5_match_score)}
          </strong>
        </article>
        <article className="dashboard-mini-stat">
          <span>최신 경기</span>
          <strong>
            {overview.match_form.latest_match_score == null
              ? "-"
              : formatMetric(overview.match_form.latest_match_score)}
          </strong>
        </article>
      </div>

      <div className="dashboard-form-highlight-grid">
        <MatchHighlightCard item={overview.match_form.best_match} title="Season Best" />
        <MatchHighlightCard item={overview.match_form.worst_match} title="Season Low" />
      </div>
    </section>
  );
}

function OverviewPositionPanel({
  overview,
}: {
  overview: TeamOverviewResponse;
}) {
  const positions = [...overview.position_balance]
    .sort(
      (left, right) =>
        right.injured_count +
          right.managed_count -
          (left.injured_count + left.managed_count) ||
        (left.recent_form_score ?? 0) - (right.recent_form_score ?? 0),
    )
    .slice(0, 4);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Position Balance</p>
          <h3>운영 우선 포지션</h3>
        </div>
      </div>

      <div className="dashboard-position-focus-grid">
        {positions.map((item) => (
          <article className="dashboard-position-focus" key={item.position}>
            <div className="dashboard-position-focus__head">
              <div>
                <span>Position</span>
                <strong>{item.position}</strong>
              </div>
              <span className={insightTone(item.insight_label)}>{insightLabel(item.insight_label)}</span>
            </div>
            <div className="dashboard-position-focus__grid">
              <div>
                <span>폼</span>
                <strong>
                  {item.recent_form_score == null ? "-" : formatMetric(item.recent_form_score)}
                </strong>
              </div>
              <div>
                <span>출전</span>
                <strong>
                  {item.average_minutes == null ? "-" : formatMetric(item.average_minutes, "분")}
                </strong>
              </div>
              <div>
                <span>스프린트</span>
                <strong>
                  {item.average_sprint_count == null ? "-" : formatMetric(item.average_sprint_count)}
                </strong>
              </div>
              <div>
                <span>거리</span>
                <strong>
                  {item.average_total_distance == null
                    ? "-"
                    : formatMetric(item.average_total_distance, " km", 2)}
                </strong>
              </div>
            </div>
            <div className="dashboard-position-focus__footer">
              <span className={signedMetricTone(item.form_delta)}>
                폼 {formatSigned(item.form_delta)}
              </span>
              <span className="dashboard-chip">
                가용 {item.available_count} / 관리 {item.managed_count} / 부상 {item.injured_count}
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function OverviewSignalsPanel({
  overview,
}: {
  overview: TeamOverviewResponse;
}) {
  const injuryParts = overview.medical.injury_parts.slice(0, 3);
  const developmentPositions = [...overview.development.positions]
    .sort((left, right) => (right.average_form_delta ?? -999) - (left.average_form_delta ?? -999))
    .slice(0, 3);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Signals</p>
          <h3>메디컬·성장 포인트</h3>
        </div>
      </div>

      <div className="dashboard-mini-stat-grid">
        <article className="dashboard-mini-stat">
          <span>최근 180일 부상</span>
          <strong>{numberFormatter.format(overview.medical.injuries_last_180d)}건</strong>
        </article>
        <article className="dashboard-mini-stat">
          <span>현재 재활</span>
          <strong>{numberFormatter.format(overview.medical.current_rehab_count)}명</strong>
        </article>
        <article className="dashboard-mini-stat">
          <span>상승 선수</span>
          <strong>{numberFormatter.format(overview.development.rising_players_count)}명</strong>
        </article>
        <article className="dashboard-mini-stat">
          <span>관리 필요</span>
          <strong>{numberFormatter.format(overview.development.falling_players_count)}명</strong>
        </article>
      </div>

      <div className="dashboard-note-stack">
        {injuryParts.map((item) => (
          <article className="dashboard-note-card" key={item.injury_part}>
            <div className="dashboard-note-card__head">
              <strong>{item.injury_part}</strong>
              <span className="dashboard-chip dashboard-chip--warning">
                {numberFormatter.format(item.count)}건
              </span>
            </div>
            <p>최근 180일 기준 반복 확인된 부위입니다.</p>
          </article>
        ))}
        {developmentPositions.map((item) => (
          <article className="dashboard-note-card" key={item.position}>
            <div className="dashboard-note-card__head">
              <strong>{item.position}</strong>
              <span className={growthBandTone(item.growth_label)}>{growthBandLabel(item.growth_label)}</span>
            </div>
            <p>
              근육 {formatSigned(item.average_muscle_mass_delta, 2)}kg · 체지방{" "}
              {formatSigned(item.average_body_fat_delta, 1)}%p · 폼{" "}
              {formatSigned(item.average_form_delta)}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ScheduleEventsPanel({
  calendar,
}: {
  calendar: TeamCalendarResponse;
}) {
  if (calendar.events.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Calendar</p>
            <h3>이번 달 일정</h3>
          </div>
        </div>
        <EmptyPanel
          title="표시할 일정이 없습니다"
          description="선택된 월에는 경기 또는 훈련 이벤트가 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Calendar</p>
          <h3>{calendar.selected_label} 일정</h3>
        </div>
        <Link
          className="ghost-button"
          href={`/calendar?year=${calendar.selected_year}&month=${calendar.selected_month}`}
        >
          캘린더 보기
        </Link>
      </div>

      <div className="dashboard-compact-list">
        {calendar.events.slice(0, 5).map((event) => (
          <article className="dashboard-compact-row" key={event.event_id}>
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>{event.event_type === "match" ? event.opponent_team ?? event.title : event.title}</strong>
                <span className={eventTone(event)}>{eventLabel(event)}</span>
              </div>
              <p>
                {[
                  formatDate(event.event_date),
                  formatTimeRange(event.start_at, event.end_at),
                  event.location,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              <div className="dashboard-compact-row__meta">
                {event.event_type === "match" && event.score_for != null && event.score_against != null ? (
                  <span className="meta-chip">
                    결과 {event.score_for}:{event.score_against}
                  </span>
                ) : null}
                {event.category ? <span className="meta-chip">{event.category}</span> : null}
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>Date</span>
              <strong>{formatShortDate(event.event_date)}</strong>
              <Link className="table-action-link" href={buildEventHref(event)}>
                상세
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function MatchesPanel({
  matches,
}: {
  matches: TeamMatchListResponse;
}) {
  if (matches.matches.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Matches</p>
            <h3>최근 경기 결과</h3>
          </div>
        </div>
        <EmptyPanel
          title="경기 데이터가 없습니다"
          description="선택된 시즌에는 표시할 경기 결과가 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Matches</p>
          <h3>{matches.selected_year} 시즌 최근 경기</h3>
        </div>
        <Link className="ghost-button" href={`/matches?year=${matches.selected_year}`}>
          전체 경기
        </Link>
      </div>

      <div className="dashboard-compact-list">
        {matches.matches.slice(0, 4).map((match) => (
          <article className="dashboard-compact-row" key={match.match_id}>
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>{match.opponent_team}</strong>
                <span
                  className={
                    match.match_type === "공식"
                      ? "table-badge table-badge--official"
                      : "table-badge table-badge--practice"
                  }
                >
                  {match.match_type}
                </span>
              </div>
              <p>{formatDate(match.match_date)} · {match.stadium_name}</p>
              <div className="dashboard-compact-row__meta">
                <span className="meta-chip">평균 점수 {formatMetric(match.team_average_match_score)}</span>
                <span className="meta-chip">평균 출전 {formatMetric(match.average_minutes, "분")}</span>
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>{match.result}</span>
              <strong>
                {match.goals_for}:{match.goals_against}
              </strong>
              <Link className="table-action-link" href={`/matches/${match.match_id}`}>
                상세
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function LoadTrendPanel({
  overview,
}: {
  overview: TeamOverviewResponse;
}) {
  const points = [...overview.load.trend_points].slice(-8).reverse();
  const maxLoad = Math.max(...points.map((item) => item.total_load), 1);

  if (points.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Load Trend</p>
            <h3>최근 세션 load 흐름</h3>
          </div>
        </div>
        <EmptyPanel
          title="load 포인트가 없습니다"
          description="표시할 최근 훈련/경기 부하 데이터가 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Load Trend</p>
          <h3>최근 세션 부하 흐름</h3>
        </div>
      </div>

      <div className="dashboard-compact-list">
        {points.slice(0, 5).map((item) => (
          <article className="dashboard-compact-row" key={`${item.session_date}-${item.session_source}`}>
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>{formatDate(item.session_date)}</strong>
                <span className="dashboard-chip">
                  {item.session_source === "match" ? "경기" : "훈련"}
                </span>
              </div>
              <div className="bar-track" aria-hidden="true">
                <div className="bar-fill" style={{ width: `${Math.max(8, (item.total_load / maxLoad) * 100)}%` }} />
              </div>
              <div className="dashboard-compact-row__meta">
                <span className="meta-chip">스프린트 {numberFormatter.format(item.sprint_count)}회</span>
                <span className="meta-chip">거리 {compactDecimalFormatter.format(item.total_distance)} km</span>
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>Load</span>
              <strong>{numberFormatter.format(Math.round(item.total_load))}</strong>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function TrainingMixPanel({
  trainings,
}: {
  trainings: TeamTrainingListResponse;
}) {
  const typeSummary = buildTrainingTypeSummary(trainings.trainings).slice(0, 5);

  if (trainings.trainings.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Training Mix</p>
            <h3>훈련 구성</h3>
          </div>
        </div>
        <EmptyPanel
          title="훈련 구성 데이터가 없습니다"
          description="선택된 시즌에는 표시할 훈련 세션이 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Training Mix</p>
          <h3>훈련 강도·유형 분포</h3>
        </div>
        <Link className="ghost-button" href={`/training?year=${trainings.selected_year}`}>
          전체 훈련
        </Link>
      </div>

      <div className="dashboard-mini-stat-grid">
        <article className="dashboard-mini-stat">
          <span>HIGH</span>
          <strong>{numberFormatter.format(trainings.summary.high_intensity_count)}회</strong>
          <p>{formatPercent((trainings.summary.high_intensity_count / Math.max(trainings.summary.training_count, 1)) * 100)}</p>
        </article>
        <article className="dashboard-mini-stat">
          <span>MEDIUM</span>
          <strong>{numberFormatter.format(trainings.summary.medium_intensity_count)}회</strong>
          <p>{formatPercent((trainings.summary.medium_intensity_count / Math.max(trainings.summary.training_count, 1)) * 100)}</p>
        </article>
        <article className="dashboard-mini-stat">
          <span>LOW</span>
          <strong>{numberFormatter.format(trainings.summary.low_intensity_count)}회</strong>
          <p>{formatPercent((trainings.summary.low_intensity_count / Math.max(trainings.summary.training_count, 1)) * 100)}</p>
        </article>
        <article className="dashboard-mini-stat">
          <span>AVG</span>
          <strong>{formatMetric(trainings.summary.average_total_distance, " km", 2)}</strong>
          <p>평균 세션 거리</p>
        </article>
      </div>

      <div className="dashboard-share-list">
        {typeSummary.map((item) => (
          <article className="dashboard-share-item" key={item.trainingType}>
            <div className="dashboard-share-item__head">
              <strong>{item.label}</strong>
              <span className={trainingTypeTone(item.trainingType)}>{numberFormatter.format(item.count)}회</span>
            </div>
            <div className="dashboard-share-item__bar" aria-hidden="true">
              <div
                className={item.share >= 20 ? "dashboard-share-item__fill dashboard-share-item__fill--strong" : "dashboard-share-item__fill"}
                style={{ width: `${Math.max(8, Math.min(100, item.share))}%` }}
              />
            </div>
            <p>전체 훈련 중 {decimalFormatter.format(item.share)}% 비중</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function TrainingsPanel({
  trainings,
}: {
  trainings: TeamTrainingListResponse;
}) {
  if (trainings.trainings.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Trainings</p>
            <h3>최근 훈련 세션</h3>
          </div>
        </div>
        <EmptyPanel
          title="훈련 세션이 없습니다"
          description="선택된 시즌에는 표시할 훈련 세션이 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Trainings</p>
          <h3>{trainings.selected_year} 시즌 최근 훈련</h3>
        </div>
      </div>

      <div className="dashboard-compact-list">
        {trainings.trainings.slice(0, 4).map((training) => (
          <article className="dashboard-compact-row" key={training.training_id}>
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>{training.session_name}</strong>
                <span className={intensityTone(training.intensity_level)}>
                  {intensityLabel(training.intensity_level)}
                </span>
              </div>
              <p>
                {[
                  formatDate(training.training_date),
                  formatTimeRange(training.start_at, training.end_at),
                  training.location,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              <div className="dashboard-compact-row__meta">
                <span className={trainingTypeTone(training.training_type)}>
                  {trainingTypeLabel(training.training_type)}
                </span>
                <span className="meta-chip">거리 {formatMetric(training.total_distance, " km", 2)}</span>
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>인원</span>
              <strong>
                {training.participant_count == null
                  ? "-"
                  : `${numberFormatter.format(training.participant_count)}명`}
              </strong>
              <Link className="table-action-link" href={`/training/${training.training_id}`}>
                상세
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function RiskWatchPanel({
  items,
}: {
  items: PlayerInjuryRiskItem[];
}) {
  if (items.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Medical Risk</p>
            <h3>리스크 워치리스트</h3>
          </div>
          <Link className="ghost-button" href="/injury">
            메디컬 페이지
          </Link>
        </div>
        <EmptyPanel
          title="리스크 워치 대상이 없습니다"
          description="현재 기준으로 표시할 부상 리스크 선수가 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Medical Risk</p>
          <h3>리스크 워치리스트</h3>
        </div>
        <Link className="ghost-button" href="/injury">
          메디컬 페이지
        </Link>
      </div>

      <div className="dashboard-compact-list">
        {items.slice(0, 4).map((item) => (
          <article
            className={`dashboard-compact-row ${
              item.risk_band === "risk"
                ? "dashboard-compact-row--danger"
                : item.risk_band === "watch"
                  ? "dashboard-compact-row--warning"
                  : ""
            }`}
            key={item.player_id}
          >
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>
                  {item.name} · {item.primary_position}
                </strong>
                <span className="dashboard-chip">{riskBandLabel(item.risk_band)}</span>
              </div>
              <p>{item.reasons[0] ?? "최근 위험 신호를 확인하세요."}</p>
              <div className="dashboard-compact-row__meta">
                <span className="meta-chip">ACWR {formatMetric(item.factors.acute_chronic_ratio, "x", 2)}</span>
                <span className="meta-chip">스프린트 {numberFormatter.format(item.factors.sprint_count_7d)}회</span>
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>Risk</span>
              <strong>{formatMetric(item.overall_risk_score)}</strong>
              <span className="dashboard-chip">
                최근 부상 {numberFormatter.format(item.factors.injuries_last_180d)}건
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ReadinessPanel({
  items,
}: {
  items: PlayerPerformanceReadinessItem[];
}) {
  if (items.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Readiness</p>
            <h3>출전 준비도 상위</h3>
          </div>
        </div>
        <EmptyPanel
          title="준비도 데이터가 없습니다"
          description="현재 기준으로 표시할 readiness 데이터가 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Readiness</p>
          <h3>출전 준비도 상위</h3>
        </div>
      </div>

      <div className="dashboard-compact-list">
        {items.slice(0, 4).map((item) => (
          <article
            className={`dashboard-compact-row ${
              item.readiness_band === "ready"
                ? "dashboard-compact-row--good"
                : item.readiness_band === "managed"
                  ? "dashboard-compact-row--warning"
                  : "dashboard-compact-row--danger"
            }`}
            key={item.player_id}
          >
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>
                  {item.name} · {item.primary_position}
                </strong>
                <span className="dashboard-chip">{readinessBandLabel(item.readiness_band)}</span>
              </div>
              <p>{item.reasons[0] ?? "최근 경기·평가·멘탈 지표를 함께 확인하세요."}</p>
              <div className="dashboard-compact-row__meta">
                <span className="meta-chip">폼 {decimalFormatter.format(item.factors.match_form_score)}</span>
                <span className="meta-chip">평가 {decimalFormatter.format(item.factors.evaluation_score)}</span>
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>Ready</span>
              <strong>{formatMetric(item.readiness_score)}</strong>
              <span className="dashboard-chip">
                멘탈 {decimalFormatter.format(item.factors.mental_readiness_score)}
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function GrowthPanel({
  items,
}: {
  items: PlayerDevelopmentReportItem[];
}) {
  if (items.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Growth</p>
            <h3>성장 지표 상위</h3>
          </div>
        </div>
        <EmptyPanel
          title="성장 데이터가 없습니다"
          description="현재 기준으로 표시할 성장 리포트가 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Growth</p>
          <h3>성장 지표 상위</h3>
        </div>
      </div>

      <div className="dashboard-compact-list">
        {items.slice(0, 4).map((item) => (
          <article
            className={`dashboard-compact-row ${
              item.growth_band === "rising"
                ? "dashboard-compact-row--good"
                : item.growth_band === "stable"
                  ? ""
                  : "dashboard-compact-row--warning"
            }`}
            key={item.player_id}
          >
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>
                  {item.name} · {item.primary_position}
                </strong>
                <span className="dashboard-chip">{growthBandLabel(item.growth_band)}</span>
              </div>
              <p>{item.reasons[0] ?? "최근 피지컬·폼·평가 변화 흐름을 확인하세요."}</p>
              <div className="dashboard-compact-row__meta">
                <span className="meta-chip">근육 {formatMetric(item.factors.muscle_mass_delta, "kg", 2)}</span>
                <span className="meta-chip">체지방 {formatMetric(item.factors.body_fat_delta, "%p", 2)}</span>
              </div>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>Growth</span>
              <strong>{formatMetric(item.growth_score)}</strong>
              <span className="dashboard-chip">폼 {formatSigned(item.factors.form_delta, 1)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function InjuryHistoryPanel({
  report,
}: {
  report: PlayerInjuryRiskResponse;
}) {
  if (report.recent_history.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Injury History</p>
            <h3>최근 부상 히스토리</h3>
          </div>
        </div>
        <EmptyPanel
          title="부상 히스토리가 없습니다"
          description="현재 기준으로 표시할 최근 부상 기록이 없습니다."
        />
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">Injury History</p>
          <h3>최근 부상 히스토리</h3>
        </div>
      </div>

      <div className="dashboard-compact-list">
        {report.recent_history.slice(0, 4).map((item) => (
          <article className="dashboard-compact-row" key={item.injury_id}>
            <div className="dashboard-compact-row__main">
              <div className="dashboard-compact-row__head">
                <strong>
                  {item.name} · {item.primary_position}
                </strong>
                <span className="dashboard-chip dashboard-chip--warning">
                  {item.severity_level ?? "미지정"}
                </span>
              </div>
              <p>{formatDate(item.injury_date)} · {[item.injury_part, item.injury_type].filter(Boolean).join(" · ") || "-"}</p>
            </div>
            <div className="dashboard-compact-row__metric">
              <span>Return</span>
              <strong>
                {item.actual_return_date
                  ? formatShortDate(item.actual_return_date)
                  : item.expected_return_date
                    ? formatShortDate(item.expected_return_date)
                    : "-"}
              </strong>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function TeamDashboardWorkspace({
  overview,
  calendar,
  matches,
  trainings,
  injuryRisk,
  readiness,
  development,
}: {
  overview: TeamOverviewResponse;
  calendar: TeamCalendarResponse;
  matches: TeamMatchListResponse;
  trainings: TeamTrainingListResponse;
  injuryRisk: PlayerInjuryRiskResponse;
  readiness: PlayerPerformanceReadinessResponse;
  development: PlayerDevelopmentReportResponse;
}) {
  return (
    <div className="dashboard-workspace">
      <section className="dashboard-grid dashboard-grid--triple">
        <MatchesPanel matches={matches} />
        <TrainingsPanel trainings={trainings} />
        <LoadTrendPanel overview={overview} />
      </section>
    </div>
  );
}
