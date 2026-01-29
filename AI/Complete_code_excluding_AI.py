# Final beast with watering formula
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
from pyrf24 import RF24, RF24_PA_MIN
import os
import numpy as np

GPIO.setmode(GPIO.BCM)

# ==============================================================================

# Motor 1
IN1_M1 = 23
IN2_M1 = 22
EN_M1 = 24

# Motor 2
IN1_M2 = 27
IN2_M2 = 18
EN_M2 = 17

# Setup pins
motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)

# PWM setup
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)

# ServoKit
kit = ServoKit(channels=16)

# Track current servo angles
current_extend_angle = 0
current_rotate_angle = 90

# Radio setup
radio = RF24(25, 0)
address = b"0001\x00"

# HC-SR04 pins
TRIG1, ECHO1 = 5, 6
TRIG2, ECHO2 = 12, 13
GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)

# Solenoid valve and buttons
RELAY_PIN = 21
START_BUTTON_PIN = 20
STOP_BUTTON_PIN = 16
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(STOP_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# =================================
# WATER FORMULA INTEGRATION
# =================================
SOIL_HUMIDITY = 75.0  # fixed soil humidity
GREEN_PERCENT = 20.0  # fixed green ratio


def predict_water(humidity, greenery):
    return 261.83 - humidity * 3.13314695 + greenery * 2.13997997


def valve_open_time_ml(V_ml):
    a = 0.11455309
    b = 36.75567689
    c = 19.817595 - V_ml

    disc = b ** 2 - 4 * a * c
    if disc < 0:
        return None

    return (-b + np.sqrt(disc)) / (2 * a)


def compute_watering_time():
    water_ml = predict_water(SOIL_HUMIDITY, GREEN_PERCENT)
    valve_time = valve_open_time_ml(water_ml)

    if valve_time is None or valve_time < 0:
        valve_time = 0

    print(f"Computed watering: {water_ml:.2f} ml -> Valve open {valve_time:.2f} s")
    return valve_time


# =================================
# INITIALIZATION
# =================================
def initialize():
    global current_extend_angle, current_rotate_angle
    pwm1.start(0)
    pwm2.start(0)
    sleep(2)
    kit.servo[0].angle = 90
    sleep(2)
    kit.servo[1].angle = 0
    current_extend_angle = 0
    current_rotate_angle = 90


# =================================
# EMERGENCY STOP
# =================================
emergency_triggered = False


def eStop(channel=None):
    global state, emergency_triggered
    print("\n!!! EMERGENCY STOP TRIGGERED !!!")
    emergency_triggered = True
    stopDriving()
    sleep(2)
    extendArm(0)
    print("Shutting down program for safety...")
    os._exit(0)


GPIO.add_event_detect(
    STOP_BUTTON_PIN,
    GPIO.FALLING,
    callback=eStop,
    bouncetime=200
)


# =================================
# DISTANCE MEASURE FUNCTIONS
# =================================
def measuringDistance1():
    GPIO.output(TRIG1, True)
    sleep(0.00001)
    GPIO.output(TRIG1, False)

    start_time = time.time()
    while GPIO.input(ECHO1) == 0:
        start_time = time.time()

    stop_time = time.time()
    while GPIO.input(ECHO1) == 1:
        stop_time = time.time()

    time_elapsed = stop_time - start_time
    return (time_elapsed * 34300) / 2


def measuringDistance2():
    GPIO.output(TRIG2, True)
    sleep(0.00001)
    GPIO.output(TRIG2, False)

    start_time = time.time()
    while GPIO.input(ECHO2) == 0:
        start_time = time.time()

    stop_time = time.time()
    while GPIO.input(ECHO2) == 1:
        stop_time = time.time()

    time_elapsed = stop_time - start_time
    return (time_elapsed * 34300) / 2


def plantFound():
    global state
    while True:
        distance1 = measuringDistance1()
        distance2 = measuringDistance2()
        print(f"Dist 1: {distance1:.1f} cm | Dist 2: {distance2:.1f} cm")

        if distance1 < 5:
            print("!!! PLANT DETECTED — STOPPING !!!")
            stopDriving()
            break
        elif distance2 < 5:
            print("!!! END OF TABLE DETECTED — STOP !!!")
            stopDriving()
            state = 10
            break
        sleep(0.1)


# =================================
# MOTOR FUNCTIONS
# =================================
def startDrivingF():
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)
    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)


def startDrivingB():
    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.HIGH)
    pwm1.ChangeDutyCycle(speed)
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


# =================================
# SERVO FUNCTIONS
# =================================
def rotateArm(target_angle, step=1, delay=0.1):
    global current_rotate_angle
    start, end = int(current_rotate_angle), int(target_angle)
    if end > start:
        angles = range(start, end + 1, step)
    else:
        angles = range(start, end - 1, -step)
    for angle in angles:
        kit.servo[0].angle = angle
        sleep(delay)
    current_rotate_angle = target_angle


def extendArm(target_angle, step=1, delay=0.02):
    global current_extend_angle
    start, end = int(current_extend_angle), int(target_angle)
    if end > start:
        angles = range(start, end + 1, step)
    else:
        angles = range(start, end - 1, -step)
    for angle in angles:
        kit.servo[1].angle = angle
        sleep(delay)
    current_extend_angle = target_angle


# =================================
# VALVE FUNCTIONS
# =================================
def solenoidValveOpen():
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Valve is Open")


def solenoidValveClosed():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("Valve is Closed")


def wateringPlant():
    sleep(1)
    solenoidValveOpen()
    sleep(wateringTime)
    print(f"Watering time: {wateringTime}")
    solenoidValveClosed()
    sleep(1)


# =================================
# MAIN LOOP
# =================================
while True:
    match state:
        case 0:
            initialize()
            sleep(1)
            state = 10

        case 10:  # Standby, wait for start command
            print("Waiting for initialization")
            if GPIO.input(START_BUTTON_PIN) == GPIO.LOW:
                print("Button was pressed!")
                state = 20

        case 20:  # Start driving until reached a plant
            startDrivingF()
            state = 30

        case 30:  # Driving stops because plant is reached
            plantFound()
            sleep(3)
            state = 40

        case 40:  # Arm is rotated outward to Left
            rotateArm(0)
            sleep(3)
            state = 50

        case 50:
            extendArm(160)
            sleep(3)
            state = 60

        case 60:
            # Compute watering time from formula
            wateringTime = compute_watering_time()
            state = 70

        case 70:
            wateringPlant()
            state = 51

        case 51:
            extendArm(180)
            sleep(3)
            state = 71

        case 71:
            wateringTime = compute_watering_time()
            wateringPlant()
            state = 80

        case 80:
            extendArm(0)
            state = 90

        case 90:
            rotateArm(90)
            state = 30

        case 999:
            exit()
