%"git clone https://github.com/adafruit/Adafruit-Motor-HAT-Pyt..."

% "sudo raspi-config" (activate I2c interface)

% "cd Adafruit-Motor-HAT-Python-Library"

% "sudo python setup.py install"

% "cd examples"

% edit line 20 of StepperTest.py to "myStepper = mh.getStepper(200, 2)"

% python StepperTest.py

while (True)
    print("Single coil steps")
    myStepper.step(100, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.SINGLE)
    myStepper.step(100, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.SINGLE)
    
