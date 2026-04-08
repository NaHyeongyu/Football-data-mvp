export type DashboardMetric = {
  label: string;
  value: string;
  description: string;
};

export type DashboardMatch = {
  id: number;
  date: string;
  league: string;
  homeTeam: string;
  awayTeam: string;
  score: string;
  possession: string;
  keyPlayer: string;
};

export const dashboardMetrics: DashboardMetric[] = [
  {
    label: "등록 경기",
    value: "128",
    description: "이번 시즌 적재된 경기 수",
  },
  {
    label: "활성 팀",
    value: "24",
    description: "현재 분석에 포함된 팀 수",
  },
  {
    label: "평균 득점",
    value: "2.67",
    description: "경기당 평균 총 득점",
  },
];

export const dashboardMatches: DashboardMatch[] = [
  {
    id: 1,
    date: "2025-03-01",
    league: "K League 1",
    homeTeam: "FC Seoul",
    awayTeam: "Ulsan HD",
    score: "2 - 1",
    possession: "54:46",
    keyPlayer: "Stanislav Iljutcenko",
  },
  {
    id: 2,
    date: "2025-03-02",
    league: "K League 1",
    homeTeam: "Jeonbuk Hyundai",
    awayTeam: "Pohang Steelers",
    score: "1 - 1",
    possession: "51:49",
    keyPlayer: "Lee Dong-jun",
  },
  {
    id: 3,
    date: "2025-03-08",
    league: "K League 1",
    homeTeam: "Ulsan HD",
    awayTeam: "Jeonbuk Hyundai",
    score: "3 - 0",
    possession: "58:42",
    keyPlayer: "Martin Adam",
  },
];
