from typing import Annotated
from fastapi import Depends
from app.services.order_service import OrderService

def get_order_service():
    return OrderService()

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]