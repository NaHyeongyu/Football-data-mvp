export const brandColors = {
  primary950: "#071A33",
  primary900: "#0B2545",
  primary800: "#123A6F",
  baseWhite: "#FFFFFF",
} as const;

export const neutralColors = {
  background: "#F5F9FF",
  surface: "#FFFFFF",
  border: "#D7E4F5",
  textPrimary: "#10233F",
  textSecondary: "#5D718F",
  disabled: "#A9B8CC",
  tableHeader: "#EEF5FF",
  tableRowHover: "#F3F8FF",
  placeholder: "#7F91AB",
} as const;

export const statusColors = {
  success: "#2F8C5B",
  warning: "#D4A72C",
  danger: "#C94C4C",
  info: "#2563EB",
} as const;

export const chartColors = {
  primaryDark: "#0B2545",
  primaryMid: "#1D4ED8",
  skyBlue: "#3B82F6",
  paleBlue: "#93C5FD",
  lightBlue: "#DBEAFE",
  positive: "#2F8C5B",
  caution: "#D4A72C",
  risk: "#C94C4C",
} as const;

export const semanticColors = {
  appBackground: neutralColors.background,
  cardBackground: neutralColors.surface,
  cardBorder: neutralColors.border,
  textDefault: neutralColors.textPrimary,
  textMuted: neutralColors.textSecondary,
  headerBackground: brandColors.primary900,
  headerActive: brandColors.primary800,
  headerText: brandColors.baseWhite,
  buttonPrimary: brandColors.primary900,
  buttonPrimaryHover: brandColors.primary800,
  buttonSecondaryBorder: brandColors.primary800,
  inputBorderFocus: brandColors.primary800,
} as const;

export const colorGuideSections = [
  {
    title: "Brand Core",
    description: "브랜드 중심 컬러와 네이비 UI 축",
    items: [
      {
        name: "Primary 900",
        value: brandColors.primary900,
        usage: "헤더, 사이드바, 주요 CTA, 선택 메뉴",
      },
      {
        name: "Primary 800",
        value: brandColors.primary800,
        usage: "서브 버튼, 활성 탭, 카드 헤더, 주요 차트 라인",
      },
      {
        name: "Base White",
        value: brandColors.baseWhite,
        usage: "메인 콘텐츠, 카드, 입력창, 다크 배경 위 텍스트",
      },
    ],
  },
  {
    title: "Neutral System",
    description: "데이터 화면의 기본 대비와 가독성 레이어",
    items: [
      {
        name: "Background",
        value: neutralColors.background,
        usage: "페이지 전체 배경",
      },
      {
        name: "Surface",
        value: neutralColors.surface,
        usage: "카드, 테이블, 모달 배경",
      },
      {
        name: "Border",
        value: neutralColors.border,
        usage: "카드 보더, 입력창 라인",
      },
      {
        name: "Text Primary",
        value: neutralColors.textPrimary,
        usage: "본문 핵심 텍스트",
      },
      {
        name: "Text Secondary",
        value: neutralColors.textSecondary,
        usage: "보조 설명, 메타 정보",
      },
      {
        name: "Disabled",
        value: neutralColors.disabled,
        usage: "비활성 상태",
      },
    ],
  },
  {
    title: "Status Colors",
    description: "상태 변화, 경고, 완료, 위험 표시용",
    items: [
      {
        name: "Success",
        value: statusColors.success,
        usage: "정상, 상승, 완료",
      },
      {
        name: "Warning",
        value: statusColors.warning,
        usage: "주의, 관리 필요",
      },
      {
        name: "Danger",
        value: statusColors.danger,
        usage: "부상 위험, 하락, 경고",
      },
      {
        name: "Info",
        value: statusColors.info,
        usage: "중립 정보, 보조 배지",
      },
    ],
  },
  {
    title: "Chart Palette",
    description: "성능 추이와 위험도 시각화를 위한 확장 팔레트",
    items: [
      {
        name: "Primary Dark",
        value: chartColors.primaryDark,
        usage: "핵심 비교선",
      },
      {
        name: "Primary Mid",
        value: chartColors.primaryMid,
        usage: "평점, 퍼포먼스 추이",
      },
      {
        name: "Sky Blue",
        value: chartColors.skyBlue,
        usage: "피지컬 변화, 보조 지표",
      },
      {
        name: "Pale Blue",
        value: chartColors.paleBlue,
        usage: "평균선, 비교 기준선",
      },
      {
        name: "Light Blue",
        value: chartColors.lightBlue,
        usage: "영역 채움, 보조 배경",
      },
    ],
  },
] as const;

export const toneKeywords = [
  "신뢰감",
  "차분함",
  "분석적",
  "현장형",
  "전문적",
] as const;

export const avoidKeywords = [
  "형광톤 남용",
  "과도한 원색",
  "화려한 그라데이션",
  "카드별 무분별한 색 분산",
] as const;
