import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from path_generator_gui import PathGeneratorTab
from measurement_gui import MeasurementTab
from visualization_gui import VisualizationTab
from analysis_gui import AnalysisTab
from settings_gui import SettingsTab

class MagneticFieldMapperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnetic Field Mapper")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add tabs
        self.path_generator_tab = PathGeneratorTab()
        self.measurement_tab = MeasurementTab()
        self.visualization_tab = VisualizationTab()
        self.analysis_tab = AnalysisTab()
        self.settings_tab = SettingsTab()
        
        self.tabs.addTab(self.path_generator_tab, "Path Generator")
        self.tabs.addTab(self.measurement_tab, "Measurement")
        self.tabs.addTab(self.visualization_tab, "Visualization")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        layout.addWidget(self.tabs)
        
        # Connect signals between tabs
        self.setup_connections()
        
    def setup_connections(self):
        # Connect path generator to measurement tab
        self.path_generator_tab.path_generated.connect(self.measurement_tab.load_path)
        
        # Connect measurement to visualization tab
        self.measurement_tab.measurement_completed.connect(self.visualization_tab.load_measurement)
        
        # Connect visualization to analysis tab
        self.visualization_tab.data_processed.connect(self.analysis_tab.load_data)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MagneticFieldMapperGUI()
    window.show()
    sys.exit(app.exec_())