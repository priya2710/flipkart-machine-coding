import threading
import time
import uuid
import json
import os
from dataclasses import asdict
from typing import Dict, List, Optional, Callable

from models import Customer, Driver, Order, Item
from constants.enums import OrderStatus, DriverStatus
from constants.config import (
    DATA_DIR, CUSTOMERS_FILE, DRIVERS_FILE, ORDERS_FILE,
    MAX_ORDER_QUANTITY, TIMEOUT_MINUTES
)
from services.notifications import NotificationService
from utils.logger import logger

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (OrderStatus, DriverStatus)):
            return obj.value
        return super().default(obj)

class DeliveryService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DeliveryService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized') and self.initialized:
            return
        
        self.lock = threading.RLock()
        self.timeout_seconds = TIMEOUT_MINUTES * 60
        
        self.users: Dict[str, Customer] = {}
        self.drivers: Dict[str, Driver] = {}
        self.orders: Dict[str, Order] = {}
        self.items: Dict[str, Item] = {
            "ITEM1": Item("ITEM1", "Laptop"),
            "ITEM2": Item("ITEM2", "Document"),
            "ITEM3": Item("ITEM3", "Food")
        }
        
        self._load_data()
        self.initialized = True
        
        # Start background monitor
        self.monitor_thread = threading.Thread(target=self._monitor_timeouts, daemon=True)
        self.monitor_thread.start()

    def _save_data(self):
        try:
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)

            with open(CUSTOMERS_FILE, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.users.items()}, f, cls=DateTimeEncoder, indent=2)
            
            with open(DRIVERS_FILE, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.drivers.items()}, f, cls=DateTimeEncoder, indent=2)

            with open(ORDERS_FILE, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.orders.items()}, f, cls=DateTimeEncoder, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def _load_data(self):
        if not os.path.exists(DATA_DIR):
            return

        try:
            if os.path.exists(CUSTOMERS_FILE):
                with open(CUSTOMERS_FILE, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.users[k] = Customer(**v)

            if os.path.exists(DRIVERS_FILE):
                with open(DRIVERS_FILE, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if 'status' in v:
                            v['status'] = DriverStatus(v['status'])
                        self.drivers[k] = Driver(**v)

            if os.path.exists(ORDERS_FILE):
                with open(ORDERS_FILE, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if 'status' in v:
                            v['status'] = OrderStatus(v['status'])
                        self.orders[k] = Order(**v)
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    def onboard_customer(self, id: str, name: str) -> Customer:
        with self.lock:
            if id in self.users:
                return self.users[id]
            customer = Customer(id, name)
            self.users[id] = customer
            self._save_data()
            return self.users[id]

    def onboard_driver(self, id: str, name: str) -> Driver:
        with self.lock:
            if id in self.drivers:
                return self.drivers[id]
            driver = Driver(id, name)
            self.drivers[id] = driver
            self._save_data()
            return self.drivers[id]

    def create_order(self, customer_id: str, item_id: str, quantity: int = 1) -> Order:
        with self.lock:
            if customer_id not in self.users:
                raise ValueError(f"Customer {customer_id} not found.")
            if item_id not in self.items:
                raise ValueError(f"Item {item_id} is not valid.")
            if quantity < 1 or quantity > MAX_ORDER_QUANTITY:
                raise ValueError(f"Invalid quantity {quantity}. Must be between 1 and {MAX_ORDER_QUANTITY}.")
            
            order_id = str(uuid.uuid4())[:8]
            order = Order(id=order_id, customer_id=customer_id, item_id=item_id, quantity=quantity)
            self.orders[order_id] = order
            self._save_data()
            
            self._try_assign_order(order)
            return order

    def _try_assign_order(self, order: Order):
        if order.status != OrderStatus.CREATED:
            return

        available_driver = None
        for driver in self.drivers.values():
            if driver.status == DriverStatus.AVAILABLE:
                available_driver = driver
                break
        
        if available_driver:
            self._assign(order, available_driver)
        else:
            logger.info(f"No driver available for order {order.id}. Queued.")

    def _assign(self, order: Order, driver: Driver):
        order.driver_id = driver.id
        order.status = OrderStatus.ASSIGNED
        order.assigned_at = time.time()
        
        driver.status = DriverStatus.BUSY
        driver.current_order_id = order.id
        
        self._save_data()
        
        logger.info(f"Order {order.id} assigned to driver {driver.id}")
        NotificationService.notify(order.customer_id, f"Order {order.id} assigned to {driver.name}")
        NotificationService.notify_driver(driver.id, f"You have been assigned order {order.id}")

    def get_order(self, order_id: str) -> Optional[Order]:
        with self.lock:
            return self.orders.get(order_id)

    def get_driver(self, driver_id: str) -> Optional[Driver]:
        with self.lock:
            return self.drivers.get(driver_id)

    def get_all_drivers(self) -> List[Driver]:
        with self.lock:
            return list(self.drivers.values())

    def pickup_order(self, driver_id: str, order_id: str) -> Order:
        with self.lock:
            if order_id not in self.orders:
                raise ValueError("Order not found")
            order = self.orders[order_id]
            
            if order.driver_id != driver_id:
                raise ValueError(f"Driver {driver_id} is not assigned to this order.")
            
            if order.status != OrderStatus.ASSIGNED:
                raise ValueError(f"Order {order_id} cannot be picked up from {order.status.value} state.")

            order.status = OrderStatus.PICKED_UP
            order.picked_up_at = time.time()
            self._save_data()
            
            logger.info(f"Order {order_id} picked up by {driver_id}")
            NotificationService.notify(order.customer_id, f"Your order {order_id} has been picked up.")
            return order

    def complete_order(self, driver_id: str, order_id: str) -> Order:
        with self.lock:
            if order_id not in self.orders:
                raise ValueError("Order not found")
            order = self.orders[order_id]
            
            if order.driver_id != driver_id:
                raise ValueError(f"Driver {driver_id} is not assigned to this order.")

            if order.status != OrderStatus.PICKED_UP:
                raise ValueError(f"Order {order_id} cannot be completed from {order.status.value} state.")
                
            order.status = OrderStatus.DELIVERED
            order.delivered_at = time.time()
            
            if driver_id in self.drivers:
                driver = self.drivers[driver_id]
                driver.status = DriverStatus.AVAILABLE
                driver.current_order_id = None
                self._save_data()
                
                logger.info(f"Order {order_id} delivered by {driver_id}")
                NotificationService.notify(order.customer_id, f"Your order {order_id} has been delivered.")
                
                self._assign_pending_orders(driver)
            return order

    def _assign_pending_orders(self, driver: Driver):
        pending_orders = [o for o in self.orders.values() if o.status == OrderStatus.CREATED]
        pending_orders.sort(key=lambda x: x.created_at)
        
        if pending_orders:
            self._assign(pending_orders[0], driver)

    def cancel_order(self, order_id: str) -> Order:
        with self.lock:
            if order_id not in self.orders:
                raise ValueError("Order not found")
            order = self.orders[order_id]
            
            if order.status == OrderStatus.PICKED_UP or order.status == OrderStatus.DELIVERED:
                raise ValueError(f"Order {order_id} cannot be cancelled as it is already {order.status.value}.")
            
            prev_status = order.status
            order.status = OrderStatus.CANCELLED
            self._save_data()
            
            logger.info(f"Order {order_id} cancelled.")
            
            if prev_status == OrderStatus.ASSIGNED and order.driver_id:
                driver = self.drivers.get(order.driver_id)
                if driver:
                    driver.status = DriverStatus.AVAILABLE
                    driver.current_order_id = None
                    self._save_data()
                    NotificationService.notify_driver(driver.id, f"Order {order_id} was cancelled. You are now free.")
                    self._assign_pending_orders(driver)
            return order

    def _monitor_timeouts(self):
        while True:
            time.sleep(5)
            try:
                with self.lock:
                    now = time.time()
                    for order in list(self.orders.values()):
                        if order.status in [OrderStatus.CREATED, OrderStatus.ASSIGNED]:
                            if now - order.created_at > self.timeout_seconds:
                                logger.info(f"Auto-cancelling order {order.id} due to timeout.")
                                self.cancel_order(order.id)
            except Exception as e:
                logger.error(f"Error in monitor thread: {e}")

    def rate_driver(self, order_id: str, stars: int):
        with self.lock:
            if order_id not in self.orders:
                raise ValueError("Order not found")
            order = self.orders[order_id]
            if order.status != OrderStatus.DELIVERED:
                raise ValueError("Can only rate delivered orders")
            if not order.driver_id:
                return
            
            order.rating = stars
            driver = self.drivers[order.driver_id]
            driver.total_rating += stars
            driver.ratings_count += 1
            self._save_data()
