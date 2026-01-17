import threading
from typing import Optional, Dict
from models import Customer

class InMemoryCustomerRepository:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(InMemoryCustomerRepository, cls).__new__(cls)
            cls._instance.lock = threading.RLock()
            cls._instance.customers = {} # Dict[str, Customer]
        return cls._instance

    def save(self, customer: Customer):
        with self.lock:
            self.customers[customer.id] = customer

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        with self.lock:
            return self.customers.get(customer_id)
            
    def clear(self):
        with self.lock:
            self.customers.clear()
