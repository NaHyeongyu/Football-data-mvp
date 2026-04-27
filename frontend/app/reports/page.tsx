import { DataPageError } from "@/components/data-page-error";
import { PlayerReportWorkspace } from "@/components/player-report-workspace";
import {
  getPlayerDetail,
  getPlayerFrontendDetailEndpoint,
  getPlayersDirectoryData,
  getPlayersDirectoryEndpoint,
} from "@/lib/data-store";

export const dynamic = "force-dynamic";

type ReportsPageProps = {
  searchParams: Promise<{
    period?: string;
    playerId?: string;
  }>;
};

export default async function ReportsPage({ searchParams }: ReportsPageProps) {
  const params = await searchParams;
  const selectedPlayerId = params.playerId?.trim() || null;
  const selectedPeriod = params.period?.trim() || null;

  try {
    const directoryData = await getPlayersDirectoryData();
    const detail = selectedPlayerId ? await getPlayerDetail(selectedPlayerId) : null;

    return (
      <main className="page">
        <PlayerReportWorkspace
          detail={detail}
          directoryData={directoryData}
          selectedPeriod={selectedPeriod}
          selectedPlayerId={selectedPlayerId}
        />
      </main>
    );
  } catch (error) {
    const endpoint = selectedPlayerId
      ? getPlayerFrontendDetailEndpoint(selectedPlayerId)
      : getPlayersDirectoryEndpoint();

    return (
      <DataPageError
        description="보고서 생성에 필요한 선수 데이터를 불러오지 못했습니다. 백엔드 API가 복구되면 선수별 보고서를 생성할 수 있습니다."
        endpoint={endpoint}
        error={error}
        eyebrow="Reports"
        title="보고서 데이터를 불러오지 못했습니다"
      />
    );
  }
}
