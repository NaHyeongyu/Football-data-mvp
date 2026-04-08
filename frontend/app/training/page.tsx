import { DataPageError } from "@/components/data-page-error";
import { TeamTrainingsBoard } from "@/components/team-trainings-board";
import { getTeamTrainings, getTeamTrainingsEndpoint } from "@/lib/team-api";

export const dynamic = "force-dynamic";

type TrainingPageProps = {
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

export default async function TrainingPage({
  searchParams,
}: TrainingPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const year = parseInteger(resolvedSearchParams.year);

  try {
    const data = await getTeamTrainings({ year });

    return (
      <main className="page">
        <TeamTrainingsBoard data={data} />
      </main>
    );
  } catch (error) {
    return (
      <DataPageError
        description="연간 훈련 리스트 데이터를 불러오지 못했습니다. team trainings API 연결이 복구되면 훈련 요약과 전체 리스트가 표시됩니다."
        endpoint={getTeamTrainingsEndpoint({ year })}
        error={error}
        eyebrow="Training"
        title="연간 훈련 리스트 데이터를 불러오지 못했습니다"
      />
    );
  }
}
