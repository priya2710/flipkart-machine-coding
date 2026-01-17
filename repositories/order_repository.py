import threading
from typing import Optional, List, Dict
from models import Order

class InMemoryOrderRepository:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(InMemoryOrderRepository, cls).__new__(cls)
            cls._instance.lock = threading.RLock()
            cls._instance.orders = {} # Dict[str, Order]
        return cls._instance

    def save(self, order: Order):
        with self.lock:
            self.orders[order.id] = order

    def get_by_id(self, order_id: str) -> Optional[Order]:
        with self.lock:
            return self.orders.get(order_id)

    def get_all(self) -> List[Order]:
        with self.lock:
            return list(self.orders.values())

    def clear(self):
        with self.lock:
            self.orders.clear()
