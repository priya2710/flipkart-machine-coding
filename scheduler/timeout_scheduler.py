import threading
import time
from services.order_service import OrderService
from services.assignment_service import AssignmentService
from constants.config import TIMEOUT_MINUTES
from constants.enums import OrderStatus
from utils.logger import logger

class OrderTimeoutScheduler:
    def __init__(self, interval_seconds: int = 5):
        self.interval = interval_seconds
        self.order_service = OrderService()
        self.assignment_service = AssignmentService()
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        logger.info("OrderTimeoutScheduler started.")

    def stop(self):
        self._stop_event.set()

    def _run(self):
        timeout_seconds = TIMEOUT_MINUTES * 60
        while not self._stop_event.is_set():
            try:
                time.sleep(self.interval)
                now = time.time()
                # We can iterate repository copies safely
                orders = self.order_service.order_repo.get_all()
                for order in orders:
                    # Timeout rule: If CREATED or ASSIGNED for too long -> Cancel
                    # Wait, requirement says "if no pickup within 30 mins -> cancel"
                    # So applicable to CREATED and ASSIGNED.
                    if order.status in [OrderStatus.CREATED, OrderStatus.ASSIGNED]:
                        if now - order.created_at > timeout_seconds:
                            logger.info(f"[Scheduler] Auto-cancelling order {order.id} due to timeout.")
                            # Use AssignmentService to cancel so it handles driver freeing/queue removal
                            self.assignment_service.cancel_order(order.id)
            except Exception as e:
                logger.error(f"[Scheduler] Error: {e}")
