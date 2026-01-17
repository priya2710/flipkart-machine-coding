import unittest
from services.driver_service import DriverService
from constants.enums import DriverStatus

class TestDriverService(unittest.TestCase):
    def setUp(self):
        self.service = DriverService()
        self.service.repo.clear()

    def test_onboard_driver(self):
        d = self.service.onboard_driver("D1", "Bob")
        self.assertEqual(d.id, "D1")
        self.assertEqual(d.status, DriverStatus.AVAILABLE)
        
        # Idempotency
        d2 = self.service.onboard_driver("D1", "Bob")
        self.assertIs(d, d2)
