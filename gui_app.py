#!/usr/bin/env python3
"""
Hack Tractor - GUI Application

This script provides a graphical user interface for the Hack Tractor application.
It integrates with main.py to control and monitor farm equipment.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import time
from datetime import datetime
import queue
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random  # For simulation data

# Import from main.py
from main import (
    load_config, initialize_equipment_interfaces, initialize_ai_models,
    start_backend_server, cleanup, logger, PROJECT_ROOT, DATA_DIR, LOGS_DIR
)

# Configure GUI-specific logger
gui_logger = logging.getLogger("hack_tractor.gui")

# Queue for thread-safe communication between backend and GUI
data_queue = queue.Queue()

class TextHandler(logging.Handler):
    """Handler to redirect logging output to a tkinter Text widget"""
    
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        
    def emit(self, record):
        msg = self.format(record)
        
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n', record.levelname)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
            
        # Schedule the append operation on the main thread
        self.text_widget.after(0, append)

class SimulationInterface:
    """Simulated equipment interface for demonstration purposes."""
    
    def __init__(self, interface_type="can"):
        self.interface_type = interface_type
        self.connected = True
        self.data = {}
        self.last_update = time.time()
        
        # Initialize with sample data
        if interface_type == "can":
            self.data = {
                "ENGINE_RPM": {"value": 1500, "timestamp": time.time()},
                "ENGINE_TEMP": {"value": 85, "timestamp": time.time()},
                "FUEL_LEVEL": {"value": 75, "timestamp": time.time()},
                "VEHICLE_SPEED": {"value": 0, "timestamp": time.time()},
                "HYDRAULIC_PRESSURE": {"value": 2000, "timestamp": time.time()},
                "PTO_SPEED": {"value": 0, "timestamp": time.time()}
            }
        elif interface_type == "obd":
            self.data = {
                "RPM": {"value": 1500, "timestamp": time.time()},
                "SPEED": {"value": 0, "timestamp": time.time()},
                "COOLANT_TEMP": {"value": 85, "timestamp": time.time()},
                "ENGINE_LOAD": {"value": 20, "timestamp": time.time()},
                "THROTTLE_POS": {"value": 15, "timestamp": time.time()}
            }
    
    def get_data(self, key=None):
        """Get simulated data."""
        # Update simulated values
        current_time = time.time()
        if current_time - self.last_update > 1.0:
            self._update_simulation_data()
            self.last_update = current_time
            
        if key is not None:
            return self.data.get(key)
        return self.data
    
    def _update_simulation_data(self):
        """Update simulation data with realistic changes."""
        for key in self.data:
            value = self.data[key]["value"]
            
            # Apply different patterns based on parameter
            if "RPM" in key:
                # RPM fluctuates slightly
                self.data[key]["value"] = max(800, min(2500, value + random.uniform(-50, 50)))
            elif "TEMP" in key:
                # Temperature slowly increases when running
                self.data[key]["value"] = max(60, min(110, value + random.uniform(-0.5, 1.0)))
            elif "FUEL" in key:
                # Fuel slowly decreases
                self.data[key]["value"] = max(0, value - random.uniform(0, 0.1))
            elif "SPEED" in key:
                # Speed changes more dramatically
                self.data[key]["value"] = max(0, min(40, value + random.uniform(-2, 2)))
            elif "PRESSURE" in key:
                # Pressure fluctuates
                self.data[key]["value"] = max(1000, min(3000, value + random.uniform(-100, 100)))
            elif "LOAD" in key or "POS" in key:
                # Load and position fluctuate
                self.data[key]["value"] = max(0, min(100, value + random.uniform(-5, 5)))
            
            # Update timestamp
            self.data[key]["timestamp"] = time.time()
    
    def disconnect(self):
        """Simulate disconnection."""
        self.connected = False
        gui_logger.info(f"Disconnected {self.interface_type} simulation interface")
    
    def save_log(self, filepath):
        """Save simulated data to a log file."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "data": {}
            }
            
            for key, value in self.data.items():
                log_data["data"][key] = {
                    "timestamp": value["timestamp"],
                    "value": value["value"]
                }
                
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            gui_logger.info(f"Saved {self.interface_type} log to {filepath}")
            return True
        except Exception as e:
            gui_logger.error(f"Failed to save {self.interface_type} log: {e}")
            return False

class HackTractorGUI:
    """Main GUI application for Hack Tractor."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Hack Tractor - Farm Equipment Control")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Variables for tracking application state
        self.running = False
        self.interfaces: Dict[str, Any] = {}
        self.models: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}
        self.data_collection_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.backend_thread = None
        
        # Data storage for graphing
        self.historical_data: Dict[str, List] = {}
        
        # Load icon if available
        try:
            icon_path = os.path.join(PROJECT_ROOT, "assets", "icon.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception:
            pass
            
        # Create GUI components
        self.create_menu()
        self.create_main_layout()
        
        # Initial setup
        self.load_default_config()
        
        # Setup update timer
        self.root.after(100, self.update_gui)
        
        gui_logger.info("GUI initialized")
    
    def create_menu(self):
        """Create the application menu."""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Load Config", command=self.load_config_file)
        file_menu.add_command(label="Save Config", command=self.save_config_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Equipment menu
        equipment_menu = tk.Menu(menu_bar, tearoff=0)
        equipment_menu.add_command(label="Connect All", command=self.connect_equipment)
        equipment_menu.add_command(label="Disconnect All", command=self.disconnect_equipment)
        equipment_menu.add_separator()
        equipment_menu.add_command(label="CAN Interface Settings", command=lambda: self.show_interface_settings("can"))
        equipment_menu.add_command(label="OBD Interface Settings", command=lambda: self.show_interface_settings("obd"))
        equipment_menu.add_command(label="John Deere API Settings", command=lambda: self.show_interface_settings("john_deere"))
        menu_bar.add_cascade(label="Equipment", menu=equipment_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="View Logs", command=self.view_logs)
        tools_menu.add_command(label="Export Data", command=self.export_data)
        tools_menu.add_separator()
        tools_menu.add_command(label="Simulation Mode", command=self.toggle_simulation_mode)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def create_main_layout(self):
        """Create the main application layout."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top status bar
        status_frame = ttk.LabelFrame(main_frame, text="System Status")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status indicators
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Connection status indicators
        ttk.Label(status_grid, text="CAN Interface:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.can_status = ttk.Label(status_grid, text="Disconnected", foreground="red")
        self.can_status.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(status_grid, text="OBD Interface:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.obd_status = ttk.Label(status_grid, text="Disconnected", foreground="red")
        self.obd_status.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(status_grid, text="John Deere API:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.jd_status = ttk.Label(status_grid, text="Disconnected", foreground="red")
        self.jd_status.grid(row=0, column=5, sticky=tk.W)
        
        # System status indicators
        ttk.Label(status_grid, text="Data Collection:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.collection_status = ttk.Label(status_grid, text="Stopped", foreground="red")
        self.collection_status.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(status_grid, text="Backend Server:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.server_status = ttk.Label(status_grid, text="Stopped", foreground="red")
        self.server_status.grid(row=1, column=3, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(status_grid, text="Mode:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.mode_status = ttk.Label(status_grid, text="Normal", foreground="blue")
        self.mode_status.grid(row=1, column=5, sticky=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.start_button = ttk.Button(button_frame, text="Start System", command=self.start_system)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop System", command=self.stop_system, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Main content area with notebook tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Dashboard tab
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        self.create_dashboard(dashboard_frame)
        
        # Equipment Control tab
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Equipment Control")
        self.create_equipment_control(control_frame)
        
        # Data Analysis tab
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Data Analysis")
        self.create_data_analysis(analysis_frame)
        
        # Configuration tab
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuration")
        self.create_configuration(config_frame)
        
        # Log Console tab
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log Console")
        self.create_log_console(log_frame)
        
        # Bottom status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def create_dashboard(self, parent):
        """Create the dashboard tab content."""
        # Main layout with two columns
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Gauges and indicators
        left_frame = ttk.LabelFrame(main_frame, text="Equipment Status")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Gauge canvas (will use matplotlib for gauges)
        gauge_frame = ttk.Frame(left_frame)
        gauge_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create figure for gauges
        self.gauge_figure = plt.Figure(figsize=(6, 8), dpi=100)
        self.gauge_canvas = FigureCanvasTkAgg(self.gauge_figure, gauge_frame)
        self.gauge_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create initial gauges
        self.setup_gauges()
        
        # Right side - Status and metrics
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Equipment info
        info_frame = ttk.LabelFrame(right_frame, text="Equipment Information")
        info_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 5))
        
        equipment_info = ttk.Frame(info_frame)
        equipment_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(equipment_info, text="Equipment Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.equipment_type = ttk.Label(equipment_info, text="Unknown")
        self.equipment_type.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(equipment_info, text="Manufacturer:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.manufacturer = ttk.Label(equipment_info, text="Unknown")
        self.manufacturer.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(equipment_info, text="Model:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.model = ttk.Label(equipment_info, text="Unknown")
        self.model.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(equipment_info, text="Connection:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.connection_type = ttk.Label(equipment_info, text="None")
        self.connection_type.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Metrics and alerts
        metrics_frame = ttk.LabelFrame(right_frame, text="Metrics & Alerts")
        metrics_frame.pack(fill=tk.BOTH, expand=True)
        
        self.metrics_tree = ttk.Treeview(metrics_frame, columns=("value", "status"), show="headings")
        self.metrics_tree.heading("value", text="Value")
        self.metrics_tree.heading("status", text="Status")
        self.metrics_tree.column("value", width=100)
        self.metrics_tree.column("status", width=100)
        self.metrics_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize metrics tree with some rows
        metrics = [
            ("Engine Hours", "0", "Normal"),
            ("Fuel Used", "0 L", "Normal"),
            ("Distance", "0 km", "Normal"),
            ("Battery", "12.6 V", "Normal"),
            ("Next Service", "250 hrs", "Normal")
        ]
        
        for metric, value, status in metrics:
            item_id = self.metrics_tree.insert("", "end", text=metric, values=(value, status))
            if status == "Warning":
                self.metrics_tree.item(item_id, tags=("warning",))
            elif status == "Alert":
                self.metrics_tree.item(item_id, tags=("alert",))
        
        self.metrics_tree.tag_configure("warning", background="#fff3cd")
        self.metrics_tree.tag_configure("alert", background="#f8d7da")
    
    def setup_gauges(self):
        """Setup matplotlib gauges on the dashboard."""
        self.gauge_figure.clear()
        
        # Create 2x2 grid of gauges
        self.gauge_axes = []
        for i in range(4):
            ax = self.gauge_figure.add_subplot(2, 2, i+1, projection='polar')
            self.gauge_axes.append(ax)
        
        # Configure each gauge
        self.configure_gauge(self.gauge_axes[0], "Engine RPM", (0, 3000), 1500)
        self.configure_gauge(self.gauge_axes[1], "Speed (km/h)", (0, 60), 0)
        self.configure_gauge(self.gauge_axes[2], "Engine Temp (°C)", (50, 130), 85, warning_high=110)
        self.configure_gauge(self.gauge_axes[3], "Fuel Level (%)", (0, 100), 75, warning_low=20)
        
        self.gauge_figure.tight_layout()
        self.gauge_canvas.draw()
    
    def configure_gauge(self, ax, title, range_values, value, warning_low=None, warning_high=None):
        """Configure a single gauge on the dashboard."""
        min_val, max_val = range_values
        
        # Normalize value to the range [0, 1]
        norm_value = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
        norm_value = max(0, min(1, norm_value))  # Clamp to [0, 1]
        
        # Gauge settings
        ax.set_theta_offset(3*np.pi/2)  # Rotate to start at 9 o'clock
        ax.set_theta_direction(-1)  # Clockwise
        
        # Remove radial labels and grid
        ax.set_rticks([])
        
        # Set custom limits for a half-circle gauge
        ax.set_thetamin(0)
        ax.set_thetamax(180)
        
        # Define the colormap for the gauge
        cmap = plt.cm.jet
        
        # Draw the gauge background
        theta = np.linspace(0, np.pi, 100)
        ax.plot(theta, [1]*100, color='lightgray', linewidth=10, solid_capstyle='round')
        
        # Draw warning zones if specified
        if warning_low is not None:
            norm_warning_low = (warning_low - min_val) / (max_val - min_val)
            warning_theta = np.linspace(0, norm_warning_low * np.pi, 30)
            ax.plot(warning_theta, [1]*30, color='orange', linewidth=10, solid_capstyle='round')
        
        if warning_high is not None:
            norm_warning_high = (warning_high - min_val) / (max_val - min_val)
            warning_theta = np.linspace(norm_warning_high * np.pi, np.pi, 30)
            ax.plot(warning_theta, [1]*30, color='orange', linewidth=10, solid_capstyle='round')
        
        # Draw the gauge value
        value_theta = np.linspace(0, norm_value * np.pi, 100)
        ax.plot(value_theta, [1]*100, color=cmap(norm_value), linewidth=10, solid_capstyle='round')
        
        # Draw the needle
        ax.plot([0, norm_value * np.pi], [0, 1], color='black', linewidth=2)
        ax.scatter(norm_value * np.pi, 1, color='black', s=20)
        
        # Add a center circle
        center_circle = plt.Circle((0, 0), 0.1, transform=ax.transData._b, color='darkgray', zorder=10)
        ax.add_artist(center_circle)
        
        # Add the value text and title
        ax.text(0, -0.2, f"{title}\n{value}", ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Show min and max values
        ax.text(0, 0.5, str(min_val), ha='left', va='center', fontsize=8)
        ax.text(np.pi, 0.5, str(max_val), ha='right', va='center', fontsize=8)
        
        # Set limits
        ax.set_ylim(0, 1.1)
    
    def create_equipment_control(self, parent):
        """Create the equipment control tab content."""
        # Main frame
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Equipment selection
        selection_frame = ttk.LabelFrame(control_frame, text="Equipment Selection")
        selection_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        equipment_frame = ttk.Frame(selection_frame)
        equipment_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(equipment_frame, text="Select Equipment:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.equipment_combo = ttk.Combobox(equipment_frame, values=["Tractor", "Implement", "Attachment"])
        self.equipment_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.equipment_combo.current(0)
        
        refresh_button = ttk.Button(equipment_frame, text="Refresh", command=self.refresh_equipment_list)
        refresh_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Control sections in a notebook
        control_notebook = ttk.Notebook(control_frame)
        control_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Basic controls tab
        basic_frame = ttk.Frame(control_notebook)
        control_notebook.add(basic_frame, text="Basic Controls")
        
        basic_controls = ttk.LabelFrame(basic_frame, text="Basic Equipment Controls")
        basic_controls.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Engine controls
        engine_frame = ttk.LabelFrame(basic_controls, text="Engine")
        engine_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(engine_frame, text="Engine Status:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.engine_status = ttk.Label(engine_frame, text="Off", foreground="red")
        self.engine_status.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(engine_frame, text="Start Engine", command=lambda: self.control_engine("start")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(engine_frame, text="Stop Engine", command=lambda: self.control_engine("stop")).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(engine_frame, text="Throttle:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.throttle_var = tk.IntVar(value=0)
        throttle_scale = ttk.Scale(engine_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.throttle_var, 
                               command=lambda x: self.update_throttle(int(float(x))))
        throttle_scale.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.throttle_label = ttk.Label(engine_frame, text="0%")
        self.throttle_label.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Hydraulics controls
        hydraulics_frame = ttk.LabelFrame(basic_controls, text="Hydraulics")
        hydraulics_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for i in range(3):
            ttk.Label(hydraulics_frame, text=f"Hydraulic {i+1}:").grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            var = tk.IntVar(value=0)
            scale = ttk.Scale(hydraulics_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=var, 
                             command=lambda x, idx=i: self.update_hydraulic(idx, int(float(x))))
            scale.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
            label = ttk.Label(hydraulics_frame, text="0%")
            label.grid(row=i, column=2, padx=5, pady=5, sticky=tk.W)
            setattr(self, f"hydraulic_{i+1}_var", var)
            setattr(self, f"hydraulic_{i+1}_label", label)
        
        # Advanced controls tab
        advanced_frame = ttk.Frame(control_notebook)
        control_notebook.add(advanced_frame, text="Advanced Controls")
        
        advanced_controls = ttk.LabelFrame(advanced_frame, text="Advanced Equipment Controls")
        advanced_controls.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Custom commands section
        custom_frame = ttk.LabelFrame(advanced_controls, text="Custom Commands")
        custom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(custom_frame, text="Command:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.command_entry = ttk.Entry(custom_frame, width=40)
        self.command_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Button(custom_frame, text="Send", command=self.send_custom_command).grid(row=0, column=2, padx=5, pady=5)
    
    def create_data_analysis(self, parent):
        """Create the data analysis tab content."""
        # Main frame
        analysis_frame = ttk.Frame(parent)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Graph controls
        controls_frame = ttk.LabelFrame(analysis_frame, text="Data Visualization Controls")
        controls_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Parameter selection
        param_frame = ttk.Frame(controls_frame)
        param_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(param_frame, text="Parameters:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.param_vars = {}
        parameters = ["ENGINE_RPM", "ENGINE_TEMP", "FUEL_LEVEL", "VEHICLE_SPEED", "HYDRAULIC_PRESSURE", "PTO_SPEED"]
        
        for i, param in enumerate(parameters):
            var = tk.BooleanVar(value=i < 3)  # First 3 are checked by default
            cb = ttk.Checkbutton(param_frame, text=param, variable=var)
            cb.grid(row=0, column=i+1, padx=5, pady=5)
            self.param_vars[param] = var
        
        # Time range
        time_frame = ttk.Frame(controls_frame)
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(time_frame, text="Time Range:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.time_range = ttk.Combobox(time_frame, values=["Last 5 minutes", "Last 15 minutes", "Last hour", "Last 4 hours", "Last 24 hours", "All data"])
        self.time_range.current(1)  # Default to "Last 15 minutes"
        self.time_range.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(time_frame, text="Update Graph", command=self.update_data_graph).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(time_frame, text="Export Data", command=self.export_graph_data).grid(row=0, column=3, padx=5, pady=5)
        
        # Graph area
        graph_frame = ttk.LabelFrame(analysis_frame, text="Data Visualization")
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create figure for data plotting
        self.data_figure = plt.Figure(figsize=(10, 6), dpi=100)
        self.data_canvas = FigureCanvasTkAgg(self.data_figure, graph_frame)
        self.data_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize an empty graph
        self.data_ax = self.data_figure.add_subplot(111)
        self.data_ax.set_title("Equipment Data")
        self.data_ax.set_xlabel("Time")
        self.data_ax.set_ylabel("Value")
        self.data_ax.grid(True)
        self.data_canvas.draw()
    
    def create_configuration(self, parent):
        """Create the configuration tab content."""
        # Create a notebook for different configuration categories
        config_notebook = ttk.Notebook(parent)
        config_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System Configuration
        system_frame = ttk.Frame(config_notebook)
        config_notebook.add(system_frame, text="System")
        
        system_config = ttk.LabelFrame(system_frame, text="System Configuration")
        system_config.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Data collection settings
        collection_frame = ttk.Frame(system_config)
        collection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(collection_frame, text="Data Collection Interval (seconds):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.collection_interval = ttk.Spinbox(collection_frame, from_=1, to=3600, width=10)
        self.collection_interval.set(60)
        self.collection_interval.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(collection_frame, text="Data Save Interval (seconds):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.save_interval = ttk.Spinbox(collection_frame, from_=60, to=86400, width=10)
        self.save_interval.set(300)
        self.save_interval.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Backend server settings
        server_frame = ttk.Frame(system_config)
        server_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(server_frame, text="Backend Server:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.enable_backend = tk.BooleanVar(value=True)
        ttk.Checkbutton(server_frame, text="Enable", variable=self.enable_backend).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(server_frame, text="Server Port:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_port = ttk.Spinbox(server_frame, from_=1024, to=65535, width=10)
        self.server_port.set(8000)
        self.server_port.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Simulation settings
        sim_frame = ttk.Frame(system_config)
        sim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(sim_frame, text="Simulation Mode:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.simulation_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(sim_frame, text="Enable", variable=self.simulation_mode).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    
    def create_log_console(self, parent):
        """Create the log console tab content."""
        # Main frame
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controls
        controls_frame = ttk.Frame(log_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(controls_frame, text="Log Level:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_level = ttk.Combobox(controls_frame, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.current(1)  # Default to INFO
        self.log_level.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Apply", command=self.set_log_level).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Save Log", command=self.save_log).pack(side=tk.LEFT, padx=5)
        
        # Log text area with scrollbars
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        y_scrollbar = ttk.Scrollbar(log_container)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = ttk.Scrollbar(log_container, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create text widget for logs
        self.log_text = tk.Text(log_container, wrap=tk.NONE, yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        y_scrollbar.config(command=self.log_text.yview)
        x_scrollbar.config(command=self.log_text.xview)
        
        # Configure text tags for different log levels
        self.log_text.tag_configure("DEBUG", foreground="gray")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("CRITICAL", foreground="red", font=("TkDefaultFont", 10, "bold"))
        
        # Add a custom handler to redirect logs to the text widget
        self.log_handler = TextHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.log_handler)
    
    # Utility functions
    def update_gui(self):
        """Update the GUI with current data."""
        # Update gauges with latest data
        self.update_gauges()
        
        # Schedule the next update
        self.root.after(1000, self.update_gui)
    
    def update_gauges(self):
        """Update gauge displays with latest data."""
        # Get latest data
        engine_rpm = 0
        speed = 0
        engine_temp = 85
        fuel_level = 75
        
        # If we have interfaces with data, use real data
        if hasattr(self, 'interfaces') and self.interfaces:
            for name, interface in self.interfaces.items():
                if name == "can" and hasattr(interface, "get_data"):
                    can_data = interface.get_data()
                    if can_data:
                        if "ENGINE_RPM" in can_data and "value" in can_data["ENGINE_RPM"]:
                            engine_rpm = can_data["ENGINE_RPM"]["value"]
                        if "VEHICLE_SPEED" in can_data and "value" in can_data["VEHICLE_SPEED"]:
                            speed = can_data["VEHICLE_SPEED"]["value"]
                        if "ENGINE_TEMP" in can_data and "value" in can_data["ENGINE_TEMP"]:
                            engine_temp = can_data["ENGINE_TEMP"]["value"]
                        if "FUEL_LEVEL" in can_data and "value" in can_data["FUEL_LEVEL"]:
                            fuel_level = can_data["FUEL_LEVEL"]["value"]
        
        # Update gauge values
        if hasattr(self, 'gauge_axes') and len(self.gauge_axes) >= 4:
            self.configure_gauge(self.gauge_axes[0], "Engine RPM", (0, 3000), engine_rpm)
            self.configure_gauge(self.gauge_axes[1], "Speed (km/h)", (0, 60), speed)
            self.configure_gauge(self.gauge_axes[2], "Engine Temp (°C)", (50, 130), engine_temp, warning_high=110)
            self.configure_gauge(self.gauge_axes[3], "Fuel Level (%)", (0, 100), fuel_level, warning_low=20)
            
            # Redraw canvas
            self.gauge_canvas.draw()
    
    def load_default_config(self):
        """Load default configuration."""
        self.config = {
            "enable_can": False,
            "enable_obd": False,
            "enable_john_deere_api": False,
            "simulation_mode": True,
            "data_collection": {
                "interval": 1,
                "save_interval": 300
            },
            "backend": {
                "enable": True,
                "port": 8000
            }
        }
        
        # Update status
        self.mode_status.config(text="Simulation" if self.config["simulation_mode"] else "Normal")
        
        gui_logger.info("Loaded default configuration")
    
    # Action methods
    def start_system(self):
        """Start the system."""
        if self.running:
            messagebox.showinfo("Already Running", "The system is already running.")
            return
        
        try:
            self.status_bar.config(text="Starting system...")
            
            # Apply simulation mode if needed
            if self.simulation_mode.get():
                self.config["simulation_mode"] = True
                self.config["enable_can"] = False
                self.config["enable_obd"] = False
                
                # Create simulation interfaces
                self.interfaces = {
                    "can": SimulationInterface("can"),
                    "obd": SimulationInterface("obd")
                }
                self.can_status.config(text="Simulation", foreground="blue")
                self.obd_status.config(text="Simulation", foreground="blue")
            else:
                # Initialize real interfaces
                self.interfaces = initialize_equipment_interfaces(self.config)
                
                # Update status indicators
                if "can" in self.interfaces:
                    self.can_status.config(text="Connected", foreground="green")
                if "obd" in self.interfaces:
                    self.obd_status.config(text="Connected", foreground="green")
                if "john_deere" in self.interfaces:
                    self.jd_status.config(text="Connected", foreground="green")
            
            # Initialize AI models
            self.models = initialize_ai_models(self.config)
            
            # Start backend server
            if self.enable_backend.get():
                self.backend_thread = start_backend_server(self.config, self.interfaces, self.models)
                if self.backend_thread:
                    self.server_status.config(text="Running", foreground="green")
            
            # Start data collection in a separate thread
            self.stop_event.clear()
            self.data_collection_thread = threading.Thread(
                target=self.data_collection_loop,
                daemon=True
            )
            self.data_collection_thread.start()
            self.collection_status.config(text="Running", foreground="green")
            
            # Update UI state
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_bar.config(text="System running")
            
            # Update equipment info
            self.equipment_type.config(text="Tractor")
            self.manufacturer.config(text="John Deere")
            self.model.config(text="8R Series")
            self.connection_type.config(text="Simulation" if self.simulation_mode.get() else "CAN Bus")
            
            # Update engine status
            self.engine_status.config(text="Running", foreground="green")
            
            gui_logger.info("System started successfully")
            
        except Exception as e:
            gui_logger.error(f"Error starting system: {e}")
            messagebox.showerror("Error", f"Failed to start system: {e}")
            self.stop_system()
    
    def stop_system(self):
        """Stop the system."""
        self.status_bar.config(text="Stopping system...")
        
        # Stop data collection
        self.stop_event.set()
        if self.data_collection_thread and self.data_collection_thread.is_alive():
            self.data_collection_thread.join(timeout=2.0)
        
        # Clean up resources
        cleanup(self.interfaces)
        
        # Update status indicators
        self.can_status.config(text="Disconnected", foreground="red")
        self.obd_status.config(text="Disconnected", foreground="red")
        self.jd_status.config(text="Disconnected", foreground="red")
        self.collection_status.config(text="Stopped", foreground="red")
        self.server_status.config(text="Stopped", foreground="red")
        self.engine_status.config(text="Off", foreground="red")
        
        # Update UI state
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_bar.config(text="System stopped")
        
        gui_logger.info("System stopped")
    
    def data_collection_loop(self):
        """Data collection loop running in a separate thread."""
        collection_interval = int(self.collection_interval.get())
        save_interval = int(self.save_interval.get())
        last_save_time = time.time()
        
        gui_logger.info(f"Starting data collection loop (interval: {collection_interval}s)")
        
        try:
            while not self.stop_event.is_set():
                # Collect data from interfaces
                for name, interface in self.interfaces.items():
                    try:
                        if hasattr(interface, "get_data"):
                            data = interface.get_data()
                            
                            # Store data for graphing
                            if data:
                                for key, value_data in data.items():
                                    if "value" in value_data:
                                        if key not in self.historical_data:
                                            self.historical_data[key] = []
                                        
                                        # Add to historical data with timestamp
                                        current_time = time.time()
                                        self.historical_data[key].append((current_time, value_data["value"]))
                                        
                                        # Limit data points (keep last 1000)
                                        if len(self.historical_data[key]) > 1000:
                                            self.historical_data[key] = self.historical_data[key][-1000:]
                                            
                    except Exception as e:
                        gui_logger.error(f"Error collecting data from {name} interface: {e}")
                
                # Save data periodically
                current_time = time.time()
                if current_time - last_save_time >= save_interval:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Save interface data
                    for name, interface in self.interfaces.items():
                        try:
                            if hasattr(interface, "save_log"):
                                interface.save_log(str(DATA_DIR / f"{name}_log_{timestamp}.json"))
                        except Exception as e:
                            gui_logger.error(f"Error saving data from {name} interface: {e}")
                    
                    last_save_time = current_time
                    gui_logger.info(f"Saved data at {timestamp}")
                
                # Sleep until next collection
                for _ in range(collection_interval):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
        except Exception as e:
            gui_logger.error(f"Error in data collection loop: {e}")
    
    def update_data_graph(self):
        """Update the data visualization graph."""
        if not hasattr(self, 'historical_data') or not self.historical_data:
            messagebox.showinfo("No Data", "No data available for graphing.")
            return
        
        # Clear the current graph
        self.data_ax.clear()
        
        # Get selected parameters
        selected_params = [param for param, var in self.param_vars.items() if var.get()]
        
        if not selected_params:
            messagebox.showinfo("No Parameters", "Please select at least one parameter to graph.")
            return
        
        # Get time range
        time_range_text = self.time_range.get()
        current_time = time.time()
        
        if time_range_text == "Last 5 minutes":
            start_time = current_time - (5 * 60)
        elif time_range_text == "Last 15 minutes":
            start_time = current_time - (15 * 60)
        elif time_range_text == "Last hour":
            start_time = current_time - (60 * 60)
        elif time_range_text == "Last 4 hours":
            start_time = current_time - (4 * 60 * 60)
        elif time_range_text == "Last 24 hours":
            start_time = current_time - (24 * 60 * 60)
        else:  # All data
            start_time = 0
        
        # Plot each selected parameter
        for param in selected_params:
            if param in self.historical_data and self.historical_data[param]:
                # Filter data by time range
                filtered_data = [(t, v) for t, v in self.historical_data[param] if t >= start_time]
                
                if filtered_data:
                    # Convert to relative time in minutes
                    times = [(t - start_time) / 60 for t, _ in filtered_data]
                    values = [v for _, v in filtered_data]
                    
                    # Plot the data
                    self.data_ax.plot(times, values, label=param)
        
        # Set up the graph
        self.data_ax.set_title("Equipment Data")
        self.data_ax.set_xlabel("Time (minutes)")
        self.data_ax.set_ylabel("Value")
        self.data_ax.grid(True)
        self.data_ax.legend()
        
        # Redraw the canvas
        self.data_canvas.draw()
        
        gui_logger.info(f"Updated graph with {len(selected_params)} parameters")
    
    # Helper methods for UI interaction
    def load_config_file(self):
        """Load configuration from a file."""
        config_file = filedialog.askopenfilename(
            initialdir=CONFIG_DIR,
            title="Select Configuration File",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if config_file:
            try:
                self.config = load_config(config_file)
                gui_logger.info(f"Loaded configuration from {config_file}")
                messagebox.showinfo("Success", "Configuration loaded successfully.")
            except Exception as e:
                gui_logger.error(f"Error loading configuration: {e}")
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def save_config_file(self):
        """Save configuration to a file."""
        config_file = filedialog.asksaveasfilename(
            initialdir=CONFIG_DIR,
            title="Save Configuration File",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if config_file:
            try:
                with open(config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                gui_logger.info(f"Saved configuration to {config_file}")
                messagebox.showinfo("Success", "Configuration saved successfully.")
            except Exception as e:
                gui_logger.error(f"Error saving configuration: {e}")
                messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def toggle_simulation_mode(self):
        """Toggle simulation mode."""
        current_mode = self.simulation_mode.get()
        self.simulation_mode.set(not current_mode)
        self.mode_status.config(text="Simulation" if not current_mode else "Normal")
        gui_logger.info(f"Simulation mode {'enabled' if not current_mode else 'disabled'}")
    
    def connect_equipment(self):
        """Connect to all configured equipment."""
        if self.running:
            messagebox.showinfo("System Running", "Please stop the system before changing connections.")
            return
        
        self.start_system()
    
    def disconnect_equipment(self):
        """Disconnect from all equipment."""
        if self.running:
            self.stop_system()
    
    def control_engine(self, action):
        """Control the engine."""
        if not self.running:
            messagebox.showinfo("System Not Running", "Please start the system first.")
            return
        
        if action == "start":
            self.engine_status.config(text="Running", foreground="green")
            gui_logger.info("Engine started")
        else:
            self.engine_status.config(text="Off", foreground="red")
            gui_logger.info("Engine stopped")
    
    def update_throttle(self, value):
        """Update throttle value."""
        self.throttle_label.config(text=f"{value}%")
        if self.running:
            gui_logger.info(f"Throttle set to {value}%")
    
    def update_hydraulic(self, index, value):
        """Update hydraulic control value."""
        getattr(self, f"hydraulic_{index+1}_label").config(text=f"{value}%")
        if self.running:
            gui_logger.info(f"Hydraulic {index+1} set to {value}%")
    
    def send_custom_command(self):
        """Send a custom command."""
        command = self.command_entry.get().strip()
        if not command:
            return
            
        if self.running:
            gui_logger.info(f"Sending command: {command}")
            messagebox.showinfo("Command Sent", f"Command '{command}' sent to equipment.")
            self.command_entry.delete(0, tk.END)
        else:
            messagebox.showinfo("System Not Running", "Please start the system first.")
    
    def refresh_equipment_list(self):
        """Refresh the equipment list."""
        # In a real implementation, this would query available equipment
        self.equipment_combo['values'] = ["Tractor", "Implement", "Attachment", "Sprayer"]
        gui_logger.info("Equipment list refreshed")
    
    def set_log_level(self):
        """Set the logging level."""
        level_name = self.log_level.get()
        level = getattr(logging, level_name)
        logging.getLogger().setLevel(level)
        self.log_handler.setLevel(level)
        gui_logger.info(f"Log level set to {level_name}")
    
    def clear_log(self):
        """Clear the log console."""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
    
    def save_log(self):
        """Save the log to a file."""
        log_file = filedialog.asksaveasfilename(
            initialdir=LOGS_DIR,
            title="Save Log File",
            defaultextension=".log",
            filetypes=(("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if log_file:
            try:
                with open(log_file, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                gui_logger.info(f"Log saved to {log_file}")
            except Exception as e:
                gui_logger.error(f"Error saving log: {e}")
                messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def export_data(self):
        """Export collected data."""
        export_file = filedialog.asksaveasfilename(
            initialdir=DATA_DIR,
            title="Export Data",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*"))
        )
        
        if export_file:
            try:
                # For JSON export
                if export_file.endswith(".json"):
                    export_data = {
                        "timestamp": datetime.now().isoformat(),
                        "data": {}
                    }
                    
                    for key, data_points in self.historical_data.items():
                        export_data["data"][key] = [
                            {"timestamp": t, "value": v} for t, v in data_points
                        ]
                    
                    with open(export_file, 'w') as f:
                        json.dump(export_data, f, indent=2)
                
                # For CSV export
                elif export_file.endswith(".csv"):
                    import csv
                    with open(export_file, 'w', newline='') as f:
                        writer = csv.writer(f)
                        
                        # Write header
                        writer.writerow(["Parameter", "Timestamp", "Value"])
                        
                        # Write data
                        for key, data_points in self.historical_data.items():
                            for t, v in data_points:
                                writer.writerow([key, datetime.fromtimestamp(t).isoformat(), v])
                
                gui_logger.info(f"Data exported to {export_file}")
                messagebox.showinfo("Success", "Data exported successfully.")
            except Exception as e:
                gui_logger.error(f"Error exporting data: {e}")
                messagebox.showerror("Error", f"Failed to export data: {e}")
    
    def export_graph_data(self):
        """Export data from the current graph."""
        self.export_data()
    
    def show_interface_settings(self, interface_type):
        """Show settings for a specific interface."""
        messagebox.showinfo("Interface Settings", f"Settings for {interface_type} interface would be shown here.")
    
    def view_logs(self):
        """View application logs."""
        self.notebook.select(4)  # Switch to Log Console tab
    
    def show_documentation(self):
        """Show documentation."""
        messagebox.showinfo("Documentation", "Documentation would be shown here.")
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About Hack Tractor", 
                           "Hack Tractor v1.0\n\n"
                           "An open-source solution to give farmers greater control\n"
                           "over their agricultural equipment using AI and Python.\n\n"
                           "Created for hackathon competition.")
    
    def quit_application(self):
        """Quit the application."""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            if self.running:
                self.stop_system()
            self.root.quit()


def main():
    """Main entry point for the GUI application."""
    root = tk.Tk()
    app = HackTractorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
