"use client";

import { usePathname, useRouter } from "next/navigation";
import { startTransition, useDeferredValue, useState } from "react";

import type {
  TeamTrainingListItem,
  TeamTrainingListResponse,
} from "@/lib/team-api-types";

const dateFormatter = new Intl.DateTimeFormat("ko-KR", {
  year: "numeric",
  month: "short",
  day: "numeric",
});
const decimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});
const compactFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});
const numberFormatter = new Intl.NumberFormat("ko-KR");

type TrainingIntensityFilter = "all" | "low" | "medium" | "high" | "very_high";

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

function intensityTone(value: string | null) {
  if (value === "very_high" || value === "high") {
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

function formatPercent(value: number) {
  return `${decimalFormatter.format(value)}%`;
}

function formatDuration(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }
  return `${numberFormatter.format(Math.round(value))}분`;
}

function formatDistance(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }
  return `${compactFormatter.format(value)} km`;
}

function formatParticipantCount(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "-";
  }
  return `${compactFormatter.format(value)}명`;
}

function buildTrainingSearchText(training: TeamTrainingListItem) {
  return [
    training.session_name,
    training.training_focus ?? "",
    training.location ?? "",
    training.coach_name ?? "",
    training.training_id,
    training.training_type,
    training.intensity_level ?? "",
  ]
    .join(" ")
    .toLowerCase();
}

function TrainingListTable({
  trainings,
  onSelectTraining,
}: {
  trainings: TeamTrainingListItem[];
  onSelectTraining: (trainingId: string) => void;
}) {
  return (
    <div className="table-scroll">
      <table className="data-table data-table--matches">
        <thead>
          <tr>
            <th>날짜</th>
            <th>세션</th>
            <th>유형</th>
            <th>장소</th>
            <th>강도</th>
          </tr>
        </thead>
        <tbody>
          {trainings.map((training) => (
            <tr
              key={training.training_id}
              className="match-list-row"
              role="link"
              tabIndex={0}
              onClick={() => onSelectTraining(training.training_id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectTraining(training.training_id);
                }
              }}
            >
              <td>{dateFormatter.format(new Date(`${training.training_date}T00:00:00`))}</td>
              <td>
                <span className="match-list-link">
                  <strong>{training.session_name}</strong>
                  <span className="training-list-note">
                    {[training.training_focus, training.coach_name]
                      .filter(Boolean)
                      .join(" · ") || training.training_id}
                  </span>
                </span>
              </td>
              <td>
                <span className={trainingTypeTone(training.training_type)}>
                  {trainingTypeLabel(training.training_type)}
                </span>
              </td>
              <td>{training.location ?? "-"}</td>
              <td>
                <span className={intensityTone(training.intensity_level)}>
                  {intensityLabel(training.intensity_level)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TeamTrainingsBoard({
  data,
}: {
  data: TeamTrainingListResponse;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState("");
  const [trainingTypeFilter, setTrainingTypeFilter] = useState<string>("all");
  const [intensityFilter, setIntensityFilter] = useState<TrainingIntensityFilter>("all");

  const deferredSearchQuery = useDeferredValue(searchQuery);
  const normalizedSearchQuery = deferredSearchQuery.trim().toLowerCase();

  const typeOptions = Array.from(
    new Set(data.trainings.map((training) => training.training_type)),
  ).sort((left, right) =>
    trainingTypeLabel(left).localeCompare(trainingTypeLabel(right), "ko"),
  );
  const yearOptions =
    data.available_years.length > 0
      ? data.available_years
      : [{ year: data.selected_year, label: `${data.selected_year} Season` }];

  const filteredTrainings = data.trainings.filter((training) => {
    if (trainingTypeFilter !== "all" && training.training_type !== trainingTypeFilter) {
      return false;
    }
    if (intensityFilter !== "all" && training.intensity_level !== intensityFilter) {
      return false;
    }
    if (!normalizedSearchQuery) {
      return true;
    }
    return buildTrainingSearchText(training).includes(normalizedSearchQuery);
  });

  const tacticalCount = data.trainings.filter((training) =>
    ["tactical", "tactical_physical"].includes(training.training_type),
  ).length;
  const preMatchCount = data.trainings.filter(
    (training) => training.training_type === "pre_match",
  ).length;
  const recoveryCount = data.trainings.filter(
    (training) => training.training_type === "recovery",
  ).length;
  const conditioningCount = data.trainings.filter(
    (training) => training.training_type === "conditioning",
  ).length;

  const highIntensityShare =
    data.summary.training_count > 0
      ? (data.summary.high_intensity_count / data.summary.training_count) * 100
      : 0;

  return (
    <>
      <section className="matches-kpi-grid" id="training-summary">
        <article className="matches-kpi-card matches-kpi-card--primary">
          <div className="matches-kpi-card__head">
            <div>
              <p className="panel-eyebrow">Total Sessions</p>
              <h2>훈련 수</h2>
            </div>
            <span className="matches-kpi-chip matches-kpi-chip--inverse">
              {data.selected_year} 시즌
            </span>
          </div>
          <div className="matches-kpi-card__single">
            <strong>{numberFormatter.format(data.summary.training_count)}</strong>
            <span>전체 훈련 세션 수</span>
          </div>
          <div className="matches-kpi-mini-record">
            <span>고 {data.summary.high_intensity_count}</span>
            <span>중 {data.summary.medium_intensity_count}</span>
            <span>저 {data.summary.low_intensity_count}</span>
          </div>
        </article>

        <article className="matches-kpi-card">
          <div className="matches-kpi-card__head">
            <div>
              <p className="panel-eyebrow">Average Duration</p>
              <h3>평균 훈련 시간</h3>
            </div>
            <span className="matches-kpi-chip matches-kpi-chip--neutral">
              훈련 시간 기준
            </span>
          </div>
          <div className="matches-kpi-card__single">
            <strong>{formatDuration(data.summary.average_duration_min)}</strong>
            <span>시작/종료 시간 기준 평균</span>
          </div>
          <div className="matches-kpi-mini-record">
            <span>{formatParticipantCount(data.summary.average_participant_count)}</span>
            <span>{formatDistance(data.summary.average_total_distance)}</span>
            <span>고강도 {data.summary.high_intensity_count}회</span>
          </div>
        </article>

        <article className="matches-kpi-card">
          <div className="matches-kpi-card__head">
            <div>
              <p className="panel-eyebrow">Training Mix</p>
              <h3>훈련 분포</h3>
            </div>
            <span className="matches-kpi-chip matches-kpi-chip--warning">
              {formatPercent(highIntensityShare)}
            </span>
          </div>
          <div className="matches-kpi-card__single">
            <strong>{numberFormatter.format(tacticalCount)}</strong>
            <span>전술 기반 훈련 수</span>
          </div>
          <div className="matches-kpi-mini-record">
            <span>프리매치 {preMatchCount}</span>
            <span>회복훈련 {recoveryCount}</span>
            <span>컨디셔닝 {conditioningCount}</span>
          </div>
        </article>
      </section>

      <section className="matches-section-stack" id="training-list">
        <section className="matches-filter-panel">
          <div className="matches-filter-panel__head">
            <div>
              <p className="panel-eyebrow">Training Filters</p>
              <h3>훈련 검색 필터</h3>
            </div>
            <div className="matches-filter-panel__summary">
              <strong>{numberFormatter.format(filteredTrainings.length)}</strong>
              <span>{numberFormatter.format(data.trainings.length)}세션 중 조회 결과</span>
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
                {yearOptions.map((yearOption) => (
                  <option key={yearOption.year} value={String(yearOption.year)}>
                    {yearOption.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field form-field--search matches-filter-field">
              <span>검색</span>
              <input
                placeholder="세션명, 장소, 코치, 훈련 ID 검색"
                type="search"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />
            </label>

            <label className="form-field matches-filter-field">
              <span>훈련 유형</span>
              <select
                value={trainingTypeFilter}
                onChange={(event) => setTrainingTypeFilter(event.target.value)}
              >
                <option value="all">전체</option>
                {typeOptions.map((trainingType) => (
                  <option key={trainingType} value={trainingType}>
                    {trainingTypeLabel(trainingType)}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field matches-filter-field">
              <span>강도</span>
              <select
                value={intensityFilter}
                onChange={(event) =>
                  setIntensityFilter(event.target.value as TrainingIntensityFilter)
                }
              >
                <option value="all">all</option>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="very_high">high</option>
              </select>
            </label>
          </div>
        </section>

        <section className="panel matches-table-panel">
          {data.trainings.length === 0 ? (
            <div className="empty-state">
              <strong>해당 연도 훈련 없음</strong>
              <p>선택한 연도에는 조회 가능한 훈련 데이터가 없습니다.</p>
            </div>
          ) : filteredTrainings.length === 0 ? (
            <div className="empty-state">
              <strong>조건에 맞는 훈련이 없습니다</strong>
              <p>검색어나 필터 조건을 조정해서 다시 조회해보세요.</p>
            </div>
          ) : (
            <TrainingListTable
              trainings={filteredTrainings}
              onSelectTraining={(trainingId) =>
                router.push(`/training/${trainingId}?year=${data.selected_year}`)
              }
            />
          )}
        </section>
      </section>
    </>
  );
}
