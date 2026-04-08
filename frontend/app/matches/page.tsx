import { DataPageError } from "@/components/data-page-error";
import { TeamMatchesBoard } from "@/components/team-matches-board";
import { getTeamMatches, getTeamMatchesEndpoint } from "@/lib/team-api";

export const dynamic = "force-dynamic";

type MatchesPageProps = {
  searchParams?: Promise<{
    year?: string;
  }>;
};

function parseInteger(value: string | undefined) {
  if (!value) {
    return undefined;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export default async function MatchesPage({
  searchParams,
}: MatchesPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const year = parseInteger(resolvedSearchParams.year);

  try {
    const data = await getTeamMatches({ year });

    return (
      <main className="page">
        <TeamMatchesBoard data={data} />
      </main>
    );
  } catch (error) {
    return (
      <DataPageError
        description="연간 경기 리스트 데이터를 불러오지 못했습니다. 팀 matches API 연결이 복구되면 경기 요약과 전체 리스트가 표시됩니다."
        endpoint={getTeamMatchesEndpoint({ year })}
        error={error}
        eyebrow="Matches"
        title="연간 경기 리스트 데이터를 불러오지 못했습니다"
      />
    );
  }
}
