import {
  avoidKeywords,
  colorGuideSections,
  toneKeywords,
} from "@/lib/design-tokens";

export function ColorGuide() {
  return (
    <section className="guide-section" aria-labelledby="color-guide-title">
      <div className="section-head section-head--stacked">
        <div>
          <p className="eyebrow">Design Guide</p>
          <h2 id="color-guide-title">축구팀 내부 데이터 시스템용 컬러 가이드</h2>
          <p className="description">
            딥그린을 중심으로 중립색과 상태색을 제한적으로 조합해 신뢰감 있는
            분석 화면을 구성합니다.
          </p>
        </div>
      </div>

      <div className="guide-grid">
        {colorGuideSections.map((section) => (
          <article className="guide-card" key={section.title}>
            <div className="guide-card__header">
              <div>
                <p className="panel-eyebrow">{section.title}</p>
                <h3>{section.description}</h3>
              </div>
            </div>

            <div className="swatch-grid">
              {section.items.map((item) => (
                <div className="swatch-card" key={item.name}>
                  <div
                    aria-hidden="true"
                    className="swatch-chip"
                    style={{ backgroundColor: item.value }}
                  />
                  <div className="swatch-copy">
                    <strong>{item.name}</strong>
                    <span>{item.value}</span>
                    <p>{item.usage}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="guide-preview-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Component Usage</p>
              <h3>버튼 적용 예시</h3>
            </div>
            <p className="panel-note">
              CTA는 딥그린, 보조 액션은 화이트 기반으로 유지
            </p>
          </div>

          <div className="button-row">
            <button className="primary-button" type="button">
              Primary Button
            </button>
            <button className="secondary-button" type="button">
              Secondary Button
            </button>
            <button className="ghost-button" type="button">
              Ghost Button
            </button>
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Tone &amp; Manner</p>
              <h3>화면 운영 원칙</h3>
            </div>
            <p className="panel-note">상태 컬러는 필요한 지점에만 제한적으로 사용</p>
          </div>

          <div className="keyword-columns">
            <div>
              <span className="keyword-label">지향 키워드</span>
              <div className="keyword-list">
                {toneKeywords.map((keyword) => (
                  <span className="keyword-chip keyword-chip--positive" key={keyword}>
                    {keyword}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <span className="keyword-label">지양 항목</span>
              <div className="keyword-list">
                {avoidKeywords.map((keyword) => (
                  <span className="keyword-chip keyword-chip--neutral" key={keyword}>
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}
