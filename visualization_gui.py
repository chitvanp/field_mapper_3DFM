import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QCheckBox,
                             QFileDialog, QSpinBox)
from PyQt5.QtCore import pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=6, height=6):
        self.fig = Figure(figsize=(width, height))
        super().__init__(self.fig)
        self.setParent(parent)
        self.setup_axes()
        
    def setup_axes(self):
        # Clear the figure first
        self.fig.clear()
        
        # Create 2x2 grid of subplots
        self.axes = []
        for i in range(4):
            ax = self.fig.add_subplot(2, 2, i+1, projection='3d')
            self.axes.append(ax)
            
        self.fig.tight_layout()

class VisualizationTab(QWidget):
    data_processed = pyqtSignal(object)  # Signal to emit processed data
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.colorbars = []  # Keep track of colorbars
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Data loading controls
        load_group = QGroupBox("Load Data")
        load_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Measurement")
        self.load_btn.clicked.connect(self.load_measurement_file)
        load_layout.addWidget(self.load_btn)
        
        self.current_file_label = QLabel("No file loaded")
        load_layout.addWidget(self.current_file_label)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Plot settings
        settings_group = QGroupBox("Plot Settings")
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("Colormap:"))
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(['coolwarm', 'viridis', 'magma', 'plasma'])
        self.cmap_combo.currentTextChanged.connect(self.update_plot)
        settings_layout.addWidget(self.cmap_combo)
        
        self.auto_scale_cb = QCheckBox("Auto Scale")
        self.auto_scale_cb.setChecked(True)
        self.auto_scale_cb.stateChanged.connect(self.update_plot)
        settings_layout.addWidget(self.auto_scale_cb)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Plot canvas
        self.canvas = PlotCanvas(self)
        layout.addWidget(self.canvas)
        
        # Analysis controls
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("Calculate Homogeneity")
        self.analyze_btn.clicked.connect(self.analyze_data)
        analysis_layout.addWidget(self.analyze_btn)
        
        self.analysis_label = QLabel("")
        analysis_layout.addWidget(self.analysis_label)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
    def load_measurement_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Load Measurement", "", "CSV Files (*.csv)")
            
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                self.current_file_label.setText(file_path.split('/')[-1])
                
                # Convert to mT
                for c in ["Bx", "By", "Bz", "Bmod"]:
                    self.df[c] /= 10000
                    
                self.update_plot()
                self.data_processed.emit(self.df)
                
            except Exception as e:
                self.current_file_label.setText(f"Error loading file: {str(e)}")
                
    # def update_plot(self):
    #     if not hasattr(self, 'df'):
    #         return
            
    #     for ax in self.canvas.axes:
    #         ax.clear()
            
    #     components = ['x', 'y', 'z', 'mod']
    #     titles = ['Bx', 'By', 'Bz', 'Bmod']
        
    #     for ax, component, title in zip(self.canvas.axes, components, titles):
    #         scatter = ax.scatter(
    #             self.df['x'], self.df['y'], self.df['z'],
    #             c=self.df[f'B{component}'],
    #             cmap=self.cmap_combo.currentText()
    #         )
    #         plt.colorbar(scatter, ax=ax)
    #         ax.set_title(title)
    #         ax.set_xlabel('x (up/down)')
    #         ax.set_ylabel('y (left/right)')
    #         ax.set_zlabel('z (along bore)')
            
    #     self.canvas.draw()

    # def load_measurement_file(self, file_path=None):
    #     if not file_path:
    #         file_path, _ = QFileDialog.getOpenFileName(self, "Load Measurement", "", "CSV Files (*.csv)")
            
    #     if file_path:
    #         try:
    #             self.df = pd.read_csv(file_path)
    #             self.current_file_label.setText(file_path.split('/')[-1])
                
    #             # Convert to mT
    #             for c in ["Bx", "By", "Bz", "Bmod"]:
    #                 self.df[c] /= 10000
                    
    #             self.update_plot()
    #             self.data_processed.emit(self.df)
                
    #         except Exception as e:
    #             self.current_file_label.setText(f"Error loading file: {str(e)}")
                
    # def update_plot(self):
    #     if not hasattr(self, 'df'):
    #         return
            
    #     # Clear all axes and remove old colorbars
    #     self.canvas.figure.clear()
    #     for cbar in self.colorbars:
    #         cbar.remove()
    #     self.colorbars = []
        
    #     # Create new subplots
    #     self.canvas.axes = []
    #     for i in range(4):
    #         self.canvas.axes.append(self.canvas.figure.add_subplot(2, 2, i+1, projection='3d'))
            
    #     components = ['x', 'y', 'z', 'mod']
    #     titles = ['Bx', 'By', 'Bz', 'Bmod']
        
    #     if self.auto_scale_cb.isChecked():
    #         vmin = vmax = None
    #     else:
    #         vmin = min(self.df[f'B{c}'].min() for c in components)
    #         vmax = max(self.df[f'B{c}'].max() for c in components)
        
    #     for ax, component, title in zip(self.canvas.axes, components, titles):
    #         scatter = ax.scatter(
    #             self.df['x'], self.df['y'], self.df['z'],
    #             c=self.df[f'B{component}'],
    #             cmap=self.cmap_combo.currentText(),
    #             vmin=vmin,
    #             vmax=vmax
    #         )
    #         cbar = plt.colorbar(scatter, ax=ax)
    #         self.colorbars.append(cbar)
    #         ax.set_title(title)
    #         ax.set_xlabel('x (up/down)')
    #         ax.set_ylabel('y (left/right)')
    #         ax.set_zlabel('z (along bore)')
            
    #     self.canvas.figure.tight_layout()
    #     self.canvas.draw()

    def update_plot(self):
        if not hasattr(self, 'df'):
            return
            
        # Store current view angles
        view_angles = []
        for ax in self.canvas.axes:
            view_angles.append((ax.elev, ax.azim))
            
        # Reset the canvas
        self.canvas.setup_axes()
        
        # Clear stored references
        self.scatter_plots = []
        self.colorbars = []
        
        components = ['x', 'y', 'z', 'mod']
        titles = ['Bx', 'By', 'Bz', 'Bmod']
        
        if self.auto_scale_cb.isChecked():
            vmin = vmax = None
        else:
            vmin = min(self.df[f'B{c}'].min() for c in components)
            vmax = max(self.df[f'B{c}'].max() for c in components)
        
        for (ax, component, title, (elev, azim)) in zip(self.canvas.axes, components, titles, view_angles):
            scatter = ax.scatter(
                self.df['x'], self.df['y'], self.df['z'],
                c=self.df[f'B{component}'],
                cmap=self.cmap_combo.currentText(),
                vmin=vmin,
                vmax=vmax
            )
            self.scatter_plots.append(scatter)
            
            # Add colorbar
            cbar = self.canvas.fig.colorbar(scatter, ax=ax)
            self.colorbars.append(cbar)
            
            ax.set_title(title)
            ax.set_xlabel('x (up/down)')
            ax.set_ylabel('y (left/right)')
            ax.set_zlabel('z (along bore)')
            
            # Restore view angle
            ax.view_init(elev, azim)
            
        self.canvas.fig.tight_layout()
        self.canvas.draw()
        
    def analyze_data(self):
        if not hasattr(self, 'df'):
            return
            
        # Calculate field homogeneity
        mean_field = np.mean(self.df['Bmod'])
        std_field = np.std(self.df['Bmod'])
        homogeneity = (std_field / mean_field) * 1e6  # ppm
        
        self.analysis_label.setText(f"Field Homogeneity: {homogeneity:.2f} ppm")
        
    def load_measurement(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Load Measurement", "", "CSV Files (*.csv)")
            
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                self.current_file_label.setText(file_path.split('/')[-1])
                
                # Validate required columns
                required_columns = ["x", "y", "z", "Bx", "By", "Bz", "Bmod"]
                if not all(col in self.df.columns for col in required_columns):
                    raise ValueError(f"CSV must contain columns: {', '.join(required_columns)}")
                
                # Convert to mT
                for c in ["Bx", "By", "Bz", "Bmod"]:
                    self.df[c] /= 10000
                    
                self.update_plot()
                self.data_processed.emit(self.df)
                
            except Exception as e:
                self.current_file_label.setText(f"Error loading file: {str(e)}")
