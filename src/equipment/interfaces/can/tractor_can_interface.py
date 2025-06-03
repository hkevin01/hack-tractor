"""
CAN bus interface for tractors and agricultural equipment.
"""

import can
import logging
import time
import json
from datetime import datetime
from threading import Thread, Event
import os

logger = logging.getLogger(__name__)

class TractorCANInterface:
    """Interface for CAN bus communication with tractors and agricultural equipment."""
    
    # Common CAN IDs for agricultural equipment (these are example values)
    CAN_IDS = {
        'ENGINE_RPM': 0x0CF00400,
        'ENGINE_TEMP': 0x0CF00401,
        'HYDRAULIC_PRESSURE': 0x0CF00402,
        'FUEL_LEVEL': 0x0CF00403,
        'VEHICLE_SPEED': 0x0CF00404,
        'PTO_SPEED': 0x0CF00405,
        'HITCH_POSITION': 0x0CF00406,
        'GPS_POSITION': 0x0CF00407,
        'IMPLEMENT_STATUS': 0x0CF00408
    }
    
    def __init__(self, channel='can0', bustype='socketcan', bitrate=250000, config_file=None):
        """
        Initialize the CAN interface.
        
        Args:
            channel (str): CAN interface name
            bustype (str): CAN interface type
            bitrate (int): Bitrate for CAN bus
            config_file (str, optional): Path to CAN configuration file
        """
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.bus = None
        self.connected = False
        self.listeners = []
        self.monitor_thread = None
        self.stop_monitoring = Event()
        self.data_buffer = {}
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                # Override CAN_IDS with config values if provided
                if 'can_ids' in self.config:
                    self.CAN_IDS.update(self.config['can_ids'])
                    
        logger.info(f"Initialized tractor CAN interface on {channel}")
    
    def connect(self):
        """
        Connect to the CAN bus.
        
        Returns:
            bool: Success status
        """
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
        """
        Disconnect from the CAN bus.
        """
        if self.monitoring:
            self.stop_monitoring.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
                
        if self.bus:
            self.bus.shutdown()
            self.connected = False
            logger.info(f"Disconnected from CAN bus on {self.channel}")
    
    def send_message(self, can_id, data, extended_id=True):
        """
        Send a message on the CAN bus.
        
        Args:
            can_id (int): CAN message ID (from CAN_IDS or custom)
            data (list or bytes): Data to send (up to 8 bytes)
            extended_id (bool): Whether to use extended ID format
            
        Returns:
            bool: Success status
        """
        if not self.connected or not self.bus:
            logger.error("Cannot send message, not connected to CAN bus")
            return False
        
        try:
            # If can_id is a string key from CAN_IDS, look it up
            if isinstance(can_id, str) and can_id in self.CAN_IDS:
                can_id = self.CAN_IDS[can_id]
                
            msg = can.Message(
                arbitration_id=can_id,
                data=data,
                extended_id=extended_id,
                timestamp=time.time()
            )
            self.bus.send(msg)
            logger.debug(f"Sent CAN message: {msg}")
            return True
        except can.CanError as e:
            logger.error(f"Failed to send CAN message: {e}")
            return False
    
    @property
    def monitoring(self):
        """
        Check if monitoring is active.
        
        Returns:
            bool: True if monitoring thread is active
        """
        return self.monitor_thread is not None and self.monitor_thread.is_alive()
    
    def start_monitoring(self, callback=None):
        """
        Start monitoring CAN messages.
        
        Args:
            callback (callable, optional): Function to call with each message
            
        Returns:
            bool: Success status
        """
        if not self.connected or not self.bus:
            logger.error("Cannot start monitoring, not connected to CAN bus")
            return False
            
        if self.monitoring:
            logger.warning("Monitoring already active")
            return True
            
        self.stop_monitoring.clear()
        self.monitor_thread = Thread(
            target=self._monitor_loop,
            args=(callback,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Started CAN bus monitoring")
        return True
    
    def _monitor_loop(self, callback=None):
        """
        Internal method for the monitoring thread.
        
        Args:
            callback (callable, optional): Function to call with each message
        """
        while not self.stop_monitoring.is_set():
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    # Process the message
                    self._process_message(msg)
                    
                    # Call the callback if provided
                    if callback:
                        callback(msg)
            except can.CanError as e:
                logger.error(f"Error in CAN monitoring: {e}")
                time.sleep(1.0)  # Prevent busy-waiting on error
    
    def _process_message(self, msg):
        """
        Process a CAN message and update internal data buffer.
        
        Args:
            msg (can.Message): CAN message to process
        """
        # Store raw message in buffer by ID
        self.data_buffer[msg.arbitration_id] = {
            'timestamp': msg.timestamp,
            'data': list(msg.data),
            'raw_message': msg
        }
        
        # Try to decode known message types
        for name, can_id in self.CAN_IDS.items():
            if msg.arbitration_id == can_id:
                decoded_value = self._decode_message(name, msg.data)
                if decoded_value is not None:
                    self.data_buffer[name] = {
                        'timestamp': msg.timestamp,
                        'value': decoded_value,
                        'raw_message': msg
                    }
                break
    
    def _decode_message(self, message_type, data):
        """
        Decode CAN message data based on message type.
        
        Args:
            message_type (str): Type of message (key from CAN_IDS)
            data (bytes): Raw message data
            
        Returns:
            object: Decoded value or None if unknown type
        """
        # Example decoders for common values (these would be replaced with actual implementations)
        if message_type == 'ENGINE_RPM':
            # Example: RPM is in bytes 0-1, scale factor 0.125
            if len(data) >= 2:
                rpm = int.from_bytes(data[0:2], byteorder='little') * 0.125
                return rpm
        elif message_type == 'ENGINE_TEMP':
            # Example: Temperature in byte 0, offset -40°C
            if len(data) >= 1:
                temp = data[0] - 40
                return temp
        elif message_type == 'FUEL_LEVEL':
            # Example: Fuel percentage in byte 0
            if len(data) >= 1:
                fuel = data[0] * 100 / 255  # Convert to percentage
                return fuel
        elif message_type == 'VEHICLE_SPEED':
            # Example: Speed in bytes 0-1, scale factor 0.01 km/h
            if len(data) >= 2:
                speed = int.from_bytes(data[0:2], byteorder='little') * 0.01
                return speed
        
        # Return None for unknown types
        return None
    
    def get_data(self, key=None):
        """
        Get current data from the buffer.
        
        Args:
            key (str or int, optional): Specific data key to retrieve
            
        Returns:
            dict or object: Data for the specified key or all data
        """
        if key is None:
            return self.data_buffer
        
        return self.data_buffer.get(key)
    
    def save_log(self, filepath):
        """
        Save CAN message log to a file.
        
        Args:
            filepath (str): Path to save the log
            
        Returns:
            bool: Success status
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Extract loggable data
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'data': {}
            }
            
            # Include decoded values
            for key, value in self.data_buffer.items():
                if isinstance(key, str):  # Only include named parameters
                    if 'value' in value:
                        log_data['data'][key] = {
                            'timestamp': value['timestamp'],
                            'value': value['value']
                        }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            logger.info(f"Saved CAN log to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save CAN log: {e}")
            return False
