class ArduinoController:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        
    def connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate)
            time.sleep(2)  # Wait for Arduino to initialize
            self.serial.flushInput()
            return True
        except Exception as e:
            raise Exception(f"Failed to connect to Arduino: {str(e)}")
    
    def send_command(self, command):
        """Send a command and get response"""
        if not self.serial or not self.serial.is_open:
            raise Exception("Arduino not connected")
            
        self.serial.write((command + '\n').encode('utf-8'))
        return self.serial.readline().decode().strip()
    
    def check_limits(self):
        """Check status of all limit switches"""
        limit_status = {
            'X_MIN': False, 'X_MAX': False,
            'Y_MIN': False, 'Y_MAX': False,
            'Z_MIN': False, 'Z_MAX': False
        }
        
        try:
            # Send command to check limit switches
            response = self.send_command('M119')  # M119 is standard G-code for endstop status
            
            # Parse response
            for line in response.split('\n'):
                line = line.strip()
                if 'x_min' in line.lower():
                    limit_status['X_MIN'] = 'TRIGGERED' in line
                elif 'x_max' in line.lower():
                    limit_status['X_MAX'] = 'TRIGGERED' in line
                elif 'y_min' in line.lower():
                    limit_status['Y_MIN'] = 'TRIGGERED' in line
                elif 'y_max' in line.lower():
                    limit_status['Y_MAX'] = 'TRIGGERED' in line
                elif 'z_min' in line.lower():
                    limit_status['Z_MIN'] = 'TRIGGERED' in line
                elif 'z_max' in line.lower():
                    limit_status['Z_MAX'] = 'TRIGGERED' in line
                    
            return limit_status
            
        except Exception as e:
            raise Exception(f"Failed to check limit switches: {str(e)}")
    
    def home_axes(self):
        """Execute homing sequence for all axes"""
        try:
            # 1. First stop any ongoing movement
            self.send_command('M410')  # Emergency stop
            time.sleep(0.5)
            
            # 2. Clear emergency stop
            self.send_command('M112')  # Reset
            time.sleep(1)
            
            # 3. Disable stepper motors briefly
            self.send_command('M18')  # Disable steppers
            time.sleep(0.5)
            
            # 4. Enable stepper motors
            self.send_command('M17')  # Enable steppers
            time.sleep(0.5)
            
            # 5. Set relative positioning
            self.send_command('G91')
            
            # 6. Home Z axis first (usually safest)
            self.log("Homing Z axis...")
            response = self.send_command('G28 Z')  # Home Z axis
            if not self._check_homing_success(response):
                raise Exception("Z axis homing failed")
            time.sleep(1)
            
            # 7. Home X axis
            self.log("Homing X axis...")
            response = self.send_command('G28 X')  # Home X axis
            if not self._check_homing_success(response):
                raise Exception("X axis homing failed")
            time.sleep(1)
            
            # 8. Home Y axis
            self.log("Homing Y axis...")
            response = self.send_command('G28 Y')  # Home Y axis
            if not self._check_homing_success(response):
                raise Exception("Y axis homing failed")
            time.sleep(1)
            
            # 9. Set absolute positioning
            self.send_command('G90')
            
            # 10. Move to safe position
            self.send_command('G1 X10 Y10 Z10 F3000')  # Move away from home
            
            return True
            
        except Exception as e:
            self.log(f"Homing error: {str(e)}")
            return False
    
    def _check_homing_success(self, response):
        """Check if homing was successful based on response"""
        # Implement based on your Arduino firmware's response format
        return "ok" in response.lower()
    
    def log(self, message):
        """Log messages for debugging"""
        print(f"Arduino: {message}")