import time
from controllers.delivery_controller import DeliveryController
from utils.logger import logger

def demo():
    logger.info("Initializing MVC System with Persistence (Refactored)...")
    
    # Controller now handles view and service internally
    controller = DeliveryController()
    
    # No direct view access in main.py, assume controller handles output via view
    # But main.py might want to print section headers?
    # I'll use logger for headers too.

    logger.info("\n--- Onboarding (Idempotent) ---")
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
        # controller.create_order already shows status via view
        
        o3_id = controller.create_order("C1", "ITEM3", quantity=2)
        
        # Test Guardrail
        logger.info("Testing Quantity Guardrail (100 items):")
        try:
            controller.create_order("C1", "ITEM1", quantity=100)
        except Exception as e:
            # Controller re-raises, view already showed error? 
            # Controller's create_order calls view.show_error AND raises?
            # My implementation: calls view.show_error, then raisess.
            # So here we might see error twice if we log it again.
            # I'll just pass here as it's expected, or let it show.
            pass
        
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
        # View shows error, we catch to proceed
        pass

    logger.info("\n--- Cancellation Flow ---")
    try:
        # Assuming o3_repeated_id was queued or assigned
        if 'o3_repeated_id' in locals():
            controller.cancel_order(o3_repeated_id)
    except Exception as e:
        pass

    logger.info("\n--- Ratings ---")
    try:
        # if o1 was delivered
        if 'o1_id' in locals():
            controller.rate_driver(o1_id, 5)
    except Exception as e:
        pass

if __name__ == "__main__":
    demo()
