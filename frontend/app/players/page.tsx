import { DataPageError } from "@/components/data-page-error";
import { PlayersDirectory } from "@/components/players-directory";
import {
  getPlayersDirectoryData,
  getPlayersDirectoryEndpoint,
} from "@/lib/data-store";

export const dynamic = "force-dynamic";

export default async function PlayersPage() {
  try {
    const data = await getPlayersDirectoryData();

    return (
      <main className="page">
        <PlayersDirectory
          latestSeasonYear={data.latestSeasonYear}
          medicalAvailability={data.medicalAvailability}
          seasonSummaries={data.playerSeasonSummary}
        />
      </main>
    );
  } catch (error) {
    return (
      <DataPageError
        description="선수 목록 데이터를 불러오지 못했습니다. 백엔드 players-directory API가 복구되면 로스터 검색 화면이 표시됩니다."
        endpoint={getPlayersDirectoryEndpoint()}
        error={error}
        eyebrow="Players"
        title="선수 목록 데이터를 불러오지 못했습니다"
      />
    );
  }
}
