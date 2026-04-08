from __future__ import annotations

from fastapi import APIRouter

from ..services.frontend_payloads import (
    build_physical_overview_payload,
    build_player_detail_payload,
    build_players_directory_payload,
)


router = APIRouter(prefix="/api/frontend", tags=["frontend"])


@router.get("/players-directory")
def get_players_directory() -> dict:
    return build_players_directory_payload()


@router.get("/players/{player_id}")
def get_player_frontend_detail(player_id: str) -> dict:
    return build_player_detail_payload(player_id=player_id)


@router.get("/physical-overview")
def get_physical_overview() -> dict:
    return build_physical_overview_payload()
