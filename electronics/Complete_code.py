#Start stop button
# Starts driving
# Detects plant -> stops

# Arm phase:
    # Arm starts extending (grit wise) to position 1
    # Humidity signal Y that was send is read for specific plant
    # solenoid valve opens for X amount of time based on read signal Y
    # Arm exstends to position 2
    # Solenoid valve opens for X amount of time based on read signal Y
    # Arm retracts

# Arm rotates 180 degrees
# Repeat arm phase

# Motor starts driving again
# Detects plant -> stops

#repeat the above until:
# end of table is reached? or after X amount of distance?

# ====================================================
# Import files
# ====================================================

    # Imports for DC motor + distance sensor
    #=======================================
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

    # Import files for Servos
    # =====================================
from time import *
from adafruit_servokit import ServoKit


# =====================================================
# PIN LAYOUT
# =====================================================

# Motor 1
IN1_M1 = 17
IN2_M1 = 27
EN_M1  = 18   # PWM for motor 1

# Motor 2
IN1_M2 = 22
IN2_M2 = 25
EN_M2  = 13   # PWM for motor 2

# HC-SR04 pins (distance sensor)
TRIG = 20
ECHO = 21

# Motor pin setup
motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)

# Ultrasone sensor pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# PWM setup
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)
pwm1.start(0)
pwm2.start(0)

# =====================================================
# MOTOR FUNCTIES
# =====================================================

def motors_forward(speed):
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)

    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)

def motors_stop():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.LOW)

# =====================================================
# Distance function HC-SR04
# =====================================================

def measured_distance():
    # Trigger puls
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Wait for echo to start
    start_time = time.time()
    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    # Wait for echo to end
    stop_time = time.time()
    while GPIO.input(ECHO) == 1:
        stop_time = time.time()

    # Time difference
    time_elapsed = stop_time - start_time

    # Speed of sound: 34300 cm/s
    distance = (time_elapsed * 34300) / 2

    return distance

# =====================================================
# Servo initialising fuctions
# =====================================================
#Below is an initialising statement stating that we will have access to 16 PWM channels of the HAT and to summon them we will use | kit |
kit = ServoKit(channels=16)

#Below desides the initial angle that the servo which is attatched to Port 0 will be. In this case we will make it zero degrees.
kit.servo[0].angle = 0
kit.servo[2].angle = 90

# =====================================================
# MAIN LOOP Motor
# =====================================================

try:
    print("Robot automatically starts driving forward.")
    motors_forward(40)  # 40% speed

    while True:
        distance = measured_distance()
        print(f"distance: {distance:.1f} cm")

        if distance < 15: # 15cm stop distance 
            print("!!! Obstacle detected within Xcm — STOP !!!")
            motors_stop()
            break

        time.sleep(0.1)

except KeyboardInterrupt:
    pass

motors_stop()
#GPIO.cleanup()
print("Programme stopped.")

# =====================================================
# ARM phase/loop
# =====================================================

# Rotating the arm Centre to Left
# ======================
while True:
#Below will rotate the Standard servo to the 180 degree point
        kit.servo[2].angle = -90
#Below will make the system wait for 3 seconds
        sleep(3) 


# Extending the arm
#=====================

#Below will make the system wait for 3 seconds
        sleep(3)

#Below will rotate the Standard servo to the 180 degree point
        kit.servo[0].angle = 180
#Below will make the system wait for 3 seconds
        sleep(3) 
#Below will rotate the Standard servo to the 180 degree point
        kit.servo[0].angle = 0


# ======================
# Rotating the arm Left to Right
# ======================
#Below will make the system wait for 3 seconds
        sleep(3)

#Below will rotate the Standard servo to the 180 degree point
        kit.servo[2].angle = 180
#Below will make the system wait for 3 seconds
        sleep(3) 

# ======================
# Rotating the arm Right to Centre
# ======================
#Below will make the system wait for 3 seconds
        sleep(3)

#Below will rotate the Standard servo to the 180 degree point
        kit.servo[2].angle = -90
#Below will make the system wait for 3 seconds
        sleep(3) 


# ======================
# Motor phase again
# ======================