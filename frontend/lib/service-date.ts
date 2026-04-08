export const SERVICE_REFERENCE_DATE = "2025-12-31";

export function formatServiceReferenceDate() {
  const [year, month, day] = SERVICE_REFERENCE_DATE.split("-").map(Number);

  return `${year}.${String(month).padStart(2, "0")}.${String(day).padStart(2, "0")}`;
}
