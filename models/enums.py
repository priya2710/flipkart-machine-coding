from enum import Enum

class OrderStatus(Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class DriverStatus(Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
