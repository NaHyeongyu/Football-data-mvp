import { DataPageError } from "@/components/data-page-error";
import { EnergyTrendChart } from "@/components/energy-trend-chart";
import { PhysicalTestsBoard } from "@/components/physical-tests-board";
import { PhysicalTabsShell } from "@/components/physical-tabs-shell";
import { formatCompactDate } from "@/lib/dashboard-formatters";
import {
  getPhysicalOverviewData,
  getPhysicalOverviewEndpoint,
} from "@/lib/data-store";
import { getTeamTrainingDetail, getTeamTrainings } from "@/lib/team-api";
import type { TeamMatchTrendItem } from "@/lib/data-types";

export const dynamic = "force-dynamic";

const oneDecimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});

const twoDecimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 2,
});

const shortDateFormatter = new Intl.DateTimeFormat("ko-KR", {
  month: "numeric",
  day: "numeric",
});

type DerivedEnergyMatch = TeamMatchTrendItem & {
  energy_score: number;
  energy_delta_pct: number;
  energy_label: string;
  energy_class_name: string;
  load_delta_pct: number;
  high_speed_delta_pct: number;
  sprint_delta_pct: number;
  distance_delta_pct: number;
  avg_max_speed_delta_pct: number;
};

type TrainingEnergySession = {
  training_id: string;
  training_date: string;
  session_name: string;
  training_type: string;
  intensity_level: string | null;
  coach_name: string | null;
  location: string | null;
  participant_count: number;
  session_duration_min: number;
  total_distance: number;
  average_distance: number;
  total_sprint_count: number;
  explosive_action_count: number;
  average_max_speed: number;
  intensity_score: number;
};

type DerivedEnergyTraining = TrainingEnergySession & {
  energy_score: number;
  energy_delta_pct: number;
  energy_label: string;
  energy_class_name: string;
  total_distance_delta_pct: number;
  average_distance_delta_pct: number;
  sprint_delta_pct: number;
  explosive_action_delta_pct: number;
  average_max_speed_delta_pct: number;
  intensity_delta_pct: number;
};

type EnergyChartItem = {
  id: string;
  label: string;
  score: number;
};

const MATCH_ENERGY_SCORE_WEIGHTS = {
  distance_total_p90: 0.2,
  high_speed_m_p90: 0.3,
  sprint_count_p90: 0.2,
  player_load_p90: 0.3,
} as const;

const TRAINING_ENERGY_SCORE_WEIGHTS = {
  total_distance: 0.25,
  average_distance: 0.25,
  total_sprint_count: 0.2,
  explosive_action_count: 0.15,
  intensity: 0.15,
} as const;

function average(values: number[]) {
  const validValues = values.filter((value) => Number.isFinite(value));
  if (validValues.length === 0) {
    return 0;
  }

  return validValues.reduce((sum, value) => sum + value, 0) / validValues.length;
}

function percentageDelta(value: number, baseline: number) {
  if (!Number.isFinite(value) || !Number.isFinite(baseline) || baseline === 0) {
    return 0;
  }

  return ((value - baseline) / baseline) * 100;
}

function formatSignedPercent(value: number, digits = 1) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

function formatSignedPoints(value: number, digits = 1) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}점`;
}

function formatShortDateLabel(value: string) {
  return shortDateFormatter.format(new Date(`${value}T00:00:00`));
}

function normalizedScore(value: number, min: number, max: number) {
  if (!Number.isFinite(value)) {
    return 0;
  }

  if (max <= min) {
    return 50;
  }

  const normalized = ((value - min) / (max - min)) * 100;
  return Math.max(0, Math.min(100, normalized));
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

function trainingIntensityLabel(value: string | null) {
  if (value === "very_high" || value === "high") {
    return "고강도";
  }
  if (value === "medium") {
    return "중강도";
  }
  if (value === "low") {
    return "저강도";
  }

  return "강도 미기록";
}

function trainingIntensityScore(value: string | null) {
  if (value === "very_high") {
    return 95;
  }
  if (value === "high") {
    return 82;
  }
  if (value === "medium") {
    return 64;
  }
  if (value === "low") {
    return 42;
  }

  return 55;
}

async function loadTrainingEnergySessions(year: number) {
  const trainingData = await getTeamTrainings({ year });
  const trainingWindow = trainingData.trainings.slice(0, 12);
  const detailResults = await Promise.allSettled(
    trainingWindow.map((training) => getTeamTrainingDetail(training.training_id)),
  );

  const sessions = detailResults.flatMap<TrainingEnergySession>((result) => {
    if (result.status !== "fulfilled") {
      return [];
    }

    const detail = result.value;
    const summary = detail.summary;

    return [
      {
        training_id: detail.training.training_id,
        training_date: detail.training.training_date,
        session_name: detail.training.session_name,
        training_type: detail.training.training_type,
        intensity_level: detail.training.intensity_level,
        coach_name: detail.training.coach_name,
        location: detail.training.location,
        participant_count: summary.participant_count,
        session_duration_min: summary.session_duration_min ?? 0,
        total_distance: summary.total_distance ?? 0,
        average_distance: summary.average_distance ?? 0,
        total_sprint_count: summary.total_sprint_count,
        explosive_action_count:
          summary.total_hi_accel_count + summary.total_hi_decel_count + summary.total_cod_count,
        average_max_speed: summary.average_max_speed ?? 0,
        intensity_score: trainingIntensityScore(detail.training.intensity_level),
      },
    ];
  });

  return {
    trainingData,
    sessions,
  };
}

function buildEnergyMatches(items: TeamMatchTrendItem[]) {
  if (items.length === 0) {
    return [] satisfies DerivedEnergyMatch[];
  }

  const distanceAverage = average(items.map((item) => item.distance_total_p90));
  const highSpeedAverage = average(items.map((item) => item.high_speed_m_p90));
  const sprintAverage = average(items.map((item) => item.sprint_count_p90));
  const loadAverage = average(items.map((item) => item.player_load_p90));
  const maxSpeedAverage = average(items.map((item) => item.avg_max_speed_kmh));
  const distanceMin = Math.min(...items.map((item) => item.distance_total_p90));
  const distanceMax = Math.max(...items.map((item) => item.distance_total_p90));
  const highSpeedMin = Math.min(...items.map((item) => item.high_speed_m_p90));
  const highSpeedMax = Math.max(...items.map((item) => item.high_speed_m_p90));
  const sprintMin = Math.min(...items.map((item) => item.sprint_count_p90));
  const sprintMax = Math.max(...items.map((item) => item.sprint_count_p90));
  const loadMin = Math.min(...items.map((item) => item.player_load_p90));
  const loadMax = Math.max(...items.map((item) => item.player_load_p90));

  return items.map<DerivedEnergyMatch>((item) => {
    const energyScore =
      normalizedScore(item.distance_total_p90, distanceMin, distanceMax) *
        MATCH_ENERGY_SCORE_WEIGHTS.distance_total_p90 +
      normalizedScore(item.high_speed_m_p90, highSpeedMin, highSpeedMax) *
        MATCH_ENERGY_SCORE_WEIGHTS.high_speed_m_p90 +
      normalizedScore(item.sprint_count_p90, sprintMin, sprintMax) *
        MATCH_ENERGY_SCORE_WEIGHTS.sprint_count_p90 +
      normalizedScore(item.player_load_p90, loadMin, loadMax) * MATCH_ENERGY_SCORE_WEIGHTS.player_load_p90;

    const energyDeltaPct =
      percentageDelta(item.distance_total_p90, distanceAverage) * MATCH_ENERGY_SCORE_WEIGHTS.distance_total_p90 +
      percentageDelta(item.high_speed_m_p90, highSpeedAverage) * MATCH_ENERGY_SCORE_WEIGHTS.high_speed_m_p90 +
      percentageDelta(item.sprint_count_p90, sprintAverage) * MATCH_ENERGY_SCORE_WEIGHTS.sprint_count_p90 +
      percentageDelta(item.player_load_p90, loadAverage) * MATCH_ENERGY_SCORE_WEIGHTS.player_load_p90;

    let energyLabel = "안정";
    let energyClassName = "metric-inline-badge metric-inline-badge--neutral";

    if (energyDeltaPct >= 5) {
      energyLabel = "상승";
      energyClassName = "metric-inline-badge metric-inline-badge--strong";
    } else if (energyDeltaPct <= -5) {
      energyLabel = "하강";
      energyClassName = "metric-inline-badge metric-inline-badge--warning";
    }

    return {
      ...item,
      energy_score: energyScore,
      energy_delta_pct: energyDeltaPct,
      energy_label: energyLabel,
      energy_class_name: energyClassName,
      load_delta_pct: percentageDelta(item.player_load_p90, loadAverage),
      high_speed_delta_pct: percentageDelta(item.high_speed_m_p90, highSpeedAverage),
      sprint_delta_pct: percentageDelta(item.sprint_count_p90, sprintAverage),
      distance_delta_pct: percentageDelta(item.distance_total_p90, distanceAverage),
      avg_max_speed_delta_pct: percentageDelta(item.avg_max_speed_kmh, maxSpeedAverage),
    };
  });
}

function buildEnergyTrainings(items: TrainingEnergySession[]) {
  if (items.length === 0) {
    return [] satisfies DerivedEnergyTraining[];
  }

  const totalDistanceAverage = average(items.map((item) => item.total_distance));
  const averageDistanceAverage = average(items.map((item) => item.average_distance));
  const sprintAverage = average(items.map((item) => item.total_sprint_count));
  const explosiveActionAverage = average(items.map((item) => item.explosive_action_count));
  const maxSpeedAverage = average(items.map((item) => item.average_max_speed));
  const intensityAverage = average(items.map((item) => item.intensity_score));
  const totalDistanceMin = Math.min(...items.map((item) => item.total_distance));
  const totalDistanceMax = Math.max(...items.map((item) => item.total_distance));
  const averageDistanceMin = Math.min(...items.map((item) => item.average_distance));
  const averageDistanceMax = Math.max(...items.map((item) => item.average_distance));
  const sprintMin = Math.min(...items.map((item) => item.total_sprint_count));
  const sprintMax = Math.max(...items.map((item) => item.total_sprint_count));
  const explosiveActionMin = Math.min(...items.map((item) => item.explosive_action_count));
  const explosiveActionMax = Math.max(...items.map((item) => item.explosive_action_count));

  return items.map<DerivedEnergyTraining>((item) => {
    const energyScore =
      normalizedScore(item.total_distance, totalDistanceMin, totalDistanceMax) *
        TRAINING_ENERGY_SCORE_WEIGHTS.total_distance +
      normalizedScore(item.average_distance, averageDistanceMin, averageDistanceMax) *
        TRAINING_ENERGY_SCORE_WEIGHTS.average_distance +
      normalizedScore(item.total_sprint_count, sprintMin, sprintMax) *
        TRAINING_ENERGY_SCORE_WEIGHTS.total_sprint_count +
      normalizedScore(item.explosive_action_count, explosiveActionMin, explosiveActionMax) *
        TRAINING_ENERGY_SCORE_WEIGHTS.explosive_action_count +
      item.intensity_score * TRAINING_ENERGY_SCORE_WEIGHTS.intensity;

    const energyDeltaPct =
      percentageDelta(item.total_distance, totalDistanceAverage) * TRAINING_ENERGY_SCORE_WEIGHTS.total_distance +
      percentageDelta(item.average_distance, averageDistanceAverage) *
        TRAINING_ENERGY_SCORE_WEIGHTS.average_distance +
      percentageDelta(item.total_sprint_count, sprintAverage) *
        TRAINING_ENERGY_SCORE_WEIGHTS.total_sprint_count +
      percentageDelta(item.explosive_action_count, explosiveActionAverage) *
        TRAINING_ENERGY_SCORE_WEIGHTS.explosive_action_count +
      percentageDelta(item.intensity_score, intensityAverage) * TRAINING_ENERGY_SCORE_WEIGHTS.intensity;

    let energyLabel = "안정";
    let energyClassName = "metric-inline-badge metric-inline-badge--neutral";

    if (energyDeltaPct >= 5) {
      energyLabel = "상승";
      energyClassName = "metric-inline-badge metric-inline-badge--strong";
    } else if (energyDeltaPct <= -5) {
      energyLabel = "하강";
      energyClassName = "metric-inline-badge metric-inline-badge--warning";
    }

    return {
      ...item,
      energy_score: energyScore,
      energy_delta_pct: energyDeltaPct,
      energy_label: energyLabel,
      energy_class_name: energyClassName,
      total_distance_delta_pct: percentageDelta(item.total_distance, totalDistanceAverage),
      average_distance_delta_pct: percentageDelta(item.average_distance, averageDistanceAverage),
      sprint_delta_pct: percentageDelta(item.total_sprint_count, sprintAverage),
      explosive_action_delta_pct: percentageDelta(item.explosive_action_count, explosiveActionAverage),
      average_max_speed_delta_pct: percentageDelta(item.average_max_speed, maxSpeedAverage),
      intensity_delta_pct: percentageDelta(item.intensity_score, intensityAverage),
    };
  });
}

export default async function PhysicalPage() {
  try {
    const physicalOverview = await getPhysicalOverviewData();
    const trainingEnergyData = await loadTrainingEnergySessions(physicalOverview.latestSeasonYear);
    const effectiveTrainingSessions = trainingEnergyData.sessions;

    const energyMatches = buildEnergyMatches(physicalOverview.matchGpsSummary);
    const energyTrainings = buildEnergyTrainings(effectiveTrainingSessions);

    const latestMatch = energyMatches[0] ?? null;
    const latestTraining = energyTrainings[0] ?? null;
    const recentSixMatches = energyMatches.slice(0, 6);
    const recentSixTrainings = energyTrainings.slice(0, 6);
    const recentThreeMatches = energyMatches.slice(0, 3);
    const previousThreeMatches = energyMatches.slice(3, 6);
    const recentFiveTrainings = energyTrainings.slice(0, 5);
    const previousFiveTrainings = energyTrainings.slice(5, 10);
    const matchAverageScore = average(energyMatches.map((item) => item.energy_score));
    const trainingAverageScore = average(energyTrainings.map((item) => item.energy_score));
    const recentThreeMatchEnergy = average(recentThreeMatches.map((item) => item.energy_score));
    const previousThreeMatchEnergy = average(previousThreeMatches.map((item) => item.energy_score));
    const recentFiveTrainingEnergy = average(recentFiveTrainings.map((item) => item.energy_score));
    const previousFiveTrainingEnergy = average(previousFiveTrainings.map((item) => item.energy_score));
    const physicalSessions = physicalOverview.physicalSessions;

    const matchChartItems = [...energyMatches.slice(0, 6)]
      .reverse()
      .map<EnergyChartItem>((item) => ({
        id: item.match_id,
        label: formatShortDateLabel(item.match_date),
        score: item.energy_score,
      }));

    const trainingChartItems = [...energyTrainings.slice(0, 6)]
      .reverse()
      .map<EnergyChartItem>((item) => ({
        id: item.training_id,
        label: formatShortDateLabel(item.training_date),
        score: item.energy_score,
      }));

    const matchReportRows = latestMatch
      ? [
          {
            label: "Player Load / 90",
            value: oneDecimalFormatter.format(latestMatch.player_load_p90),
            note: `평균 대비 ${formatSignedPercent(latestMatch.load_delta_pct)}`,
          },
          {
            label: "총 거리 / 90",
            value: `${twoDecimalFormatter.format(latestMatch.distance_total_p90)} km`,
            note: `평균 대비 ${formatSignedPercent(latestMatch.distance_delta_pct)}`,
          },
          {
            label: "High-Speed / 90",
            value: `${Math.round(latestMatch.high_speed_m_p90).toLocaleString("ko-KR")}m`,
            note: `평균 대비 ${formatSignedPercent(latestMatch.high_speed_delta_pct)}`,
          },
          {
            label: "Sprint / 90",
            value: oneDecimalFormatter.format(latestMatch.sprint_count_p90),
            note: `평균 대비 ${formatSignedPercent(latestMatch.sprint_delta_pct)}`,
          },
          {
            label: "평균 Max Speed",
            value: `${oneDecimalFormatter.format(latestMatch.avg_max_speed_kmh)} km/h`,
            note: `평균 대비 ${formatSignedPercent(latestMatch.avg_max_speed_delta_pct)}`,
          },
          {
            label: "가동 인원",
            value: `${latestMatch.active_players}명`,
            note: `${latestMatch.result} · ${latestMatch.opponent}`,
          },
        ]
      : [];

    const trainingReportRows = latestTraining
      ? [
          {
            label: "총 이동거리",
            value: `${twoDecimalFormatter.format(latestTraining.total_distance)} km`,
            note: `평균 대비 ${formatSignedPercent(latestTraining.total_distance_delta_pct)}`,
          },
          {
            label: "1인당 이동거리",
            value: `${twoDecimalFormatter.format(latestTraining.average_distance)} km`,
            note: `평균 대비 ${formatSignedPercent(latestTraining.average_distance_delta_pct)}`,
          },
          {
            label: "총 스프린트",
            value: `${latestTraining.total_sprint_count.toLocaleString("ko-KR")}회`,
            note: `평균 대비 ${formatSignedPercent(latestTraining.sprint_delta_pct)}`,
          },
          {
            label: "폭발 액션",
            value: `${latestTraining.explosive_action_count.toLocaleString("ko-KR")}회`,
            note: `평균 대비 ${formatSignedPercent(latestTraining.explosive_action_delta_pct)}`,
          },
          {
            label: "평균 최고속도",
            value: `${oneDecimalFormatter.format(latestTraining.average_max_speed)} km/h`,
            note: `평균 대비 ${formatSignedPercent(latestTraining.average_max_speed_delta_pct)}`,
          },
          {
            label: "훈련 강도",
            value: trainingIntensityLabel(latestTraining.intensity_level),
            note: `${Math.round(latestTraining.intensity_score)}점 · ${trainingTypeLabel(latestTraining.training_type)}`,
          },
        ]
      : [];
    const statsContent = (
      <section className="stat-grid physical-kpi-grid" id="physical-summary">
        <article className="metric-card metric-card--highlight">
          <p>최근 경기 에너지</p>
          <strong>{latestMatch ? oneDecimalFormatter.format(latestMatch.energy_score) : "-"}</strong>
          <span>
            {latestMatch ? `시즌 평균 대비 ${formatSignedPercent(latestMatch.energy_delta_pct)}` : "경기 원장 없음"}
          </span>
        </article>
        <article className="metric-card">
          <p>최근 훈련 에너지</p>
          <strong>{latestTraining ? oneDecimalFormatter.format(latestTraining.energy_score) : "-"}</strong>
          <span>
            {latestTraining
              ? `GPS+강도 평균 대비 ${formatSignedPercent(latestTraining.energy_delta_pct)}`
              : "훈련 원장 없음"}
          </span>
        </article>
        <article className="metric-card">
          <p>최근 3경기 평균</p>
          <strong>{recentThreeMatches.length > 0 ? oneDecimalFormatter.format(recentThreeMatchEnergy) : "-"}</strong>
          <span>
            {previousThreeMatches.length > 0
              ? `직전 3경기 대비 ${formatSignedPoints(recentThreeMatchEnergy - previousThreeMatchEnergy)}`
              : "비교 경기 부족"}
          </span>
        </article>
        <article className="metric-card">
          <p>최근 5훈련 평균</p>
          <strong>{recentFiveTrainings.length > 0 ? oneDecimalFormatter.format(recentFiveTrainingEnergy) : "-"}</strong>
          <span>
            {previousFiveTrainings.length > 0
              ? `직전 5훈련 대비 ${formatSignedPoints(recentFiveTrainingEnergy - previousFiveTrainingEnergy)}`
              : "비교 세션 부족"}
          </span>
        </article>
      </section>
    );

    return (
      <main className="page physical-workspace">
        {statsContent}

        <PhysicalTabsShell
          energyContent={
            <>
              <section className="physical-energy-board-grid">
                <article className="panel panel--tight physical-energy-panel physical-energy-panel--match">
                  <div className="panel-header">
                    <div>
                      <p className="panel-eyebrow">Match Energy</p>
                      <h2>경기 에너지 레벨</h2>
                    </div>
                  </div>

                  {latestMatch ? (
                    <>
                      <div className="physical-energy-spotlight">
                        <div className="physical-energy-spotlight__score">
                          <span>{latestMatch.match_label}</span>
                          <strong>{oneDecimalFormatter.format(latestMatch.energy_score)}</strong>
                          <p>
                            {formatCompactDate(latestMatch.match_date)} · {latestMatch.opponent} · {latestMatch.result}
                          </p>
                        </div>
                        <div className="physical-energy-spotlight__meta">
                          <article>
                            <span>100점 만점</span>
                            <strong>{oneDecimalFormatter.format(latestMatch.energy_score)}</strong>
                          </article>
                          <article>
                            <span>시즌 평균 대비</span>
                            <strong>{formatSignedPercent(latestMatch.energy_delta_pct)}</strong>
                          </article>
                          <article>
                            <span>최근 3경기 평균</span>
                            <strong>{oneDecimalFormatter.format(recentThreeMatchEnergy)}</strong>
                          </article>
                        </div>
                      </div>

                      <EnergyTrendChart
                        averageScore={matchAverageScore}
                        items={matchChartItems}
                        rangeLabel={`최근 ${matchChartItems.length}경기 흐름`}
                        tone="match"
                      />

                      <div className="physical-energy-strip">
                        {recentSixMatches.map((match) => (
                          <article className="physical-energy-card" key={match.match_id}>
                            <div className="physical-energy-card__top">
                              <span>{match.match_label}</span>
                              <span className={match.energy_class_name}>{match.energy_label}</span>
                            </div>
                            <strong>{oneDecimalFormatter.format(match.energy_score)}</strong>
                            <p>
                              {match.opponent} · {formatCompactDate(match.match_date)}
                            </p>
                            <small>평균 대비 {formatSignedPercent(match.energy_delta_pct)}</small>
                          </article>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="empty-state">
                      <strong>경기 에너지 데이터 없음</strong>
                      <p>경기 GPS 원장이 들어오면 경기별 에너지 흐름을 표시합니다.</p>
                    </div>
                  )}
                </article>

                <article className="panel panel--tight physical-energy-panel physical-energy-panel--training">
                  <div className="panel-header">
                    <div>
                      <p className="panel-eyebrow">Training Energy</p>
                      <h2>훈련 에너지 레벨</h2>
                    </div>
                  </div>

                  {latestTraining ? (
                    <>
                      <div className="physical-energy-spotlight">
                        <div className="physical-energy-spotlight__score">
                          <span>{trainingIntensityLabel(latestTraining.intensity_level)}</span>
                          <strong>{oneDecimalFormatter.format(latestTraining.energy_score)}</strong>
                          <p>
                            {formatCompactDate(latestTraining.training_date)} · {latestTraining.session_name}
                          </p>
                        </div>
                        <div className="physical-energy-spotlight__meta">
                          <article>
                            <span>100점 만점</span>
                            <strong>{oneDecimalFormatter.format(latestTraining.energy_score)}</strong>
                          </article>
                          <article>
                            <span>GPS+강도 평균 대비</span>
                            <strong>{formatSignedPercent(latestTraining.energy_delta_pct)}</strong>
                          </article>
                          <article>
                            <span>최근 5훈련 평균</span>
                            <strong>{oneDecimalFormatter.format(recentFiveTrainingEnergy)}</strong>
                          </article>
                          <article>
                            <span>데이터 소스</span>
                            <strong>DB</strong>
                          </article>
                        </div>
                      </div>

                      <EnergyTrendChart
                        averageScore={trainingAverageScore}
                        items={trainingChartItems}
                        rangeLabel={`최근 ${trainingChartItems.length}세션 흐름`}
                        tone="training"
                      />

                      <div className="physical-energy-strip">
                        {recentSixTrainings.map((training) => (
                          <article className="physical-energy-card" key={training.training_id}>
                            <div className="physical-energy-card__top">
                              <span>{formatCompactDate(training.training_date)}</span>
                              <span className={training.energy_class_name}>{training.energy_label}</span>
                            </div>
                            <strong>{oneDecimalFormatter.format(training.energy_score)}</strong>
                            <p>
                              {training.session_name} · {trainingTypeLabel(training.training_type)}
                            </p>
                            <small>평균 대비 {formatSignedPercent(training.energy_delta_pct)}</small>
                          </article>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="empty-state">
                      <strong>훈련 에너지 데이터 없음</strong>
                      <p>훈련 세션 데이터가 아직 부족합니다.</p>
                    </div>
                  )}
                </article>
              </section>

              <section className="physical-energy-report-grid">
                <article className="panel panel--tight physical-energy-report-panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-eyebrow">Latest Match Report</p>
                      <h2>최근 경기 활동량</h2>
                    </div>
                  </div>

                  {matchReportRows.length > 0 ? (
                    <div className="physical-energy-report">
                      {matchReportRows.map((row) => (
                        <article className="physical-energy-row" key={row.label}>
                          <div className="physical-energy-row__meta">
                            <span>{row.label}</span>
                            <small>{row.note}</small>
                          </div>
                          <strong>{row.value}</strong>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <strong>경기 활동량 리포트 없음</strong>
                      <p>최근 경기 GPS 데이터가 있으면 주요 활동량을 함께 표시합니다.</p>
                    </div>
                  )}
                </article>

                <article className="panel panel--tight physical-energy-report-panel physical-energy-report-panel--training">
                  <div className="panel-header">
                    <div>
                      <p className="panel-eyebrow">Latest Training Report</p>
                      <h2>최근 훈련 활동량</h2>
                    </div>
                  </div>

                  {trainingReportRows.length > 0 ? (
                    <div className="physical-energy-report">
                      {trainingReportRows.map((row) => (
                        <article className="physical-energy-row" key={row.label}>
                          <div className="physical-energy-row__meta">
                            <span>{row.label}</span>
                            <small>{row.note}</small>
                          </div>
                          <strong>{row.value}</strong>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <strong>훈련 활동량 리포트 없음</strong>
                      <p>훈련 세션이 연결되면 최근 훈련 기준 활동량을 별도로 보여줍니다.</p>
                    </div>
                  )}
                </article>
              </section>
            </>
          }
          physicalContent={
            <>
              <PhysicalTestsBoard sessions={physicalSessions} />
            </>
          }
        />
      </main>
    );
  } catch (error) {
    return (
      <DataPageError
        description="피지컬 / GPS 데이터를 불러오지 못했습니다. 백엔드 physical-overview API와 팀 훈련 API가 복구되면 화면이 다시 표시됩니다."
        endpoint={getPhysicalOverviewEndpoint()}
        error={error}
        eyebrow="Physical"
        title="Physical / GPS 화면 데이터를 불러오지 못했습니다"
      />
    );
  }
}
