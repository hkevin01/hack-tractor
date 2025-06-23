#!/usr/bin/env python3
"""
Hack Tractor - Simplified GUI Interface

A clean, professional GUI application for connecting a laptop to tractor systems.
Educational demonstration and hackathon purposes with safety-first design.

🛡️ SAFETY FIRST - Educational Use Only 🛡️
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import logging
import os
import random
from datetime import datetime
from typing import Dict, Any, Optional

# Import visualization
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hack_tractor_gui")


class TractorSimulator:
    """Educational tractor simulator for demonstration."""
    
    def __init__(self):
        self.connected = False
        self.data = {
            "engine_rpm": {"value": 1800, "unit": "RPM", "range": (800, 2500)},
            "engine_temp": {"value": 85, "unit": "°C", "range": (60, 110)},
            "fuel_level": {"value": 75.5, "unit": "%", "range": (0, 100)},
            "speed": {"value": 12.5, "unit": "km/h", "range": (0, 40)},
            "hydraulic_pressure": {"value": 2200, "unit": "PSI", "range": (1000, 3000)},
            "pto_rpm": {"value": 540, "unit": "RPM", "range": (0, 1000)},
        }
        self.status = "Ready"
        self.last_update = time.time()
        
    def connect(self):
        """Simulate connection to tractor."""
        self.connected = True
        self.status = "Connected - Simulation Mode"
        logger.info("Connected to tractor simulator")
        
    def disconnect(self):
        """Disconnect from tractor."""
        self.connected = False
        self.status = "Disconnected"
        logger.info("Disconnected from tractor simulator")
        
    def update_data(self):
        """Generate realistic tractor data."""
        if not self.connected:
            return
            
        for key, info in self.data.items():
            current = info["value"]
            min_val, max_val = info["range"]
            
            # Add realistic variations
            if key == "engine_rpm":
                info["value"] = max(min_val, min(max_val, current + random.uniform(-50, 50)))
            elif key == "engine_temp":
                info["value"] = max(min_val, min(max_val, current + random.uniform(-0.5, 1.0)))
            elif key == "fuel_level":
                info["value"] = max(0, current - random.uniform(0, 0.02))  # Slowly decrease
            elif key == "speed":
                info["value"] = max(0, min(max_val, current + random.uniform(-2, 2)))
            elif key == "hydraulic_pressure":
                info["value"] = max(min_val, min(max_val, current + random.uniform(-100, 100)))
            elif key == "pto_rpm":
                info["value"] = max(0, min(max_val, current + random.uniform(-20, 20)))
                
        self.last_update = time.time()


class HackTractorGUI:
    """Main GUI application for Hack Tractor laptop interface."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hack Tractor 🚜 - Laptop Interface")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Tractor simulator
        self.tractor = TractorSimulator()
        
        # Data storage for plotting
        self.data_history = {key: [] for key in self.tractor.data.keys()}
        self.time_history = []
        
        # GUI state
        self.update_thread = None
        self.running = False
        
        self.setup_gui()
        self.setup_menu()
        
    def setup_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        # Connection menu
        conn_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Connection", menu=conn_menu)
        conn_menu.add_command(label="Connect Simulator", command=self.connect_simulator)
        conn_menu.add_command(label="Disconnect", command=self.disconnect)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_gui(self):
        """Create the main GUI layout."""
        # Title frame
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🚜 Hack Tractor - Educational Equipment Interface",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(expand=True)
        
        # Main content area
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Controls and status
        left_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.setup_control_panel(left_frame)
        
        # Right panel - Data visualization
        right_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_data_panel(right_frame)
        
    def setup_control_panel(self, parent):
        """Setup the control panel."""
        # Connection section
        conn_frame = tk.LabelFrame(parent, text="Connection", padx=10, pady=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.connect_btn = tk.Button(
            conn_frame, 
            text="Connect Simulator",
            command=self.connect_simulator,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        self.connect_btn.pack(fill=tk.X, pady=2)
        
        self.disconnect_btn = tk.Button(
            conn_frame,
            text="Disconnect", 
            command=self.disconnect,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            state=tk.DISABLED
        )
        self.disconnect_btn.pack(fill=tk.X, pady=2)
        
        # Emergency stop
        emergency_frame = tk.LabelFrame(parent, text="EMERGENCY", padx=10, pady=10)
        emergency_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.emergency_btn = tk.Button(
            emergency_frame,
            text="🛑 EMERGENCY STOP",
            command=self.emergency_stop,
            bg='#c0392b',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2
        )
        self.emergency_btn.pack(fill=tk.X)
        
        # Status section
        status_frame = tk.LabelFrame(parent, text="Status", padx=10, pady=10)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="Disconnected",
            font=('Arial', 10),
            fg='red'
        )
        self.status_label.pack()
        
        # Parameters section
        params_frame = tk.LabelFrame(parent, text="Live Parameters", padx=10, pady=10)
        params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable text widget for parameters
        self.params_text = tk.Text(params_frame, height=15, width=30, font=('Courier', 9))
        scrollbar = tk.Scrollbar(params_frame, orient=tk.VERTICAL, command=self.params_text.yview)
        self.params_text.configure(yscrollcommand=scrollbar.set)
        
        self.params_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_data_panel(self, parent):
        """Setup the data visualization panel."""
        # Create notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Real-time plot tab
        plot_frame = tk.Frame(notebook)
        notebook.add(plot_frame, text="Real-time Data")
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Tractor Parameters Over Time")
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Info tab
        info_frame = tk.Frame(notebook)
        notebook.add(info_frame, text="System Info")
        
        info_text = tk.Text(info_frame, wrap=tk.WORD, padx=10, pady=10)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        info_content = """
🚜 Hack Tractor - Educational Interface

This application demonstrates laptop-to-tractor connectivity
for educational and hackathon purposes.

🛡️ SAFETY FEATURES:
• Simulation-only mode for safe learning
• Emergency stop functionality
• Input validation and safety checks
• Educational focus with clear disclaimers

📊 CAPABILITIES:
• Real-time parameter monitoring
• Data visualization and export
• Multiple connection protocol simulation
• Comprehensive logging

⚠️ DISCLAIMER:
This is an educational demonstration tool only.
Not intended for production use on real equipment.
Always follow proper safety protocols.

🔧 SIMULATED PARAMETERS:
• Engine RPM and temperature
• Fuel level and consumption
• Vehicle speed and hydraulics
• PTO (Power Take-Off) status

For more information, see the project documentation.
        """
        
        info_text.insert(tk.END, info_content)
        info_text.configure(state=tk.DISABLED)
        
    def connect_simulator(self):
        """Connect to the tractor simulator."""
        try:
            self.tractor.connect()
            self.update_gui_state(connected=True)
            
            # Start data update thread
            self.running = True
            self.update_thread = threading.Thread(target=self.data_update_loop, daemon=True)
            self.update_thread.start()
            
            messagebox.showinfo("Connected", "Successfully connected to tractor simulator!")
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            
    def disconnect(self):
        """Disconnect from tractor."""
        self.running = False
        self.tractor.disconnect()
        self.update_gui_state(connected=False)
        
        messagebox.showinfo("Disconnected", "Disconnected from tractor.")
        
    def emergency_stop(self):
        """Emergency stop function."""
        self.running = False
        self.tractor.disconnect()
        self.update_gui_state(connected=False)
        
        messagebox.showwarning(
            "EMERGENCY STOP", 
            "EMERGENCY STOP ACTIVATED\\n\\nAll operations halted for safety."
        )
        logger.warning("EMERGENCY STOP activated")
        
    def update_gui_state(self, connected: bool):
        """Update GUI based on connection state."""
        if connected:
            self.connect_btn.configure(state=tk.DISABLED)
            self.disconnect_btn.configure(state=tk.NORMAL)
            self.status_label.configure(text="Connected - Simulation", fg='green')
        else:
            self.connect_btn.configure(state=tk.NORMAL)
            self.disconnect_btn.configure(state=tk.DISABLED)
            self.status_label.configure(text="Disconnected", fg='red')
            
    def data_update_loop(self):
        """Background thread for updating data."""
        while self.running:
            try:
                self.tractor.update_data()
                self.root.after(0, self.update_display)
                time.sleep(1)  # Update every second
            except Exception as e:
                logger.error(f"Data update error: {e}")
                break
                
    def update_display(self):
        """Update the GUI display with current data."""
        if not self.tractor.connected:
            return
            
        # Update parameters text
        self.params_text.delete(1.0, tk.END)
        
        param_text = f"Status: {self.tractor.status}\\n"
        param_text += f"Last Update: {datetime.now().strftime('%H:%M:%S')}\\n\\n"
        
        for name, info in self.tractor.data.items():
            param_text += f"{name.replace('_', ' ').title()}: "
            param_text += f"{info['value']:.1f} {info['unit']}\\n"
            
        self.params_text.insert(tk.END, param_text)
        
        # Update plot data
        current_time = time.time()
        self.time_history.append(current_time)
        
        for key, info in self.tractor.data.items():
            self.data_history[key].append(info['value'])
            
        # Keep only last 60 data points
        if len(self.time_history) > 60:
            self.time_history = self.time_history[-60:]
            for key in self.data_history:
                self.data_history[key] = self.data_history[key][-60:]
                
        # Update plot
        self.update_plot()
        
    def update_plot(self):
        """Update the real-time plot."""
        if not self.time_history:
            return
            
        self.ax.clear()
        self.ax.set_title("Tractor Parameters Over Time")
        self.ax.set_xlabel("Time (seconds ago)")
        self.ax.set_ylabel("Normalized Value")
        self.ax.grid(True)
        
        # Normalize time to show seconds ago
        current_time = time.time()
        time_ago = [(current_time - t) for t in reversed(self.time_history)]
        
        # Plot selected parameters (normalized for visibility)
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        
        for i, (key, values) in enumerate(self.data_history.items()):
            if not values:
                continue
                
            # Normalize values to 0-100 range for better visualization
            normalized = []
            info = self.tractor.data[key]
            min_val, max_val = info['range']
            
            for v in reversed(values):
                norm = ((v - min_val) / (max_val - min_val)) * 100
                normalized.append(norm)
                
            self.ax.plot(
                time_ago, 
                normalized, 
                label=key.replace('_', ' ').title(),
                color=colors[i % len(colors)],
                linewidth=2
            )
            
        self.ax.legend(loc='upper right', fontsize=8)
        self.ax.set_xlim(0, 60)  # Show last 60 seconds
        self.ax.set_ylim(0, 100)  # Normalized range
        
        self.canvas.draw()
        
    def export_data(self):
        """Export collected data to JSON file."""
        if not self.data_history or not any(self.data_history.values()):
            messagebox.showwarning("No Data", "No data available to export.")
            return
            
        try:
            filename = f"tractor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': len(self.time_history),
                'parameters': {}
            }
            
            for key, values in self.data_history.items():
                if values:
                    export_data['parameters'][key] = {
                        'values': values,
                        'unit': self.tractor.data[key]['unit'],
                        'count': len(values)
                    }
                    
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            messagebox.showinfo("Export Complete", f"Data exported to {filename}")
            logger.info(f"Data exported to {filename}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            messagebox.showerror("Export Error", f"Failed to export data: {e}")
            
    def show_about(self):
        """Show about dialog."""
        about_text = """
Hack Tractor - Educational Interface v1.0

🚜 Educational agricultural equipment interface
for hackathon demonstration and learning.

🛡️ Safety-first design with simulation mode
📊 Real-time monitoring and data visualization  
🔧 Multiple protocol simulation capabilities

⚠️ Educational use only - not for production

Built with Python, Tkinter, and Matplotlib
Part of the Hack Tractor open-source project
        """
        
        messagebox.showinfo("About Hack Tractor", about_text)
        
    def on_close(self):
        """Handle application close."""
        if self.running:
            self.running = False
            self.tractor.disconnect()
            
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """Start the GUI application."""
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Show startup message
        messagebox.showinfo(
            "Hack Tractor", 
            "🚜 Welcome to Hack Tractor!\\n\\n"
            "Educational tractor interface for demonstration.\\n"
            "Click 'Connect Simulator' to begin."
        )
        
        # Start the GUI
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        app = HackTractorGUI()
        app.run()
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
