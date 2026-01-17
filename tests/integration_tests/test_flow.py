import unittest
import shutil
import os
import time
from unittest.mock import patch
from services.delivery_service import DeliveryService
from constants.enums import OrderStatus

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.test_dir = "data_test"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        # Reset Singleton
        DeliveryService._instance = None
        
    def tearDown(self):
        # Reset Singleton
        DeliveryService._instance = None
        if os.path.exists(self.test_dir):
            # Attempt to remove, might fail if file locked by process?
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass

    def test_scenario_1(self):
        # Patch config values in the services module where they are used
        with patch('services.delivery_service.DATA_DIR', self.test_dir), \
             patch('services.delivery_service.CUSTOMERS_FILE', os.path.join(self.test_dir, "customers.json")), \
             patch('services.delivery_service.DRIVERS_FILE', os.path.join(self.test_dir, "drivers.json")), \
             patch('services.delivery_service.ORDERS_FILE', os.path.join(self.test_dir, "orders.json")):
            
            service = DeliveryService()
            
            # 1. Onboard
            c1 = service.onboard_customer("C1", "Alice")
            d1 = service.onboard_driver("D1", "Bob")
            
            # 2. Create Order
            order = service.create_order("C1", "ITEM1")
            order_id = order.id
            self.assertEqual(order.status.value, "ASSIGNED")
            self.assertEqual(order.driver_id, "D1")
            
            # 3. Persistence Check
            # Force new instance (simulating restart)
            DeliveryService._instance = None
            service2 = DeliveryService()
            
            self.assertIn("C1", service2.users)
            self.assertEqual(len(service2.orders), 1)
            self.assertIn(order_id, service2.orders)
            
            loaded_order = service2.orders[order_id]
            self.assertEqual(loaded_order.status.value, "ASSIGNED")
            self.assertEqual(loaded_order.driver_id, "D1")
