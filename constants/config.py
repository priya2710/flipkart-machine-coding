import os

DATA_DIR = "data"
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
DRIVERS_FILE = os.path.join(DATA_DIR, "drivers.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")

MAX_ORDER_QUANTITY = 10
TIMEOUT_MINUTES = 0.5 # 30 seconds for demo purposes, or typical business logic
