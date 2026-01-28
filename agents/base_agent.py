"""
Base Agent Module
=================
Contains the base classes for all agents in the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class MessageType(Enum):
    """Types of messages that agents can exchange."""
    ORDER_REQUEST = "order_request"
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPMENT_NOTIFICATION = "shipment_notification"
    STOCK_REQUEST = "stock_request"
    STOCK_UPDATE = "stock_update"
    DEMAND_FORECAST = "demand_forecast"
    REORDER_ALERT = "reorder_alert"
    SYSTEM_STATUS = "system_status"


class OrderStatus(Enum):
    """Status of an order in the system."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class Message:
    """Represents a message exchanged between agents."""
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1=low, 2=medium, 3=high
    
    @classmethod
    def create(cls, sender_id: str, recipient_id: str, 
               message_type: MessageType, content: Dict[str, Any],
               priority: int = 1) -> 'Message':
        """Factory method to create a new message."""
        return cls(
            message_id=str(uuid.uuid4())[:8],
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            priority=priority
        )


@dataclass
class Order:
    """Represents an order in the system."""
    order_id: str
    product_id: str
    quantity: int
    source_agent_id: str
    target_agent_id: str
    unit_cost: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expected_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    
    @classmethod
    def create(cls, product_id: str, quantity: int, 
               source_id: str, target_id: str, unit_cost: float = 0.0) -> 'Order':
        """Factory method to create a new order."""
        return cls(
            order_id=f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}",
            product_id=product_id,
            quantity=quantity,
            source_agent_id=source_id,
            target_agent_id=target_id,
            unit_cost=unit_cost
        )
    
    @property
    def total_cost(self) -> float:
        """Calculate total order cost."""
        return self.quantity * self.unit_cost
    
    def update_status(self, new_status: OrderStatus):
        """Update the order status."""
        self.status = new_status


class BaseAgent:
    """
    Base class for all agents in the multi-agent inventory system.
    
    Provides:
    - Message queue management
    - Inter-agent communication
    - Basic lifecycle methods (step, process_messages)
    """
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.message_queue: List[Message] = []
        self.sent_messages: List[Message] = []
        self.received_messages: List[Message] = []
        self.is_active = True
        self.current_time: datetime = datetime.now()
        self._registered_agents: Dict[str, 'BaseAgent'] = {}
        
    def register_agent(self, agent: 'BaseAgent'):
        """Register another agent for communication."""
        self._registered_agents[agent.agent_id] = agent
        
    def get_agent(self, agent_id: str) -> Optional['BaseAgent']:
        """Get a registered agent by ID."""
        return self._registered_agents.get(agent_id)
    
    def send_message(self, recipient: 'BaseAgent', message_type: MessageType, 
                     content: Dict[str, Any], priority: int = 1):
        """Send a message to another agent."""
        message = Message.create(
            sender_id=self.agent_id,
            recipient_id=recipient.agent_id,
            message_type=message_type,
            content=content,
            priority=priority
        )
        recipient.receive_message(message)
        self.sent_messages.append(message)
        return message
    
    def receive_message(self, message: Message):
        """Receive a message from another agent."""
        self.message_queue.append(message)
        self.received_messages.append(message)
        
    def process_messages(self):
        """Process all messages in the queue (sorted by priority)."""
        # Sort by priority (highest first)
        self.message_queue.sort(key=lambda m: m.priority, reverse=True)
        
        while self.message_queue:
            message = self.message_queue.pop(0)
            self.handle_message(message)
    
    def handle_message(self, message: Message):
        """
        Handle a specific message. Override in subclasses.
        
        Args:
            message: The message to handle
        """
        pass
    
    def step(self, current_time: datetime = None):
        """
        Execute one time step for this agent.
        Override in subclasses for specific behavior.
        
        Args:
            current_time: The current simulation time
        """
        if current_time:
            self.current_time = current_time
        self.process_messages()
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of this agent."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "is_active": self.is_active,
            "pending_messages": len(self.message_queue),
            "total_sent": len(self.sent_messages),
            "total_received": len(self.received_messages)
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name})"
