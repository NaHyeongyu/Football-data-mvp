import { DataPageError } from "@/components/data-page-error";
import { InjuryTabsShell } from "@/components/injury-tabs-shell";
import { getPlayerInjuryRisk, getPlayerInjuryRiskEndpoint } from "@/lib/team-api";
import type { PlayerInjuryRiskItem, PlayerRecentInjuryHistoryItem } from "@/lib/team-api-types";

import styles from "./page.module.css";

export const dynamic = "force-dynamic";

const oneDecimalFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});

const integerFormatter = new Intl.NumberFormat("ko-KR");

type AlertEntry = {
  id: string;
  title: string;
  subtitle: string;
  metric: string;
  note: string;
  tone: "risk" | "watch" | "normal";
};

const METRIC_HINTS = {
  overall: {
    title: "총 위험도",
    description:
      "부하, 이력, 복귀, 증상 요인을 합산한 운영용 위험도입니다. 점수가 높을수록 우선 확인 대상입니다.",
  },
  load: {
    title: "부하 점수",
    description:
      "최근 7일 부하, ACR, 스프린트 급증, 활동량 급감 신호를 반영한 점수입니다.",
  },
  history: {
    title: "이력 점수",
    description:
      "최근 부상 이력, 결장일, 반복 이벤트를 반영한 점수입니다.",
  },
  return: {
    title: "복귀 점수",
    description:
      "재활 중 상태와 복귀 후 30일 이내 관리 구간을 반영한 점수입니다.",
  },
  symptom: {
    title: "증상 점수",
    description:
      "최근 120일 통증·불편감 기록과 최신 증상 시점을 반영한 점수입니다.",
  },
  acr: {
    title: "ACR",
    description:
      "최근 7일 부하를 개인 기준 부하와 비교한 비율입니다. 1.00은 평소 수준, 1.22 이상은 급증, 0.82 이하는 급감 신호로 봅니다.",
  },
  sprint: {
    title: "스프린트 비율",
    description:
      "최근 7일 스프린트 수를 개인 기준과 비교한 비율입니다. 1.25 이상이면 급증 신호로 봅니다.",
  },
  activity: {
    title: "활동량 비율",
    description:
      "최근 7일 활동량(거리)을 개인 기준과 비교한 비율입니다. 0.82 이하이면 급감 신호로 보며 GK는 예외 처리합니다.",
  },
  returnWindow: {
    title: "복귀 상태",
    description:
      "재활 중이거나 복귀 후 30일 이내면 별도 관리 대상으로 표시합니다.",
  },
  symptomWindow: {
    title: "증상 기록",
    description:
      "최근 120일 통증·불편감 기록의 최신 시점을 표시합니다.",
  },
} as const;

type MetricHintKey = keyof typeof METRIC_HINTS;

const FACTOR_MAX = {
  load: 36,
  history: 30,
  return: 18,
  symptom: 15,
} as const;

function formatScore(value: number) {
  return oneDecimalFormatter.format(value);
}

function formatRatio(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return "-";
  }

  return `${value.toFixed(2)}배`;
}

function formatDaysLabel(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return "-";
  }

  return `${integerFormatter.format(value)}일`;
}

function formatDateLabel(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  const normalized = value.slice(0, 10);
  const [year, month, day] = normalized.split("-");
  if (!year || !month || !day) {
    return value;
  }

  return `${year}.${month}.${day}`;
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

function statusLabel(status: string) {
  return status === "injured" ? "부상 상태" : "훈련 가능";
}

function severityLabel(value: string | null | undefined) {
  if (value === "severe") {
    return "중증";
  }
  if (value === "moderate") {
    return "중등도";
  }
  if (value === "minor") {
    return "경미";
  }

  return "확인 필요";
}

function severityBadgeClassName(value: string | null | undefined) {
  if (value === "severe") {
    return `${styles.severityBadge} ${styles.severityBadgeSevere}`;
  }
  if (value === "moderate") {
    return `${styles.severityBadge} ${styles.severityBadgeModerate}`;
  }
  if (value === "minor") {
    return `${styles.severityBadge} ${styles.severityBadgeMinor}`;
  }

  return `${styles.severityBadge} ${styles.severityBadgeNeutral}`;
}

function injuryStatusLabel(value: string | null | undefined) {
  if (value === "rehab") {
    return "재활 중";
  }
  if (value === "injured" || value === "open") {
    return "부상 중";
  }
  if (value === "returned" || value === "resolved" || value === "closed") {
    return "복귀 완료";
  }

  return value ? value : "확인 필요";
}

function injuryHistoryLabel(item: PlayerRecentInjuryHistoryItem) {
  if (item.injury_part && item.injury_type) {
    return `${item.injury_part} · ${item.injury_type}`;
  }
  if (item.injury_part) {
    return item.injury_part;
  }
  if (item.injury_type) {
    return item.injury_type;
  }

  return "기록 확인";
}

function riskBadgeClassName(riskBand: string) {
  if (riskBand === "risk") {
    return `${styles.riskBadge} ${styles.riskBadgeRisk}`;
  }
  if (riskBand === "watch") {
    return `${styles.riskBadge} ${styles.riskBadgeWatch}`;
  }

  return `${styles.riskBadge} ${styles.riskBadgeNormal}`;
}

function alertTone(riskBand: string): AlertEntry["tone"] {
  if (riskBand === "risk") {
    return "risk";
  }
  if (riskBand === "watch") {
    return "watch";
  }

  return "normal";
}

function factorBarClassName(name: keyof typeof FACTOR_MAX) {
  if (name === "load") {
    return `${styles.factorBarFill} ${styles.factorBarFillLoad}`;
  }
  if (name === "history") {
    return `${styles.factorBarFill} ${styles.factorBarFillHistory}`;
  }
  if (name === "return") {
    return `${styles.factorBarFill} ${styles.factorBarFillReturn}`;
  }

  return `${styles.factorBarFill} ${styles.factorBarFillSymptom}`;
}

function alertCardClassName(tone: AlertEntry["tone"]) {
  if (tone === "risk") {
    return `${styles.alertCard} ${styles.alertCardRisk}`;
  }
  if (tone === "watch") {
    return `${styles.alertCard} ${styles.alertCardWatch}`;
  }

  return `${styles.alertCard} ${styles.alertCardNormal}`;
}

function factorWidth(value: number, max: number) {
  const ratio = max <= 0 ? 0 : (value / max) * 100;
  return `${Math.max(8, Math.min(100, ratio))}%`;
}

function isSprintSpike(item: PlayerInjuryRiskItem) {
  return (
    (item.factors.sprint_ratio ?? 0) >= 1.25 &&
    item.factors.sprint_count_7d >= 35
  );
}

function isLoadSpike(item: PlayerInjuryRiskItem) {
  return (item.factors.acute_chronic_ratio ?? 0) >= 1.22;
}

function isActivityDrop(item: PlayerInjuryRiskItem) {
  if (item.primary_position === "GK") {
    return false;
  }

  return (
    (item.factors.acute_chronic_ratio ?? Number.POSITIVE_INFINITY) <= 0.82 ||
    (item.factors.distance_ratio ?? Number.POSITIVE_INFINITY) <= 0.82
  );
}

function returnManagementLabel(item: PlayerInjuryRiskItem) {
  if (
    item.factors.days_since_return != null &&
    item.factors.days_since_return <= 30
  ) {
    return `복귀 ${formatDaysLabel(item.factors.days_since_return)}`;
  }

  return "최근 복귀";
}

function prioritySubtitle(item: PlayerInjuryRiskItem) {
  return `${item.primary_position} · ${statusLabel(item.status)}`;
}

function buildLoadAlertEntries(items: PlayerInjuryRiskItem[]) {
  return items
    .filter((item) => isLoadSpike(item) || isActivityDrop(item) || isSprintSpike(item))
    .sort((left, right) => right.factors.load_score - left.factors.load_score)
    .slice(0, 5)
    .map((item) => {
      let metric = `부하 ${formatRatio(item.factors.acute_chronic_ratio)}`;

      if (isSprintSpike(item)) {
        metric = `스프린트 ${formatRatio(item.factors.sprint_ratio)}`;
      } else if (isActivityDrop(item)) {
        metric =
          item.primary_position === "GK"
            ? "활동량 예외"
            : `활동량 ${formatRatio(item.factors.distance_ratio)}`;
      }

      return {
        id: item.player_id,
        title: item.name,
        subtitle: prioritySubtitle(item),
        metric,
        note: item.reasons[0] ?? "최근 부하 신호를 확인하세요.",
        tone: alertTone(item.risk_band),
      } satisfies AlertEntry;
    });
}

function buildReturnEntries(items: PlayerInjuryRiskItem[]) {
  return items
    .filter(
      (item) =>
        item.factors.days_since_return != null && item.factors.days_since_return <= 30,
    )
    .sort((left, right) => {
      const leftDays = left.factors.days_since_return ?? -1;
      const rightDays = right.factors.days_since_return ?? -1;
      return leftDays - rightDays;
    })
    .slice(0, 5)
    .map((item) => ({
      id: item.player_id,
      title: item.name,
      subtitle: prioritySubtitle(item),
      metric: returnManagementLabel(item),
      note: item.reasons[0] ?? "복귀 후 노출량을 점검하세요.",
      tone: item.risk_band === "risk" ? "risk" : "watch",
    } satisfies AlertEntry));
}

function buildSymptomEntries(items: PlayerInjuryRiskItem[]) {
  return items
    .filter((item) => item.factors.recent_symptom_flag)
    .sort((left, right) => {
      const leftDays = left.factors.latest_symptom_days_ago ?? Number.POSITIVE_INFINITY;
      const rightDays = right.factors.latest_symptom_days_ago ?? Number.POSITIVE_INFINITY;
      return leftDays - rightDays;
    })
    .slice(0, 5)
    .map((item) => ({
      id: item.player_id,
      title: item.name,
      subtitle: `${item.primary_position} · 증상 ${item.factors.recent_symptom_count_120d}회`,
      metric:
        item.factors.latest_symptom_days_ago == null
          ? "기록 확인"
          : `${item.factors.latest_symptom_days_ago}일 전`,
      note: item.reasons.find((reason) => reason.includes("통증") || reason.includes("불편감")) ??
        item.reasons[0] ??
        "최근 증상 기록을 확인하세요.",
      tone: alertTone(item.risk_band),
    } satisfies AlertEntry));
}

function injuryHistoryTone(item: PlayerRecentInjuryHistoryItem): AlertEntry["tone"] {
  if (item.severity_level === "severe") {
    return "risk";
  }
  if (
    item.injury_status === "rehab" ||
    item.injury_status === "injured" ||
    item.injury_status === "open" ||
    item.severity_level === "moderate"
  ) {
    return "watch";
  }

  return "normal";
}

function injuryHistoryReturnLabel(item: PlayerRecentInjuryHistoryItem) {
  if (item.actual_return_date) {
    return `복귀 ${formatDateLabel(item.actual_return_date)}`;
  }
  if (item.expected_return_date) {
    return `예상 복귀 ${formatDateLabel(item.expected_return_date)}`;
  }

  return "복귀 일정 확인 필요";
}

function MetricHint({
  hintKey,
  align = "center",
}: {
  hintKey: MetricHintKey;
  align?: "center" | "start";
}) {
  const hint = METRIC_HINTS[hintKey];

  return (
    <span className={align === "start" ? `${styles.metricHint} ${styles.metricHintStart}` : styles.metricHint}>
      <button
        aria-label={`${hint.title} 설명`}
        className={styles.metricHintButton}
        type="button"
      >
        ?
      </button>
      <span className={styles.metricHintPanel}>
        <strong>{hint.title}</strong>
        <span>{hint.description}</span>
      </span>
    </span>
  );
}

function MetricLabel({
  label,
  hintKey,
}: {
  label: string;
  hintKey: MetricHintKey;
}) {
  return (
    <span>
      {label}
      <MetricHint hintKey={hintKey} />
    </span>
  );
}

function SignalChip({
  hintKey,
  text,
}: {
  hintKey: MetricHintKey;
  text: string;
}) {
  return (
    <span>
      <span className={styles.prioritySignalText}>{text}</span>
      <MetricHint align="start" hintKey={hintKey} />
    </span>
  );
}

function HeaderWithHint({
  hintKey,
  label,
}: {
  hintKey: MetricHintKey;
  label: string;
}) {
  return (
    <span className={styles.matrixHeaderLabel}>
      <span>{label}</span>
      <MetricHint align="start" hintKey={hintKey} />
    </span>
  );
}

function AlertList({
  items,
  emptyText,
}: {
  items: AlertEntry[];
  emptyText: string;
}) {
  if (items.length === 0) {
    return <p className={styles.emptyHint}>{emptyText}</p>;
  }

  return (
    <div className={styles.alertList}>
      {items.map((item) => (
        <article className={alertCardClassName(item.tone)} key={item.id}>
          <div className={styles.alertTopline}>
            <strong>{item.title}</strong>
            <span>{item.metric}</span>
          </div>
          <p className={styles.alertSubtitle}>{item.subtitle}</p>
          <p className={styles.alertNote}>{item.note}</p>
        </article>
      ))}
    </div>
  );
}

function historyCardClassName() {
  return styles.historyCard;
}

function RecentHistoryList({ items }: { items: PlayerRecentInjuryHistoryItem[] }) {
  if (items.length === 0) {
    return <p className={styles.emptyHint}>최근 부상 기록이 없습니다.</p>;
  }

  return (
    <div className={styles.historyList}>
      {items.slice(0, 6).map((item) => (
        <article className={historyCardClassName()} key={item.injury_id}>
          <div className={styles.historyCardHeader}>
            <div className={styles.historyPlayerBlock}>
              <strong>{item.name}</strong>
              <span>
                {item.primary_position} · {statusLabel(item.status)}
              </span>
            </div>
            <span className={styles.historyStatusPill}>{injuryStatusLabel(item.injury_status)}</span>
          </div>

          <p className={styles.historyIssue}>{injuryHistoryLabel(item)}</p>

          <dl className={styles.historyFacts}>
            <div className={styles.historyFact}>
              <dt>발생일</dt>
              <dd>{formatDateLabel(item.injury_date)}</dd>
            </div>
            <div className={styles.historyFact}>
              <dt>심각도</dt>
              <dd>
                <span className={severityBadgeClassName(item.severity_level)}>
                  {severityLabel(item.severity_level)}
                </span>
              </dd>
            </div>
            <div className={`${styles.historyFact} ${styles.historyFactWide}`}>
              <dt>복귀</dt>
              <dd>{injuryHistoryReturnLabel(item)}</dd>
            </div>
          </dl>

          {item.notes ? (
            <p className={styles.historyNote}>{item.notes}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function PriorityPlayerCard({ item }: { item: PlayerInjuryRiskItem }) {
  const factors = [
    { label: "부하", value: item.factors.load_score, max: FACTOR_MAX.load, key: "load" as const },
    { label: "이력", value: item.factors.injury_history_score, max: FACTOR_MAX.history, key: "history" as const },
    { label: "복귀", value: item.factors.return_to_play_score, max: FACTOR_MAX.return, key: "return" as const },
    { label: "증상", value: item.factors.symptom_score, max: FACTOR_MAX.symptom, key: "symptom" as const },
  ];

  return (
    <article className={styles.priorityCard}>
      <div className={styles.priorityHeader}>
        <div>
          <p className={styles.priorityMeta}>{prioritySubtitle(item)}</p>
          <h3>{item.name}</h3>
        </div>
        <span className={riskBadgeClassName(item.risk_band)}>{riskBandLabel(item.risk_band)}</span>
      </div>

      <div className={styles.priorityBody}>
          <div className={styles.priorityGraphColumn}>
            <div className={styles.priorityScoreRow}>
              <strong>{formatScore(item.overall_risk_score)}</strong>
              <span>
                총 위험도
                <MetricHint align="start" hintKey="overall" />
              </span>
            </div>

          <div className={styles.factorGrid}>
            {factors.map((factor) => (
              <div className={styles.factorMetric} key={factor.label}>
                <div className={styles.factorMetricTopline}>
                  <MetricLabel
                    hintKey={factor.key}
                    label={factor.label}
                  />
                  <strong>{formatScore(factor.value)}</strong>
                </div>
                <div className={styles.factorBarTrack} aria-hidden="true">
                  <div
                    className={factorBarClassName(factor.key)}
                    style={{ width: factorWidth(factor.value, factor.max) }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.priorityDetailColumn}>
          <div className={styles.prioritySignalRow}>
            <SignalChip
              hintKey="acr"
              text={`ACR ${formatRatio(item.factors.acute_chronic_ratio)}`}
            />
            <SignalChip
              hintKey="sprint"
              text={`스프린트 ${formatRatio(item.factors.sprint_ratio)}`}
            />
            <SignalChip
              hintKey="activity"
              text={
                item.primary_position === "GK"
                  ? "활동량 예외(GK)"
                  : `활동량 ${formatRatio(item.factors.distance_ratio)}`
              }
            />
          </div>

          <ul className={styles.reasonList}>
            {item.reasons.slice(0, 3).map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

export default async function InjuryPage() {
  try {
    const report = await getPlayerInjuryRisk();
    const items = report.items;
    const recentHistory = report.recent_history;
    const riskCount = items.filter((item) => item.risk_band === "risk").length;
    const watchCount = items.filter((item) => item.risk_band === "watch").length;
    const rehabCount = items.filter((item) => item.factors.open_rehab_flag).length;
    const recentReturnCount = items.filter(
      (item) =>
        item.factors.days_since_return != null && item.factors.days_since_return <= 30,
    ).length;
    const symptomCount = items.filter((item) => item.factors.recent_symptom_flag).length;
    const loadAlertCount = new Set(
      items
        .filter((item) => isLoadSpike(item) || isActivityDrop(item) || isSprintSpike(item))
        .map((item) => item.player_id),
    ).size;
    const priorityShare =
      report.total === 0 ? 0 : ((riskCount + watchCount) / report.total) * 100;
    const topPriorityItems = items.slice(0, 6);
    const statsContent = (
      <section className="stat-grid">
        <article className="metric-card metric-card--highlight">
          <p>실시간 관리 대상</p>
          <strong>{riskCount + watchCount}명</strong>
          <span>{priorityShare.toFixed(1)}% of roster</span>
        </article>
        <article className="metric-card">
          <p>재활 중</p>
          <strong>{rehabCount}명</strong>
          <span>현재 재활 상태 기준</span>
        </article>
        <article className="metric-card">
          <p>복귀 30일 이내</p>
          <strong>{recentReturnCount}명</strong>
          <span>재부상 관리 윈도우</span>
        </article>
        <article className="metric-card">
          <p>부하 변화 감지</p>
          <strong>{loadAlertCount}명</strong>
          <span>급증·급감·스프린트 급증 포함</span>
        </article>
        <article className="metric-card">
          <p>증상 기록 감지</p>
          <strong>{symptomCount}명</strong>
          <span>최근 120일 통증·불편감 키워드</span>
        </article>
      </section>
    );
    const dashboardContent = (
      <>
        <section className={styles.workspace}>
          <article className={`panel panel--tight ${styles.priorityPanel}`}>
            <div className="panel-header">
              <div>
                <p className="panel-eyebrow">Priority Queue</p>
                <h2>우선 체크 선수</h2>
              </div>
            </div>

            <div className={styles.priorityGrid}>
              {topPriorityItems.map((item) => (
                <PriorityPlayerCard item={item} key={item.player_id} />
              ))}
            </div>
          </article>

          <div className={styles.sideRail}>
            <article className={`panel panel--tight ${styles.signalPanel}`}>
              <div className="panel-header">
                <div>
                  <p className="panel-eyebrow">Recent Injury Log</p>
                  <h2>최근 부상 히스토리</h2>
                </div>
              </div>
              <RecentHistoryList items={recentHistory} />
            </article>
          </div>
        </section>
      </>
    );
    const playersContent = (
      <section className={`panel ${styles.matrixPanel}`}>
        <div className="panel-header">
          <div>
            <p className="panel-eyebrow">Roster Matrix</p>
            <h2>전체 선수 매트릭스</h2>
          </div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.matrixTable}>
            <thead>
              <tr>
                <th>선수</th>
                <th>밴드</th>
                <th>
                  <HeaderWithHint hintKey="overall" label="총점" />
                </th>
                <th>
                  <HeaderWithHint hintKey="acr" label="부하" />
                </th>
                <th>
                  <HeaderWithHint hintKey="sprint" label="스프린트" />
                </th>
                <th>
                  <HeaderWithHint hintKey="activity" label="활동량" />
                </th>
                <th>
                  <HeaderWithHint hintKey="returnWindow" label="복귀" />
                </th>
                <th>
                  <HeaderWithHint hintKey="symptomWindow" label="증상" />
                </th>
                <th>사유</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.player_id}>
                  <td>
                    <div className={styles.playerCell}>
                      <strong>{item.name}</strong>
                      <span>
                        {item.primary_position} · {statusLabel(item.status)}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={riskBadgeClassName(item.risk_band)}>
                      {riskBandLabel(item.risk_band)}
                    </span>
                  </td>
                  <td>{formatScore(item.overall_risk_score)}</td>
                  <td>{formatRatio(item.factors.acute_chronic_ratio)}</td>
                  <td>{formatRatio(item.factors.sprint_ratio)}</td>
                  <td>
                    {item.primary_position === "GK"
                      ? "GK 제외"
                      : formatRatio(item.factors.distance_ratio)}
                  </td>
                  <td>
                    {item.factors.open_rehab_flag
                      ? "재활 중"
                      : item.factors.days_since_return != null &&
                          item.factors.days_since_return <= 30
                        ? formatDaysLabel(item.factors.days_since_return)
                        : "-"}
                  </td>
                  <td>
                    {item.factors.recent_symptom_flag
                      ? item.factors.latest_symptom_days_ago == null
                        ? "확인 필요"
                        : `${item.factors.latest_symptom_days_ago}일 전`
                      : "-"}
                  </td>
                  <td>
                    <div className={styles.reasonCell}>
                      {item.reasons.slice(0, 2).map((reason) => (
                        <span className={styles.reasonChip} key={reason}>
                          {reason}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    );
    return (
      <main className="page">
        {statsContent}
        <InjuryTabsShell
          dashboardContent={dashboardContent}
          playerCount={report.total}
          playersContent={playersContent}
        />
      </main>
    );
  } catch (error) {
    return (
      <DataPageError
        description="실시간 부상 위험 리포트를 불러오지 못했습니다. 백엔드 API와 데이터베이스 연결 상태를 확인하세요."
        endpoint={getPlayerInjuryRiskEndpoint()}
        error={error}
        eyebrow="Medical Risk"
        title="부상 위험 운영 보드를 불러오지 못했습니다"
      />
    );
  }
}
