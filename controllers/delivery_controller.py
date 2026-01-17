from typing import List, Optional
from services.order_service import OrderService
from services.driver_service import DriverService
from services.assignment_service import AssignmentService
from views.console_view import ConsoleView
from models import Customer, Driver, Order
from scheduler.timeout_scheduler import OrderTimeoutScheduler

class DeliveryController:
    def __init__(self):
        self.order_service = OrderService()
        self.driver_service = DriverService()
        self.assignment_service = AssignmentService()
        self.view = ConsoleView()
        
        # Start Scheduler
        self.scheduler = OrderTimeoutScheduler()
        self.scheduler.start()

    # --- Customer/Driver Onboarding ---
    def onboard_customer(self, id: str, name: str) -> Customer:
        try:
            customer = self.order_service.onboard_customer(id, name)
            self.view.show_onboarded_customer(customer)
            return customer
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def onboard_driver(self, id: str, name: str) -> Driver:
        try:
            driver = self.driver_service.onboard_driver(id, name)
            # Try to assign any pending orders since a new driver arrived
            self.assignment_service.on_driver_available(id)
            self.view.show_onboarded_driver(driver)
            return driver
        except Exception as e:
            self.view.show_error(str(e))
            raise

    # --- Order Management ---
    def create_order(self, customer_id: str, item_id: str, quantity: int = 1) -> str:
        try:
            order = self.order_service.create_order(customer_id, item_id, quantity)
            self.assignment_service.queue_order(order.id)
            
            self.view.show_order_created(order.id)
            self.view.show_order_status(order)
            return order.id
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.order_service.get_order(order_id)
        
    def get_all_drivers(self) -> List[Driver]:
        return self.driver_service.get_all_drivers()

    def show_order_status(self, order_id: str):
        order = self.order_service.get_order(order_id)
        self.view.show_order_status(order)

    # --- Delivery Flow ---
    def pickup_order(self, driver_id: str, order_id: str):
        try:
            # We must validate strict state via OrderService transition
            # But we also need to check driver assignment.
            
            # The logic "pickup_order" is business logic combining Driver an Order.
            # Ideally AssignmentService or similar handles this coordination? 
            # Or we keep simple actions in Controller calling specific service methods.
            
            # Use OrderService for state transition, but we need extra validation (DRIVER_MATCH)
            order = self.order_service.get_order(order_id)
            if not order: 
                raise ValueError("Order not found")
            if order.driver_id != driver_id:
                raise ValueError("Order not assigned to this driver")
                
            self.order_service.transition_state(order_id, "PICKED_UP") # Will convert str to Enum if we pass Enum? 
            # Update: transition_state expects Enum.
            from constants.enums import OrderStatus
            self.order_service.transition_state(order_id, OrderStatus.PICKED_UP)
            
            self.view.show_order_status(order)
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def complete_order(self, driver_id: str, order_id: str):
        try:
            from constants.enums import OrderStatus, DriverStatus
            
            order = self.order_service.get_order(order_id)
            if not order:
                raise ValueError("Order not found")
            if order.driver_id != driver_id:
                raise ValueError("Order not assigned to this driver")

            self.order_service.transition_state(order_id, OrderStatus.DELIVERED)
            
            # Free the driver
            self.driver_service.set_driver_status(driver_id, DriverStatus.AVAILABLE)
            driver = self.driver_service.get_driver(driver_id)
            if driver:
                driver.current_order_id = None
                self.driver_service.repo.save(driver)
            
            self.assignment_service.on_driver_available(driver_id)
            
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def cancel_order(self, order_id: str):
        try:
            self.assignment_service.cancel_order(order_id)
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def rate_driver(self, order_id: str, stars: int):
        try:
            from constants.enums import OrderStatus
            order = self.order_service.get_order(order_id)
            if not order: raise ValueError("Order not found")
            if order.status != OrderStatus.DELIVERED:
                raise ValueError("Can only rate delivered orders")
            
            if order.driver_id:
                driver = self.driver_service.get_driver(order.driver_id)
                if driver:
                     driver.total_rating += stars
                     driver.ratings_count += 1
                     self.driver_service.repo.save(driver)
            
            self.view.show_top_drivers(self.driver_service.get_all_drivers())
        except Exception as e:
            self.view.show_error(str(e))
            raise
