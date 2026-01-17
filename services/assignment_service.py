import threading
import collections
from typing import Deque, Optional, List
from services.order_service import OrderService
from services.driver_service import DriverService
from models import Order, Driver
from constants.enums import OrderStatus, DriverStatus
from utils.logger import logger
from services.notifications import NotificationService

class AssignmentService:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(AssignmentService, cls).__new__(cls)
            cls._instance.lock = threading.RLock()
            cls._instance.pending_orders: Deque[str] = collections.deque()
            cls._instance.order_service = OrderService()
            cls._instance.driver_service = DriverService()
        return cls._instance

    def queue_order(self, order_id: str):
        with self.lock:
            self.pending_orders.append(order_id)
            logger.info(f"Order {order_id} added to pending queue.")
            self._process_queue_unsafe()

    def on_driver_available(self, driver_id: str):
        with self.lock:
            # Mark driver available first (responsibility of DriverService, 
            # but AssignmentService needs to know availability triggered)
            # Assuming DriverService already updated status, now we just process queue.
            self._process_queue_unsafe()

    def _process_queue_unsafe(self):
        # Must be called within self.lock
        if not self.pending_orders:
            return

        available_drivers = [d for d in self.driver_service.get_all_drivers() if d.status == DriverStatus.AVAILABLE]
        if not available_drivers:
            return

        # Simple FIFO matching
        while self.pending_orders and available_drivers:
            order_id = self.pending_orders[0] # Peek
            order = self.order_service.get_order(order_id)
            
            # Validation: Order might have been cancelled while in queue
            if not order or order.status != OrderStatus.CREATED:
                self.pending_orders.popleft() # Remove invalid
                continue
            
            driver = available_drivers.pop(0)
            self.pending_orders.popleft() # Remove assigned
            
            try:
                self._assign_atomic(order, driver)
            except Exception as e:
                logger.error(f"Failed to assign order {order_id} to {driver.id}: {e}")
                # Logic to retry or re-queue? For now, if atomic assign fails, maybe driver status changed?
                # We should re-queue order if order is still valid.
                if order.status == OrderStatus.CREATED:
                     self.pending_orders.appendleft(order_id)

    def _assign_atomic(self, order: Order, driver: Driver):
        # Critical Section: Locking both Order and Driver could be complex.
        # We use AssignmentService Lock + Service methods which adhere to their own logic.
        # But to be "Atomic", we need to ensure no one else steals this driver/order in between.
        # Since we are inside `_process_queue_unsafe` which has `self.lock`, 
        # as long as ALL assignments go through `AssignmentService` and its lock, we are safe.
        
        # 1. Update Order Status
        try:
            self.order_service.transition_state(order.id, OrderStatus.ASSIGNED)
            order.driver_id = driver.id
            self.order_service.order_repo.save(order) # Save metadata
        except ValueError as e:
            logger.warning(f"Assignment failed: Order state invalid ({e})")
            raise

        # 2. Update Driver Status
        # We need to ensure driver is still available if we didn't lock him explicitly.
        # But we queried list inside the lock.
        self.driver_service.set_driver_status(driver.id, DriverStatus.BUSY)
        driver.current_order_id = order.id
        self.driver_service.repo.save(driver)

        logger.info(f"Order {order.id} assigned to driver {driver.id}")
        NotificationService.notify(order.customer_id, f"Order {order.id} assigned to {driver.name}")
        NotificationService.notify_driver(driver.id, f"You have been assigned order {order.id}")

    def cancel_order(self, order_id: str):
        with self.lock:
            # Remove from queue if present
            if order_id in self.pending_orders:
                self.pending_orders.remove(order_id) # O(N) scan, acceptable for demo
                
            # Delegate state transition to OrderService
            # Check current status handles atomic check
            try:
                order = self.order_service.get_order(order_id)
                if not order: 
                    return
                
                prev_status = order.status
                driver_id = order.driver_id
                
                self.order_service.transition_state(order_id, OrderStatus.CANCELLED)
                logger.info(f"Order {order_id} cancelled.")
                
                # If was assigned, free driver
                if prev_status == OrderStatus.ASSIGNED and driver_id:
                    self.driver_service.set_driver_status(driver_id, DriverStatus.AVAILABLE)
                    driver = self.driver_service.get_driver(driver_id)
                    if driver:
                        driver.current_order_id = None
                        self.driver_service.repo.save(driver)
                        NotificationService.notify_driver(driver_id, f"Order {order_id} cancelled. You are free.")
                        # Trigger queue processing since a driver became free
                        self._process_queue_unsafe()
                        
            except ValueError as e:
                logger.error(f"Cannot cancel order {order_id}: {e}")
