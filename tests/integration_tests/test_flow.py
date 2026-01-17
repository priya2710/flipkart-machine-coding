import unittest
import shutil
import os
import time
from unittest.mock import patch
# We use DeliveryController as the entry point for integration tests
from controllers.delivery_controller import DeliveryController
from services.assignment_service import AssignmentService
from services.order_service import OrderService
from services.driver_service import DriverService
from constants.enums import OrderStatus, DriverStatus

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        # We need to clean singleton states because they persist across tests in memory
        AssignmentService._instance = None
        # OrderService/DriverService are not singletons in my implementation, but their underlying repos ARE.
        from repositories.order_repository import InMemoryOrderRepository
        from repositories.driver_repository import InMemoryDriverRepository
        from repositories.customer_repository import InMemoryCustomerRepository
        
        InMemoryOrderRepository().clear()
        InMemoryDriverRepository().clear()
        InMemoryCustomerRepository().clear()
        
        # Also Scheduler might be running? 
        # The controller starts a scheduler. We should probably stop it or mock it to avoid loose threads.
        self.patcher = patch('controllers.delivery_controller.OrderTimeoutScheduler')
        self.mock_scheduler = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        InMemoryOrderRepository().clear()
        InMemoryDriverRepository().clear()
        InMemoryCustomerRepository().clear()
        AssignmentService._instance = None

    def test_full_flow_success(self):
        controller = DeliveryController()
        
        # 1. Onboard
        controller.onboard_customer("C1", "Alice")
        controller.onboard_driver("D1", "Bob")
        
        # 2. Create Order
        order_id = controller.create_order("C1", "ITEM1")
        
        # Should be assigned immediately via AssignmentService logic
        order = controller.get_order(order_id)
        self.assertEqual(order.status, OrderStatus.ASSIGNED)
        self.assertEqual(order.driver_id, "D1")
        
        # 3. Pickup
        controller.pickup_order("D1", order_id)
        self.assertEqual(order.status, OrderStatus.PICKED_UP)
        
        # 4. Complete
        controller.complete_order("D1", order_id)
        self.assertEqual(order.status, OrderStatus.DELIVERED)
        
        # 5. Rate
        controller.rate_driver(order_id, 5)
        drivers = controller.get_all_drivers()
        d1 = next(d for d in drivers if d.id == "D1")
        self.assertEqual(d1.total_rating, 5)

    def test_queue_flow(self):
        controller = DeliveryController()
        controller.onboard_customer("C1", "Alice")
        
        # Create Order (No drivers)
        order_id = controller.create_order("C1", "ITEM1")
        order = controller.get_order(order_id)
        self.assertEqual(order.status, OrderStatus.CREATED)
        
        # Onboard Driver -> Triggers Assignment
        controller.onboard_driver("D1", "Bob")
        
        self.assertEqual(order.status, OrderStatus.ASSIGNED)
        self.assertEqual(order.driver_id, "D1")
