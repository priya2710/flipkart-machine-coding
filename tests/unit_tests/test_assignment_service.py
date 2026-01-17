import unittest
from unittest.mock import MagicMock
from services.assignment_service import AssignmentService
from services.order_service import OrderService
from services.driver_service import DriverService
from constants.enums import OrderStatus, DriverStatus

class TestAssignmentService(unittest.TestCase):
    def setUp(self):
        # Reset singleton and repos
        AssignmentService._instance = None
        OrderService._instance = None # If they were singletons? They are not implemented as singletons in my code (only AssignmentService might be if I did new logic)
        # Wait, I implemented AssignmentService as Singleton in `__new__` but OrderService is just normal class? 
        # Let's check my implementation.
        # OrderService/DriverService in previous step did NOT have `__new__` singleton logic. 
        # But AssignmentService DID.
        
        self.service = AssignmentService()
        self.service.pending_orders.clear()
        
        # Helper to clear underlying repos directly since services are composites
        self.service.order_service.order_repo.clear()
        self.service.order_service.customer_repo.clear()
        self.service.driver_service.repo.clear() # Driver Repo

    def test_queue_processing(self):
        # Setup
        self.service.order_service.onboard_customer("C1", "Alice")
        d1 = self.service.driver_service.onboard_driver("D1", "Bob")
        
        # Create Order
        order = self.service.order_service.create_order("C1", "ITEM1")
        
        # Queue it
        self.service.queue_order(order.id)
        
        # Should be assigned immediately because D1 is available
        self.assertEqual(order.status, OrderStatus.ASSIGNED)
        self.assertEqual(order.driver_id, "D1")
        self.assertEqual(d1.status, DriverStatus.BUSY)

    def test_queue_wait(self):
        # Setup: No drivers
        self.service.order_service.onboard_customer("C1", "Alice")
        order = self.service.order_service.create_order("C1", "ITEM1")
        
        # Queue
        self.service.queue_order(order.id)
        
        # Should be pending
        self.assertEqual(order.status, OrderStatus.CREATED)
        self.assertIn(order.id, self.service.pending_orders)
        
        # Add Driver
        d1 = self.service.driver_service.onboard_driver("D1", "Bob")
        
        # Trigger processing (usually automatic in onboard_driver via controller, 
        # but here we test service directly, so we call on_driver_available)
        self.service.on_driver_available("D1")
        
        # Should be assigned
        self.assertEqual(order.status, OrderStatus.ASSIGNED)
        self.assertEqual(order.driver_id, "D1")
        self.assertNotIn(order.id, self.service.pending_orders)
