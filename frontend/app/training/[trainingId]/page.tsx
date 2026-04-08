import { DataPageError } from "@/components/data-page-error";
import { TrainingDetailWorkspace } from "@/components/training-detail-workspace";
import {
  getTeamTrainingDetail,
  getTeamTrainingDetailEndpoint,
} from "@/lib/team-api";

export const dynamic = "force-dynamic";

type TrainingDetailPageProps = {
  params: Promise<{
    trainingId: string;
  }>;
  searchParams?: Promise<{
    from?: string;
    tab?: string;
    year?: string;
    month?: string;
    view?: string;
  }>;
};

function parseInteger(value: string | undefined) {
  if (!value) {
    return undefined;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function buildCalendarHref(year?: number, month?: number, view?: string) {
  const searchParams = new URLSearchParams();

  if (year) {
    searchParams.set("year", String(year));
  }
  if (month) {
    searchParams.set("month", String(month));
  }
  if (view === "list") {
    searchParams.set("view", "list");
  }

  return searchParams.size > 0 ? `/calendar?${searchParams.toString()}` : "/calendar";
}

function buildTrainingListHref(year?: number) {
  if (!year) {
    return "/training";
  }

  return `/training?year=${year}`;
}

function buildTrainingDetailTabHref(
  trainingId: string,
  params: {
    fromCalendar: boolean;
    month?: number;
    tab: "session" | "gps";
    view?: string;
    year?: number;
  },
) {
  const searchParams = new URLSearchParams();

  if (params.fromCalendar) {
    searchParams.set("from", "calendar");
  }
  if (params.year) {
    searchParams.set("year", String(params.year));
  }
  if (params.month) {
    searchParams.set("month", String(params.month));
  }
  if (params.view === "list") {
    searchParams.set("view", "list");
  }
  if (params.tab !== "session") {
    searchParams.set("tab", params.tab);
  }

  const query = searchParams.toString();
  return query ? `/training/${trainingId}?${query}` : `/training/${trainingId}`;
}

export default async function TrainingDetailPage({
  params,
  searchParams,
}: TrainingDetailPageProps) {
  const { trainingId } = await params;
  const resolvedSearchParams = (await searchParams) ?? {};
  const year = parseInteger(resolvedSearchParams.year);
  const month = parseInteger(resolvedSearchParams.month);
  const view = resolvedSearchParams.view === "list" ? "list" : undefined;
  const activeView = resolvedSearchParams.tab === "gps" ? "gps" : "session";
  const fromCalendar = resolvedSearchParams.from === "calendar";

  try {
    const data = await getTeamTrainingDetail(trainingId);
    const trainingDate = new Date(`${data.training.training_date}T00:00:00`);
    const fallbackYear = trainingDate.getFullYear();
    const fallbackMonth = trainingDate.getMonth() + 1;
    const backHref = fromCalendar
      ? buildCalendarHref(year ?? fallbackYear, month ?? fallbackMonth, view)
      : buildTrainingListHref(year ?? fallbackYear);
    const tabBaseParams = {
      fromCalendar,
      month: month ?? (fromCalendar ? fallbackMonth : undefined),
      view,
      year: year ?? fallbackYear,
    };

    return (
      <TrainingDetailWorkspace
        activeView={activeView}
        backHref={backHref}
        backLabel={fromCalendar ? "캘린더로" : "훈련 목록으로"}
        data={data}
        tabHrefs={{
          session: buildTrainingDetailTabHref(trainingId, {
            ...tabBaseParams,
            tab: "session",
          }),
          gps: buildTrainingDetailTabHref(trainingId, {
            ...tabBaseParams,
            tab: "gps",
          }),
        }}
      />
    );
  } catch (error) {
    return (
      <DataPageError
        description="훈련 상세 데이터를 불러오지 못했습니다. training detail API 연결이 복구되면 세션 브리프와 선수별 GPS가 표시됩니다."
        endpoint={getTeamTrainingDetailEndpoint(trainingId)}
        error={error}
        eyebrow="Training Detail"
        title="훈련 상세 데이터를 불러오지 못했습니다"
      />
    );
  }
}
