import time
from controllers.delivery_controller import DeliveryController
from utils.logger import logger

def peer_service():
    logger.info("Initializing System...")
    # Controller now handles view and service internally
    controller = DeliveryController()
    logger.info("\n--- Onboarding ---")
    try:
        controller.onboard_customer("C1", "Alice")
        controller.onboard_customer("C2", "Bob")
        controller.onboard_driver("D1", "Dave")
        controller.onboard_driver("D2", "Eve")
    except Exception as e:
        logger.error(f"Error in onboarding: {e}")

    logger.info("\n--- Creating Orders ---")
    try:
        o1_id = controller.create_order("C1", "ITEM1")
        o3_id = controller.create_order("C1", "ITEM3", quantity=2)
        logger.info("Testing Quantity Guardrail (100 items):")
        try:
            controller.create_order("C1", "ITEM1", quantity=100)
        except Exception as e:
            logger.error(f"Error in order creation: {e}")
        
        o2_id = controller.create_order("C2", "ITEM2")
        o3_repeated_id = controller.create_order("C1", "ITEM3")
    except Exception as e:
        logger.error(f"Error in order creation: {e}")
    logger.info("\n--- Pickup and Delivery Flow ---")

    try:
        # Note: In a second run, o1 might already be delivered. Ideally we check status.
        # But for demo, we'll try to pickup o1_id (if valid variable)
        # We need to make sure variables are defined.
        if 'o1_id' in locals():
            order1 = controller.get_order(o1_id)
            if order1 and order1.status.value == "ASSIGNED":
                controller.pickup_order("D1", o1_id)
                time.sleep(1)
                controller.complete_order("D1", o1_id)

    except Exception as e:
        logger.error(f"Error in pickup or delivery: {e}")

    logger.info("\n--- Cancellation Flow ---")
    try:
        # Assuming o3_repeated_id was queued or assigned
        if 'o3_repeated_id' in locals():
            controller.cancel_order(o3_repeated_id)
    except Exception as e:
        logger.error(f"Error in cancellation: {e}")

    logger.info("\n--- Ratings ---")
    try:
        # if o1 was delivered
        if 'o1_id' in locals():
            controller.rate_driver(o1_id, 5)
    except Exception as e:
        logger.error(f"Error in rating: {e}")

if __name__ == "__main__":
    peer_service()

