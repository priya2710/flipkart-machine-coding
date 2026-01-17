from utils.logger import logger

class NotificationService:
    @staticmethod
    def notify(user_id: str, message: str):
        logger.info(f"[Notification] To User {user_id}: {message}")

    @staticmethod
    def notify_driver(driver_id: str, message: str):
        logger.info(f"[Notification] To Driver {driver_id}: {message}")
