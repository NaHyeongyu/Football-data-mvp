import { redirect } from "next/navigation";

type LegacyTrainingDetailPageProps = {
  searchParams?: Promise<{
    eventId?: string;
    year?: string;
    month?: string;
    view?: string;
  }>;
};

export default async function LegacyTrainingDetailPage({
  searchParams,
}: LegacyTrainingDetailPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const eventId = resolvedSearchParams.eventId;

  if (!eventId) {
    redirect("/training");
  }

  const query = new URLSearchParams({
    from: "calendar",
  });

  if (resolvedSearchParams.year) {
    query.set("year", resolvedSearchParams.year);
  }
  if (resolvedSearchParams.month) {
    query.set("month", resolvedSearchParams.month);
  }
  if (resolvedSearchParams.view === "list") {
    query.set("view", "list");
  }

  redirect(`/training/${eventId}?${query.toString()}`);
}
