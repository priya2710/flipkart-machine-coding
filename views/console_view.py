from typing import List, Optional
from models import Order, Driver, Customer
from utils.logger import logger

class ConsoleView:
    def show_message(self, message: str):
        logger.info(message)

    def show_error(self, error: str):
        logger.error(f"{error}")

    def show_notification(self, user_id: str, message: str):
        prefix = f"[Notification -> {user_id}]"
        logger.info(f"{prefix} {message}")

    def show_order_created(self, order_id: str):
        logger.info(f"Order created successfully: {order_id}")

    def show_order_status(self, order: Optional[Order]):
        if not order:
            logger.warning("Order not found.")
            return
        driver_info = f", Driver: {order.driver_id}" if order.driver_id else "None"
        logger.info(f"Order Status: {order.status.value}, Driver: {driver_info}")

    def show_driver_status(self, driver: Optional[Driver]):
        if not driver:
            logger.warning("Driver not found.")
            return
        logger.info(f"Driver Status: {driver.status.value}, Current Order: {driver.current_order_id}")

    def show_top_drivers(self, drivers: List[Driver]):
        logger.info("--- Top Drivers (by Rating) ---")
        for d in drivers:
            logger.info(f"{d.name} ({d.id}): {d.average_rating:.2f} stars ({d.ratings_count} ratings)")

    def show_onboarded_customer(self, customer: Customer):
        logger.info(f"Customer assigned: {customer.name}")

    def show_onboarded_driver(self, driver: Driver):
        logger.info(f"Driver onboarded: {driver.name}")
