import uuid
import time
from typing import Optional, Dict
from repositories.order_repository import InMemoryOrderRepository
from repositories.customer_repository import InMemoryCustomerRepository
from models import Order, Customer, Item
from constants.enums import OrderStatus
from constants.config import MAX_ORDER_QUANTITY

class OrderService:
    def __init__(self):
        self.order_repo = InMemoryOrderRepository()
        self.customer_repo = InMemoryCustomerRepository()
        self.items: Dict[str, Item] = {
            "ITEM1": Item("ITEM1", "Laptop"),
            "ITEM2": Item("ITEM2", "Document"),
            "ITEM3": Item("ITEM3", "Food")
        }

    def onboard_customer(self, id: str, name: str) -> Customer:
        existing = self.customer_repo.get_by_id(id)
        if existing:
            return existing
        customer = Customer(id=id, name=name)
        self.customer_repo.save(customer)
        return customer

    def create_order(self, customer_id: str, item_id: str, quantity: int = 1) -> Order:
        if not self.customer_repo.get_by_id(customer_id):
            raise ValueError(f"Customer {customer_id} not found.")
        if item_id not in self.items:
            raise ValueError(f"Item {item_id} is not valid.")
        if quantity < 1 or quantity > MAX_ORDER_QUANTITY:
            raise ValueError(f"Invalid quantity {quantity}.")

        order_id = str(uuid.uuid4())[:8]
        order = Order(
            id=order_id, 
            customer_id=customer_id, 
            item_id=item_id, 
            quantity=quantity,
            status=OrderStatus.CREATED
        )
        self.order_repo.save(order)
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.order_repo.get_by_id(order_id)

    def transition_state(self, order_id: str, new_status: OrderStatus):
        """
        Strict State Machine Implementation.
        """
        # We need a lock here to ensure atomic state transition check-and-set
        # Using the repo's lock is one way, or a lock on the order ID.
        # Since repo.lock guards the map, not the object properties necessarily (though in this simple repo it's same lock context if we used get_and_update pattern).
        # Let's rely on synchronized block for this operation.
        with self.order_repo.lock: 
            order = self.order_repo.orders.get(order_id) # Direct access to ensure lock coverage
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            current_status = order.status
            
            # Allow Idempotency (Same status -> Same Status is OK)
            if current_status == new_status:
                return

            valid = False
            if current_status == OrderStatus.CREATED:
                if new_status in [OrderStatus.ASSIGNED, OrderStatus.CANCELLED]:
                    valid = True
            elif current_status == OrderStatus.ASSIGNED:
                if new_status in [OrderStatus.PICKED_UP, OrderStatus.CANCELLED]:
                    valid = True
            elif current_status == OrderStatus.PICKED_UP:
                if new_status in [OrderStatus.DELIVERED]:
                    valid = True
            # DELIVERED and CANCELLED are terminal states (mostly), though business rules might allow return? 
            # Requirements say: PICKED -> CANCELLED is INVALID. 
            # DELIVERED -> CANCELLED is INVALID.
            
            if not valid:
                raise ValueError(f"Invalid state transition: {current_status.value} -> {new_status.value} for Order {order_id}")
            
            order.status = new_status
            
            # timestamp updates
            now = time.time()
            if new_status == OrderStatus.ASSIGNED:
                order.assigned_at = now
            elif new_status == OrderStatus.PICKED_UP:
                order.picked_up_at = now
            elif new_status == OrderStatus.DELIVERED:
                order.delivered_at = now
                
            self.order_repo.orders[order_id] = order # Persist (if logic changed)
