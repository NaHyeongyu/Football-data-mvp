import {
  getFrontendPlayerDetail,
  getFrontendPlayerDetailEndpoint,
  getPhysicalOverview,
  getPhysicalOverviewEndpoint,
  getPlayersDirectory,
  getPlayersDirectoryEndpoint,
} from "@/lib/team-api";

export {
  getFrontendPlayerDetailEndpoint as getPlayerFrontendDetailEndpoint,
  getPhysicalOverviewEndpoint,
  getPlayersDirectoryEndpoint,
};

export async function getPlayersDirectoryData() {
  return getPlayersDirectory();
}

export async function getPlayerDetail(playerId: string) {
  return getFrontendPlayerDetail(playerId);
}

export async function getPhysicalOverviewData() {
  return getPhysicalOverview();
}
