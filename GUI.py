import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                           QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                           QPushButton, QSpinBox, QDoubleSpinBox, QLineEdit,
                           QProgressBar, QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
import pandas as pd
import serial
import serial.tools.list_ports
import time
from path_generator import PathGenerator

class SetupTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # COM Port Selection
        port_group = QGroupBox("Serial Connection")
        port_layout = QVBoxLayout()
        
        port_select_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports_btn = QPushButton("Refresh")
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        port_select_layout.addWidget(QLabel("COM Port:"))
        port_select_layout.addWidget(self.port_combo)
        port_select_layout.addWidget(self.refresh_ports_btn)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_hardware)
        
        port_layout.addLayout(port_select_layout)
        port_layout.addWidget(self.connect_btn)
        port_group.setLayout(port_layout)
        
        # Probe Configuration
        probe_group = QGroupBox("Probe Configuration")
        probe_layout = QVBoxLayout()
        
        self.range_combo = QComboBox()
        self.range_combo.addItems(['0.1T', '0.3T', '1T', '3T'])
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Range:"))
        range_layout.addWidget(self.range_combo)
        
        self.average_spin = QSpinBox()
        self.average_spin.setRange(1, 100000)
        self.average_spin.setValue(30000)
        avg_layout = QHBoxLayout()
        avg_layout.addWidget(QLabel("Average:"))
        avg_layout.addWidget(self.average_spin)
        
        probe_layout.addLayout(range_layout)
        probe_layout.addLayout(avg_layout)
        probe_group.setLayout(probe_layout)
        
        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Not Connected")
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        
        layout.addWidget(port_group)
        layout.addWidget(probe_group)
        layout.addWidget(status_group)
        layout.addStretch()
        
        self.setLayout(layout)
        self.refresh_ports()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)

    def connect_hardware(self):
        try:
            port = self.port_combo.currentText()
            if not port:
                raise ValueError("No COM port selected")

            # Test serial connection
            s = serial.Serial(port, 115200)
            s.write(b"\r\n\r\n")
            time.sleep(2)
            s.flushInput()
            
            # Test GRBL response
            s.write(b"$\n")  # Request settings
            response = s.readline().decode().strip()
            if not response:
                raise ConnectionError("No response from GRBL controller")

            # Test probe connection
            import usbtmc as backend
            import pyTHM1176.api.thm_usbtmc_api as thm_api
            devices = backend.list_devices()
            if not devices:
                raise ConnectionError("THM1176 probe not found")

            params = {
                "trigger_type": "single",
                "range": self.range_combo.currentText(),
                "average": self.average_spin.value(),
                "format": "ASCII"
            }
            
            thm = thm_api.Thm1176(devices[0], **params)
            device_id = thm.get_id()
            thm.close()
            
            # Store the serial port for later use
            self.serial_port = port
            
            # Update UI
            self.status_label.setText(
                f"Connected\nProbe: {device_id.get('serial_number', 'Unknown')}\n"
                f"Port: {port}"
            )
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText("Connected")
            self.port_combo.setEnabled(False)
            self.range_combo.setEnabled(False)
            self.average_spin.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")
            self.status_label.setText("Connection failed")

class PathPlanningTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Path Type Selection
        type_group = QGroupBox("Path Type")
        type_layout = QVBoxLayout()
        
        self.path_type_combo = QComboBox()
        self.path_type_combo.addItems(['Cube', 'Sphere'])
        self.path_type_combo.currentTextChanged.connect(self.update_parameters)
        
        type_layout.addWidget(self.path_type_combo)
        type_group.setLayout(type_layout)
        
        # Parameters
        self.param_group = QGroupBox("Parameters")
        self.param_layout = QVBoxLayout()
        self.param_group.setLayout(self.param_layout)
        
        # Preview
        preview_group = QGroupBox("Path Preview")
        preview_layout = QVBoxLayout()
        self.preview_widget = gl.GLViewWidget()
        preview_layout.addWidget(self.preview_widget)
        preview_group.setLayout(preview_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate Path")
        self.generate_btn.clicked.connect(self.generate_path)
        self.save_btn = QPushButton("Save Path")
        self.save_btn.clicked.connect(self.save_path)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addWidget(type_group)
        layout.addWidget(self.param_group)
        layout.addWidget(preview_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.update_parameters()

    def update_parameters(self):
        # Clear existing parameters
        for i in reversed(range(self.param_layout.count())): 
            self.param_layout.itemAt(i).widget().setParent(None)
        
        path_type = self.path_type_combo.currentText()
        
        if path_type == 'Cube':
            # Add cube parameters
            size_layout = QHBoxLayout()
            self.cube_size = QDoubleSpinBox()
            self.cube_size.setRange(0.1, 1000)
            self.cube_size.setValue(20)
            size_layout.addWidget(QLabel("Size (mm):"))
            size_layout.addWidget(self.cube_size)
            self.param_layout.addLayout(size_layout)
            
            points_layout = QHBoxLayout()
            self.points_per_side = QSpinBox()
            self.points_per_side.setRange(2, 100)
            self.points_per_side.setValue(5)
            points_layout.addWidget(QLabel("Points per side:"))
            points_layout.addWidget(self.points_per_side)
            self.param_layout.addLayout(points_layout)
            
        elif path_type == 'Sphere':
            # Add sphere parameters
            radius_layout = QHBoxLayout()
            self.sphere_radius = QDoubleSpinBox()
            self.sphere_radius.setRange(0.1, 1000)
            self.sphere_radius.setValue(35)
            radius_layout.addWidget(QLabel("Radius (mm):"))
            radius_layout.addWidget(self.sphere_radius)
            self.param_layout.addLayout(radius_layout)
            
            points_layout = QHBoxLayout()
            self.points_theta = QSpinBox()
            self.points_theta.setRange(2, 100)
            self.points_theta.setValue(20)
            points_layout.addWidget(QLabel("Points (theta):"))
            points_layout.addWidget(self.points_theta)
            self.param_layout.addLayout(points_layout)
            
            phi_layout = QHBoxLayout()
            self.points_phi = QSpinBox()
            self.points_phi.setRange(2, 100)
            self.points_phi.setValue(20)
            phi_layout.addWidget(QLabel("Points (phi):"))
            phi_layout.addWidget(self.points_phi)
            self.param_layout.addLayout(phi_layout)


    def generate_path(self):
        path_type = self.path_type_combo.currentText()
        try:
            if path_type == 'Cube':
                self.current_path = PathGenerator.generate_cube_path(
                    size_mm=self.cube_size.value(),
                    points_per_side=self.points_per_side.value(),
                    measurements_per_pos=1  # You can make this configurable if needed
                )
            else:  # Sphere
                self.current_path = PathGenerator.generate_sphere_path(
                    radius=self.sphere_radius.value(),
                    num_points_theta=self.points_theta.value(),
                    num_points_phi=self.points_phi.value(),
                    measurements_per_pos=1  # You can make this configurable if needed
                )
                
            # Enable save button once path is generated
            self.save_btn.setEnabled(True)
            
            # Update the 3D preview
            self.update_preview()
            
            # Show success message
            QMessageBox.information(self, "Success", "Path generated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Path generation failed: {str(e)}")

   

    def update_preview(self):
        try:
            # Clear existing items
            self.preview_widget.clear()
            
            if not hasattr(self, 'current_path'):
                return
                
            # Get points for visualization
            points = np.array([
                self.current_path['x'].values,
                self.current_path['y'].values,
                self.current_path['z'].values
            ]).T
            
            # Create point cloud
            scatter = gl.GLScatterPlotItem(
                pos=points,
                color=(0, 1, 0, 1),  # Green color
                size=5
            )
            self.preview_widget.addItem(scatter)
            
            # Add coordinate axes for reference
            axis_length = max(
                points[:, 0].max() - points[:, 0].min(),
                points[:, 1].max() - points[:, 1].min(),
                points[:, 2].max() - points[:, 2].min()
            ) * 0.5
            
            # X-axis (red)
            x_axis = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
                color=(1, 0, 0, 1),
                width=2
            )
            self.preview_widget.addItem(x_axis)
            
            # Y-axis (green)
            y_axis = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
                color=(0, 1, 0, 1),
                width=2
            )
            self.preview_widget.addItem(y_axis)
            
            # Z-axis (blue)
            z_axis = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
                color=(0, 0, 1, 1),
                width=2
            )
            self.preview_widget.addItem(z_axis)
            
            # Set camera position
            self.preview_widget.setCameraPosition(distance=axis_length*3)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update preview: {str(e)}")

    def save_path(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Path", "", "CSV Files (*.csv)")
        if filename:
            try:
                # Save path to CSV
                pass
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export plot: {str(e)}")

class MeasurementThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    data_update = pyqtSignal(float, float, float, float)  # Bx, By, Bz, Bmod
    measurement_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, path_file, serial_port, probe_params):
        super().__init__()
        self.path_file = path_file
        self.serial_port = serial_port
        self.probe_params = probe_params
        self.running = False
        self.paused = False

    def run(self):
        try:
            # Initialize hardware
            self.status_update.emit("Initializing hardware...")
            s = serial.Serial(self.serial_port, 115200)
            s.write(b"\r\n\r\n")
            time.sleep(2)
            s.flushInput()

            # Load path file
            self.status_update.emit("Loading path file...")
            df_table = pd.read_csv(self.path_file)
            total_points = len(df_table)

            # Initialize probe
            thm = thm_api.Thm1176(backend.list_devices()[0], **self.probe_params)

            self.running = True
            current_point = 0

            # Create output file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"measurements/measurement_{timestamp}.csv"
            header = "index,dx,dy,dz,Bx,By,Bz,Bmod,x,y,z\n"
            with open(output_filename, "w") as f:
                f.write(header)

            for index, row in df_table.iterrows():
                if not self.running:
                    break

                while self.paused:
                    time.sleep(0.1)
                    if not self.running:
                        break

                # Execute movement
                self.status_update.emit(f"Moving to position {current_point + 1}/{total_points}")
                
                # Create movement command
                movement_command = f"G91"
                if row['dx'] != 0:
                    movement_command += f" X{row['dx']}"
                if row['dy'] != 0:
                    movement_command += f" Y{row['dy']}"
                if row['dz'] != 0:
                    movement_command += f" Z{row['dz']}"
                movement_command += " F100000"

                # Send movement command
                s.write(movement_command.encode('utf-8') + b'\n')
                s.readline()  # Wait for ok response

                # Wait for movement to complete
                wait_command = "G4 P0"  # Dwell command to ensure movement completion
                s.write(wait_command.encode('utf-8') + b'\n')
                s.readline()

                # Delay based on path file or default
                delay = row.get('delay', 0.5)
                time.sleep(delay)

                # Take measurement
                self.status_update.emit("Taking measurement...")
                thm.make_measurement(**self.probe_params)
                meas = thm.last_reading
                measurements = list(meas.values())
                Bx = np.array(measurements[0])*10000
                By = np.array(measurements[1])*10000
                Bz = np.array(measurements[2])*10000
                Bmod = np.sqrt(Bx**2 + By**2 + Bz**2)

                # Save measurement to file
                measurement_line = (f"{index},{row['dx']},{row['dy']},{row['dz']},"
                                 f"{Bx[0]},{By[0]},{Bz[0]},{Bmod[0]},"
                                 f"{row['x']},{row['y']},{row['z']}\n")
                with open(output_filename, "a") as f:
                    f.write(measurement_line)

                # Emit measurement data
                self.data_update.emit(Bx[0], By[0], Bz[0], Bmod[0])

                current_point += 1
                progress = int((current_point / total_points) * 100)
                self.progress_update.emit(progress)

            # Clean up
            s.close()
            thm.close()
            
            if self.running:  # If we completed normally
                self.measurement_complete.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.running = False

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('3D Field Mapper')
        self.setGeometry(100, 100, 1200, 800)

        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
        self.setup_tab = SetupTab()
        self.path_tab = PathPlanningTab()
        self.measurement_tab = MeasurementTab()
        self.visualization_tab = VisualizationTab()

        # Add tabs
        self.tabs.addTab(self.setup_tab, "Setup")
        self.tabs.addTab(self.path_tab, "Path Planning")
        self.tabs.addTab(self.measurement_tab, "Measurement")
        self.tabs.addTab(self.visualization_tab, "Visualization")

        # Connect signals
        self.measurement_tab.start_btn.clicked.connect(self.start_measurement)
        self.measurement_thread = None

    def start_measurement(self):
        if not hasattr(self.setup_tab, 'serial_port') or not self.setup_tab.serial_port:
            QMessageBox.warning(self, "Warning", "Please connect to hardware first")
            return

        path_file = self.measurement_tab.path_edit.text()
        if not path_file:
            QMessageBox.warning(self, "Warning", "Please select a path file")
            return

        # Get probe parameters
        probe_params = {
            "trigger_type": "single",
            "range": self.setup_tab.range_combo.currentText(),
            "average": self.setup_tab.average_spin.value(),
            "format": "ASCII"
        }

        # Create and start measurement thread
        self.measurement_thread = MeasurementThread(
            path_file=path_file,
            serial_port=self.setup_tab.serial_port,
            probe_params=probe_params
        )

        # Connect thread signals
        self.measurement_thread.progress_update.connect(self.measurement_tab.progress_bar.setValue)
        self.measurement_thread.status_update.connect(self.measurement_tab.status_label.setText)
        self.measurement_thread.data_update.connect(self.update_live_data)
        self.measurement_thread.measurement_complete.connect(self.measurement_complete)
        self.measurement_thread.error_occurred.connect(self.measurement_error)

        # Start measurement
        self.measurement_thread.start()
        self.measurement_tab.start_btn.setEnabled(False)
        self.measurement_tab.pause_btn.setEnabled(True)
        self.measurement_tab.stop_btn.setEnabled(True)

    def update_live_data(self, Bx, By, Bz, Bmod):
        if not hasattr(self.measurement_tab, 'data_points'):
            self.measurement_tab.data_points = {
                'Bx': [], 'By': [], 'Bz': [], 'Bmod': [],
                'time': [], 'count': 0
            }
            
            # Set up plot
            self.measurement_tab.data_plot.clear()
            self.measurement_tab.data_plot.setLabel('left', 'Field Strength', units='T')
            self.measurement_tab.data_plot.setLabel('bottom', 'Measurement Number')
            self.measurement_tab.plot_items = {
                'Bx': self.measurement_tab.data_plot.plot(pen='r', name='Bx'),
                'By': self.measurement_tab.data_plot.plot(pen='g', name='By'),
                'Bz': self.measurement_tab.data_plot.plot(pen='b', name='Bz'),
                'Bmod': self.measurement_tab.data_plot.plot(pen='w', name='|B|')
            }
            self.measurement_tab.data_plot.addLegend()

        # Update data
        data = self.measurement_tab.data_points
        data['count'] += 1
        data['time'].append(data['count'])
        data['Bx'].append(Bx)
        data['By'].append(By)
        data['Bz'].append(Bz)
        data['Bmod'].append(Bmod)

        # Update plots
        for field in ['Bx', 'By', 'Bz', 'Bmod']:
            self.measurement_tab.plot_items[field].setData(
                data['time'], 
                data[field]
            )

        # Auto-scale the view to show all data
        self.measurement_tab.data_plot.enableAutoRange()

    def measurement_complete(self):
        self.measurement_tab.status_label.setText("Measurement complete")
        self.measurement_tab.start_btn.setEnabled(True)
        self.measurement_tab.pause_btn.setEnabled(False)
        self.measurement_tab.stop_btn.setEnabled(False)
        self.measurement_tab.progress_bar.setValue(100)

    def measurement_error(self, error_message):
        QMessageBox.critical(self, "Error", f"Measurement failed: {error_message}")
        self.measurement_tab.start_btn.setEnabled(True)
        self.measurement_tab.pause_btn.setEnabled(False)
        self.measurement_tab.stop_btn.setEnabled(False)


class MeasurementTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Control Group
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_path)
        file_layout.addWidget(QLabel("Path File:"))
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(self.browse_btn)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_measurement)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_measurement)
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_measurement)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)
        
        control_layout.addLayout(file_layout)
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        
        # Progress Group
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        
        # Live Data Group
        data_group = QGroupBox("Live Data")
        data_layout = QVBoxLayout()
        self.data_plot = pg.PlotWidget()
        data_layout.addWidget(self.data_plot)
        data_group.setLayout(data_layout)
        
        layout.addWidget(control_group)
        layout.addWidget(progress_group)
        layout.addWidget(data_group)
        
        self.setLayout(layout)

    def browse_path(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Path File", "", "CSV Files (*.csv)")
        if filename:
            self.path_edit.setText(filename)

    def start_measurement(self):
        if not self.path_edit.text():
            QMessageBox.warning(self, "Warning", "Please select a path file first")
            return

        # Get serial port from setup tab
        main_window = self.window()
        setup_tab = main_window.setup_tab
        if not hasattr(setup_tab, 'serial_port'):
            QMessageBox.warning(self, "Warning", "Please connect to hardware first")
            return

        # Get probe parameters
        probe_params = {
            "trigger_type": "single",
            "range": setup_tab.range_combo.currentText(),
            "average": setup_tab.average_spin.value(),
            "format": "ASCII"
        }

        # Create and start measurement thread
        self.measurement_thread = MeasurementThread(
            path_file=self.path_edit.text(),
            serial_port=setup_tab.serial_port,
            probe_params=probe_params
        )

        # Connect thread signals
        self.measurement_thread.progress_update.connect(self.progress_bar.setValue)
        self.measurement_thread.status_update.connect(self.status_label.setText)
        self.measurement_thread.data_update.connect(self.update_live_data)
        self.measurement_thread.measurement_complete.connect(self.measurement_complete)
        self.measurement_thread.error_occurred.connect(self.measurement_error)

        # Update UI
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Starting measurement...")

        # Start measurement
        self.measurement_thread.start()

    def pause_measurement(self):
        if self.measurement_thread and self.measurement_thread.isRunning():
            if self.measurement_thread.paused:
                self.measurement_thread.resume()
                self.pause_btn.setText("Pause")
                self.status_label.setText("Measurement resumed...")
            else:
                self.measurement_thread.pause()
                self.pause_btn.setText("Resume")
                self.status_label.setText("Measurement paused...")

    def stop_measurement(self):
        if self.measurement_thread and self.measurement_thread.isRunning():
            self.measurement_thread.stop()
            self.status_label.setText("Stopping measurement...")
            self.measurement_thread.wait()  # Wait for thread to finish
            self.measurement_complete()

    def measurement_complete(self):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("Pause")
        self.status_label.setText("Measurement complete")
        QMessageBox.information(self, "Success", "Measurement completed successfully!")

    def measurement_error(self, error_message):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Measurement failed")
        QMessageBox.critical(self, "Error", f"Measurement failed: {error_message}")

class VisualizationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Data Loading
        load_group = QGroupBox("Data")
        load_layout = QHBoxLayout()
        self.data_edit = QLineEdit()
        self.data_edit.setReadOnly(True)
        self.load_btn = QPushButton("Load Data")
        self.load_btn.clicked.connect(self.load_data)
        load_layout.addWidget(self.data_edit)
        load_layout.addWidget(self.load_btn)
        load_group.setLayout(load_layout)
        
        # Plot Controls
        control_group = QGroupBox("Plot Controls")
        control_layout = QHBoxLayout()
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(['Bx', 'By', 'Bz', 'Bmod'])
        self.plot_type_combo.currentTextChanged.connect(self.update_plot)
        self.export_btn = QPushButton("Export Plot")
        self.export_btn.clicked.connect(self.export_plot)
        control_layout.addWidget(QLabel("Plot Type:"))
        control_layout.addWidget(self.plot_type_combo)
        control_layout.addWidget(self.export_btn)
        control_group.setLayout(control_layout)
        
        # 3D Plot
        plot_group = QGroupBox("3D Visualization")
        plot_layout = QVBoxLayout()
        self.plot_widget = gl.GLViewWidget()
        plot_layout.addWidget(self.plot_widget)
        plot_group.setLayout(plot_layout)
        
        layout.addWidget(load_group)
        layout.addWidget(control_group)
        layout.addWidget(plot_group)
        
        self.setLayout(layout)

    def load_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Data File", "", "CSV Files (*.csv)")
        if filename:
            self.data_edit.setText(filename)
            self.update_plot()

    def update_plot(self):
        if not self.data_edit.text():
            return
            
        try:
            # Load and plot data
            pass
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update plot: {str(e)}")

    def export_plot(self):
        if not self.data_edit.text():
            QMessageBox.warning(self, "Warning", "No data loaded")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Files (*.png)")
        if filename:
            try:
                # Take screenshot of the 3D plot
                self.plot_widget.grabFramebuffer().save(filename)
                QMessageBox.information(self, "Success", "Plot exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export plot: {str(e)}")

    def load_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Data File", "", "CSV Files (*.csv)")
        if filename:
            try:
                self.data = pd.read_csv(filename)
                self.data_edit.setText(filename)
                self.update_plot()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def update_plot(self):
        if not hasattr(self, 'data'):
            return

        try:
            self.plot_widget.clear()

            # Get plot type
            plot_type = self.plot_type_combo.currentText()
            
            # Create points array
            points = np.array([
                self.data['x'].values,
                self.data['y'].values,
                self.data['z'].values
            ]).T

            # Create colors based on field values
            if plot_type == 'Bmod':
                values = self.data['Bmod'].values
            else:
                values = self.data[plot_type].values

            # Normalize values for coloring
            norm_values = (values - values.min()) / (values.max() - values.min())
            colors = np.zeros((len(norm_values), 4))
            colors[:, 0] = norm_values  # Red channel
            colors[:, 2] = 1 - norm_values  # Blue channel
            colors[:, 3] = 1.0  # Alpha channel

            # Create scatter plot
            scatter = gl.GLScatterPlotItem(
                pos=points,
                color=colors,
                size=5
            )
            self.plot_widget.addItem(scatter)

            # Add coordinate axes
            axis_length = max(
                self.data['x'].max() - self.data['x'].min(),
                self.data['y'].max() - self.data['y'].min(),
                self.data['z'].max() - self.data['z'].min()
            ) * 0.5

            # X-axis (red)
            x_axis = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
                color=(1, 0, 0, 1),
                width=2
            )
            self.plot_widget.addItem(x_axis)

            # Y-axis (green)
            y_axis = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
                color=(0, 1, 0, 1),
                width=2
            )
            self.plot_widget.addItem(y_axis)

            # Z-axis (blue)
            z_axis = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
                color=(0, 0, 1, 1),
                width=2
            )
            self.plot_widget.addItem(z_axis)

            # Set camera position
            self.plot_widget.setCameraPosition(distance=axis_length*3)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update plot: {str(e)}")

    def add_colorbar(self):
        # Create colorbar widget
        colorbar = pg.GradientLegend((20, 150))
        colorbar.setParentItem(self.plot_widget.scene())
        
        # Create gradient
        grad = pg.GradientWidget(orientation='right')
        grad.setGradient({
            0.0: (1, 0, 0),
            0.5: (1, 1, 0),
            1.0: (0, 0, 1)
        })
        
        colorbar.setGradient(grad.gradient)
        
        # Position colorbar
        colorbar.setPos(self.plot_widget.width() - 30, 10)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()