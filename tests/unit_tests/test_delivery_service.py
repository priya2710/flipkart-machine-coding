import unittest
from unittest.mock import MagicMock, patch
from services.delivery_service import DeliveryService
from constants.enums import OrderStatus, DriverStatus
from models import Order, Driver, Customer

class TestDeliveryService(unittest.TestCase):
    def setUp(self):
        # Reset singleton for each test
        DeliveryService._instance = None
        # Patch load/save to prevent file operations
        with patch('services.delivery_service.DeliveryService._load_data'), \
             patch('services.delivery_service.DeliveryService._save_data'), \
             patch('services.delivery_service.threading.Thread'):  # No background thread
            self.service = DeliveryService()
            self.service.users = {}
            self.service.drivers = {}
            self.service.orders = {}

    def test_onboard_customer(self):
        c = self.service.onboard_customer("C1", "Alice")
        self.assertEqual(len(self.service.users), 1)
        self.assertEqual(c.name, "Alice")
        
        # Idempotency
        c2 = self.service.onboard_customer("C1", "Alice")
        self.assertEqual(len(self.service.users), 1)
        self.assertIs(c, c2)

    def test_create_order_no_customer(self):
        with self.assertRaises(ValueError):
            self.service.create_order("CX", "ITEM1")

    def test_create_order_success(self):
        self.service.onboard_customer("C1", "Alice")
        order = self.service.create_order("C1", "ITEM1")
        self.assertIsNotNone(order.id)
        self.assertEqual(order.status, OrderStatus.CREATED)
        self.assertIn(order.id, self.service.orders)

    def test_assign_order_immediate(self):
        self.service.onboard_customer("C1", "Alice")
        d1 = self.service.onboard_driver("D1", "Dave")
        
        order = self.service.create_order("C1", "ITEM1")
        
        # Should be assigned immediately
        self.assertEqual(order.status, OrderStatus.ASSIGNED)
        self.assertEqual(order.driver_id, "D1")
        self.assertEqual(d1.status, DriverStatus.BUSY)

    def test_delivery_flow(self):
        self.service.onboard_customer("C1", "Alice")
        self.service.onboard_driver("D1", "Dave")
        order = self.service.create_order("C1", "ITEM1")

        # Pickup
        self.service.pickup_order("D1", order.id)
        self.assertEqual(order.status, OrderStatus.PICKED_UP)

        # Complete
        self.service.complete_order("D1", order.id)
        self.assertEqual(order.status, OrderStatus.DELIVERED)
        
        # Driver free
        d1 = self.service.drivers["D1"]
        self.assertEqual(d1.status, DriverStatus.AVAILABLE)

    def test_cancel_order(self):
        self.service.onboard_customer("C1", "Alice")
        order = self.service.create_order("C1", "ITEM1")
        
        self.service.cancel_order(order.id)
        self.assertEqual(order.status, OrderStatus.CANCELLED)
