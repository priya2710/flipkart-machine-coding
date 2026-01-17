import unittest
from services.order_service import OrderService
from constants.enums import OrderStatus
from models import Order

class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.service = OrderService()
        self.service.order_repo.clear()
        self.service.customer_repo.clear()

    def test_create_order_validations(self):
        self.service.onboard_customer("C1", "Alice")
        
        # Valid
        o = self.service.create_order("C1", "ITEM1")
        self.assertEqual(o.status, OrderStatus.CREATED)
        
        # Invalid Item
        with self.assertRaises(ValueError):
            self.service.create_order("C1", "INVALID_ITEM")
            
        # Invalid Quantity
        with self.assertRaises(ValueError):
            self.service.create_order("C1", "ITEM1", quantity=100)

    def test_state_transitions(self):
        self.service.onboard_customer("C1", "Alice")
        o = self.service.create_order("C1", "ITEM1")
        
        # Valid: CREATED -> ASSIGNED
        self.service.transition_state(o.id, OrderStatus.ASSIGNED)
        self.assertEqual(o.status, OrderStatus.ASSIGNED)
        
        # Invalid: ASSIGNED -> CREATED
        with self.assertRaises(ValueError):
             self.service.transition_state(o.id, OrderStatus.CREATED)

        # Valid: ASSIGNED -> PICKED_UP
        self.service.transition_state(o.id, OrderStatus.PICKED_UP)
        
        # Invalid: PICKED_UP -> CANCELLED
        with self.assertRaises(ValueError):
            self.service.transition_state(o.id, OrderStatus.CANCELLED)

        # Valid: PICKED_UP -> DELIVERED
        self.service.transition_state(o.id, OrderStatus.DELIVERED)
