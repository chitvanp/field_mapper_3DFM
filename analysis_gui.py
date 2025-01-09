from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QFileDialog)
from PyQt5.QtCore import pyqtSignal
import pandas as pd
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AnalysisTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Data selection
        data_group = QGroupBox("Data Selection")
        data_layout = QHBoxLayout()
        
        self.load_ref_btn = QPushButton("Load Reference Data")
        self.load_ref_btn.clicked.connect(self.load_reference_data)
        data_layout.addWidget(self.load_ref_btn)
        
        self.load_comp_btn = QPushButton("Load Comparison Data")
        self.load_comp_btn.clicked.connect(self.load_comparison_data)
        data_layout.addWidget(self.load_comp_btn)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Analysis type selection
        analysis_group = QGroupBox("Analysis Type")
        analysis_layout = QHBoxLayout()
        
        self.analysis_type = QComboBox()
        self.analysis_type.addItems([
            "Field Homogeneity",
            "Field Differences",
            "Gradient Analysis",
            "Statistical Analysis"
        ])
        self.analysis_type.currentTextChanged.connect(self.update_analysis)
        analysis_layout.addWidget(self.analysis_type)
        
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.perform_analysis)
        analysis_layout.addWidget(self.analyze_btn)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Results display
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        # Table for numerical results
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        results_layout.addWidget(self.results_table)
        
        # Plot for visual results
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        results_layout.addWidget(self.canvas)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Export controls
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout()
        
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_results)
        export_layout.addWidget(self.export_csv_btn)
        
        self.export_plot_btn = QPushButton("Export Plot")
        self.export_plot_btn.clicked.connect(self.export_plot)
        export_layout.addWidget(self.export_plot_btn)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
    def load_reference_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Reference Data", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.ref_data = pd.read_csv(file_path)
                self.update_analysis()
            except Exception as e:
                print(f"Error loading reference data: {str(e)}")
                
    def load_comparison_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Comparison Data", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.comp_data = pd.read_csv(file_path)
                self.update_analysis()
            except Exception as e:
                print(f"Error loading comparison data: {str(e)}")
                
    def load_data(self, data):
        """Called when new data is available from visualization tab"""
        self.ref_data = data
        self.update_analysis()
        
    def update_analysis(self):
        """Update available analysis options based on loaded data"""
        current_analysis = self.analysis_type.currentText()
        self.analyze_btn.setEnabled(
            (current_analysis == "Field Homogeneity" and hasattr(self, 'ref_data')) or
            (current_analysis in ["Field Differences", "Gradient Analysis"] and 
             hasattr(self, 'ref_data') and hasattr(self, 'comp_data'))
        )
        
    def perform_analysis(self):
        """Perform selected analysis type"""
        analysis_type = self.analysis_type.currentText()
        
        if analysis_type == "Field Homogeneity":
            self.analyze_homogeneity()
        elif analysis_type == "Field Differences":
            self.analyze_differences()
        elif analysis_type == "Gradient Analysis":
            self.analyze_gradients()
        elif analysis_type == "Statistical Analysis":
            self.analyze_statistics()
            
    def analyze_homogeneity(self):
        """Analyze field homogeneity"""
        if not hasattr(self, 'ref_data'):
            return
            
        # Calculate homogeneity metrics
        results = {}
        for component in ['Bx', 'By', 'Bz', 'Bmod']:
            mean_val = np.mean(self.ref_data[component])
            std_val = np.std(self.ref_data[component])
            ppm = (std_val / mean_val) * 1e6
            results[f"{component} Mean (mT)"] = mean_val / 10000
            results[f"{component} Std (mT)"] = std_val / 10000
            results[f"{component} Homogeneity (ppm)"] = ppm
            
        self.display_results(results)
        self.plot_homogeneity()
        
    def analyze_differences(self):
        """Analyze differences between two datasets"""
        if not hasattr(self, 'ref_data') or not hasattr(self, 'comp_data'):
            return
            
        # Calculate differences
        results = {}
        for component in ['Bx', 'By', 'Bz', 'Bmod']:
            diff = self.comp_data[component] - self.ref_data[component]
            results[f"{component} Max Diff (mT)"] = np.max(np.abs(diff)) / 10000
            results[f"{component} Mean Diff (mT)"] = np.mean(diff) / 10000
            results[f"{component} RMS Diff (mT)"] = np.sqrt(np.mean(diff**2)) / 10000
            
        self.display_results(results)
        self.plot_differences()
        
    def analyze_gradients(self):
        """Analyze field gradients"""
        if not hasattr(self, 'ref_data'):
            return
            
        # Calculate spatial gradients
        results = {}
        for component in ['Bx', 'By', 'Bz', 'Bmod']:
            dx = np.gradient(self.ref_data[component], self.ref_data['x'])
            dy = np.gradient(self.ref_data[component], self.ref_data['y'])
            dz = np.gradient(self.ref_data[component], self.ref_data['z'])
            
            results[f"{component} Max Gradient (mT/mm)"] = np.max(np.sqrt(dx**2 + dy**2 + dz**2)) / 10000
            
        self.display_results(results)
        self.plot_gradients()
        
    def analyze_statistics(self):
        """Perform statistical analysis"""
        if not hasattr(self, 'ref_data'):
            return
            
        # Calculate statistical metrics
        results = {}
        for component in ['Bx', 'By', 'Bz', 'Bmod']:
            results[f"{component} Mean (mT)"] = np.mean(self.ref_data[component]) / 10000
            results[f"{component} Median (mT)"] = np.median(self.ref_data[component]) / 10000
            results[f"{component} Std (mT)"] = np.std(self.ref_data[component]) / 10000
            results[f"{component} Skewness"] = pd.Series(self.ref_data[component]).skew()
            results[f"{component} Kurtosis"] = pd.Series(self.ref_data[component]).kurtosis()
            
        self.display_results(results)
        self.plot_statistics()
        
    def display_results(self, results):
        """Display results in the table"""
        self.results_table.setRowCount(len(results))
        for i, (metric, value) in enumerate(results.items()):
            self.results_table.setItem(i, 0, QTableWidgetItem(metric))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{value:.6f}"))
            
    def plot_homogeneity(self):
        """Plot homogeneity analysis results"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        scatter = ax.scatter(
            self.ref_data['x'], self.ref_data['y'], self.ref_data['z'],
            c=self.ref_data['Bmod'],
            cmap='coolwarm'
        )
        self.figure.colorbar(scatter)
        ax.set_title('Field Magnitude Distribution')
        self.canvas.draw()
        
    def plot_differences(self):
        """Plot difference analysis results"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        diff = self.comp_data['Bmod'] - self.ref_data['Bmod']
        scatter = ax.scatter(
            self.ref_data['x'], self.ref_data['y'], self.ref_data['z'],
            c=diff,
            cmap='coolwarm'
        )
        self.figure.colorbar(scatter)
        ax.set_title('Field Magnitude Differences')
        self.canvas.draw()
        
    def plot_gradients(self):
        """Plot gradient analysis results"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        dx = np.gradient(self.ref_data['Bmod'], self.ref_data['x'])
        dy = np.gradient(self.ref_data['Bmod'], self.ref_data['y'])
        dz = np.gradient(self.ref_data['Bmod'], self.ref_data['z'])
        grad_mag = np.sqrt(dx**2 + dy**2 + dz**2)
        scatter = ax.scatter(
            self.ref_data['x'], self.ref_data['y'], self.ref_data['z'],
            c=grad_mag,
            cmap='coolwarm'
        )
        self.figure.colorbar(scatter)
        ax.set_title('Field Gradient Magnitude')
        self.canvas.draw()
        
    def plot_statistics(self):
        """Plot statistical analysis results"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        components = ['Bx', 'By', 'Bz', 'Bmod']
        for component in components:
            ax.hist(self.ref_data[component]/10000, bins=50, alpha=0.5, label=component)
        ax.set_xlabel('Field (mT)')
        ax.set_ylabel('Count')
        ax.set_title('Field Component Distributions')
        ax.legend()
        self.canvas.draw()
        
    def export_results(self):
        """Export analysis results to CSV"""
        if self.results_table.rowCount() == 0:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "CSV Files (*.csv)")
        if file_path:
            results = {}
            for i in range(self.results_table.rowCount()):
                metric = self.results_table.item(i, 0).text()
                value = float(self.results_table.item(i, 1).text())
                results[metric] = value
            pd.Series(results).to_csv(file_path)
            
    def export_plot(self):
        """Export current plot to file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Files (*.png)")
        if file_path:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')