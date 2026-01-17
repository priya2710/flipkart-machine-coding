from dataclasses import dataclass, field
from typing import Optional
import time
from constants.enums import OrderStatus

@dataclass
class Order:
    id: str
    customer_id: str
    item_id: str
    quantity: int = 1
    status: OrderStatus = OrderStatus.CREATED
    driver_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    picked_up_at: Optional[float] = None
    delivered_at: Optional[float] = None
    rating: Optional[int] = None

    def __str__(self):
        driver_info = f", Driver: {self.driver_id}" if self.driver_id else ""
        return f"Order(ID: {self.id}, Status: {self.status.value}, Item: {self.item_id}, Customer: {self.customer_id}{driver_info})"
