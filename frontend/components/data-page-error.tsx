type DataPageErrorProps = {
  eyebrow: string;
  title: string;
  description: string;
  endpoint: string;
  error: unknown;
};

export function DataPageError({
  eyebrow,
  title,
  description,
  endpoint,
  error,
}: DataPageErrorProps) {
  return (
    <main className="page">
      <section className="section-head">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="description">{description}</p>
        </div>
      </section>

      <section className="panel">
        <div className="empty-state">
          <strong>데이터 소스</strong>
          <p>{endpoint}</p>
          <p>{error instanceof Error ? error.message : "Unknown error"}</p>
        </div>
      </section>
    </main>
  );
}
