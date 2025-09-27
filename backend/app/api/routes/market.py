from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.dependencies.my_alpaca_client import AlpacaDep, AlpacaOrderStatus, AlpacaOrder

from alpaca.common.exceptions import APIError


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/next_close_date")
def next_close_date(alpaca_client: AlpacaDep):
    return {"date": alpaca_client.get_next_close().date().isoformat()}

@router.get("/is_next_close_today")
def is_next_close_today(alpaca_client: AlpacaDep) -> bool:
    return alpaca_client.is_next_close_today()






