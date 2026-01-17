import threading
from typing import Optional, List, Dict
from models import Driver

class InMemoryDriverRepository:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(InMemoryDriverRepository, cls).__new__(cls)
            cls._instance.lock = threading.RLock()
            cls._instance.drivers = {} # Dict[str, Driver]
        return cls._instance

    def save(self, driver: Driver):
        with self.lock:
            self.drivers[driver.id] = driver

    def get_by_id(self, driver_id: str) -> Optional[Driver]:
        with self.lock:
            return self.drivers.get(driver_id)

    def get_all(self) -> List[Driver]:
        with self.lock:
            return list(self.drivers.values())
            
    def clear(self):
        with self.lock:
            self.drivers.clear()
