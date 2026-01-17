from typing import List, Optional
from services.delivery_service import DeliveryService
from views.console_view import ConsoleView
from models import Customer, Driver, Order

class DeliveryController:
    def __init__(self):
        self.service = DeliveryService()
        self.view = ConsoleView()

    # --- Customer/Driver Onboarding ---
    def onboard_customer(self, id: str, name: str) -> Customer:
        try:
            customer = self.service.onboard_customer(id, name)
            self.view.show_onboarded_customer(customer)
            return customer
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def onboard_driver(self, id: str, name: str) -> Driver:
        try:
            driver = self.service.onboard_driver(id, name)
            self.view.show_onboarded_driver(driver)
            return driver
        except Exception as e:
            self.view.show_error(str(e))
            raise

    # --- Order Management ---
    def create_order(self, customer_id: str, item_id: str, quantity: int = 1) -> str:
        try:
            order = self.service.create_order(customer_id, item_id, quantity)
            self.view.show_order_created(order.id)
            # Automatically show status after creation as per original flow
            self.view.show_order_status(order)
            return order.id
        except Exception as e:
            self.view.show_error(str(e))
            # Return empty string or handle error appropriately. 
            # Original code raised error or showed error. 
            # We'll re-raise if key for the caller (main.py) to know it failed? 
            # Or main.py catches it?
            # Looking at original main.py, it caught ValueError. 
            # So let's re-raise or let it bubble up.
            raise

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.service.get_order(order_id)
        
    def get_all_drivers(self) -> List[Driver]:
        return self.service.get_all_drivers()

    def show_order_status(self, order_id: str):
        order = self.service.get_order(order_id)
        self.view.show_order_status(order)

    # --- Delivery Flow ---
    def pickup_order(self, driver_id: str, order_id: str):
        try:
            order = self.service.pickup_order(driver_id, order_id)
            self.view.show_order_status(order)
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def complete_order(self, driver_id: str, order_id: str):
        try:
            self.service.complete_order(driver_id, order_id)
            # Status update done in service logs, but view can explicitly show it if needed.
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def cancel_order(self, order_id: str):
        try:
            self.service.cancel_order(order_id)
        except Exception as e:
            self.view.show_error(str(e))
            raise

    def rate_driver(self, order_id: str, stars: int):
        try:
            self.service.rate_driver(order_id, stars)
            # Show top drivers after rating
            self.view.show_top_drivers(self.service.get_all_drivers())
        except Exception as e:
            self.view.show_error(str(e))
            raise
