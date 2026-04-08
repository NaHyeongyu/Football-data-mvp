from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .mappers import _optional_float
from .queries import _fetch_form_match_frame, _fetch_roster_positions
from ..pipelines.match_score_pipeline import prepare_objective_match_scores
from ..pipelines.recent_form_pipeline import attach_form_benchmarks, summarize_recent_form


def _build_form_summary_map(matches_per_player: int = 10) -> dict[str, dict[str, Any]]:
    roster_frame = _fetch_roster_positions()
    form_frame = _fetch_form_match_frame(roster_frame["player_id"].tolist(), matches_per_player=matches_per_player)
    if form_frame.empty:
        return {}

    # Use the same roster-wide benchmark pipeline for list and detail endpoints so summaries stay consistent.
    scored_frame = prepare_objective_match_scores(form_frame)
    summary_frame = summarize_recent_form(scored_frame)
    summary_frame = attach_form_benchmarks(summary_frame, roster_frame)
    if summary_frame.empty:
        return {}
    return {
        row["player_id"]: row
        for row in summary_frame.to_dict("records")
    }


def _apply_form_summary(row: dict[str, Any], form_summary: dict[str, Any] | None) -> dict[str, Any]:
    enriched = dict(row)
    if not form_summary:
        enriched.setdefault("previous_form_score", None)
        enriched.setdefault("form_delta", None)
        enriched.setdefault("form_trend", None)
        enriched.setdefault("evaluated_match_count", 0)
        enriched.setdefault("latest_match_score", None)
        enriched.setdefault("position_average_form_score", None)
        enriched.setdefault("team_average_form_score", None)
        enriched.setdefault("form_vs_position_average", None)
        enriched.setdefault("form_vs_team_average", None)
        return enriched

    enriched["recent_form_score"] = _optional_float(form_summary.get("recent_form_score"))
    enriched["previous_form_score"] = _optional_float(form_summary.get("previous_form_score"))
    enriched["form_delta"] = _optional_float(form_summary.get("form_delta"))
    enriched["form_trend"] = form_summary.get("form_trend")
    enriched["evaluated_match_count"] = int(form_summary.get("evaluated_match_count") or 0)
    enriched["latest_match_score"] = _optional_float(form_summary.get("latest_match_score"))
    enriched["position_average_form_score"] = _optional_float(form_summary.get("position_average_form_score"))
    enriched["team_average_form_score"] = _optional_float(form_summary.get("team_average_form_score"))
    enriched["form_vs_position_average"] = _optional_float(form_summary.get("form_vs_position_average"))
    enriched["form_vs_team_average"] = _optional_float(form_summary.get("form_vs_team_average"))
    return enriched
