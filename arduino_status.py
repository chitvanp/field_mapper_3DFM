from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel)
from PyQt5.QtCore import QTimer

class ArduinoStatusWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Arduino Status", parent)
        self.setup_ui()
        self._setup_timer()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Limit switch status
        limit_group = QGroupBox("Limit Switches")
        limit_layout = QGridLayout()
        
        # Create indicators for each limit switch
        self.limit_indicators = {}
        positions = [
            ('X_MIN', 0, 0), ('X_MAX', 0, 1),
            ('Y_MIN', 1, 0), ('Y_MAX', 1, 1),
            ('Z_MIN', 2, 0), ('Z_MAX', 2, 1)
        ]
        
        for name, row, col in positions:
            label = QLabel(name)
            indicator = QLabel('⚪')  # White circle for not triggered
            self.limit_indicators[name] = indicator
            limit_layout.addWidget(label, row, col*2)
            limit_layout.addWidget(indicator, row, col*2+1)
            
        limit_group.setLayout(limit_layout)
        layout.addWidget(limit_group)
        
        # Position information
        pos_group = QGroupBox("Current Position")
        pos_layout = QHBoxLayout()
        
        self.pos_labels = {}
        for axis in ['X', 'Y', 'Z']:
            label = QLabel(f"{axis}:")
            value = QLabel("0.000")
            self.pos_labels[axis] = value
            pos_layout.addWidget(label)
            pos_layout.addWidget(value)
            
        pos_group.setLayout(pos_layout)
        layout.addWidget(pos_group)
        
    def _setup_timer(self):
        """Setup timer for periodic status updates"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
        
    def update_status(self):
        """Update status displays"""
        if hasattr(self, 'arduino'):
            try:
                # Update limit switch status
                limits = self.arduino.check_limits()
                for name, triggered in limits.items():
                    self.limit_indicators[name].setText('🔴' if triggered else '⚪')
                    
                # Could add position updating here if your Arduino firmware supports it
                
            except Exception as e:
                print(f"Error updating status: {str(e)}")
                
    def set_arduino(self, arduino):
        """Set the Arduino controller instance"""
        self.arduino = arduino