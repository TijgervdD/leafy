#Final beast
state = 0  # global statemachine variable
speed = 80  # global motor speed setting
wateringTime = 2  # defining start value wateringTime
humidity = 0  # define start value humidity

# Import files
import RPi.GPIO as GPIO
import time
from time import *
from adafruit_servokit import ServoKit
import sys
import time
import os
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

# ==============================================================================
# PIN layout and initial setup
# HC-SR04 pins (sonar sensor)
TRIG1 = 5
ECHO1 = 6

TRIG2 = 12
ECHO2 = 13


# relais pin / Solenoid valve
RELAY_PIN = 19
START_BUTTON_PIN = 16
STOP_BUTTON_PIN = 21

# --- PIN DEFINITIONS ---
IN1_M1, IN2_M1, EN_M1 = 23, 22, 24
IN1_M2, IN2_M2, EN_M2 = 27, 18, 17

# Create a master list of ALL pins used in the script
# This ensures we don't miss any or double-up
output_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2, TRIG1, TRIG2, RELAY_PIN]
input_pins = [ECHO1, ECHO2, START_BUTTON_PIN, STOP_BUTTON_PIN]

# --- PHYSICAL SETUP (Do this ONLY once) ---
# 1. Clean up any previous "stuck" allocations
try:
    GPIO.cleanup()
except:
    pass

GPIO.setmode(GPIO.BCM)

# 2. Setup all outputs in one go
for pin in output_pins:
    GPIO.setup(pin, GPIO.OUT)

# 3. Setup all inputs in one go
for pin in input_pins:
    # Note: Trigger and Echo don't usually need pull-ups, 
    # but buttons definitely do.
    if pin in [START_BUTTON_PIN, STOP_BUTTON_PIN]:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    else:
        GPIO.setup(pin, GPIO.IN)

# 4. Initialize PWM (This links to the EN pins already set as OUT)
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)

#################
# Initialising statement stating that we will have access to 16 PWM channels of the HAT and to summon them we will use | kit |
kit = ServoKit(channels=16)

# Track current angle of extend servo (servo[1])


# =====================================================================================

def initialize():
    global current_extend_angle, current_rotate_angle
    # initialize the system
    # initializing the start speed of the DC motors
    pwm1.start(0)
    pwm2.start(0)

    # Deciding the initial angle that the servos will be
    sleep(0.5)
    #current_extend_angle = 0
    #sleep(2)
    #current_rotate_angle = 90
    kit.servo[1].angle = 0   # extend servo
    sleep(0.5)
    kit.servo[0].angle = 90   # rotate servo

    current_extend_angle = 0  # keep software in sync
    current_rotate_angle = 90  # keep software in sync

emergency_triggered = False

def eStop(channel=None):
    global state, emergency_triggered
    print("\n!!! EMERGENCY STOP TRIGGERED !!!")
    
    # Set the flag so the main loop knows to stop
    emergency_triggered = True
    
    # Physical stop actions
    #stopDriving()
    #sleep(2)
    #extendArm(0)
    #sleep(2)
    #rotateArm(90)
    
    # OPTION A: Kill the program entirely (Safest)
    print("Shutting down program for safety...")
    os._exit(0)

#GPIO.add_event_detect(
#        STOP_BUTTON_PIN,
#        GPIO.FALLING,
#        callback=eStop,
#        bouncetime=200
#    )

def measuringDistance1():
    # Distance sensor initialization - sensor measuring that a plant is nearby
    # Trigger pulse
    GPIO.output(TRIG1, True)
    time.sleep(0.00001)
    GPIO.output(TRIG1, False)

    # Waiting on echo start
    start_time = time.time()
    while GPIO.input(ECHO1) == 0:
        start_time = time.time()

    # Waiting on echo end
    stop_time = time.time()
    while GPIO.input(ECHO1) == 1:
        stop_time = time.time()

    # Time difference
    time_elapsed = stop_time - start_time

    # Speed of sound: 34300 cm/s
    distance1 = (time_elapsed * 34300) / 2

    return distance1

def measuringDistance2():
    # Distance sensor initialization - sensor measuring that a plant is nearby
    # Trigger pulse
    GPIO.output(TRIG2, True)
    time.sleep(0.00001)
    GPIO.output(TRIG2, False)

    # Waiting on echo start
    start_time = time.time()
    while GPIO.input(ECHO2) == 0:
        start_time = time.time()

    # Waiting on echo end
    stop_time = time.time()
    while GPIO.input(ECHO2) == 1:
        stop_time = time.time()

    # Time difference
    time_elapsed = stop_time - start_time

    # Speed of sound: 34300 cm/s
    distance2 = (time_elapsed * 34300) / 2

    return distance2

def plantFound():
    global state
    while True:
        distance1 = measuringDistance1()
        distance2 = measuringDistance2()
        
        print(f"Dist 1: {distance1:.1f} cm | Dist 2: {distance2:.1f} cm")

        # Specific check for Sensor 1
        if distance1 < 10:
            print("!!! PLANT DETECTED — STOPPING !!!")
            sleep(1)
            stopDriving()
            break
        
        # Specific check for Sensor 2
        elif distance2 > 80:
            print("!!! END OF TABLE DETECTED — STOP !!!")
            stopDriving()
            os._exit(0)
            break

        time.sleep(0.1)

def startDrivingF():
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)

    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)

def startDrivingB():
    # Motor 1
    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.HIGH)
    pwm1.ChangeDutyCycle(speed)

    # Motor 2
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.HIGH)
    pwm2.ChangeDutyCycle(speed)

def stopDriving():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.LOW)

def rotateArm(target_angle, step=1, delay=0.1):
    """
    Slowly extend/retract the arm on servo[1].
    Moves from current_extend_angle to target_angle in small steps.
    step  = degrees per step (smaller = smoother/slower)
    delay = seconds between steps (larger = slower)
    """
    global current_rotate_angle

    start = int(current_rotate_angle)
    end = int(target_angle)

    if end > start:
        angle_range = range(start, end + 1, step)
    else:
        angle_range = range(start, end - 1, -step)

    for angle in angle_range:
        kit.servo[0].angle = angle
        time.sleep(delay)

    current_rotate_angle = target_angle

    # control servo to move arm to pos (instant move)
    #kit.servo[0].angle = pos

def extendArm(target_angle, step=1, delay=0.02):
    """
    Slowly extend/retract the arm on servo[1].
    Moves from current_extend_angle to target_angle in small steps.
    step  = degrees per step (smaller = smoother/slower)
    delay = seconds between steps (larger = slower)
    """
    global current_extend_angle

    start = int(current_extend_angle)
    end = int(target_angle)

    if end > start:
        angle_range = range(start, end + 1, step)
    else:
        angle_range = range(start, end - 1, -step)

    for angle in angle_range:
        kit.servo[1].angle = angle
        time.sleep(delay)

    current_extend_angle = target_angle

def retractArm(pos):
    kit.servo[1].angle = pos

def solenoidValveOpen():
    # If your relay is 'Active Low', use GPIO.LOW to turn it on
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Valve is Open")

def solenoidValveClosed():
    # Use GPIO.HIGH to turn it off
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("Valve is Closed")

def wateringPlant():
    sleep(1)
    solenoidValveOpen()
    sleep(wateringTime)  # wateringTime
    print(f"Watering time: {wateringTime}")
    solenoidValveClosed()
    sleep(1)

# =========================================================================================
# LOOP
while True:
    # if GPIO.input(STOP_BUTTON_PIN) == GPIO.LOW:  # Button pressed
    #     print("Emergency STOP button was pressed!")
    #     eStop()

    match state:
        case 0:
            initialize()
            sleep(1)
            state = 10

        case 10:  # Standby, wait for start command
            print("Waiting for initialization")
            if GPIO.input(START_BUTTON_PIN) == GPIO.LOW:  # Button pressed
                print("Programme is initiated!")
                state = 20

        case 20:  # Start driving until reached a plant
            startDrivingB()
            state = 30

        case 30:  # Driving stops because plant is reached
            print("looking for plants!")
            plantFound()
            sleep(3)
            state = 40

        case 40:  # Arm is rotated outward to Left
            rotateArm(0)
            sleep(3)
            state = 50

        case 50:
            extendArm(120)# Arm is extended to first position (slowly)
            sleep(3)
            state = 80

        case 60:
            wateringPlant()  # Solenoid valve opens and water goes to plant
            state = 51

        case 51:
            extendArm(140) # Arm is extended further (slowly)
            sleep(3)
            state = 71

        case 71:
            wateringPlant()  # Solenoid valve opens and water goes to plant
            state = 80

        case 80:
            retractArm(0)  # Arm retract (slowly)
            state = 90

        case 90:
            rotateArm(90)
            state = 20

        case 999:
            exit()