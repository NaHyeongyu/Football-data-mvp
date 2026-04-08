import { DataPageError } from "@/components/data-page-error";
import { TeamCalendarBoard } from "@/components/team-calendar-board";
import { getTeamCalendar, getTeamCalendarEndpoint } from "@/lib/team-api";

export const dynamic = "force-dynamic";

type CalendarPageProps = {
  searchParams?: Promise<{
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

export default async function CalendarPage({
  searchParams,
}: CalendarPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const year = parseInteger(resolvedSearchParams.year);
  const month = parseInteger(resolvedSearchParams.month);
  const view = resolvedSearchParams.view === "list" ? "list" : "calendar";

  try {
    const data = await getTeamCalendar({ year, month });

    return (
      <main className="page page--calendar">
        <TeamCalendarBoard data={data} view={view} />
      </main>
    );
  } catch (error) {
    return (
      <DataPageError
        description="월간 일정 캘린더 데이터를 불러오지 못했습니다. 팀 calendar API 연결이 복구되면 일정 보드와 상세 리스트가 표시됩니다."
        endpoint={getTeamCalendarEndpoint({ year, month })}
        error={error}
        eyebrow="Calendar"
        title="일정 캘린더 데이터를 불러오지 못했습니다"
      />
    );
  }
}
