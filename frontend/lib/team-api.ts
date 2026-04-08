import type {
  PhysicalOverviewPayload,
  PlayerDetailPayload,
  PlayersDirectoryPayload,
} from "@/lib/data-types";
import type {
  PlayerDevelopmentReportResponse,
  PlayerInjuryRiskResponse,
  PlayerPerformanceReadinessResponse,
  TeamCalendarResponse,
  TeamMatchDetailResponse,
  TeamMatchListResponse,
  TeamOverviewResponse,
  TeamTrainingDetailResponse,
  TeamTrainingListResponse,
} from "@/lib/team-api-types";

const DEFAULT_BACKEND_API_BASE_URL = "http://127.0.0.1:8000";

export function getBackendApiBaseUrl() {
  return (
    process.env.BACKEND_API_BASE_URL ??
    process.env.API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    DEFAULT_BACKEND_API_BASE_URL
  );
}

export function getTeamOverviewEndpoint(asOfDate?: string) {
  if (!asOfDate) {
    return `${getBackendApiBaseUrl()}/api/team/overview`;
  }

  const searchParams = new URLSearchParams();
  searchParams.set("as_of_date", asOfDate);
  return `${getBackendApiBaseUrl()}/api/team/overview?${searchParams.toString()}`;
}

export async function getTeamOverview(asOfDate?: string) {
  const response = await fetch(getTeamOverviewEndpoint(asOfDate), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as TeamOverviewResponse;
}

export function getPlayerInjuryRiskEndpoint(params?: {
  asOfDate?: string;
  riskBand?: string;
  limit?: number;
}) {
  const searchParams = new URLSearchParams();

  if (params?.asOfDate) {
    searchParams.set("as_of_date", params.asOfDate);
  }
  if (params?.riskBand) {
    searchParams.set("risk_band", params.riskBand);
  }
  if (typeof params?.limit === "number") {
    searchParams.set("limit", String(params.limit));
  }

  const query = searchParams.toString();
  return `${getBackendApiBaseUrl()}/api/players/injury-risk${query ? `?${query}` : ""}`;
}

export async function getPlayerInjuryRisk(params?: {
  asOfDate?: string;
  riskBand?: string;
  limit?: number;
}) {
  const response = await fetch(getPlayerInjuryRiskEndpoint(params), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as PlayerInjuryRiskResponse;
}

export function getPlayerPerformanceReadinessEndpoint(params?: {
  asOfDate?: string;
  readinessBand?: string;
  limit?: number;
}) {
  const searchParams = new URLSearchParams();

  if (params?.asOfDate) {
    searchParams.set("as_of_date", params.asOfDate);
  }
  if (params?.readinessBand) {
    searchParams.set("readiness_band", params.readinessBand);
  }
  if (typeof params?.limit === "number") {
    searchParams.set("limit", String(params.limit));
  }

  const query = searchParams.toString();
  return `${getBackendApiBaseUrl()}/api/players/performance-readiness${query ? `?${query}` : ""}`;
}

export async function getPlayerPerformanceReadiness(params?: {
  asOfDate?: string;
  readinessBand?: string;
  limit?: number;
}) {
  const response = await fetch(getPlayerPerformanceReadinessEndpoint(params), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as PlayerPerformanceReadinessResponse;
}

export function getPlayerDevelopmentReportEndpoint(params?: {
  asOfDate?: string;
  growthBand?: string;
  limit?: number;
}) {
  const searchParams = new URLSearchParams();

  if (params?.asOfDate) {
    searchParams.set("as_of_date", params.asOfDate);
  }
  if (params?.growthBand) {
    searchParams.set("growth_band", params.growthBand);
  }
  if (typeof params?.limit === "number") {
    searchParams.set("limit", String(params.limit));
  }

  const query = searchParams.toString();
  return `${getBackendApiBaseUrl()}/api/players/development-report${query ? `?${query}` : ""}`;
}

export async function getPlayerDevelopmentReport(params?: {
  asOfDate?: string;
  growthBand?: string;
  limit?: number;
}) {
  const response = await fetch(getPlayerDevelopmentReportEndpoint(params), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as PlayerDevelopmentReportResponse;
}

export function getTeamCalendarEndpoint(params?: {
  year?: number;
  month?: number;
}) {
  const searchParams = new URLSearchParams();

  if (params?.year) {
    searchParams.set("year", String(params.year));
  }
  if (params?.month) {
    searchParams.set("month", String(params.month));
  }

  const query = searchParams.toString();
  return `${getBackendApiBaseUrl()}/api/team/calendar${query ? `?${query}` : ""}`;
}

export async function getTeamCalendar(params?: {
  year?: number;
  month?: number;
}) {
  const response = await fetch(getTeamCalendarEndpoint(params), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as TeamCalendarResponse;
}

export function getTeamTrainingDetailEndpoint(trainingId: string) {
  return `${getBackendApiBaseUrl()}/api/team/training/${trainingId}`;
}

export async function getTeamTrainingDetail(trainingId: string) {
  const response = await fetch(getTeamTrainingDetailEndpoint(trainingId), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as TeamTrainingDetailResponse;
}

export function getTeamTrainingsEndpoint(params?: {
  year?: number;
}) {
  const searchParams = new URLSearchParams();

  if (params?.year) {
    searchParams.set("year", String(params.year));
  }

  const query = searchParams.toString();
  return `${getBackendApiBaseUrl()}/api/team/trainings${query ? `?${query}` : ""}`;
}

export async function getTeamTrainings(params?: {
  year?: number;
}) {
  const response = await fetch(getTeamTrainingsEndpoint(params), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as TeamTrainingListResponse;
}

export function getTeamMatchesEndpoint(params?: {
  year?: number;
}) {
  const searchParams = new URLSearchParams();

  if (params?.year) {
    searchParams.set("year", String(params.year));
  }

  const query = searchParams.toString();
  return `${getBackendApiBaseUrl()}/api/team/matches${query ? `?${query}` : ""}`;
}

export async function getTeamMatches(params?: {
  year?: number;
}) {
  const response = await fetch(getTeamMatchesEndpoint(params), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as TeamMatchListResponse;
}

export function getTeamMatchDetailEndpoint(matchId: string) {
  return `${getBackendApiBaseUrl()}/api/team/matches/${matchId}`;
}

export async function getTeamMatchDetail(matchId: string) {
  const response = await fetch(getTeamMatchDetailEndpoint(matchId), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as TeamMatchDetailResponse;
}

export function getPlayersDirectoryEndpoint() {
  return `${getBackendApiBaseUrl()}/api/frontend/players-directory`;
}

export async function getPlayersDirectory() {
  const response = await fetch(getPlayersDirectoryEndpoint(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as PlayersDirectoryPayload;
}

export function getFrontendPlayerDetailEndpoint(playerId: string) {
  return `${getBackendApiBaseUrl()}/api/frontend/players/${playerId}`;
}

export async function getFrontendPlayerDetail(playerId: string) {
  const response = await fetch(getFrontendPlayerDetailEndpoint(playerId), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as PlayerDetailPayload;
}

export function getPhysicalOverviewEndpoint() {
  return `${getBackendApiBaseUrl()}/api/frontend/physical-overview`;
}

export async function getPhysicalOverview() {
  const response = await fetch(getPhysicalOverviewEndpoint(), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as PhysicalOverviewPayload;
}
