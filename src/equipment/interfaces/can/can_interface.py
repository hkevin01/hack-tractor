"""CAN bus interface for agricultural equipment."""

import can
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CANInterface:
    """Interface for CAN bus communication with agricultural equipment."""
    
    def __init__(self, channel='can0', bustype='socketcan', bitrate=250000):
        """Initialize the CAN interface.
        
        Args:
            channel (str): CAN interface name
            bustype (str): CAN interface type
            bitrate (int): Bitrate for CAN bus
        """
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.bus = None
        self.connected = False
        self.listeners = []
        logger.info(f"Initialized CAN interface on {channel}")
    
    def connect(self):
        """Connect to the CAN bus."""
        try:
            self.bus = can.Bus(
                channel=self.channel,
                bustype=self.bustype,
                bitrate=self.bitrate
            )
            self.connected = True
            logger.info(f"Connected to CAN bus on {self.channel}")
            return True
        except can.CanError as e:
            logger.error(f"Failed to connect to CAN bus: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the CAN bus."""
        if self.bus:
            self.bus.shutdown()
            self.connected = False
            logger.info(f"Disconnected from CAN bus on {self.channel}")
    
    def send_message(self, arbitration_id, data, extended_id=False):
        """Send a message on the CAN bus.
        
        Args:
            arbitration_id (int): CAN message ID
            data (list or bytes): Data to send
            extended_id (bool): Whether to use extended ID format
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.connected or not self.bus:
            logger.error("Cannot send message, not connected to CAN bus")
            return False
        
        try:
            msg = can.Message(
                arbitration_id=arbitration_id,
                data=data,
                extended_id=extended_id,
                timestamp=datetime.now().timestamp()
            )
            self.bus.send(msg)
            logger.debug(f"Sent CAN message: {msg}")
            return True
        except can.CanError as e:
            logger.error(f"Failed to send CAN message: {e}")
            return False
    
    def add_listener(self, listener):
        """Add a listener for CAN messages.
        
        Args:
            listener: Listener object that implements the can.Listener interface
        """
        if self.bus:
            notifier = can.Notifier(self.bus, [listener])
            self.listeners.append((listener, notifier))
            logger.info(f"Added listener {listener}")
    
    def receive(self, timeout=1.0):
        """Receive a message from the CAN bus.
        
        Args:
            timeout (float): Timeout in seconds
            
        Returns:
            can.Message or None: Received message or None if timeout
        """
        if not self.connected or not self.bus:
            logger.error("Cannot receive message, not connected to CAN bus")
            return None
        
        try:
            msg = self.bus.recv(timeout=timeout)
            if msg:
                logger.debug(f"Received CAN message: {msg}")
            return msg
        except can.CanError as e:
            logger.error(f"Failed to receive CAN message: {e}")
            return None
