from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QRadioButton, QSpinBox, QDoubleSpinBox, QPushButton, 
                             QLabel, QFileDialog, QComboBox)
from PyQt5.QtCore import pyqtSignal
import numpy as np
from path_generator import PathGenerator
import pandas as pd

class PathGeneratorTab(QWidget):
    path_generated = pyqtSignal(str)  # Signal to emit when path is generated
    
    def __init__(self):
        super().__init__()
        self.path_generator = PathGenerator()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Path Type Selection
        type_group = QGroupBox("Path Type")
        type_layout = QVBoxLayout()
        
        self.cube_radio = QRadioButton("Cube")
        self.sphere_radio = QRadioButton("Sphere")
        self.custom_radio = QRadioButton("Custom (from CSV)")
        self.cube_radio.setChecked(True)
        
        type_layout.addWidget(self.cube_radio)
        type_layout.addWidget(self.sphere_radio)
        type_layout.addWidget(self.custom_radio)
        type_group.setLayout(type_layout)
        
        # Parameters Group
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout()
        
        # Cube parameters
        self.cube_params = QWidget()
        cube_layout = QHBoxLayout()
        cube_layout.addWidget(QLabel("Size (mm):"))
        self.cube_size = QDoubleSpinBox()
        self.cube_size.setRange(1, 1000)
        self.cube_size.setValue(20)
        cube_layout.addWidget(self.cube_size)
        cube_layout.addWidget(QLabel("Points per side:"))
        self.cube_points = QSpinBox()
        self.cube_points.setRange(2, 100)
        self.cube_points.setValue(5)
        cube_layout.addWidget(self.cube_points)
        self.cube_params.setLayout(cube_layout)
        
        # Sphere parameters
        self.sphere_params = QWidget()
        sphere_layout = QHBoxLayout()
        sphere_layout.addWidget(QLabel("Radius (mm):"))
        self.sphere_radius = QDoubleSpinBox()
        self.sphere_radius.setRange(1, 1000)
        self.sphere_radius.setValue(35)
        sphere_layout.addWidget(self.sphere_radius)
        sphere_layout.addWidget(QLabel("Points (theta):"))
        self.sphere_points_theta = QSpinBox()
        self.sphere_points_theta.setRange(4, 100)
        self.sphere_points_theta.setValue(20)
        sphere_layout.addWidget(self.sphere_points_theta)
        sphere_layout.addWidget(QLabel("Points (phi):"))
        self.sphere_points_phi = QSpinBox()
        self.sphere_points_phi.setRange(4, 100)
        self.sphere_points_phi.setValue(20)
        sphere_layout.addWidget(self.sphere_points_phi)
        self.sphere_params.setLayout(sphere_layout)
        
        # Custom path parameters
        self.custom_params = QWidget()
        custom_layout = QHBoxLayout()
        self.csv_path_button = QPushButton("Select CSV")
        self.csv_path_button.clicked.connect(self.select_csv)
        custom_layout.addWidget(self.csv_path_button)
        self.custom_params.setLayout(custom_layout)
        
        # Add parameter widgets
        params_layout.addWidget(self.cube_params)
        params_layout.addWidget(self.sphere_params)
        params_layout.addWidget(self.custom_params)
        params_group.setLayout(params_layout)
        
        # Common parameters
        common_group = QGroupBox("Common Parameters")
        common_layout = QHBoxLayout()
        common_layout.addWidget(QLabel("Measurements per position:"))
        self.measurements_per_pos = QSpinBox()
        self.measurements_per_pos.setRange(1, 100)
        self.measurements_per_pos.setValue(1)
        common_layout.addWidget(self.measurements_per_pos)
        common_group.setLayout(common_layout)
        
        # Generate button
        self.generate_button = QPushButton("Generate Path")
        self.generate_button.clicked.connect(self.generate_path)
        self.preview_btn = QPushButton("Preview Path")
        self.preview_btn.clicked.connect(self.preview_path)
        
        # Add all widgets to main layout
        layout.addWidget(type_group)
        layout.addWidget(params_group)
        layout.addWidget(common_group)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.preview_btn)
        
        # Connect radio buttons
        self.cube_radio.toggled.connect(self.update_params_visibility)
        self.sphere_radio.toggled.connect(self.update_params_visibility)
        self.custom_radio.toggled.connect(self.update_params_visibility)
        
        # Initial visibility
        self.update_params_visibility()
        
    def update_params_visibility(self):
        self.cube_params.setVisible(self.cube_radio.isChecked())
        self.sphere_params.setVisible(self.sphere_radio.isChecked())
        self.custom_params.setVisible(self.custom_radio.isChecked())
        
    def select_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.csv_path = file_name
            self.csv_path_button.setText(file_name.split('/')[-1])
            
    def generate_path(self):
        try:
            if self.cube_radio.isChecked():
                df = self.path_generator.generate_cube_path(
                    size_mm=self.cube_size.value(),
                    points_per_side=self.cube_points.value(),
                    measurements_per_pos=self.measurements_per_pos.value()
                )
                output_file = f"movement_paths/cube_{self.cube_size.value()}mm_{self.cube_points.value()}pts.csv"

            elif self.sphere_radio.isChecked():
                df = self.path_generator.generate_sphere_path(
                    radius=self.sphere_radius.value(),
                    num_points_theta=self.sphere_points_theta.value(),
                    num_points_phi=self.sphere_points_phi.value(),
                    measurements_per_pos=self.measurements_per_pos.value()
                )
                output_file = f"movement_paths/sphere_{self.sphere_radius.value()}mm_{self.sphere_points_theta.value()}x{self.sphere_points_phi.value()}pts.csv"

            elif self.custom_radio.isChecked() and hasattr(self, 'csv_path'):
                df = pd.read_csv(self.csv_path)  # Ensure CSV is loaded properly
                output_file = f"movement_paths/custom_{self.csv_path.split('/')[-1]}"

            else:
                raise ValueError("No valid path type selected or CSV not provided for custom path.")

            df.to_csv(output_file, index=False)
            self.path_generated.emit(output_file)

        except Exception as e:
            print(f"Error generating path: {str(e)}")


    def preview_path(self):
        try:
            if self.cube_radio.isChecked():
                df = self.path_generator.generate_cube_path(
                    size_mm=self.cube_size.value(),
                    points_per_side=self.cube_points.value(),
                    measurements_per_pos=self.measurements_per_pos.value()
                )
            elif self.sphere_radio.isChecked():
                df = self.path_generator.generate_sphere_path(
                    radius=self.sphere_radius.value(),
                    num_points_theta=self.sphere_points_theta.value(),
                    num_points_phi=self.sphere_points_phi.value(),
                    measurements_per_pos=self.measurements_per_pos.value()
                )
            else:
                raise ValueError("Invalid path type selected for preview.")
            
            # Plot Preview
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(df['x'], df['y'], df['z'], c='blue', marker='o')
            ax.set_title('Path Preview')
            ax.set_xlabel('x (up/down)')
            ax.set_ylabel('y (left/right)')
            ax.set_zlabel('z (along bore)')
            plt.show()
            
        except Exception as e:
            print(f"Error previewing path: {str(e)}")

