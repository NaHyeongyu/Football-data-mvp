import Link from "next/link";

import type {
  TeamCalendarEvent,
  TeamCalendarResponse,
} from "@/lib/team-api-types";

const weekdayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const timeFormatter = new Intl.DateTimeFormat("ko-KR", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});
const listDateFormatter = new Intl.DateTimeFormat("ko-KR", {
  month: "numeric",
  day: "numeric",
  weekday: "short",
});

type CalendarViewMode = "calendar" | "list";

function buildCalendarHref(year: number, month: number, view: CalendarViewMode) {
  const query = new URLSearchParams({
    year: String(year),
    month: String(month),
  });

  if (view === "list") {
    query.set("view", "list");
  }

  return `/calendar?${query.toString()}`;
}

function buildTrainingDetailHref(
  eventId: string,
  year: number,
  month: number,
  view: CalendarViewMode,
) {
  const query = new URLSearchParams({
    from: "calendar",
    year: String(year),
    month: String(month),
  });

  if (view === "list") {
    query.set("view", "list");
  }

  return `/training/${eventId}?${query.toString()}`;
}

function dateKey(year: number, month: number, day: number) {
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function compareEvents(left: TeamCalendarEvent, right: TeamCalendarEvent) {
  const dateCompare = left.event_date.localeCompare(right.event_date);
  if (dateCompare !== 0) {
    return dateCompare;
  }

  const leftTime = left.start_at ?? `${left.event_date}T23:59:59`;
  const rightTime = right.start_at ?? `${right.event_date}T23:59:59`;
  const timeCompare = leftTime.localeCompare(rightTime);
  if (timeCompare !== 0) {
    return timeCompare;
  }

  return left.title.localeCompare(right.title, "ko-KR");
}

function formatTimeRange(event: TeamCalendarEvent) {
  if (!event.start_at) {
    return event.event_type === "match" ? "시간 미기록" : "시간 미정";
  }

  const start = timeFormatter.format(new Date(event.start_at));
  if (!event.end_at) {
    return start;
  }

  return `${start} - ${timeFormatter.format(new Date(event.end_at))}`;
}

function gridItemTone(event: TeamCalendarEvent) {
  if (event.event_type === "match") {
    return event.category === "공식"
      ? "calendar-grid-item calendar-grid-item--official"
      : "calendar-grid-item calendar-grid-item--match";
  }

  if (event.intensity_level === "high") {
    return "calendar-grid-item calendar-grid-item--high";
  }

  return "calendar-grid-item calendar-grid-item--training";
}

function eventPillTone(event: TeamCalendarEvent) {
  if (event.event_type === "match") {
    return event.category === "공식"
      ? "calendar-event-pill calendar-event-pill--official"
      : "calendar-event-pill calendar-event-pill--match";
  }

  if (event.intensity_level === "high") {
    return "calendar-event-pill calendar-event-pill--high";
  }

  return "calendar-event-pill calendar-event-pill--training";
}

function eventTagLabel(event: TeamCalendarEvent) {
  if (event.event_type === "match") {
    return event.category === "공식" ? "공식전" : "연습경기";
  }

  if (event.intensity_level === "very_high") {
    return "high";
  }
  if (event.intensity_level === "high") {
    return "high";
  }
  if (event.intensity_level === "medium") {
    return "medium";
  }
  if (event.intensity_level === "low") {
    return "low";
  }

  return "훈련";
}

function eventHeadline(event: TeamCalendarEvent) {
  if (event.event_type === "match") {
    return event.opponent_team ?? event.title;
  }

  return event.title;
}

function buildEventDetailHref(
  event: TeamCalendarEvent,
  selectedYear: number,
  selectedMonth: number,
  view: CalendarViewMode,
) {
  if (event.event_type === "match") {
    return `/matches/${event.event_id}`;
  }

  return buildTrainingDetailHref(event.event_id, selectedYear, selectedMonth, view);
}

function eventListMeta(event: TeamCalendarEvent) {
  const parts = [formatTimeRange(event)];

  if (event.location) {
    parts.push(event.location);
  }

  return parts.join(" · ");
}

export function TeamCalendarBoard({
  data,
  view,
}: {
  data: TeamCalendarResponse;
  view: CalendarViewMode;
}) {
  const availableYears = Array.from(
    new Set(data.available_months.map((item) => item.year)),
  ).sort((left, right) => right - left);
  const monthIndex = data.available_months.findIndex(
    (item) => item.year === data.selected_year && item.month === data.selected_month,
  );
  const nextMonth =
    monthIndex >= 0 && monthIndex < data.available_months.length - 1
      ? data.available_months[monthIndex + 1]
      : null;
  const firstWeekday = new Date(
    Date.UTC(data.selected_year, data.selected_month - 1, 1),
  ).getUTCDay();
  const daysInMonth = new Date(
    Date.UTC(data.selected_year, data.selected_month, 0),
  ).getUTCDate();
  const sortedEvents = [...data.events].sort(compareEvents);
  const eventsByDate = new Map<string, TeamCalendarEvent[]>();

  sortedEvents.forEach((event) => {
    const existing = eventsByDate.get(event.event_date) ?? [];
    existing.push(event);
    eventsByDate.set(event.event_date, existing);
  });

  const cells: Array<{ day: number | null; events: TeamCalendarEvent[] }> = [];

  for (let index = 0; index < firstWeekday; index += 1) {
    cells.push({ day: null, events: [] });
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push({
      day,
      events: eventsByDate.get(dateKey(data.selected_year, data.selected_month, day)) ?? [],
    });
  }

  while (cells.length % 7 !== 0) {
    cells.push({ day: null, events: [] });
  }

  return (
    <section className="panel calendar-board" id="calendar-month">
      <div className="calendar-nav">
        <div className="calendar-nav__title">
          <p className="panel-eyebrow">Calendar</p>
          <h1>{data.selected_label}</h1>
        </div>

        <div className="calendar-nav__actions">
          <div className="calendar-nav__group">
            <div className="calendar-nav__toggle">
              <Link
                className={
                  view === "calendar"
                    ? "calendar-nav__toggle-link calendar-nav__toggle-link--active"
                    : "calendar-nav__toggle-link"
                }
                href={buildCalendarHref(data.selected_year, data.selected_month, "calendar")}
              >
                캘린더형
              </Link>
              <Link
                className={
                  view === "list"
                    ? "calendar-nav__toggle-link calendar-nav__toggle-link--active"
                    : "calendar-nav__toggle-link"
                }
                href={buildCalendarHref(data.selected_year, data.selected_month, "list")}
              >
                리스트형
              </Link>
            </div>
          </div>

          <div className="calendar-nav__group calendar-nav__group--selectors">
            <form action="/calendar" className="calendar-period-select" method="get">
              {view === "list" ? <input name="view" type="hidden" value="list" /> : null}

              <label className="calendar-select-field">
                <span>연도</span>
                <select defaultValue={String(data.selected_year)} name="year">
                  {availableYears.map((year) => (
                    <option key={year} value={String(year)}>
                      {year}년
                    </option>
                  ))}
                </select>
              </label>

              <label className="calendar-select-field">
                <span>월</span>
                <select defaultValue={String(data.selected_month)} name="month">
                  {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                    <option key={month} value={String(month)}>
                      {month}월
                    </option>
                  ))}
                </select>
              </label>

              <button className="ghost-button" type="submit">
                이동
              </button>
            </form>
          </div>

          {nextMonth ? (
            <div className="calendar-nav__pager">
              <Link
                className="ghost-button"
                href={buildCalendarHref(nextMonth.year, nextMonth.month, view)}
              >
                다음 월
              </Link>
            </div>
          ) : null}
        </div>
      </div>

      {view === "calendar" ? (
        <div className="calendar-grid-shell">
          <div className="calendar-grid">
            {weekdayLabels.map((label, index) => (
              <div
                className={
                  index === 0 || index === 6
                    ? "calendar-grid__weekday calendar-grid__weekday--weekend"
                    : "calendar-grid__weekday"
                }
                key={label}
              >
                {label}
              </div>
            ))}

            {cells.map((cell, index) => (
              <div
                className={
                  cell.day === null
                    ? "calendar-grid__cell calendar-grid__cell--empty"
                    : "calendar-grid__cell"
                }
                key={`${cell.day ?? "empty"}-${index}`}
              >
                {cell.day !== null ? (
                  <>
                    <div className="calendar-grid__cell-head">
                      <div className="calendar-grid__day">{cell.day}</div>
                      {cell.events.length > 0 ? (
                        <span className="calendar-grid__count">{cell.events.length}</span>
                      ) : null}
                    </div>
                    <div className="calendar-grid__events">
                      {cell.events.slice(0, 2).map((event) => (
                        <Link
                          className={`${gridItemTone(event)} calendar-grid-link`}
                          href={buildEventDetailHref(
                            event,
                            data.selected_year,
                            data.selected_month,
                            view,
                          )}
                          key={event.event_id}
                        >
                          <span className="calendar-grid-item__label">{eventTagLabel(event)}</span>
                          <strong>{eventHeadline(event)}</strong>
                          <p>{formatTimeRange(event)}</p>
                        </Link>
                      ))}
                      {cell.events.length > 2 ? (
                        <span className="calendar-grid__more">+{cell.events.length - 2}</span>
                      ) : null}
                    </div>
                  </>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : sortedEvents.length === 0 ? (
        <div className="empty-state">
          <strong>해당 월 일정 없음</strong>
          <p>선택한 월에는 기록된 일정이 없습니다.</p>
        </div>
      ) : (
        <div className="calendar-list">
          {sortedEvents.map((event) => (
            <Link
              className="calendar-list-item calendar-list-link"
              href={buildEventDetailHref(event, data.selected_year, data.selected_month, view)}
              key={event.event_id}
            >
              <div className="calendar-list-item__date">
                <strong>{listDateFormatter.format(new Date(`${event.event_date}T00:00:00`))}</strong>
              </div>
              <div className="calendar-list-item__content">
                <div className="calendar-list-item__topline">
                  <span className={eventPillTone(event)}>{eventTagLabel(event)}</span>
                  <strong>{eventHeadline(event)}</strong>
                </div>
                <p>{eventListMeta(event)}</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
