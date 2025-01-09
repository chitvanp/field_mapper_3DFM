from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                             QLineEdit, QCheckBox, QComboBox)
from PyQt5.QtCore import pyqtSignal
import json
import os

class SettingsTab(QWidget):
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.settings_file = "config/settings.json"
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Hardware Settings
        hw_group = QGroupBox("Hardware Settings")
        hw_layout = QVBoxLayout()
        
        # CNC Settings
        cnc_layout = QHBoxLayout()
        cnc_layout.addWidget(QLabel("Step Sizes (mm):"))
        
        self.dx_spin = QDoubleSpinBox()
        self.dx_spin.setRange(0.0001, 10.0)
        self.dx_spin.setValue(0.6402)
        self.dx_spin.setDecimals(4)
        cnc_layout.addWidget(QLabel("dx:"))
        cnc_layout.addWidget(self.dx_spin)
        
        self.dy_spin = QDoubleSpinBox()
        self.dy_spin.setRange(0.0001, 10.0)
        self.dy_spin.setValue(0.6415)
        self.dy_spin.setDecimals(4)
        cnc_layout.addWidget(QLabel("dy:"))
        cnc_layout.addWidget(self.dy_spin)
        
        self.dz_spin = QDoubleSpinBox()
        self.dz_spin.setRange(0.0001, 10.0)
        self.dz_spin.setValue(0.1596)
        self.dz_spin.setDecimals(4)
        cnc_layout.addWidget(QLabel("dz:"))
        cnc_layout.addWidget(self.dz_spin)
        
        hw_layout.addLayout(cnc_layout)
        
        # Feed rate
        feed_layout = QHBoxLayout()
        feed_layout.addWidget(QLabel("Feed Rate:"))
        self.feed_rate = QSpinBox()
        self.feed_rate.setRange(1000, 1000000)
        self.feed_rate.setValue(100000)
        feed_layout.addWidget(self.feed_rate)
        hw_layout.addLayout(feed_layout)
        
        hw_group.setLayout(hw_layout)
        layout.addWidget(hw_group)
        
        # Measurement Settings
        meas_group = QGroupBox("Measurement Settings")
        meas_layout = QVBoxLayout()
        
        # Default delays
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Default Delay (s):"))
        self.default_delay = QDoubleSpinBox()
        self.default_delay.setRange(0.1, 10.0)
        self.default_delay.setValue(0.5)
        self.default_delay.setDecimals(1)
        delay_layout.addWidget(self.default_delay)
        meas_layout.addLayout(delay_layout)
        
        # Long move delay
        long_delay_layout = QHBoxLayout()
        long_delay_layout.addWidget(QLabel("Long Move Delay (s):"))
        self.long_move_delay = QDoubleSpinBox()
        self.long_move_delay.setRange(0.1, 10.0)
        self.long_move_delay.setValue(3.0)
        self.long_move_delay.setDecimals(1)
        long_delay_layout.addWidget(self.long_move_delay)
        meas_layout.addLayout(long_delay_layout)
        
        # Long move threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Long Move Threshold (mm):"))
        self.move_threshold = QDoubleSpinBox()
        self.move_threshold.setRange(1.0, 100.0)
        self.move_threshold.setValue(10.0)
        self.move_threshold.setDecimals(1)
        threshold_layout.addWidget(self.move_threshold)
        meas_layout.addLayout(threshold_layout)
        
        # Default magnetometer settings
        mag_layout = QHBoxLayout()
        mag_layout.addWidget(QLabel("Default Range:"))
        self.default_range = QComboBox()
        self.default_range.addItems(["0.1T", "0.3T", "1T", "3T"])
        mag_layout.addWidget(self.default_range)
        
        mag_layout.addWidget(QLabel("Default Average:"))
        self.default_average = QSpinBox()
        self.default_average.setRange(1, 100000)
        self.default_average.setValue(30000)
        mag_layout.addWidget(self.default_average)
        meas_layout.addLayout(mag_layout)
        
        meas_group.setLayout(meas_layout)
        layout.addWidget(meas_group)
        
        # File Settings
        file_group = QGroupBox("File Settings")
        file_layout = QVBoxLayout()
        
        # Default directories
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Path Directory:"))
        self.path_dir = QLineEdit("movement_paths/")
        path_layout.addWidget(self.path_dir)
        file_layout.addLayout(path_layout)
        
        meas_dir_layout = QHBoxLayout()
        meas_dir_layout.addWidget(QLabel("Measurement Directory:"))
        self.meas_dir = QLineEdit("measurements/")
        meas_dir_layout.addWidget(self.meas_dir)
        file_layout.addLayout(meas_dir_layout)
        
        # Auto-save settings
        self.auto_save = QCheckBox("Auto-save measurements")
        self.auto_save.setChecked(True)
        file_layout.addWidget(self.auto_save)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("Load Settings")
        self.load_btn.clicked.connect(self.load_settings)
        button_layout.addWidget(self.load_btn)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
    def get_settings(self):
        """Get current settings as dictionary"""
        return {
            "hardware": {
                "step_sizes": {
                    "dx": self.dx_spin.value(),
                    "dy": self.dy_spin.value(),
                    "dz": self.dz_spin.value()
                },
                "feed_rate": self.feed_rate.value()
            },
            "measurement": {
                "default_delay": self.default_delay.value(),
                "long_move_delay": self.long_move_delay.value(),
                "move_threshold": self.move_threshold.value(),
                "default_range": self.default_range.currentText(),
                "default_average": self.default_average.value()
            },
            "files": {
                "path_directory": self.path_dir.text(),
                "measurement_directory": self.meas_dir.text(),
                "auto_save": self.auto_save.isChecked()
            }
        }
        
    def apply_settings(self, settings):
        """Apply settings from dictionary"""
        try:
            # Hardware settings
            hw = settings["hardware"]
            self.dx_spin.setValue(hw["step_sizes"]["dx"])
            self.dy_spin.setValue(hw["step_sizes"]["dy"])
            self.dz_spin.setValue(hw["step_sizes"]["dz"])
            self.feed_rate.setValue(hw["feed_rate"])
            
            # Measurement settings
            meas = settings["measurement"]
            self.default_delay.setValue(meas["default_delay"])
            self.long_move_delay.setValue(meas["long_move_delay"])
            self.move_threshold.setValue(meas["move_threshold"])
            self.default_range.setCurrentText(meas["default_range"])
            self.default_average.setValue(meas["default_average"])
            
            # File settings
            files = settings["files"]
            self.path_dir.setText(files["path_directory"])
            self.meas_dir.setText(files["measurement_directory"])
            self.auto_save.setChecked(files["auto_save"])
            
            self.settings_changed.emit(settings)
            
        except Exception as e:
            print(f"Error applying settings: {str(e)}")
            
    def save_settings(self):
        """Save current settings to file"""
        try:
            os.makedirs("config", exist_ok=True)
            settings = self.get_settings()
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                self.apply_settings(settings)
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            
    def reset_settings(self):
        """Reset settings to defaults"""
        default_settings = {
            "hardware": {
                "step_sizes": {
                    "dx": 0.6402,
                    "dy": 0.6415,
                    "dz": 0.1596
                },
                "feed_rate": 100000
            },
            "measurement": {
                "default_delay": 0.5,
                "long_move_delay": 3.0,
                "move_threshold": 10.0,
                "default_range": "0.1T",
                "default_average": 30000
            },
            "files": {
                "path_directory": "movement_paths/",
                "measurement_directory": "measurements/",
                "auto_save": True
            }
        }
        self.apply_settings(default_settings)