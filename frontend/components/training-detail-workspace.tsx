import Link from "next/link";

import type {
  TeamTrainingDetailPlayerStat,
  TeamTrainingDetailResponse,
} from "@/lib/team-api-types";

const compactFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});
const dateFormatter = new Intl.DateTimeFormat("ko-KR", {
  year: "numeric",
  month: "short",
  day: "numeric",
  weekday: "short",
});
const timeFormatter = new Intl.DateTimeFormat("ko-KR", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const trainingDetailViews = [
  { key: "session", label: "세션 내용" },
  { key: "gps", label: "GPS 데이터" },
] as const;

type TrainingDetailViewKey = (typeof trainingDetailViews)[number]["key"];

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

function hasText(value: string | null | undefined): value is string {
  return Boolean(value && value.trim().length > 0);
}

function intensityLabel(value: string | null) {
  if (value === "very_high") {
    return "high";
  }
  if (value === "high") {
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

function intensityTone(value: string | null) {
  if (value === "very_high") {
    return "table-badge table-badge--danger";
  }
  if (value === "high") {
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

function formatTimeRange(startAt: string | null, endAt: string | null) {
  if (!startAt) {
    return "시간 미정";
  }

  const start = timeFormatter.format(new Date(startAt));
  if (!endAt) {
    return start;
  }

  return `${start} - ${timeFormatter.format(new Date(endAt))}`;
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

function GpsTable({ players }: { players: TeamTrainingDetailPlayerStat[] }) {
  if (players.length === 0) {
    return (
      <div className="empty-state">
        <strong>GPS 데이터 없음</strong>
        <p>선수별 훈련 GPS 기록이 아직 연결되지 않았습니다.</p>
      </div>
    );
  }

  const sortedPlayers = [...players].sort((left, right) => {
    return (
      compareNullableNumber(right.total_distance, left.total_distance) ||
      compareNullableNumber(right.sprint_count, left.sprint_count) ||
      compareNullableNumber(right.play_time_min, left.play_time_min) ||
      compareNullableNumber(left.jersey_number, right.jersey_number) ||
      compareText(left.name, right.name)
    );
  });

  return (
    <div className="table-scroll table-scroll--match-detail">
      <table className="data-table data-table--training-detail-gps">
        <thead>
          <tr>
            <th><div className="match-detail-static-header-group"><span>No.</span></div></th>
            <th><div className="match-detail-static-header-group"><span>선수</span></div></th>
            <th><div className="match-detail-static-header-group"><span>GPS 시간</span></div></th>
            <th><div className="match-detail-static-header-group"><span>총 거리</span></div></th>
            <th><div className="match-detail-static-header-group"><span>평균속도</span></div></th>
            <th><div className="match-detail-static-header-group"><span>최고속도</span></div></th>
            <th><div className="match-detail-static-header-group"><span>스프린트</span></div></th>
            <th><div className="match-detail-static-header-group"><span>스프린트 거리</span></div></th>
            <th><div className="match-detail-static-header-group"><span>가속</span></div></th>
            <th><div className="match-detail-static-header-group"><span>감속</span></div></th>
            <th><div className="match-detail-static-header-group"><span>고강도 가속</span></div></th>
            <th><div className="match-detail-static-header-group"><span>고강도 감속</span></div></th>
            <th><div className="match-detail-static-header-group"><span>방향전환</span></div></th>
            <th><div className="match-detail-static-header-group"><span>0-15분</span></div></th>
            <th><div className="match-detail-static-header-group"><span>15-30분</span></div></th>
            <th><div className="match-detail-static-header-group"><span>30-45분</span></div></th>
            <th><div className="match-detail-static-header-group"><span>45-60분</span></div></th>
            <th><div className="match-detail-static-header-group"><span>60-75분</span></div></th>
            <th><div className="match-detail-static-header-group"><span>75-90분</span></div></th>
            <th><div className="match-detail-static-header-group"><span>0-5 km/h</span></div></th>
            <th><div className="match-detail-static-header-group"><span>5-10 km/h</span></div></th>
            <th><div className="match-detail-static-header-group"><span>10-15 km/h</span></div></th>
            <th><div className="match-detail-static-header-group"><span>15-20 km/h</span></div></th>
            <th><div className="match-detail-static-header-group"><span>20-25 km/h</span></div></th>
            <th><div className="match-detail-static-header-group"><span>25+ km/h</span></div></th>
          </tr>
        </thead>
        <tbody>
          {sortedPlayers.map((player) => (
            <tr key={player.training_gps_id}>
              <td>{player.jersey_number}</td>
              <td>
                <div className="match-detail-player-cell">
                  <Link className="table-action-link" href={`/players/${player.player_id}`}>
                    {player.name}
                  </Link>
                  <span>{player.position}</span>
                </div>
              </td>
              <td>{formatInteger(player.play_time_min, "분")}</td>
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SessionOverviewSection({ data }: { data: TeamTrainingDetailResponse }) {
  const overviewSections = [
    hasText(data.training.training_focus)
      ? {
          label: "훈련 목표",
          body: data.training.training_focus,
        }
      : null,
    hasText(data.training.training_detail)
      ? {
          label: "훈련 내용",
          body: data.training.training_detail,
        }
      : null,
  ].filter((section): section is { label: string; body: string } => section !== null);

  if (overviewSections.length === 0) {
    overviewSections.push({
      label: "훈련 개요",
      body: `${data.training.session_name} · ${trainingTypeLabel(data.training.training_type)}`,
    });
  }

  const noteText = hasText(data.training.notes) ? data.training.notes : null;

  return (
    <section className="panel panel--tight">
      <div className="panel-header match-detail-section-head">
        <div>
          <h2>훈련 개요</h2>
        </div>
      </div>

      <div className={noteText ? "training-detail-overview" : "training-detail-overview training-detail-overview--single"}>
        <article className="training-detail-overview-card training-detail-overview-card--primary">
          <div className="training-detail-overview-card__header">
            <strong>{trainingTypeLabel(data.training.training_type)}</strong>
          </div>

          <div className="training-detail-overview-stack">
            {overviewSections.map((section, index) => (
              <div className="training-detail-overview-section" key={section.label}>
                {index > 0 ? <div className="training-detail-overview-divider" aria-hidden="true" /> : null}
                <span>{section.label}</span>
                <p>{section.body}</p>
              </div>
            ))}
          </div>
        </article>

        {noteText ? (
          <aside className="training-detail-overview-card training-detail-overview-card--note">
            <div className="training-detail-overview-card__header">
              <span>현장 메모</span>
            </div>
            <p>{noteText}</p>
          </aside>
        ) : null}
      </div>
    </section>
  );
}

function SessionDataPanel({ data }: { data: TeamTrainingDetailResponse }) {
  const sessionCards = [
    { label: "훈련 일자", value: dateFormatter.format(new Date(`${data.training.training_date}T00:00:00`)) },
    { label: "세션 시간", value: formatTimeRange(data.training.start_at, data.training.end_at) },
    { label: "훈련 유형", value: trainingTypeLabel(data.training.training_type) },
    { label: "훈련 목적", value: data.training.training_focus ?? "-" },
    { label: "담당 코치", value: data.training.coach_name ?? "-" },
    { label: "장소", value: data.training.location ?? "-" },
    { label: "참여 인원", value: formatInteger(data.summary.participant_count, "명") },
    { label: "훈련 ID", value: data.training.training_id },
  ];

  return (
    <div className="match-detail-tab-panel">
      <SessionOverviewSection data={data} />

      <section className="panel panel--tight">
        <div className="panel-header match-detail-section-head">
          <div>
            <h2>세션 데이터</h2>
          </div>
        </div>

        <div className="match-detail-data-grid">
          {sessionCards.map((card) => (
            <article className="match-detail-data-card" key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function GpsDataPanel({ data }: { data: TeamTrainingDetailResponse }) {
  const gpsCards = [
    { label: "총 거리", value: formatValue(data.summary.total_distance, " km") },
    { label: "평균 거리", value: formatValue(data.summary.average_distance, " km") },
    { label: "총 스프린트", value: formatInteger(data.summary.total_sprint_count, "회") },
    { label: "평균 최고속도", value: formatValue(data.summary.average_max_speed, " km/h") },
    { label: "평균 속도", value: formatValue(data.summary.average_avg_speed, " km/h") },
    { label: "총 가속", value: formatInteger(data.summary.total_accel_count, "회") },
    { label: "총 감속", value: formatInteger(data.summary.total_decel_count, "회") },
    { label: "총 COD", value: formatInteger(data.summary.total_cod_count, "회") },
  ];

  return (
    <div className="match-detail-tab-panel">
      <section className="panel panel--tight">
        <div className="panel-header match-detail-section-head">
          <div>
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
            <h2>선수별 GPS 기록</h2>
          </div>
        </div>

        <GpsTable players={data.players} />
      </section>
    </div>
  );
}

export function TrainingDetailWorkspace({
  data,
  backHref,
  backLabel,
  activeView,
  tabHrefs,
}: {
  data: TeamTrainingDetailResponse;
  backHref: string;
  backLabel?: string;
  activeView: TrainingDetailViewKey;
  tabHrefs: Record<TrainingDetailViewKey, string>;
}) {
  const metricStrip = [
    { label: "총 거리", value: formatValue(data.summary.total_distance, " km") },
    { label: "총 스프린트", value: formatInteger(data.summary.total_sprint_count, "회") },
    { label: "평균 속도", value: formatValue(data.summary.average_avg_speed, " km/h") },
    { label: "평균 최고속도", value: formatValue(data.summary.average_max_speed, " km/h") },
    { label: "총 가속", value: formatInteger(data.summary.total_accel_count, "회") },
  ];

  return (
    <main className="page match-detail-workspace training-detail-workspace">
      <section className="match-detail-header-card">
        <div className="match-detail-commandbar">
          <Link className="secondary-button match-detail-back-link" href={backHref}>
            {backLabel ?? "목록으로"}
          </Link>
          <div className="match-detail-commandbar__meta">
            <span className="match-detail-commandbar__id">{data.training.training_id}</span>
            <span className="meta-chip">{trainingTypeLabel(data.training.training_type)}</span>
            <span className={intensityTone(data.training.intensity_level)}>
              {intensityLabel(data.training.intensity_level)}
            </span>
          </div>
        </div>

        <div className="match-detail-header-main">
          <div className="match-detail-header-main__title">
            <h1>{data.training.session_name}</h1>
            <div className="match-detail-header-main__meta">
              <span>{dateFormatter.format(new Date(`${data.training.training_date}T00:00:00`))}</span>
              <span>{formatTimeRange(data.training.start_at, data.training.end_at)}</span>
              <span>{data.training.location ?? "장소 미기록"}</span>
              <span>{`참여 인원 ${formatInteger(data.summary.participant_count, "명")}`}</span>
            </div>
          </div>

          <div className="match-detail-score-panel">
            <span className="match-detail-score-panel__label">{intensityLabel(data.training.intensity_level)}</span>
            <strong>{`${data.summary.participant_count}명`}</strong>
          </div>
        </div>

        <div className="match-detail-metric-strip">
          {metricStrip.map((metric) => (
            <article className="match-detail-metric" key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <nav className="match-detail-tab-nav" aria-label="Training detail views">
        {trainingDetailViews.map((view) => (
          <Link
            aria-current={view.key === activeView ? "page" : undefined}
            className={view.key === activeView ? "match-detail-tab match-detail-tab--active" : "match-detail-tab"}
            href={tabHrefs[view.key]}
            key={view.key}
          >
            <strong>{view.label}</strong>
          </Link>
        ))}
      </nav>

      {activeView === "session" ? <SessionDataPanel data={data} /> : null}
      {activeView === "gps" ? <GpsDataPanel data={data} /> : null}
    </main>
  );
}
