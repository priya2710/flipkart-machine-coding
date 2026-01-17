from dataclasses import dataclass, field
from typing import Optional
from constants.enums import DriverStatus

@dataclass
class Customer:
    id: str
    name: str

@dataclass
class Driver:
    id: str
    name: str
    status: DriverStatus = DriverStatus.AVAILABLE
    vehicle_type: str = "Two Wheeler"
    current_order_id: Optional[str] = None
    total_rating: float = 0.0
    ratings_count: int = 0

    @property
    def average_rating(self) -> float:
        if self.ratings_count == 0:
            return 0.0
        return self.total_rating / self.ratings_count
