"""
Warehouse Agent Module
======================
Manages inventory levels, calculates reorder points, and places orders.

Responsibilities:
- Track inventory levels for all products
- Calculate EOQ (Economic Order Quantity)
- Calculate Safety Stock and Reorder Points
- Automatically place orders when stock falls below ROP
- Receive shipments and update inventory
- Handle stock requests from retailers
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, Message, MessageType, Order, OrderStatus


@dataclass
class InventoryItem:
    """Represents a single inventory item in the warehouse."""
    product_id: str
    product_name: str
    category: str
    current_stock: int
    reorder_level: int
    max_capacity: int
    unit_cost: float
    holding_cost_pct: float  # Annual holding cost as % of unit cost
    ordering_cost: float     # Fixed cost per order
    lead_time_days: int
    daily_demand_avg: float
    daily_demand_std: float
    supplier_id: str
    last_order_date: Optional[datetime] = None
    last_order_qty: int = 0
    
    # Calculated fields (updated by warehouse)
    calculated_eoq: int = 0
    calculated_rop: int = 0
    calculated_safety_stock: int = 0
    
    @property
    def stock_value(self) -> float:
        """Current stock value."""
        return self.current_stock * self.unit_cost
    
    @property
    def days_of_supply(self) -> float:
        """Estimated days of supply remaining."""
        if self.daily_demand_avg > 0:
            return self.current_stock / self.daily_demand_avg
        return float('inf')
    
    @property
    def is_below_reorder_point(self) -> bool:
        """Check if stock is below reorder point."""
        return self.current_stock <= self.calculated_rop
    
    @property
    def is_critical(self) -> bool:
        """Check if stock is critically low (below safety stock)."""
        return self.current_stock <= self.calculated_safety_stock
    
    def get_status(self) -> str:
        """Get inventory status string."""
        if self.is_critical:
            return "CRITICAL"
        elif self.is_below_reorder_point:
            return "REORDER"
        elif self.current_stock >= self.max_capacity * 0.9:
            return "OVERSTOCKED"
        return "OK"


@dataclass
class PendingOrder:
    """Tracks an order that has been placed but not yet received."""
    order: Order
    expected_delivery: datetime
    placed_at: datetime = field(default_factory=datetime.now)


class WarehouseAgent(BaseAgent):
    """
    Warehouse Agent - Manages inventory and ordering operations.
    
    Features:
    - Inventory tracking with multiple products
    - EOQ (Economic Order Quantity) calculation
    - Safety stock calculation for service level
    - Reorder Point (ROP) calculation
    - Automatic reordering when stock is low
    - Shipment receiving and stock updates
    
    Attributes:
        warehouse_id: Unique warehouse identifier
        location: Physical location of warehouse
        service_level: Target service level (0-1), default 0.95 (95%)
    """
    
    def __init__(self, agent_id: str, name: str,
                 location: str = "",
                 service_level: float = 0.95,
                 inventory_df: pd.DataFrame = None):
        super().__init__(agent_id, name)
        
        self.location = location
        self.service_level = service_level
        self.z_score = self._get_z_score(service_level)
        
        # Inventory storage
        self.inventory: Dict[str, InventoryItem] = {}
        
        # Order tracking
        self.pending_orders: List[PendingOrder] = []
        self.completed_orders: List[Order] = []
        self.order_history: List[Dict] = []
        
        # Statistics
        self.total_orders_placed = 0
        self.total_units_received = 0
        self.total_stockouts = 0
        self.total_holding_cost = 0.0
        self.total_ordering_cost = 0.0
        
        # Load inventory if provided
        if inventory_df is not None:
            self._load_inventory(inventory_df)
    
    def _get_z_score(self, service_level: float) -> float:
        """Get Z-score for given service level."""
        # Common Z-scores for service levels
        z_scores = {
            0.90: 1.28,
            0.95: 1.65,
            0.99: 2.33,
            0.999: 3.09
        }
        # Find closest match or interpolate
        if service_level in z_scores:
            return z_scores[service_level]
        # Default to 95% service level
        return 1.65
    
    def _load_inventory(self, df: pd.DataFrame):
        """Load inventory from DataFrame."""
        # Filter for this warehouse
        warehouse_df = df[df['warehouse_id'] == self.agent_id].copy()
        
        for _, row in warehouse_df.iterrows():
            item = InventoryItem(
                product_id=row['product_id'],
                product_name=row['product_name'],
                category=row['category'],
                current_stock=int(row['current_stock']),
                reorder_level=int(row['reorder_level']),
                max_capacity=int(row['max_capacity']),
                unit_cost=float(row['unit_cost']),
                holding_cost_pct=float(row['holding_cost_pct']),
                ordering_cost=float(row['ordering_cost']),
                lead_time_days=int(row['lead_time_days']),
                daily_demand_avg=float(row['daily_demand_avg']),
                daily_demand_std=float(row['daily_demand_std']),
                supplier_id=row['supplier_id'],
                last_order_date=pd.to_datetime(row['last_order_date']) if pd.notna(row.get('last_order_date')) else None,
                last_order_qty=int(row.get('last_order_qty', 0))
            )
            
            # Calculate optimal parameters
            self._calculate_inventory_parameters(item)
            self.inventory[item.product_id] = item
    
    def _calculate_inventory_parameters(self, item: InventoryItem):
        """Calculate EOQ, Safety Stock, and ROP for an item."""
        item.calculated_eoq = self.calculate_eoq(item)
        item.calculated_safety_stock = self.calculate_safety_stock(item)
        item.calculated_rop = self.calculate_reorder_point(item)
    
    def calculate_eoq(self, item: InventoryItem) -> int:
        """
        Calculate Economic Order Quantity using the Wilson Formula.
        
        EOQ = sqrt((2 * D * S) / H)
        
        Where:
            D = Annual demand
            S = Ordering cost per order
            H = Annual holding cost per unit
        """
        D = item.daily_demand_avg * 365  # Annual demand
        S = item.ordering_cost            # Setup/ordering cost
        H = item.unit_cost * item.holding_cost_pct  # Annual holding cost per unit
        
        if H <= 0 or D <= 0:
            # Fallback to 30-day supply
            return max(1, int(item.daily_demand_avg * 30))
        
        eoq = np.sqrt((2 * D * S) / H)
        
        # Ensure EOQ doesn't exceed max capacity
        eoq = min(eoq, item.max_capacity - item.current_stock)
        
        return max(1, int(eoq))
    
    def calculate_safety_stock(self, item: InventoryItem) -> int:
        """
        Calculate Safety Stock for target service level.
        
        SS = Z * σ_d * sqrt(L)
        
        Where:
            Z = Z-score for service level
            σ_d = Standard deviation of daily demand
            L = Lead time in days
        """
        z = self.z_score
        sigma_d = item.daily_demand_std
        L = item.lead_time_days
        
        safety_stock = z * sigma_d * np.sqrt(L)
        
        return max(0, int(np.ceil(safety_stock)))
    
    def calculate_reorder_point(self, item: InventoryItem) -> int:
        """
        Calculate Reorder Point.
        
        ROP = (Average daily demand * Lead time) + Safety Stock
        """
        lead_time_demand = item.daily_demand_avg * item.lead_time_days
        safety_stock = item.calculated_safety_stock or self.calculate_safety_stock(item)
        
        rop = lead_time_demand + safety_stock
        
        return int(np.ceil(rop))
    
    def handle_message(self, message: Message):
        """Handle incoming messages."""
        if message.message_type == MessageType.ORDER_CONFIRMATION:
            self._handle_order_confirmation(message)
        elif message.message_type == MessageType.SHIPMENT_NOTIFICATION:
            self._handle_shipment_notification(message)
        elif message.message_type == MessageType.STOCK_REQUEST:
            self._handle_stock_request(message)
        elif message.message_type == MessageType.DEMAND_FORECAST:
            self._handle_demand_forecast(message)
    
    def _handle_order_confirmation(self, message: Message):
        """Handle order confirmation from supplier."""
        content = message.content
        status = content.get("status")
        order_id = content.get("order_id")
        
        if status == "confirmed":
            print(f"  [{self.name}] Order {order_id} confirmed by supplier")
        elif status == "rejected":
            reason = content.get("reason", "Unknown")
            print(f"  [{self.name}] Order {order_id} rejected: {reason}")
            # Remove from pending if it was added
            self.pending_orders = [
                po for po in self.pending_orders 
                if po.order.order_id != order_id
            ]
    
    def _handle_shipment_notification(self, message: Message):
        """Handle shipment notification from supplier."""
        content = message.content
        status = content.get("status")
        
        if status == "delivered":
            self._receive_shipment(
                product_id=content.get("product_id"),
                quantity=content.get("quantity"),
                order_id=content.get("order_id")
            )
        elif status == "shipped":
            print(f"  [{self.name}] Shipment {content.get('order_id')} is on the way")
    
    def _handle_stock_request(self, message: Message):
        """Handle stock request from retailer."""
        content = message.content
        product_id = content.get("product_id")
        quantity = content.get("quantity", 0)
        
        # Check if we can fulfill
        if product_id in self.inventory:
            item = self.inventory[product_id]
            if item.current_stock >= quantity:
                # Fulfill the request
                item.current_stock -= quantity
                
                # Send confirmation
                requester = self.get_agent(message.sender_id)
                if requester:
                    self.send_message(
                        requester,
                        MessageType.STOCK_UPDATE,
                        {
                            "product_id": product_id,
                            "quantity": quantity,
                            "status": "fulfilled"
                        }
                    )
                print(f"  [{self.name}] Fulfilled {quantity} units of {product_id}")
            else:
                # Stockout
                self.total_stockouts += 1
                print(f"  [{self.name}] [!] STOCKOUT: Cannot fulfill {quantity} units of {product_id}")
    
    def _handle_demand_forecast(self, message: Message):
        """Handle demand forecast update from retailer."""
        content = message.content
        product_id = content.get("product_id")
        new_demand_avg = content.get("daily_demand_avg")
        new_demand_std = content.get("daily_demand_std")
        
        if product_id in self.inventory:
            item = self.inventory[product_id]
            if new_demand_avg is not None:
                item.daily_demand_avg = new_demand_avg
            if new_demand_std is not None:
                item.daily_demand_std = new_demand_std
            
            # Recalculate parameters
            self._calculate_inventory_parameters(item)
            print(f"  [{self.name}] Updated forecast for {product_id}")
    
    def _receive_shipment(self, product_id: str, quantity: int, order_id: str = None):
        """Receive a shipment and update inventory."""
        if product_id in self.inventory:
            item = self.inventory[product_id]
            
            # Update stock (respecting max capacity)
            old_stock = item.current_stock
            item.current_stock = min(item.current_stock + quantity, item.max_capacity)
            actual_received = item.current_stock - old_stock
            
            self.total_units_received += actual_received
            
            # Remove from pending orders
            self.pending_orders = [
                po for po in self.pending_orders 
                if po.order.order_id != order_id
            ]
            
            print(f"  [{self.name}] [RECV] Received {actual_received} units of {product_id}. "
                  f"Stock: {old_stock} -> {item.current_stock}")
    
    def check_and_reorder(self, suppliers: Dict[str, 'BaseAgent']) -> List[Dict]:
        """
        Check inventory levels and place orders for items below ROP.
        
        Args:
            suppliers: Dictionary of supplier agents by ID
            
        Returns:
            List of reorder actions taken
        """
        reorder_actions = []
        
        for product_id, item in self.inventory.items():
            # Skip if already have pending order for this product
            has_pending = any(
                po.order.product_id == product_id 
                for po in self.pending_orders
            )
            
            if item.is_below_reorder_point and not has_pending:
                # Calculate order quantity
                order_qty = item.calculated_eoq
                
                # Adjust if critical - order more
                if item.is_critical:
                    order_qty = max(order_qty, int(item.daily_demand_avg * item.lead_time_days * 2))
                
                # Ensure we don't exceed capacity
                max_order = item.max_capacity - item.current_stock
                order_qty = min(order_qty, max_order)
                
                if order_qty > 0:
                    # Place order
                    supplier = suppliers.get(item.supplier_id)
                    if supplier:
                        action = self._place_order(supplier, item, order_qty)
                        if action:
                            reorder_actions.append(action)
        
        return reorder_actions
    
    def _place_order(self, supplier: 'BaseAgent', item: InventoryItem, quantity: int) -> Optional[Dict]:
        """Place an order with a supplier."""
        # Create order
        order = Order.create(
            product_id=item.product_id,
            quantity=quantity,
            source_id=supplier.agent_id,
            target_id=self.agent_id,
            unit_cost=item.unit_cost
        )
        
        # Send order request
        self.send_message(
            supplier,
            MessageType.ORDER_REQUEST,
            {
                "product_id": item.product_id,
                "quantity": quantity,
                "unit_cost": item.unit_cost,
                "urgency": "high" if item.is_critical else "normal"
            },
            priority=3 if item.is_critical else 2
        )
        
        # Track pending order
        expected_delivery = self.current_time + timedelta(days=item.lead_time_days)
        pending = PendingOrder(
            order=order,
            expected_delivery=expected_delivery,
            placed_at=self.current_time
        )
        self.pending_orders.append(pending)
        
        # Update item
        item.last_order_date = self.current_time
        item.last_order_qty = quantity
        
        # Update statistics
        self.total_orders_placed += 1
        self.total_ordering_cost += item.ordering_cost
        
        # Log
        self.order_history.append({
            "timestamp": self.current_time,
            "order_id": order.order_id,
            "product_id": item.product_id,
            "quantity": quantity,
            "supplier_id": supplier.agent_id,
            "status": item.get_status()
        })
        
        print(f"  [{self.name}] [ORDER] Ordered {quantity} units of {item.product_name} "
              f"(Status: {item.get_status()}, Stock: {item.current_stock}/{item.calculated_rop})")
        
        return {
            "order_id": order.order_id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity": quantity,
            "supplier_id": supplier.agent_id,
            "expected_delivery": expected_delivery,
            "status": item.get_status()
        }
    
    def simulate_daily_demand(self):
        """Simulate daily demand consumption (for testing)."""
        for product_id, item in self.inventory.items():
            # Generate random demand based on normal distribution
            demand = max(0, int(np.random.normal(
                item.daily_demand_avg, 
                item.daily_demand_std
            )))
            
            # Consume stock
            if item.current_stock >= demand:
                item.current_stock -= demand
            else:
                # Partial fulfillment + stockout
                self.total_stockouts += 1
                item.current_stock = 0
    
    def calculate_daily_holding_cost(self) -> float:
        """Calculate daily holding cost for all inventory."""
        daily_cost = 0.0
        
        for item in self.inventory.values():
            # Annual holding cost per unit / 365
            daily_holding_per_unit = (item.unit_cost * item.holding_cost_pct) / 365
            daily_cost += item.current_stock * daily_holding_per_unit
        
        self.total_holding_cost += daily_cost
        return daily_cost
    
    def step(self, current_time: datetime = None):
        """Execute one time step for the warehouse agent."""
        super().step(current_time)
        
        # Calculate holding costs
        self.calculate_daily_holding_cost()
    
    def get_inventory_summary(self) -> pd.DataFrame:
        """Get a summary DataFrame of all inventory."""
        data = []
        for item in self.inventory.values():
            data.append({
                "product_id": item.product_id,
                "product_name": item.product_name,
                "category": item.category,
                "current_stock": item.current_stock,
                "reorder_point": item.calculated_rop,
                "safety_stock": item.calculated_safety_stock,
                "eoq": item.calculated_eoq,
                "days_of_supply": round(item.days_of_supply, 1),
                "stock_value": round(item.stock_value, 2),
                "status": item.get_status()
            })
        
        return pd.DataFrame(data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive warehouse status."""
        base_status = super().get_status()
        
        # Count items by status
        status_counts = {"OK": 0, "REORDER": 0, "CRITICAL": 0, "OVERSTOCKED": 0}
        total_value = 0.0
        
        for item in self.inventory.values():
            status = item.get_status()
            status_counts[status] = status_counts.get(status, 0) + 1
            total_value += item.stock_value
        
        base_status.update({
            "location": self.location,
            "total_products": len(self.inventory),
            "total_stock_value": round(total_value, 2),
            "status_counts": status_counts,
            "pending_orders": len(self.pending_orders),
            "total_orders_placed": self.total_orders_placed,
            "total_units_received": self.total_units_received,
            "total_stockouts": self.total_stockouts,
            "total_holding_cost": round(self.total_holding_cost, 2),
            "total_ordering_cost": round(self.total_ordering_cost, 2),
            "service_level": self.service_level
        })
        
        return base_status
    
    def get_items_needing_reorder(self) -> List[InventoryItem]:
        """Get list of items that need reordering."""
        return [
            item for item in self.inventory.values()
            if item.is_below_reorder_point
        ]
    
    def get_critical_items(self) -> List[InventoryItem]:
        """Get list of items with critical stock levels."""
        return [
            item for item in self.inventory.values()
            if item.is_critical
        ]
