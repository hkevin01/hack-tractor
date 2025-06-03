"""OBD-II interface for agricultural equipment."""

import obd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class OBDInterface:
    """Interface for OBD-II communication with agricultural equipment."""
    
    def __init__(self, portstr=None, baudrate=38400, protocol=None, fast=True):
        """Initialize the OBD-II interface.
        
        Args:
            portstr (str, optional): Serial port to use
            baudrate (int): Baud rate for serial communication
            protocol (str, optional): OBD protocol to use
            fast (bool): Whether to connect in fast mode
        """
        self.portstr = portstr
        self.baudrate = baudrate
        self.protocol = protocol
        self.fast = fast
        self.connection = None
        self.connected = False
        logger.info("Initialized OBD-II interface")
    
    def connect(self):
        """Connect to the OBD-II interface."""
        try:
            self.connection = obd.OBD(
                portstr=self.portstr,
                baudrate=self.baudrate,
                protocol=self.protocol,
                fast=self.fast
            )
            self.connected = self.connection.is_connected()
            if self.connected:
                logger.info(f"Connected to OBD-II interface on {self.connection.port_name()}")
                logger.info(f"Protocol: {self.connection.protocol_name()}")
            else:
                logger.error("Failed to connect to OBD-II interface")
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to OBD-II interface: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the OBD-II interface."""
        if self.connection:
            self.connection.close()
            self.connected = False
            logger.info("Disconnected from OBD-II interface")
    
    def query(self, command):
        """Query the OBD-II interface.
        
        Args:
            command (str or obd.Command): Command to query
            
        Returns:
            obd.Response: Response from the OBD-II interface
        """
        if not self.connected or not self.connection:
            logger.error("Cannot query, not connected to OBD-II interface")
            return None
        
        try:
            if isinstance(command, str):
                cmd = obd.commands[command]
            else:
                cmd = command
                
            response = self.connection.query(cmd)
            logger.debug(f"Query: {cmd}, Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error querying OBD-II interface: {e}")
            return None
    
    def get_supported_commands(self):
        """Get the list of supported commands.
        
        Returns:
            list: List of supported commands
        """
        if not self.connected or not self.connection:
            logger.error("Cannot get supported commands, not connected to OBD-II interface")
            return []
        
        return self.connection.supported_commands
