"""
Supplier Agent Module
=====================
Manages supply capacity, processes orders, and handles deliveries.

Responsibilities:
- Receive and validate order requests from warehouses
- Simulate realistic lead times with reliability factors
- Track pending, processing, and fulfilled orders
- Send shipment and delivery notifications
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, Message, MessageType, Order, OrderStatus


@dataclass
class SupplierCapacity:
    """Tracks supplier capacity constraints."""
    max_daily_capacity: int
    current_daily_used: int = 0
    capacity_date: datetime = field(default_factory=lambda: datetime.now().date())
    
    def reset_if_new_day(self, current_date: datetime):
        """Reset capacity counter if it's a new day."""
        if current_date.date() != self.capacity_date:
            self.current_daily_used = 0
            self.capacity_date = current_date.date()
    
    def can_fulfill(self, quantity: int) -> bool:
        """Check if we can fulfill the requested quantity."""
        return (self.current_daily_used + quantity) <= self.max_daily_capacity
    
    def reserve_capacity(self, quantity: int) -> bool:
        """Reserve capacity for an order."""
        if self.can_fulfill(quantity):
            self.current_daily_used += quantity
            return True
        return False
    
    @property
    def available_capacity(self) -> int:
        """Get remaining capacity for today."""
        return max(0, self.max_daily_capacity - self.current_daily_used)


@dataclass
class PendingShipment:
    """Represents a shipment scheduled for delivery."""
    order: Order
    scheduled_delivery: datetime
    shipped_at: datetime = field(default_factory=datetime.now)
    
    def is_ready_for_delivery(self, current_time: datetime) -> bool:
        """Check if shipment is ready for delivery."""
        return current_time >= self.scheduled_delivery


class SupplierAgent(BaseAgent):
    """
    Supplier Agent - Manages supply operations and fulfills warehouse orders.
    
    Features:
    - Order validation and confirmation
    - Realistic lead time simulation with reliability factor
    - Capacity management
    - Shipment tracking and delivery notifications
    
    Attributes:
        lead_time_days: Base lead time for deliveries
        reliability: Probability (0-1) of on-time delivery
        min_order_quantity: Minimum order quantity accepted
        products_supplied: List of product IDs this supplier handles
    """
    
    def __init__(self, agent_id: str, name: str, 
                 lead_time_days: int = 5,
                 reliability: float = 0.95,
                 max_daily_capacity: int = 10000,
                 min_order_quantity: int = 1,
                 products_supplied: List[str] = None):
        super().__init__(agent_id, name)
        
        self.lead_time_days = lead_time_days
        self.reliability = min(1.0, max(0.0, reliability))  # Clamp to [0, 1]
        self.min_order_quantity = min_order_quantity
        self.products_supplied = products_supplied or []
        
        # Capacity tracking
        self.capacity = SupplierCapacity(max_daily_capacity=max_daily_capacity)
        
        # Order tracking
        self.pending_orders: List[Order] = []
        self.processing_orders: List[Order] = []
        self.pending_shipments: List[PendingShipment] = []
        self.fulfilled_orders: List[Order] = []
        self.rejected_orders: List[Order] = []
        
        # Statistics
        self.total_orders_received = 0
        self.total_units_shipped = 0
        self.total_revenue = 0.0
        self.on_time_deliveries = 0
        self.late_deliveries = 0
    
    def handle_message(self, message: Message):
        """Handle incoming messages from other agents."""
        if message.message_type == MessageType.ORDER_REQUEST:
            self._handle_order_request(message)
        elif message.message_type == MessageType.SYSTEM_STATUS:
            self._handle_status_request(message)
    
    def _handle_order_request(self, message: Message):
        """Process an incoming order request."""
        content = message.content
        
        # Create order from request
        order = Order.create(
            product_id=content.get("product_id"),
            quantity=content.get("quantity", 0),
            source_id=self.agent_id,
            target_id=message.sender_id,
            unit_cost=content.get("unit_cost", 0.0)
        )
        
        self.total_orders_received += 1
        
        # Validate order
        validation_result = self._validate_order(order)
        
        if validation_result["is_valid"]:
            self._accept_order(order, message.sender_id)
        else:
            self._reject_order(order, message.sender_id, validation_result["reason"])
    
    def _validate_order(self, order: Order) -> Dict[str, Any]:
        """Validate an incoming order."""
        # Check minimum quantity
        if order.quantity < self.min_order_quantity:
            return {
                "is_valid": False,
                "reason": f"Quantity {order.quantity} below minimum {self.min_order_quantity}"
            }
        
        # Check if we supply this product
        if self.products_supplied and order.product_id not in self.products_supplied:
            return {
                "is_valid": False,
                "reason": f"Product {order.product_id} not supplied by this supplier"
            }
        
        # Check capacity
        self.capacity.reset_if_new_day(self.current_time)
        if not self.capacity.can_fulfill(order.quantity):
            return {
                "is_valid": False,
                "reason": f"Insufficient capacity. Available: {self.capacity.available_capacity}"
            }
        
        return {"is_valid": True, "reason": None}
    
    def _accept_order(self, order: Order, requester_id: str):
        """Accept and process a valid order."""
        # Reserve capacity
        self.capacity.reserve_capacity(order.quantity)
        
        # Calculate delivery date with reliability factor
        actual_lead_time = self._calculate_actual_lead_time()
        expected_delivery = self.current_time + timedelta(days=actual_lead_time)
        order.expected_delivery = expected_delivery
        order.update_status(OrderStatus.CONFIRMED)
        
        # Add to processing
        self.processing_orders.append(order)
        
        # Send confirmation to requester
        requester = self.get_agent(requester_id)
        if requester:
            self.send_message(
                requester,
                MessageType.ORDER_CONFIRMATION,
                {
                    "order_id": order.order_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "status": "confirmed",
                    "expected_delivery": expected_delivery.isoformat(),
                    "lead_time_days": actual_lead_time
                },
                priority=2
            )
        
        print(f"  [{self.name}] [OK] Order {order.order_id} confirmed: "
              f"{order.quantity} x {order.product_id}, delivery in {actual_lead_time} days")
    
    def _reject_order(self, order: Order, requester_id: str, reason: str):
        """Reject an invalid order."""
        order.update_status(OrderStatus.CANCELLED)
        self.rejected_orders.append(order)
        
        # Send rejection to requester
        requester = self.get_agent(requester_id)
        if requester:
            self.send_message(
                requester,
                MessageType.ORDER_CONFIRMATION,
                {
                    "order_id": order.order_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "status": "rejected",
                    "reason": reason
                },
                priority=2
            )
        
        print(f"  [{self.name}] ✗ Order rejected: {reason}")
    
    def _calculate_actual_lead_time(self) -> int:
        """Calculate actual lead time with reliability simulation."""
        base_lead_time = self.lead_time_days
        
        # Simulate reliability - chance of delay
        if np.random.random() > self.reliability:
            # Order is delayed (1-5 extra days)
            delay = np.random.randint(1, 6)
            return base_lead_time + delay
        
        return base_lead_time
    
    def _handle_status_request(self, message: Message):
        """Handle a status inquiry."""
        requester = self.get_agent(message.sender_id)
        if requester:
            self.send_message(
                requester,
                MessageType.SYSTEM_STATUS,
                self.get_status()
            )
    
    def process_shipments(self):
        """Process orders and create shipments for those ready."""
        # Move confirmed orders to shipping
        orders_to_ship = []
        for order in self.processing_orders:
            if order.status == OrderStatus.CONFIRMED:
                order.update_status(OrderStatus.PROCESSING)
                
                # Create shipment
                shipment = PendingShipment(
                    order=order,
                    scheduled_delivery=order.expected_delivery,
                    shipped_at=self.current_time
                )
                self.pending_shipments.append(shipment)
                orders_to_ship.append(order)
                order.update_status(OrderStatus.SHIPPED)
                
                # Send shipment notification
                target = self.get_agent(order.target_agent_id)
                if target:
                    self.send_message(
                        target,
                        MessageType.SHIPMENT_NOTIFICATION,
                        {
                            "order_id": order.order_id,
                            "product_id": order.product_id,
                            "quantity": order.quantity,
                            "status": "shipped",
                            "expected_delivery": order.expected_delivery.isoformat()
                        }
                    )
        
        # Remove shipped orders from processing
        for order in orders_to_ship:
            self.processing_orders.remove(order)
    
    def deliver_shipments(self):
        """Deliver shipments that have reached their delivery date."""
        delivered = []
        
        for shipment in self.pending_shipments:
            if shipment.is_ready_for_delivery(self.current_time):
                order = shipment.order
                order.actual_delivery = self.current_time
                order.update_status(OrderStatus.DELIVERED)
                
                # Track on-time vs late
                if self.current_time <= shipment.scheduled_delivery:
                    self.on_time_deliveries += 1
                else:
                    self.late_deliveries += 1
                
                # Update statistics
                self.total_units_shipped += order.quantity
                self.total_revenue += order.total_cost
                
                # Notify warehouse of delivery
                target = self.get_agent(order.target_agent_id)
                if target:
                    self.send_message(
                        target,
                        MessageType.SHIPMENT_NOTIFICATION,
                        {
                            "order_id": order.order_id,
                            "product_id": order.product_id,
                            "quantity": order.quantity,
                            "status": "delivered",
                            "delivery_date": self.current_time.isoformat()
                        },
                        priority=3
                    )
                
                self.fulfilled_orders.append(order)
                delivered.append(shipment)
                
                print(f"  [{self.name}] [DELIVERED] Delivered: {order.quantity} x {order.product_id} "
                      f"to {order.target_agent_id}")
        
        # Remove delivered shipments
        for shipment in delivered:
            self.pending_shipments.remove(shipment)
    
    def step(self, current_time: datetime = None):
        """Execute one time step for the supplier agent."""
        super().step(current_time)
        
        # Reset daily capacity if needed
        self.capacity.reset_if_new_day(self.current_time)
        
        # Process shipments
        self.process_shipments()
        
        # Deliver ready shipments
        self.deliver_shipments()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive supplier status."""
        base_status = super().get_status()
        base_status.update({
            "lead_time_days": self.lead_time_days,
            "reliability": self.reliability,
            "available_capacity": self.capacity.available_capacity,
            "pending_orders": len(self.processing_orders),
            "pending_shipments": len(self.pending_shipments),
            "total_orders_received": self.total_orders_received,
            "total_units_shipped": self.total_units_shipped,
            "total_revenue": self.total_revenue,
            "on_time_delivery_rate": (
                self.on_time_deliveries / max(1, self.on_time_deliveries + self.late_deliveries)
            ),
            "rejected_orders": len(self.rejected_orders)
        })
        return base_status
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for this supplier."""
        total_deliveries = self.on_time_deliveries + self.late_deliveries
        
        return {
            "order_fulfillment_rate": (
                len(self.fulfilled_orders) / max(1, self.total_orders_received)
            ),
            "on_time_delivery_rate": (
                self.on_time_deliveries / max(1, total_deliveries)
            ),
            "average_order_size": (
                self.total_units_shipped / max(1, len(self.fulfilled_orders))
            ),
            "capacity_utilization": (
                self.capacity.current_daily_used / max(1, self.capacity.max_daily_capacity)
            ),
            "rejection_rate": (
                len(self.rejected_orders) / max(1, self.total_orders_received)
            )
        }
