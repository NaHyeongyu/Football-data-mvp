import { DataPageError } from "@/components/data-page-error";
import { MatchDetailWorkspace } from "@/components/match-detail-workspace";
import { getTeamMatchDetail, getTeamMatchDetailEndpoint } from "@/lib/team-api";

export const dynamic = "force-dynamic";

type MatchDetailPageProps = {
  params: Promise<{
    matchId: string;
  }>;
};

export default async function MatchDetailPage({
  params,
}: MatchDetailPageProps) {
  const { matchId } = await params;

  try {
    const data = await getTeamMatchDetail(matchId);
    return <MatchDetailWorkspace data={data} />;
  } catch (error) {
    return (
      <DataPageError
        description="경기 상세 데이터를 불러오지 못했습니다. match detail API 연결이 복구되면 경기 메타와 선수별 기록이 표시됩니다."
        endpoint={getTeamMatchDetailEndpoint(matchId)}
        error={error}
        eyebrow="Match Detail"
        title="경기 상세 데이터를 불러오지 못했습니다"
      />
    );
  }
}
