"""
Laptop to Tractor Interface

This module provides the main interface for connecting a laptop
to tractor systems via various communication protocols.
Educational and demonstration purposes only.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ....core.constants import (
    EMERGENCY_STOP_TIMEOUT,
    SAFETY_CHECKS_ENABLED,
    SIMULATION_MODE,
)
from ....core.exceptions import CommunicationError, EquipmentError, SafetyError


class ConnectionType(Enum):
    """Types of tractor connections."""
    SIMULATION = "simulation"
    CAN_BUS = "can_bus"
    OBD_II = "obd_ii"
    SERIAL = "serial"
    ETHERNET = "ethernet"
    WIFI = "wifi"


class TractorStatus(Enum):
    """Tractor operational status."""
    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class TractorParameter:
    """Represents a tractor parameter with metadata."""
    name: str
    value: Any
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    description: str = ""


@dataclass
class TractorInfo:
    """Information about connected tractor."""
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    year: str = "Unknown"
    serial_number: str = "Unknown"
    engine_type: str = "Unknown"
    horsepower: Optional[float] = None
    operating_hours: float = 0.0
    last_maintenance: Optional[datetime] = None


class LaptopTractorInterface:
    """
    Main interface for laptop-to-tractor communication.
    
    Provides a unified interface for connecting to various tractor
    communication protocols while maintaining safety and educational focus.
    """
    
    def __init__(self, connection_type: ConnectionType = ConnectionType.SIMULATION):
        """
        Initialize the laptop-tractor interface.
        
        Args:
            connection_type: Type of connection to establish
        """
        self.connection_type = connection_type
        self.logger = logging.getLogger(f"hack_tractor.interface.{connection_type.value}")
        
        # Connection state
        self.status = TractorStatus.DISCONNECTED
        self.connected = False
        self.last_communication = None
        
        # Tractor information
        self.tractor_info = TractorInfo()
        
        # Data storage
        self.parameters: Dict[str, TractorParameter] = {}
        self.parameter_history: Dict[str, List[TractorParameter]] = {}
        self.max_history_length = 1000
        
        # Safety systems
        self.emergency_stop_active = False
        self.safety_checks_enabled = SAFETY_CHECKS_ENABLED
        self.safe_mode = True
        
        # Communication thread
        self.comm_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Callbacks for events
        self.data_callbacks: List[Callable] = []
        self.status_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        self.logger.info(f"Laptop-Tractor Interface initialized for {connection_type.value}")
    
    def scan_for_tractors(self) -> List[Dict[str, Any]]:
        """
        Scan for available tractor connections.
        
        Returns:
            List of available tractor interfaces
        """
        self.logger.info("Scanning for available tractor interfaces...")
        
        available_interfaces = []
        
        # Educational simulation is always available
        available_interfaces.append({
            'type': ConnectionType.SIMULATION,
            'name': 'Educational Simulator',
            'description': 'Safe simulation environment for learning',
            'port': 'virtual',
            'available': True,
            'recommended': True
        })
        
        # Check for CAN interfaces (Linux only)
        try:
            import subprocess
            import sys
            
            if sys.platform.startswith('linux'):
                result = subprocess.run(
                    ['ip', 'link', 'show'], 
                    capture_output=True, 
                    text=True,
                    timeout=5
                )
                if 'can' in result.stdout.lower():
                    available_interfaces.append({
                        'type': ConnectionType.CAN_BUS,
                        'name': 'CAN Bus Interface',
                        'description': 'Direct CAN bus communication',
                        'port': 'can0',
                        'available': True,
                        'recommended': False
                    })
        except Exception as e:
            self.logger.debug(f"CAN interface scan failed: {e}")
        
        # Check for serial ports (OBD-II adapters)
        try:
            import serial.tools.list_ports
            
            ports = serial.tools.list_ports.comports()
            for port in ports:
                description = port.description.lower()
                if any(keyword in description for keyword in [
                    'obd', 'elm', 'adapter', 'diagnostic', 'tractor'
                ]):
                    available_interfaces.append({
                        'type': ConnectionType.OBD_II,
                        'name': f'OBD-II Adapter ({port.device})',
                        'description': port.description,
                        'port': port.device,
                        'available': True,
                        'recommended': True
                    })
        except ImportError:
            self.logger.debug("Serial port scanning not available")
        except Exception as e:
            self.logger.debug(f"Serial port scan failed: {e}")
        
        self.logger.info(f"Found {len(available_interfaces)} available interfaces")
        return available_interfaces
    
    def connect(self, interface_info: Dict[str, Any]) -> bool:
        """
        Connect to a tractor interface.
        
        Args:
            interface_info: Interface information from scan_for_tractors()
            
        Returns:
            True if connection successful
        """
        if self.connected:
            raise EquipmentError("Already connected to a tractor")
        
        self.logger.info(f"Attempting to connect to {interface_info['name']}")
        
        try:
            connection_type = interface_info['type']
            
            if connection_type == ConnectionType.SIMULATION:
                success = self._connect_simulation(interface_info)
            elif connection_type == ConnectionType.CAN_BUS:
                success = self._connect_can_bus(interface_info)
            elif connection_type == ConnectionType.OBD_II:
                success = self._connect_obd_ii(interface_info)
            else:
                raise EquipmentError(f"Unsupported connection type: {connection_type}")
            
            if success:
                self.connected = True
                self.status = TractorStatus.CONNECTED
                self.last_communication = datetime.now()
                self._start_communication_thread()
                self._notify_status_callbacks()
                self.logger.info("Successfully connected to tractor")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.status = TractorStatus.ERROR
            self._notify_status_callbacks()
            raise CommunicationError(f"Failed to connect: {e}")
    
    def _connect_simulation(self, interface_info: Dict[str, Any]) -> bool:
        """Connect to simulation mode."""
        self.connection_type = ConnectionType.SIMULATION
        
        # Set up simulated tractor info
        self.tractor_info = TractorInfo(
            manufacturer="Educational Tractors Inc.",
            model="EduDemo 2025",
            year="2025",
            serial_number="EDU-SIM-001",
            engine_type="Simulated Diesel",
            horsepower=120.0,
            operating_hours=1250.5,
            last_maintenance=datetime(2025, 6, 1)
        )
        
        # Initialize simulated parameters
        self._initialize_simulation_parameters()
        
        return True
    
    def _connect_can_bus(self, interface_info: Dict[str, Any]) -> bool:
        """Connect to CAN bus interface."""
        # This would implement actual CAN bus connection
        # For educational purposes, we simulate the connection
        self.connection_type = ConnectionType.CAN_BUS
        
        self.tractor_info = TractorInfo(
            manufacturer="CAN Tractor Co.",
            model="CAN-Enabled 300",
            year="2023",
            engine_type="Tier 4 Diesel"
        )
        
        self.logger.info("CAN bus connection simulated for educational purposes")
        return True
    
    def _connect_obd_ii(self, interface_info: Dict[str, Any]) -> bool:
        """Connect to OBD-II interface."""
        # This would implement actual OBD-II connection
        # For educational purposes, we simulate the connection
        self.connection_type = ConnectionType.OBD_II
        
        self.tractor_info = TractorInfo(
            manufacturer="OBD Tractors",
            model="OBD-Compatible 250",
            year="2022",
            engine_type="Electronic Diesel"
        )
        
        self.logger.info("OBD-II connection simulated for educational purposes")
        return True
    
    def _initialize_simulation_parameters(self):
        """Initialize parameters for simulation mode."""
        base_time = datetime.now()
        
        # Engine parameters
        self.parameters.update({
            'engine_rpm': TractorParameter(
                name='Engine RPM',
                value=1500.0,
                unit='rpm',
                timestamp=base_time,
                min_value=800.0,
                max_value=2400.0,
                warning_threshold=2200.0,
                critical_threshold=2350.0,
                description='Engine rotational speed'
            ),
            'engine_temp': TractorParameter(
                name='Engine Temperature',
                value=85.0,
                unit='°C',
                timestamp=base_time,
                min_value=60.0,
                max_value=120.0,
                warning_threshold=105.0,
                critical_threshold=115.0,
                description='Engine coolant temperature'
            ),
            'engine_load': TractorParameter(
                name='Engine Load',
                value=25.0,
                unit='%',
                timestamp=base_time,
                min_value=0.0,
                max_value=100.0,
                warning_threshold=90.0,
                critical_threshold=95.0,
                description='Engine load percentage'
            ),
            # Vehicle parameters
            'vehicle_speed': TractorParameter(
                name='Vehicle Speed',
                value=12.0,
                unit='km/h',
                timestamp=base_time,
                min_value=0.0,
                max_value=50.0,
                description='Current vehicle speed'
            ),
            'fuel_level': TractorParameter(
                name='Fuel Level',
                value=75.0,
                unit='%',
                timestamp=base_time,
                min_value=0.0,
                max_value=100.0,
                warning_threshold=20.0,
                critical_threshold=10.0,
                description='Fuel tank level'
            ),
            # Hydraulic system
            'hydraulic_pressure': TractorParameter(
                name='Hydraulic Pressure',
                value=2000.0,
                unit='psi',
                timestamp=base_time,
                min_value=1000.0,
                max_value=3000.0,
                warning_threshold=2800.0,
                critical_threshold=2900.0,
                description='Main hydraulic system pressure'
            ),
            'pto_speed': TractorParameter(
                name='PTO Speed',
                value=540.0,
                unit='rpm',
                timestamp=base_time,
                min_value=0.0,
                max_value=1000.0,
                description='Power Take-Off speed'
            ),
            # Environmental
            'coolant_temp': TractorParameter(
                name='Coolant Temperature',
                value=82.0,
                unit='°C',
                timestamp=base_time,
                min_value=60.0,
                max_value=110.0,
                warning_threshold=100.0,
                critical_threshold=105.0,
                description='Engine coolant temperature'
            ),
            'transmission_temp': TractorParameter(
                name='Transmission Temperature',
                value=75.0,
                unit='°C',
                timestamp=base_time,
                min_value=40.0,
                max_value=120.0,
                warning_threshold=100.0,
                critical_threshold=110.0,
                description='Transmission oil temperature'
            ),
            # GPS coordinates (sample location)
            'latitude': TractorParameter(
                name='Latitude',
                value=40.7128,
                unit='°',
                timestamp=base_time,
                description='GPS latitude coordinate'
            ),
            'longitude': TractorParameter(
                name='Longitude',
                value=-74.0060,
                unit='°',
                timestamp=base_time,
                description='GPS longitude coordinate'
            )
        })
    
    def _start_communication_thread(self):
        """Start the communication thread for continuous data updates."""
        if self.comm_thread and self.comm_thread.is_alive():
            return
        
        self.stop_event.clear()
        self.comm_thread = threading.Thread(
            target=self._communication_loop,
            daemon=True,
            name="TractorComm"
        )
        self.comm_thread.start()
        self.logger.info("Communication thread started")
    
    def _communication_loop(self):
        """Main communication loop for data updates."""
        self.logger.info("Starting communication loop")
        
        while not self.stop_event.is_set() and self.connected:
            try:
                # Update parameter values based on connection type
                if self.connection_type == ConnectionType.SIMULATION:
                    self._update_simulation_data()
                elif self.connection_type == ConnectionType.CAN_BUS:
                    self._update_can_data()
                elif self.connection_type == ConnectionType.OBD_II:
                    self._update_obd_data()
                
                # Update timestamps and check thresholds
                self._process_parameter_updates()
                
                # Store historical data
                self._store_historical_data()
                
                # Notify callbacks
                self._notify_data_callbacks()
                
                # Update last communication time
                self.last_communication = datetime.now()
                
                # Sleep for update interval
                time.sleep(0.1)  # 10Hz update rate
                
            except Exception as e:
                self.logger.error(f"Communication loop error: {e}")
                if not self.stop_event.is_set():
                    time.sleep(1.0)  # Pause before retry
        
        self.logger.info("Communication loop ended")
    
    def _update_simulation_data(self):
        """Update simulated tractor data with realistic patterns."""
        import math
        import random
        
        current_time = time.time()
        
        # Update engine RPM with slight variations
        rpm = self.parameters['engine_rpm']
        base_rpm = 1500 + math.sin(current_time * 0.1) * 200
        rpm.value = max(800, min(2400, base_rpm + random.gauss(0, 25)))
        rpm.timestamp = datetime.now()
        
        # Engine temperature slowly increases with load
        temp = self.parameters['engine_temp']
        load_factor = self.parameters['engine_load'].value / 100.0
        target_temp = 80 + load_factor * 25
        temp.value += (target_temp - temp.value) * 0.05 + random.gauss(0, 0.5)
        temp.value = max(60, min(120, temp.value))
        temp.timestamp = datetime.now()
        
        # Engine load varies with operating conditions
        load = self.parameters['engine_load']
        base_load = 25 + math.sin(current_time * 0.08) * 15
        load.value = max(0, min(100, base_load + random.gauss(0, 5)))
        load.timestamp = datetime.now()
        
        # Vehicle speed
        speed = self.parameters['vehicle_speed']
        speed.value = max(0, min(50, 12 + math.sin(current_time * 0.05) * 8 + random.gauss(0, 2)))
        speed.timestamp = datetime.now()
        
        # Fuel level slowly decreases
        fuel = self.parameters['fuel_level']
        fuel.value = max(0, fuel.value - random.uniform(0, 0.01))
        fuel.timestamp = datetime.now()
        
        # Hydraulic pressure fluctuates
        pressure = self.parameters['hydraulic_pressure']
        pressure.value = max(1000, min(3000, 2000 + random.gauss(0, 50)))
        pressure.timestamp = datetime.now()
        
        # PTO speed
        pto = self.parameters['pto_speed']
        if random.random() > 0.8:  # PTO occasionally active
            pto.value = 540 + random.gauss(0, 10)
        else:
            pto.value = 0
        pto.timestamp = datetime.now()
    
    def _update_can_data(self):
        """Update data from CAN bus (simulated for educational purposes)."""
        # In a real implementation, this would read actual CAN messages
        self._update_simulation_data()  # Use simulation for demo
    
    def _update_obd_data(self):
        """Update data from OBD-II interface (simulated for educational purposes)."""
        # In a real implementation, this would query OBD-II PIDs
        self._update_simulation_data()  # Use simulation for demo
    
    def _process_parameter_updates(self):
        """Process parameter updates and check for threshold violations."""
        for param_name, param in self.parameters.items():
            # Check warning thresholds
            if param.warning_threshold is not None:
                if param.value >= param.warning_threshold:
                    self._trigger_alert(f"Warning: {param.name} is {param.value} {param.unit}")
            
            # Check critical thresholds
            if param.critical_threshold is not None:
                if param.value >= param.critical_threshold:
                    self._trigger_alert(f"CRITICAL: {param.name} is {param.value} {param.unit}")
    
    def _store_historical_data(self):
        """Store current parameter values in historical data."""
        for param_name, param in self.parameters.items():
            if param_name not in self.parameter_history:
                self.parameter_history[param_name] = []
            
            # Add current value to history
            self.parameter_history[param_name].append(param)
            
            # Limit history length
            if len(self.parameter_history[param_name]) > self.max_history_length:
                self.parameter_history[param_name] = self.parameter_history[param_name][-self.max_history_length:]
    
    def _trigger_alert(self, message: str):
        """Trigger an alert for abnormal conditions."""
        self.logger.warning(f"TRACTOR ALERT: {message}")
        
        # Notify alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def _notify_data_callbacks(self):
        """Notify registered data callbacks of new data."""
        for callback in self.data_callbacks:
            try:
                callback(self.parameters.copy())
            except Exception as e:
                self.logger.error(f"Data callback error: {e}")
    
    def _notify_status_callbacks(self):
        """Notify registered status callbacks of status changes."""
        for callback in self.status_callbacks:
            try:
                callback(self.status)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    def disconnect(self):
        """Disconnect from the tractor."""
        self.logger.info("Disconnecting from tractor")
        
        # Stop communication thread
        self.stop_event.set()
        if self.comm_thread and self.comm_thread.is_alive():
            self.comm_thread.join(timeout=2.0)
        
        # Update status
        self.connected = False
        self.status = TractorStatus.DISCONNECTED
        self.last_communication = None
        
        # Clear emergency stop if active
        self.emergency_stop_active = False
        
        # Notify callbacks
        self._notify_status_callbacks()
        
        self.logger.info("Disconnected from tractor")
    
    def send_command(self, command: str, value: Any = None) -> bool:
        """
        Send a command to the tractor.
        
        Args:
            command: Command to send
            value: Optional command value
            
        Returns:
            True if command was sent successfully
        """
        if not self.connected:
            raise EquipmentError("Not connected to tractor")
        
        if self.emergency_stop_active:
            raise SafetyError("Emergency stop active - cannot send commands")
        
        # Safety checks
        if self.safety_checks_enabled:
            if not self._validate_command(command, value):
                raise SafetyError(f"Command failed safety validation: {command}")
        
        self.logger.info(f"Sending command: {command} = {value}")
        
        # Handle special commands
        if command == "emergency_stop":
            self.emergency_stop_active = True
            self.status = TractorStatus.EMERGENCY_STOP
            self._notify_status_callbacks()
            self.logger.warning("EMERGENCY STOP ACTIVATED")
            return True
        
        # For educational purposes, log the command
        # In a real implementation, this would send actual commands to the tractor
        return True
    
    def _validate_command(self, command: str, value: Any) -> bool:
        """
        Validate command for safety.
        
        Args:
            command: Command to validate
            value: Command value to validate
            
        Returns:
            True if command is safe
        """
        # Always allow emergency stop
        if command == "emergency_stop":
            return True
        
        # Check if in safe mode
        if self.safe_mode:
            safe_commands = [
                "get_status", "get_data", "set_lights", 
                "horn", "start_engine", "stop_engine"
            ]
            if command not in safe_commands:
                self.logger.warning(f"Command {command} not allowed in safe mode")
                return False
        
        # Validate value ranges for specific commands
        if command == "set_engine_rpm" and value is not None:
            if not (800 <= value <= 2400):
                self.logger.warning(f"Engine RPM {value} out of safe range")
                return False
        
        return True
    
    def get_parameter(self, name: str) -> Optional[TractorParameter]:
        """
        Get a specific parameter value.
        
        Args:
            name: Parameter name
            
        Returns:
            TractorParameter object or None if not found
        """
        return self.parameters.get(name)
    
    def get_all_parameters(self) -> Dict[str, TractorParameter]:
        """
        Get all current parameter values.
        
        Returns:
            Dictionary of all parameters
        """
        return self.parameters.copy()
    
    def get_parameter_history(self, name: str, count: int = 100) -> List[TractorParameter]:
        """
        Get historical values for a parameter.
        
        Args:
            name: Parameter name
            count: Number of historical values to return
            
        Returns:
            List of historical TractorParameter objects
        """
        if name not in self.parameter_history:
            return []
        
        return self.parameter_history[name][-count:]
    
    def register_data_callback(self, callback: Callable):
        """Register a callback for data updates."""
        self.data_callbacks.append(callback)
    
    def register_status_callback(self, callback: Callable):
        """Register a callback for status updates."""
        self.status_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for alerts."""
        self.alert_callbacks.append(callback)
    
    def clear_emergency_stop(self):
        """Clear emergency stop condition (requires manual confirmation)."""
        if self.emergency_stop_active:
            self.emergency_stop_active = False
            if self.connected:
                self.status = TractorStatus.CONNECTED
            else:
                self.status = TractorStatus.DISCONNECTED
            self._notify_status_callbacks()
            self.logger.info("Emergency stop cleared")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.
        
        Returns:
            Dictionary with connection information
        """
        return {
            'connection_type': self.connection_type.value,
            'status': self.status.value,
            'connected': self.connected,
            'last_communication': self.last_communication,
            'emergency_stop_active': self.emergency_stop_active,
            'safe_mode': self.safe_mode,
            'tractor_info': {
                'manufacturer': self.tractor_info.manufacturer,
                'model': self.tractor_info.model,
                'year': self.tractor_info.year,
                'serial_number': self.tractor_info.serial_number,
                'engine_type': self.tractor_info.engine_type,
                'horsepower': self.tractor_info.horsepower,
                'operating_hours': self.tractor_info.operating_hours
            }
        }
