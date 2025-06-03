"""
OBD-II interface for tractors and agricultural equipment.
"""

import obd
import logging
import time
import json
from datetime import datetime
from threading import Thread, Event
import os

logger = logging.getLogger(__name__)

class TractorOBDInterface:
    """Interface for OBD-II communication with agricultural equipment."""
    
    # Common OBD commands for agricultural equipment
    COMMON_COMMANDS = [
        obd.commands.RPM,
        obd.commands.SPEED,
        obd.commands.COOLANT_TEMP,
        obd.commands.ENGINE_LOAD,
        obd.commands.FUEL_LEVEL,
        obd.commands.THROTTLE_POS,
        obd.commands.RUN_TIME,
        obd.commands.FUEL_RATE,
        obd.commands.INTAKE_TEMP,
        obd.commands.OIL_TEMP
    ]
    
    def __init__(self, portstr=None, baudrate=38400, protocol=None, fast=True, config_file=None):
        """
        Initialize the OBD-II interface.
        
        Args:
            portstr (str, optional): Serial port to use
            baudrate (int): Baud rate for serial communication
            protocol (str, optional): OBD protocol to use
            fast (bool): Whether to connect in fast mode
            config_file (str, optional): Path to OBD configuration file
        """
        self.portstr = portstr
        self.baudrate = baudrate
        self.protocol = protocol
        self.fast = fast
        self.connection = None
        self.connected = False
        self.data_buffer = {}
        self.monitor_thread = None
        self.stop_monitoring = Event()
        self.custom_commands = {}
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                
                # Load custom commands if available
                if 'custom_commands' in self.config:
                    for cmd_name, cmd_data in self.config['custom_commands'].items():
                        mode = cmd_data.get('mode')
                        pid = cmd_data.get('pid')
                        
                        if mode is not None and pid is not None:
                            cmd = obd.OBDCommand(
                                name=cmd_name,
                                desc=cmd_data.get('description', cmd_name),
                                mode=mode,
                                pid=pid,
                                bytes=cmd_data.get('bytes', 0),
                                decoder=None  # We'll handle decoding separately
                            )
                            self.custom_commands[cmd_name] = cmd
        
        logger.info("Initialized tractor OBD-II interface")
    
    def connect(self):
        """
        Connect to the OBD-II interface.
        
        Returns:
            bool: Success status
        """
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
                
                # Register custom commands
                for cmd_name, cmd in self.custom_commands.items():
                    self.connection.supported_commands.add(cmd)
                    logger.info(f"Registered custom command: {cmd_name}")
                
                return True
            else:
                logger.error("Failed to connect to OBD-II interface")
                return False
        except Exception as e:
            logger.error(f"Error connecting to OBD-II interface: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """
        Disconnect from the OBD-II interface.
        """
        if self.monitoring:
            self.stop_monitoring.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
                
        if self.connection:
            self.connection.close()
            self.connected = False
            logger.info("Disconnected from OBD-II interface")
    
    def query(self, command):
        """
        Query the OBD-II interface.
        
        Args:
            command (str or obd.Command): Command to query
            
        Returns:
            obd.Response: Response from the OBD-II interface
        """
        if not self.connected or not self.connection:
            logger.error("Cannot query, not connected to OBD-II interface")
            return None
        
        try:
            # Handle command by name (string)
            if isinstance(command, str):
                # Check if it's a custom command
                if command in self.custom_commands:
                    cmd = self.custom_commands[command]
                else:
                    # Try to find it in standard commands
                    try:
                        cmd = obd.commands[command]
                    except KeyError:
                        logger.error(f"Unknown command: {command}")
                        return None
            else:
                cmd = command
                
            response = self.connection.query(cmd)
            logger.debug(f"Query: {cmd}, Response: {response}")
            
            # Store in data buffer
            if not response.is_null():
                self.data_buffer[cmd.name] = {
                    'timestamp': time.time(),
                    'value': response.value,
                    'raw_response': response
                }
                
            return response
        except Exception as e:
            logger.error(f"Error querying OBD-II interface: {e}")
            return None
    
    @property
    def monitoring(self):
        """
        Check if monitoring is active.
        
        Returns:
            bool: True if monitoring thread is active
        """
        return self.monitor_thread is not None and self.monitor_thread.is_alive()
    
    def start_monitoring(self, commands=None, interval=1.0):
        """
        Start monitoring OBD-II commands.
        
        Args:
            commands (list, optional): List of commands to monitor (defaults to COMMON_COMMANDS)
            interval (float): Polling interval in seconds
            
        Returns:
            bool: Success status
        """
        if not self.connected or not self.connection:
            logger.error("Cannot start monitoring, not connected to OBD-II interface")
            return False
            
        if self.monitoring:
            logger.warning("Monitoring already active")
            return True
        
        if commands is None:
            # Filter to only include supported commands
            commands = [cmd for cmd in self.COMMON_COMMANDS if cmd in self.connection.supported_commands]
            
            # Add supported custom commands
            for cmd_name, cmd in self.custom_commands.items():
                if cmd in self.connection.supported_commands:
                    commands.append(cmd)
        
        self.stop_monitoring.clear()
        self.monitor_thread = Thread(
            target=self._monitor_loop,
            args=(commands, interval),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started OBD-II monitoring with {len(commands)} commands")
        return True
    
    def _monitor_loop(self, commands, interval):
        """
        Internal method for the monitoring thread.
        
        Args:
            commands (list): List of commands to monitor
            interval (float): Polling interval in seconds
        """
        while not self.stop_monitoring.is_set():
            for cmd in commands:
                if self.stop_monitoring.is_set():
                    break
                    
                try:
                    self.query(cmd)
                except Exception as e:
                    logger.error(f"Error monitoring command {cmd}: {e}")
            
            # Wait for the specified interval
            time.sleep(interval)
    
    def get_data(self, key=None):
        """
        Get current data from the buffer.
        
        Args:
            key (str, optional): Specific data key to retrieve
            
        Returns:
            dict or object: Data for the specified key or all data
        """
        if key is None:
            return self.data_buffer
        
        return self.data_buffer.get(key)
    
    def get_supported_commands(self):
        """
        Get the list of supported commands.
        
        Returns:
            list: List of supported commands
        """
        if not self.connected or not self.connection:
            logger.error("Cannot get supported commands, not connected to OBD-II interface")
            return []
        
        return list(self.connection.supported_commands)
    
    def save_log(self, filepath):
        """
        Save OBD-II data log to a file.
        
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
            
            # Include values that can be serialized
            for key, value in self.data_buffer.items():
                try:
                    # Convert value to a serializable format
                    if hasattr(value['value'], '__dict__'):
                        serialized_value = str(value['value'])
                    else:
                        serialized_value = value['value']
                        
                    log_data['data'][key] = {
                        'timestamp': value['timestamp'],
                        'value': serialized_value
                    }
                except Exception as e:
                    logger.warning(f"Could not serialize value for {key}: {e}")
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            logger.info(f"Saved OBD-II log to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save OBD-II log: {e}")
            return False
