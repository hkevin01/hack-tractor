#!/usr/bin/env python3
"""
Hack Tractor - Enhanced GUI Application for Laptop-to-Tractor Connection

This enhanced GUI provides a professional interface for connecting a laptop
directly to tractor systems via CAN bus, OBD-II, or other communication protocols.
Designed for educational demonstration and hackathon purposes.
"""

import json
import logging
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

# Enhanced imports for tractor connection
import serial
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Import core modules
try:
    from src.hack_tractor.core import (
        EQUIPMENT_TYPES,
        SAFETY_CHECKS_ENABLED,
        Config,
        get_config,
        setup_logging,
    )
    from src.hack_tractor.core.exceptions import EquipmentError, SafetyError
except ImportError:
    # Fallback for development
    print("Warning: Core modules not found, running in development mode")


@dataclass
class TractorConnectionInfo:
    """Information about tractor connection."""
    connection_type: str = "unknown"
    interface: str = "none"
    port: str = ""
    baudrate: int = 0
    status: str = "disconnected"
    manufacturer: str = "unknown"
    model: str = "unknown"
    year: str = "unknown"
    engine_hours: float = 0.0
    last_communication: Optional[datetime] = None


class TractorInterface:
    """Enhanced interface for laptop-to-tractor communication."""
    
    def __init__(self, connection_type: str = "simulation"):
        self.connection_type = connection_type
        self.connected = False
        self.connection_info = TractorConnectionInfo()
        self.data_buffer = {}
        self.last_update = time.time()
        self.communication_thread = None
        self.stop_event = threading.Event()
        
        # Safety settings
        self.emergency_stop_active = False
        self.safe_mode = True
        
    def scan_for_tractors(self) -> List[Dict[str, Any]]:
        """Scan for available tractor connections."""
        found_devices = []
        
        # Scan for CAN interfaces
        try:
            # Check for SocketCAN interfaces on Linux
            if sys.platform.startswith('linux'):
                result = subprocess.run(['ip', 'link', 'show'], 
                                      capture_output=True, text=True)
                if 'can' in result.stdout:
                    found_devices.append({
                        'type': 'CAN',
                        'interface': 'SocketCAN',
                        'port': 'can0',
                        'description': 'Linux SocketCAN Interface'
                    })
        except Exception:
            pass
            
        # Scan for serial ports (OBD-II adapters)
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if any(keyword in port.description.lower() 
                      for keyword in ['obd', 'elm', 'adapter', 'diagnostic']):
                    found_devices.append({
                        'type': 'OBD-II',
                        'interface': 'Serial',
                        'port': port.device,
                        'description': port.description
                    })
        except ImportError:
            pass
            
        # Add simulation option for demo
        found_devices.append({
            'type': 'Simulation',
            'interface': 'Virtual',
            'port': 'virtual',
            'description': 'Educational Simulation Mode'
        })
        
        return found_devices
    
    def connect(self, device_info: Dict[str, Any]) -> bool:
        """Connect to a specific tractor interface."""
        try:
            self.connection_info.connection_type = device_info['type']
            self.connection_info.interface = device_info['interface']
            self.connection_info.port = device_info['port']
            
            if device_info['type'] == 'Simulation':
                return self._connect_simulation()
            elif device_info['type'] == 'CAN':
                return self._connect_can(device_info)
            elif device_info['type'] == 'OBD-II':
                return self._connect_obd(device_info)
            else:
                raise EquipmentError("Unsupported connection type")
                
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False
    
    def _connect_simulation(self) -> bool:
        """Connect to simulation mode."""
        self.connected = True
        self.connection_info.status = "connected"
        self.connection_info.manufacturer = "SimuTractor"
        self.connection_info.model = "EduDemo 2025"
        self.connection_info.year = "2025"
        self.connection_info.last_communication = datetime.now()
        
        # Start simulation thread
        self.communication_thread = threading.Thread(
            target=self._simulation_loop,
            daemon=True
        )
        self.communication_thread.start()
        
        logging.info("Connected to simulation mode")
        return True
    
    def _connect_can(self, device_info: Dict[str, Any]) -> bool:
        """Connect to CAN bus interface."""
        try:
            # This would implement actual CAN connection
            # For demo, we'll simulate
            self.connected = True
            self.connection_info.status = "connected"
            self.connection_info.baudrate = 250000
            logging.info(f"Connected to CAN interface: {device_info['port']}")
            return True
        except Exception as e:
            logging.error(f"CAN connection failed: {e}")
            return False
    
    def _connect_obd(self, device_info: Dict[str, Any]) -> bool:
        """Connect to OBD-II interface."""
        try:
            # This would implement actual OBD connection
            # For demo, we'll simulate
            self.connected = True
            self.connection_info.status = "connected"
            self.connection_info.baudrate = 38400
            logging.info(f"Connected to OBD interface: {device_info['port']}")
            return True
        except Exception as e:
            logging.error(f"OBD connection failed: {e}")
            return False
    
    def _simulation_loop(self):
        """Main loop for simulation data generation."""
        while not self.stop_event.is_set() and self.connected:
            # Generate realistic tractor data
            current_time = time.time()
            
            self.data_buffer = {
                'engine_rpm': 1500 + np.sin(current_time * 0.1) * 200,
                'engine_temp': 85 + np.random.normal(0, 2),
                'fuel_level': max(0, 75 - (current_time - self.last_update) * 0.01),
                'vehicle_speed': max(0, 15 + np.sin(current_time * 0.05) * 5),
                'hydraulic_pressure': 2000 + np.random.normal(0, 50),
                'pto_speed': 540 + np.random.normal(0, 10),
                'engine_load': 25 + np.sin(current_time * 0.08) * 15,
                'coolant_temp': 82 + np.random.normal(0, 1),
                'transmission_temp': 75 + np.random.normal(0, 3),
                'brake_pressure': 0 if np.random.random() > 0.1 else 50,
                'steering_angle': np.sin(current_time * 0.02) * 30,
                'latitude': 40.7128 + np.random.normal(0, 0.0001),
                'longitude': -74.0060 + np.random.normal(0, 0.0001),
                'timestamp': datetime.now().isoformat()
            }
            
            self.connection_info.last_communication = datetime.now()
            time.sleep(0.1)  # Update at 10Hz
    
    def disconnect(self):
        """Disconnect from tractor."""
        self.stop_event.set()
        self.connected = False
        self.connection_info.status = "disconnected"
        if self.communication_thread:
            self.communication_thread.join(timeout=1.0)
        logging.info("Disconnected from tractor")
    
    def get_data(self, parameter: str = None):
        """Get current tractor data."""
        if parameter:
            return self.data_buffer.get(parameter, 0)
        return self.data_buffer.copy()
    
    def send_command(self, command: str, value: Any = None) -> bool:
        """Send command to tractor (with safety checks)."""
        if not self.connected:
            raise EquipmentError("Not connected to tractor")
            
        if self.emergency_stop_active:
            raise SafetyError("Emergency stop active - cannot send commands")
            
        # Safety validation
        if command in ['emergency_stop', 'engine_shutdown']:
            self.emergency_stop_active = True
            logging.warning(f"Emergency command executed: {command}")
            return True
            
        # For simulation, just log the command
        logging.info(f"Command sent: {command} = {value}")
        return True


class EnhancedTractorGUI:
    """Enhanced GUI for laptop-to-tractor connection."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Hack Tractor - Laptop to Tractor Interface")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Application state
        self.tractor_interface = TractorInterface()
        self.connection_info = TractorConnectionInfo()
        self.data_queue = queue.Queue()
        self.update_interval = 100  # ms
        
        # Data storage for graphs
        self.historical_data = {param: [] for param in [
            'engine_rpm', 'engine_temp', 'fuel_level', 'vehicle_speed'
        ]}
        self.time_data = []
        
        # Setup logging
        self.setup_logging()
        
        # Create GUI
        self.create_styles()
        self.create_main_interface()
        
        # Start update loop
        self.root.after(self.update_interval, self.update_display)
        
        logging.info("Enhanced Tractor GUI initialized")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('tractor_interface.log')
            ]
        )
    
    def create_styles(self):
        """Create custom styles for the interface."""
        style = ttk.Style()
        
        # Configure styles for status indicators
        style.configure("Connected.TLabel", foreground="green", font=("Arial", 10, "bold"))
        style.configure("Disconnected.TLabel", foreground="red", font=("Arial", 10, "bold"))
        style.configure("Warning.TLabel", foreground="orange", font=("Arial", 10, "bold"))
        style.configure("Emergency.TLabel", foreground="red", background="yellow", 
                       font=("Arial", 12, "bold"))
    
    def create_main_interface(self):
        """Create the main interface layout."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top toolbar
        self.create_toolbar(main_frame)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left panel - Connection and Control
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.create_connection_panel(left_panel)
        self.create_control_panel(left_panel)
        
        # Right panel - Dashboard and Data
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_dashboard_panel(right_panel)
        
        # Bottom status bar
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """Create the top toolbar."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Emergency stop button (prominent)
        self.emergency_btn = ttk.Button(
            toolbar, 
            text="🛑 EMERGENCY STOP", 
            command=self.emergency_stop,
            style="Emergency.TLabel"
        )
        self.emergency_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Connection buttons
        self.scan_btn = ttk.Button(toolbar, text="🔍 Scan for Tractors", 
                                  command=self.scan_for_tractors)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.connect_btn = ttk.Button(toolbar, text="🔗 Connect", 
                                     command=self.connect_to_tractor)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(toolbar, text="🔌 Disconnect", 
                                        command=self.disconnect_from_tractor,
                                        state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Mode selector
        ttk.Label(toolbar, text="Mode:").pack(side=tk.LEFT, padx=(0, 5))
        self.mode_var = tk.StringVar(value="Safe")
        mode_combo = ttk.Combobox(toolbar, textvariable=self.mode_var,
                                 values=["Safe", "Educational", "Advanced"],
                                 state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=(0, 20))
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)
    
    def create_connection_panel(self, parent):
        """Create the connection configuration panel."""
        conn_frame = ttk.LabelFrame(parent, text="🚜 Tractor Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Available devices listbox
        ttk.Label(conn_frame, text="Available Devices:").pack(anchor=tk.W)
        
        devices_frame = ttk.Frame(conn_frame)
        devices_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.devices_listbox = tk.Listbox(devices_frame, height=6)
        self.devices_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        devices_scroll = ttk.Scrollbar(devices_frame, orient=tk.VERTICAL,
                                      command=self.devices_listbox.yview)
        devices_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.devices_listbox.config(yscrollcommand=devices_scroll.set)
        
        # Connection info
        info_frame = ttk.LabelFrame(conn_frame, text="Connection Info")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Connection details
        labels = ["Type:", "Interface:", "Port:", "Status:", "Manufacturer:", "Model:"]
        self.info_labels = {}
        
        for i, label in enumerate(labels):
            ttk.Label(info_grid, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            self.info_labels[label.rstrip(':')] = ttk.Label(info_grid, text="Unknown")
            self.info_labels[label.rstrip(':')].grid(row=i, column=1, sticky=tk.W, 
                                                    padx=(10, 0), pady=2)
    
    def create_control_panel(self, parent):
        """Create the tractor control panel."""
        control_frame = ttk.LabelFrame(parent, text="🎛️ Equipment Control", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Quick commands
        ttk.Label(control_frame, text="Quick Commands:").pack(anchor=tk.W)
        
        cmd_frame = ttk.Frame(control_frame)
        cmd_frame.pack(fill=tk.X, pady=(5, 0))
        
        commands = [
            ("Engine On", "engine_start"),
            ("Engine Off", "engine_stop"),
            ("PTO On", "pto_start"),
            ("PTO Off", "pto_stop"),
            ("Hydraulics", "hydraulics_toggle"),
            ("Lights", "lights_toggle")
        ]
        
        for i, (text, cmd) in enumerate(commands):
            btn = ttk.Button(cmd_frame, text=text, width=12,
                           command=lambda c=cmd: self.send_command(c))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky=tk.W)
    
    def create_dashboard_panel(self, parent):
        """Create the main dashboard panel."""
        # Create notebook for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Live Data tab
        live_frame = ttk.Frame(notebook)
        notebook.add(live_frame, text="📊 Live Data")
        self.create_live_data_tab(live_frame)
        
        # Graphs tab
        graphs_frame = ttk.Frame(notebook)
        notebook.add(graphs_frame, text="📈 Graphs")
        self.create_graphs_tab(graphs_frame)
        
        # Diagnostics tab
        diag_frame = ttk.Frame(notebook)
        notebook.add(diag_frame, text="🔧 Diagnostics")
        self.create_diagnostics_tab(diag_frame)
    
    def create_live_data_tab(self, parent):
        """Create the live data display tab."""
        # Main layout
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Engine parameters
        engine_frame = ttk.LabelFrame(main_frame, text="🔥 Engine Parameters")
        engine_frame.pack(fill=tk.X, pady=(0, 10))
        
        engine_grid = ttk.Frame(engine_frame, padding="10")
        engine_grid.pack(fill=tk.X)
        
        # Create value displays for engine parameters
        engine_params = [
            ("RPM", "engine_rpm", "rpm"),
            ("Temperature", "engine_temp", "°C"),
            ("Load", "engine_load", "%"),
            ("Hours", "engine_hours", "hrs")
        ]
        
        self.engine_labels = {}
        for i, (name, key, unit) in enumerate(engine_params):
            ttk.Label(engine_grid, text=f"{name}:").grid(row=i//2, column=(i%2)*2, 
                                                        sticky=tk.W, padx=5, pady=5)
            label = ttk.Label(engine_grid, text=f"0 {unit}", font=("Arial", 12, "bold"))
            label.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=5)
            self.engine_labels[key] = label
        
        # Vehicle parameters
        vehicle_frame = ttk.LabelFrame(main_frame, text="🚗 Vehicle Parameters")
        vehicle_frame.pack(fill=tk.X, pady=(0, 10))
        
        vehicle_grid = ttk.Frame(vehicle_frame, padding="10")
        vehicle_grid.pack(fill=tk.X)
        
        vehicle_params = [
            ("Speed", "vehicle_speed", "km/h"),
            ("Fuel Level", "fuel_level", "%"),
            ("Hydraulic Pressure", "hydraulic_pressure", "psi"),
            ("PTO Speed", "pto_speed", "rpm")
        ]
        
        self.vehicle_labels = {}
        for i, (name, key, unit) in enumerate(vehicle_params):
            ttk.Label(vehicle_grid, text=f"{name}:").grid(row=i//2, column=(i%2)*2, 
                                                         sticky=tk.W, padx=5, pady=5)
            label = ttk.Label(vehicle_grid, text=f"0 {unit}", font=("Arial", 12, "bold"))
            label.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=5)
            self.vehicle_labels[key] = label
        
        # GPS and location
        gps_frame = ttk.LabelFrame(main_frame, text="🗺️ GPS Location")
        gps_frame.pack(fill=tk.X)
        
        gps_grid = ttk.Frame(gps_frame, padding="10")
        gps_grid.pack(fill=tk.X)
        
        ttk.Label(gps_grid, text="Latitude:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.lat_label = ttk.Label(gps_grid, text="0.000000", font=("Arial", 10, "bold"))
        self.lat_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(gps_grid, text="Longitude:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.lon_label = ttk.Label(gps_grid, text="0.000000", font=("Arial", 10, "bold"))
        self.lon_label.grid(row=0, column=3, sticky=tk.W, padx=5)
    
    def create_graphs_tab(self, parent):
        """Create the graphs tab with real-time plotting."""
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 8), dpi=100)
        
        # Create subplots for different parameters
        self.ax1 = self.fig.add_subplot(221)
        self.ax2 = self.fig.add_subplot(222)
        self.ax3 = self.fig.add_subplot(223)
        self.ax4 = self.fig.add_subplot(224)
        
        # Setup plots
        self.ax1.set_title("Engine RPM")
        self.ax1.set_ylabel("RPM")
        
        self.ax2.set_title("Engine Temperature")
        self.ax2.set_ylabel("°C")
        
        self.ax3.set_title("Vehicle Speed")
        self.ax3.set_ylabel("km/h")
        
        self.ax4.set_title("Fuel Level")
        self.ax4.set_ylabel("%")
        
        self.fig.tight_layout()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initialize plot data
        self.max_points = 100
        self.plot_data = {
            'time': [],
            'engine_rpm': [],
            'engine_temp': [],
            'vehicle_speed': [],
            'fuel_level': []
        }
    
    def create_diagnostics_tab(self, parent):
        """Create the diagnostics tab."""
        diag_frame = ttk.Frame(parent, padding="10")
        diag_frame.pack(fill=tk.BOTH, expand=True)
        
        # Diagnostic codes area
        codes_frame = ttk.LabelFrame(diag_frame, text="🚨 Diagnostic Codes")
        codes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for diagnostic codes
        self.diag_tree = ttk.Treeview(codes_frame, columns=("Code", "Description", "Status"))
        self.diag_tree.heading("#0", text="Type")
        self.diag_tree.heading("Code", text="Code")
        self.diag_tree.heading("Description", text="Description")
        self.diag_tree.heading("Status", text="Status")
        
        self.diag_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add sample diagnostic codes
        sample_codes = [
            ("Engine", "P0101", "Mass Air Flow Sensor", "Active"),
            ("Transmission", "P0700", "Transmission Control System", "Pending"),
            ("Hydraulics", "H0001", "Hydraulic Pressure Low", "Cleared"),
        ]
        
        for type_code, code, desc, status in sample_codes:
            self.diag_tree.insert("", "end", text=type_code, values=(code, desc, status))
        
        # Control buttons
        btn_frame = ttk.Frame(diag_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="🔄 Refresh Codes", 
                  command=self.refresh_diagnostic_codes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🗑️ Clear Codes", 
                  command=self.clear_diagnostic_codes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="💾 Export Log", 
                  command=self.export_diagnostic_log).pack(side=tk.LEFT)
    
    def create_status_bar(self, parent):
        """Create the bottom status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready - No tractor connected")
        self.status_label.pack(side=tk.LEFT)
        
        # Connection indicator
        self.connection_indicator = ttk.Label(status_frame, text="●", 
                                            style="Disconnected.TLabel")
        self.connection_indicator.pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Label(status_frame, text="Connection:").pack(side=tk.RIGHT)
    
    # Event handlers and methods
    
    def scan_for_tractors(self):
        """Scan for available tractor connections."""
        self.status_label.config(text="Scanning for tractors...")
        self.root.update()
        
        # Clear existing items
        self.devices_listbox.delete(0, tk.END)
        
        try:
            devices = self.tractor_interface.scan_for_tractors()
            
            for device in devices:
                display_text = f"{device['type']} - {device['description']} ({device['port']})"
                self.devices_listbox.insert(tk.END, display_text)
            
            if devices:
                self.status_label.config(text=f"Found {len(devices)} available interfaces")
                self.devices_listbox.selection_set(0)  # Select first item
            else:
                self.status_label.config(text="No tractor interfaces found")
                
        except Exception as e:
            messagebox.showerror("Scan Error", f"Failed to scan for devices: {e}")
            self.status_label.config(text="Scan failed")
    
    def connect_to_tractor(self):
        """Connect to the selected tractor."""
        selection = self.devices_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tractor interface first")
            return
        
        # Get device info (simplified for demo)
        device_types = ["Simulation", "CAN", "OBD-II"]
        device_info = {
            'type': device_types[min(selection[0], len(device_types)-1)],
            'interface': 'Demo',
            'port': 'demo_port'
        }
        
        self.status_label.config(text="Connecting to tractor...")
        self.root.update()
        
        try:
            if self.tractor_interface.connect(device_info):
                self.connected = True
                self.update_connection_info()
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.connection_indicator.config(style="Connected.TLabel")
                self.status_label.config(text="Connected to tractor")
                messagebox.showinfo("Connected", "Successfully connected to tractor!")
            else:
                messagebox.showerror("Connection Error", "Failed to connect to tractor")
                self.status_label.config(text="Connection failed")
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.status_label.config(text="Connection error")
    
    def disconnect_from_tractor(self):
        """Disconnect from the tractor."""
        try:
            self.tractor_interface.disconnect()
            self.connected = False
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.connection_indicator.config(style="Disconnected.TLabel")
            self.status_label.config(text="Disconnected from tractor")
            
            # Reset connection info
            for label in self.info_labels.values():
                label.config(text="Unknown")
                
            messagebox.showinfo("Disconnected", "Disconnected from tractor")
            
        except Exception as e:
            messagebox.showerror("Disconnect Error", f"Failed to disconnect: {e}")
    
    def emergency_stop(self):
        """Execute emergency stop procedure."""
        result = messagebox.askyesno("Emergency Stop", 
                                   "This will immediately stop all tractor operations!\n\n"
                                   "Are you sure you want to continue?",
                                   icon="warning")
        if result:
            try:
                self.tractor_interface.send_command("emergency_stop")
                self.status_label.config(text="EMERGENCY STOP ACTIVATED")
                messagebox.showwarning("Emergency Stop", "Emergency stop has been activated!")
            except Exception as e:
                messagebox.showerror("Emergency Stop Error", f"Failed to execute emergency stop: {e}")
    
    def send_command(self, command: str):
        """Send a command to the tractor."""
        if not hasattr(self, 'connected') or not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to a tractor first")
            return
        
        try:
            if self.tractor_interface.send_command(command):
                self.status_label.config(text=f"Command sent: {command}")
            else:
                self.status_label.config(text=f"Failed to send command: {command}")
        except SafetyError as e:
            messagebox.showerror("Safety Error", str(e))
        except Exception as e:
            messagebox.showerror("Command Error", f"Failed to send command: {e}")
    
    def on_mode_change(self, event):
        """Handle mode change."""
        mode = self.mode_var.get()
        self.status_label.config(text=f"Mode changed to: {mode}")
        
        if mode == "Safe":
            self.tractor_interface.safe_mode = True
        else:
            self.tractor_interface.safe_mode = False
    
    def update_connection_info(self):
        """Update the connection information display."""
        info = self.tractor_interface.connection_info
        
        self.info_labels["Type"].config(text=info.connection_type)
        self.info_labels["Interface"].config(text=info.interface)
        self.info_labels["Port"].config(text=info.port)
        self.info_labels["Status"].config(text=info.status)
        self.info_labels["Manufacturer"].config(text=info.manufacturer)
        self.info_labels["Model"].config(text=info.model)
    
    def update_display(self):
        """Update the live data display."""
        if hasattr(self, 'connected') and self.connected:
            # Get current data
            data = self.tractor_interface.get_data()
            
            if data:
                # Update engine parameters
                for key, label in self.engine_labels.items():
                    if key in data:
                        value = data[key]
                        if key == "engine_rpm":
                            label.config(text=f"{value:.0f} rpm")
                        elif key == "engine_temp":
                            label.config(text=f"{value:.1f} °C")
                        elif key == "engine_load":
                            label.config(text=f"{value:.1f} %")
                        elif key == "engine_hours":
                            label.config(text=f"{value:.1f} hrs")
                
                # Update vehicle parameters
                for key, label in self.vehicle_labels.items():
                    if key in data:
                        value = data[key]
                        if key == "vehicle_speed":
                            label.config(text=f"{value:.1f} km/h")
                        elif key == "fuel_level":
                            label.config(text=f"{value:.1f} %")
                        elif key == "hydraulic_pressure":
                            label.config(text=f"{value:.0f} psi")
                        elif key == "pto_speed":
                            label.config(text=f"{value:.0f} rpm")
                
                # Update GPS
                if 'latitude' in data and 'longitude' in data:
                    self.lat_label.config(text=f"{data['latitude']:.6f}")
                    self.lon_label.config(text=f"{data['longitude']:.6f}")
                
                # Update graphs
                self.update_graphs(data)
        
        # Schedule next update
        self.root.after(self.update_interval, self.update_display)
    
    def update_graphs(self, data):
        """Update the real-time graphs."""
        current_time = time.time()
        
        # Add new data point
        self.plot_data['time'].append(current_time)
        
        for param in ['engine_rpm', 'engine_temp', 'vehicle_speed', 'fuel_level']:
            value = data.get(param, 0)
            self.plot_data[param].append(value)
        
        # Limit data points
        if len(self.plot_data['time']) > self.max_points:
            for key in self.plot_data:
                self.plot_data[key] = self.plot_data[key][-self.max_points:]
        
        # Update plots if we have enough data
        if len(self.plot_data['time']) > 1:
            try:
                # Clear and redraw plots
                self.ax1.clear()
                self.ax2.clear()
                self.ax3.clear()
                self.ax4.clear()
                
                time_data = self.plot_data['time']
                
                self.ax1.plot(time_data, self.plot_data['engine_rpm'], 'b-')
                self.ax1.set_title("Engine RPM")
                self.ax1.set_ylabel("RPM")
                
                self.ax2.plot(time_data, self.plot_data['engine_temp'], 'r-')
                self.ax2.set_title("Engine Temperature")
                self.ax2.set_ylabel("°C")
                
                self.ax3.plot(time_data, self.plot_data['vehicle_speed'], 'g-')
                self.ax3.set_title("Vehicle Speed")
                self.ax3.set_ylabel("km/h")
                
                self.ax4.plot(time_data, self.plot_data['fuel_level'], 'orange')
                self.ax4.set_title("Fuel Level")
                self.ax4.set_ylabel("%")
                
                self.fig.tight_layout()
                self.canvas.draw()
                
            except Exception as e:
                logging.error(f"Graph update error: {e}")
    
    def refresh_diagnostic_codes(self):
        """Refresh diagnostic codes."""
        self.status_label.config(text="Refreshing diagnostic codes...")
        # In a real implementation, this would query the tractor for current codes
        messagebox.showinfo("Diagnostic Codes", "Diagnostic codes refreshed")
        self.status_label.config(text="Diagnostic codes updated")
    
    def clear_diagnostic_codes(self):
        """Clear diagnostic codes."""
        result = messagebox.askyesno("Clear Codes", 
                                   "This will clear all diagnostic trouble codes.\n\n"
                                   "Are you sure?")
        if result:
            # In a real implementation, this would clear codes on the tractor
            messagebox.showinfo("Codes Cleared", "Diagnostic codes have been cleared")
            self.status_label.config(text="Diagnostic codes cleared")
    
    def export_diagnostic_log(self):
        """Export diagnostic log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Diagnostic Log"
        )
        
        if filename:
            try:
                # Create sample diagnostic data
                diagnostic_data = {
                    "timestamp": datetime.now().isoformat(),
                    "tractor_info": {
                        "manufacturer": self.tractor_interface.connection_info.manufacturer,
                        "model": self.tractor_interface.connection_info.model,
                        "connection_type": self.tractor_interface.connection_info.connection_type
                    },
                    "codes": [
                        {"type": "Engine", "code": "P0101", "description": "Mass Air Flow Sensor", "status": "Active"},
                        {"type": "Transmission", "code": "P0700", "description": "Transmission Control System", "status": "Pending"}
                    ]
                }
                
                with open(filename, 'w') as f:
                    json.dump(diagnostic_data, f, indent=2)
                
                messagebox.showinfo("Export Complete", f"Diagnostic log exported to {filename}")
                self.status_label.config(text="Diagnostic log exported")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export log: {e}")


def main():
    """Main entry point for the enhanced GUI application."""
    root = tk.Tk()
    
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create and run the application
        app = EnhancedTractorGUI(root)
        
        # Handle application shutdown
        def on_closing():
            if hasattr(app, 'tractor_interface'):
                app.tractor_interface.disconnect()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Show educational notice
        messagebox.showinfo(
            "Educational Tool", 
            "Hack Tractor - Educational Tractor Interface\n\n"
            "This is an educational tool for hackathon demonstration.\n"
            "All equipment interfaces are simulated for safety.\n\n"
            "🛡️ Safety First - Educational Use Only 🛡️"
        )
        
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        messagebox.showerror("Application Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()
