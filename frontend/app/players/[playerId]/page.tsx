import { DataPageError } from "@/components/data-page-error";
import { PlayerDetailWorkspace } from "@/components/player-detail-workspace";
import {
  getPlayerDetail,
  getPlayerFrontendDetailEndpoint,
} from "@/lib/data-store";

export const dynamic = "force-dynamic";

type PlayerDetailPageProps = {
  params: Promise<{ playerId: string }>;
};

export default async function PlayerDetailPage({
  params,
}: PlayerDetailPageProps) {
  const { playerId } = await params;

  try {
    const data = await getPlayerDetail(playerId);

    return (
      <main className="page">
        <PlayerDetailWorkspace data={data} />
      </main>
    );
  } catch (error) {
    return (
      <DataPageError
        description="선수 상세 데이터를 불러오지 못했습니다. 백엔드 선수 상세 API가 복구되면 탭형 상세 화면이 표시됩니다."
        endpoint={getPlayerFrontendDetailEndpoint(playerId)}
        error={error}
        eyebrow="Player Detail"
        title="선수 상세 데이터를 불러오지 못했습니다"
      />
    );
  }
}
