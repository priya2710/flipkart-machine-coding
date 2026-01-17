import unittest
from models import Order, Driver, Customer
from constants.enums import OrderStatus, DriverStatus

class TestModels(unittest.TestCase):
    def test_customer_creation(self):
        c = Customer(id="C1", name="Alice")
        self.assertEqual(c.id, "C1")
        self.assertEqual(c.name, "Alice")

    def test_driver_creation(self):
        d = Driver(id="D1", name="Bob")
        self.assertEqual(d.id, "D1")
        self.assertEqual(d.name, "Bob")
        self.assertEqual(d.status, DriverStatus.AVAILABLE)
        self.assertEqual(d.average_rating, 0.0)

    def test_driver_rating_calculation(self):
        d = Driver(id="D1", name="Bob")
        d.total_rating = 10
        d.ratings_count = 2
        self.assertEqual(d.average_rating, 5.0)

        d.total_rating = 14
        d.ratings_count = 3
        self.assertAlmostEqual(d.average_rating, 4.67, places=2)

    def test_order_creation(self):
        o = Order(id="O1", customer_id="C1", item_id="ITEM1")
        self.assertEqual(o.id, "O1")
        self.assertEqual(o.status, OrderStatus.CREATED)
        self.assertIsNone(o.driver_id)
