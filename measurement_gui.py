from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QSpinBox,
                             QTextEdit, QProgressBar, QFileDialog, QCheckBox)
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
import serial
import serial.tools.list_ports
import pandas as pd
import numpy as np
import time
from lakeshore import Teslameter
from arduino_status import ArduinoStatusWidget
from arduino_control import ArduinoController

class MeasurementWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, path_file, output_file, arduino_port, sim_mode=False):
        super().__init__()
        self.path_file = path_file
        self.output_file = output_file
        self.arduino_port = arduino_port
        self.sim_mode = sim_mode
        self.is_running = True
        
    def run(self):
        try:
            # Load path file
            df_table = pd.read_csv(self.path_file)
            total_steps = len(df_table)
            
            if not self.sim_mode:
                # Initialize Arduino controller
                self.status.emit("Initializing Arduino...")
                self.arduino = ArduinoController(self.arduino_port)
                self.arduino.connect()
                
                # Initialize Lakeshore
                self.status.emit("Initializing Lakeshore Teslameter...")
                tm = Teslameter()
                tm.connect_tcp('TCPIP0::localhost::INSTR')
                
            # Set up output file
            self.status.emit("Setting up output file...")
            headers = ["index", "dx", "dy", "dz", "Bx", "By", "Bz", "Bmod", "x", "y", "z"]
            with open(self.output_file, "w") as f:
                f.write(",".join(headers) + "\n")
            
            # Execute measurements
            for index, row in df_table.iterrows():
                if not self.is_running:
                    break
                    
                self.status.emit(f"Measuring point {index + 1}/{total_steps}")
                
                if not self.sim_mode:
                    # Check limit switches before moving
                    limits = self.arduino.check_limits()
                    if any(limits.values()):
                        raise Exception("Limit switch triggered - stopping measurement")
                    
                    # Move Arduino
                    self.arduino.move_relative(
                        x=row['dx'],
                        y=row['dy'],
                        z=row['dz']
                    )
                    
                    # Wait for movement and stabilization
                    time.sleep(row.get('delay', 1))
                    
                    # Take measurement with Lakeshore
                    fields = tm.measure()  # Get X, Y, Z components
                    Bx, By, Bz = fields
                    Bmod = np.sqrt(Bx**2 + By**2 + Bz**2)
                else:
                    # Simulation mode - generate dummy data
                    Bx = np.random.normal(100, 10)
                    By = np.random.normal(100, 10)
                    Bz = np.random.normal(1000, 50)
                    Bmod = np.sqrt(Bx**2 + By**2 + Bz**2)
                    time.sleep(0.1)  # Simulate measurement delay
                
                # Save data
                data = [str(x) for x in [
                    index, row['dx'], row['dy'], row['dz'],
                    Bx, By, Bz, Bmod,
                    row['x'], row['y'], row['z']
                ]]
                with open(self.output_file, "a") as f:
                    f.write(",".join(data) + "\n")
                
                # Update progress
                self.progress.emit(int((index + 1) / total_steps * 100))
            
            # Clean up
            if not self.sim_mode:
                self.arduino.disconnect()
                tm.disconnect()
            
            if self.is_running:
                self.finished.emit(self.output_file)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def stop(self):
        self.is_running = False
        if hasattr(self, 'arduino'):
            try:
                self.arduino.send_command('M410')  # Emergency stop
            except:
                pass

class MeasurementTab(QWidget):
    measurement_completed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.worker = None
        
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create status text first (since it's used by other methods)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        
        # Mode Selection
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QHBoxLayout()
        self.sim_mode = QCheckBox("Simulation Mode (No Hardware)")
        self.sim_mode.setChecked(True)
        self.sim_mode.toggled.connect(self.update_hardware_state)
        mode_layout.addWidget(self.sim_mode)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Hardware settings
        hw_group = QGroupBox("Hardware Settings")
        hw_layout = QHBoxLayout()
        
        # Arduino port selection
        hw_layout.addWidget(QLabel("Arduino Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        hw_layout.addWidget(self.port_combo)
        
        # Refresh ports button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        hw_layout.addWidget(refresh_btn)
        
        # Lakeshore settings (add specific settings if needed)
        hw_layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.sample_rate = QSpinBox()
        self.sample_rate.setRange(1, 100)
        self.sample_rate.setValue(10)
        hw_layout.addWidget(self.sample_rate)
        
        hw_group.setLayout(hw_layout)
        layout.addWidget(hw_group)
        
        # Path and output settings
        path_group = QGroupBox("Path and Output")
        path_layout = QVBoxLayout()
        
        # Path display
        path_info = QHBoxLayout()
        path_info.addWidget(QLabel("Current Path:"))
        self.path_label = QLabel("No path loaded")
        path_info.addWidget(self.path_label)
        path_layout.addLayout(path_info)
        
        # Output file
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output File:"))
        self.output_label = QLabel("No output file selected")
        output_layout.addWidget(self.output_label)
        self.select_output_btn = QPushButton("Select")
        self.select_output_btn.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.select_output_btn)
        path_layout.addLayout(output_layout)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # Add Arduino status widget
        self.arduino_status = ArduinoStatusWidget()
        layout.addWidget(self.arduino_status)
        
        # Status and control
        status_group = QGroupBox("Status and Control")
        status_layout = QVBoxLayout()

        status_layout.addWidget(self.status_text)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        status_layout.addWidget(self.progress_bar)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        # Home Arduino button
        self.home_btn = QPushButton("Home Arduino")
        self.home_btn.clicked.connect(self.home_arduino)
        button_layout.addWidget(self.home_btn)
        
        self.start_btn = QPushButton("Start Measurement")
        self.start_btn.clicked.connect(self.start_measurement)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_measurement)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        
        status_layout.addLayout(button_layout)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Initial hardware state update
        self.update_hardware_state()
        
    def update_hardware_state(self):
        """Update UI elements based on simulation mode"""
        hardware_enabled = not self.sim_mode.isChecked()
        self.port_combo.setEnabled(hardware_enabled)
        self.home_btn.setEnabled(hardware_enabled)
        self.arduino_status.setEnabled(hardware_enabled)
        self.sample_rate.setEnabled(hardware_enabled)
        
    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if ports:
            self.port_combo.addItems(ports)
            self.log_status(f"Found ports: {', '.join(ports)}")
        else:
            self.port_combo.addItem("No ports available")
            self.log_status("No serial ports found")
        
    def home_arduino(self):
        """Home all axes of the Arduino"""
        if self.sim_mode.isChecked():
            self.log_status("Cannot home in simulation mode")
            return
            
        try:
            arduino = ArduinoController(self.port_combo.currentText())
            arduino.connect()
            arduino.home_axes()
            arduino.disconnect()
            self.log_status("Homing completed successfully")
        except Exception as e:
            self.log_status(f"Homing error: {str(e)}")
    
    def load_path(self, path_file):
        self.path_file = path_file
        self.path_label.setText(path_file.split('/')[-1])
        self.log_status(f"Loaded path file: {path_file}")
        
    def select_output_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Select Output File", "", "CSV Files (*.csv)")
        if file_name:
            self.output_file = file_name
            self.output_label.setText(file_name.split('/')[-1])
    
    def start_measurement(self):
        if not hasattr(self, 'path_file') or not hasattr(self, 'output_file'):
            self.log_status("Error: Please select path and output files")
            return

        if not self.sim_mode.isChecked():
            # Validate hardware connections
            try:
                # Test Arduino connection
                arduino = ArduinoController(self.port_combo.currentText())
                arduino.connect()
                arduino.disconnect()
                
                # Test Lakeshore connection
                tm = Teslameter()
                tm.connect_tcp('TCPIP0::localhost::INSTR')
                tm.disconnect()
            except Exception as e:
                self.log_status(f"Hardware connection error: {str(e)}")
                return
        
        self.worker = MeasurementWorker(
            self.path_file,
            self.output_file,
            self.port_combo.currentText(),
            self.sim_mode.isChecked()
        )
        
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.log_status)
        self.worker.finished.connect(self.measurement_finished)
        self.worker.error.connect(self.handle_error)
        
        self.worker.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
    def stop_measurement(self):
        if self.worker:
            self.worker.stop()
            self.log_status("Stopping measurement...")
            
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def log_status(self, message):
        self.status_text.append(message)
        
    def measurement_finished(self, output_file):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_status("Measurement completed")
        self.measurement_completed.emit(output_file)
        
    def handle_error(self, error_message):
        self.log_status(f"Error: {error_message}")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)