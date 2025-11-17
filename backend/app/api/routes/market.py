from fastapi import APIRouter

from app.api.deps.alpaca_dep import AlpacaDep

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/next_close_date")
def next_close_date(alpaca_client: AlpacaDep) -> dict[str, str]:
    return {"date": alpaca_client.get_next_close().date().isoformat()}


@router.get("/is_next_close_today")
def is_next_close_today(alpaca_client: AlpacaDep) -> bool:
    return alpaca_client.is_next_close_today()
