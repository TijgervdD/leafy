# Final beast - Optimized for Raspberry Pi 4
state = 0  # global statemachine variable
speed = 80  # global motor speed setting
wateringTime = 2  # defining start value wateringTime
humidity = [0, 0, 0]  # Changed to list to prevent index errors

# Import files
import RPi.GPIO as GPIO
import time
from adafruit_servokit import ServoKit
import sys
from pyrf24 import RF24, RF24_PA_MIN
import os

# Use BCM Pin numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ==============================================================================
# PIN layout and initial setup
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

# PWM on both motors
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)

# PCA9685 Servo HAT setup
kit = ServoKit(channels=16)

# Track current angles
current_extend_angle = 0
current_rotate_angle = 90

# RF24 Setup for Pi 4: CE on GPIO 25, CSN on SPI0 (CE0 / GPIO 8)
# On Pi 4, (25, 0) refers to CE pin 25 and SPI Bus 0, Chip Select 0.
radio = RF24(25, 0)
address = b"0001\x00"

# HC-SR04 pins
TRIG1, ECHO1 = 5, 6
TRIG2, ECHO2 = 12, 13

GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)

# Relays and Buttons
RELAY_PIN = 21
START_BUTTON_PIN = 20
STOP_BUTTON_PIN = 16

GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(STOP_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# =====================================================================================

def initialize():
    global current_extend_angle, current_rotate_angle
    pwm1.start(0)
    pwm2.start(0)
    
    print("Initializing Servos...")
    time.sleep(1)
    kit.servo[0].angle = 90   # rotate servo
    time.sleep(1)
    kit.servo[1].angle = 0    # extend servo
    
    current_extend_angle = 0
    current_rotate_angle = 90

def eStop(channel=None):
    print("\n!!! EMERGENCY STOP TRIGGERED !!!")
    stopDriving()
    # Close valve for safety
    GPIO.output(RELAY_PIN, GPIO.LOW)
    os._exit(0)

# Interrupt for Emergency Stop
GPIO.add_event_detect(STOP_BUTTON_PIN, GPIO.FALLING, callback=eStop, bouncetime=200)

def measuringDistance1():
    GPIO.output(TRIG1, True)
    time.sleep(0.00001)
    GPIO.output(TRIG1, False)
    
    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO1) == 0:
        start_time = time.time()
    while GPIO.input(ECHO1) == 1:
        stop_time = time.time()

    return ((stop_time - start_time) * 34300) / 2

def measuringDistance2():
    GPIO.output(TRIG2, True)
    time.sleep(0.00001)
    GPIO.output(TRIG2, False)
    
    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO2) == 0:
        start_time = time.time()
    while GPIO.input(ECHO2) == 1:
        stop_time = time.time()

    return ((stop_time - start_time) * 34300) / 2

def plantFound():
    global state
    while True:
        d1 = measuringDistance1()
        d2 = measuringDistance2()
        print(f"Dist 1: {d1:.1f} cm | Dist 2: {d2:.1f} cm")

        if d1 < 5:
            print("!!! PLANT DETECTED !!!")
            stopDriving()
            break
        elif d2 < 5:
            print("!!! END OF TABLE !!!")
            stopDriving()
            state = 10
            break
        time.sleep(0.1)

def startDrivingF():
    GPIO.output(IN1_M1, GPIO.HIGH); GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)
    GPIO.output(IN1_M2, GPIO.HIGH); GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)

def stopDriving():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)
    GPIO.output(IN1_M1, GPIO.LOW); GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW); GPIO.output(IN2_M2, GPIO.LOW)

def receiveRemoteControlData():
    if not radio.is_chip_connected():
        radio.begin()
        radio.setDataRate(RF24_250KBPS)
        radio.openReadingPipe(1, address)
        radio.setPALevel(RF24_PA_MIN)
        radio.startListening()

def rotateArm(target_angle, step=1, delay=0.05):
    global current_rotate_angle
    start = int(current_rotate_angle)
    end = int(target_angle)
    angle_range = range(start, end + 1, step) if end > start else range(start, end - 1, -step)
    
    for angle in angle_range:
        kit.servo[0].angle = angle
        time.sleep(delay)
    current_rotate_angle = target_angle

def extendArm(target_angle, step=1, delay=0.02):
    global current_extend_angle
    start = int(current_extend_angle)
    end = int(target_angle)
    angle_range = range(start, end + 1, step) if end > start else range(start, end - 1, -step)

    for angle in angle_range:
        kit.servo[1].angle = angle
        time.sleep(delay)
    current_extend_angle = target_angle

def wateringPlant():
    time.sleep(1)
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print(f"Watering for {wateringTime}s...")
    time.sleep(wateringTime)
    GPIO.output(RELAY_PIN, GPIO.LOW)
    time.sleep(1)

# =========================================================================================
# MAIN LOOP
try:
    while True:
        if state == 0:
            initialize()
            state = 10

        elif state == 10:
            print("Standby: Press Start Button...")
            if GPIO.input(START_BUTTON_PIN) == GPIO.LOW:
                state = 20

        elif state == 20:
            startDrivingF()
            state = 30

        elif state == 30:
            plantFound()
            state = 40

        elif state == 40:
            rotateArm(0)
            state = 50

        elif state == 50:
            extendArm(160)
            state = 70

        elif state == 70:
            wateringPlant()
            state = 51

        elif state == 51:
            extendArm(180)
            state = 71

        elif state == 71:
            wateringPlant()
            state = 80

        elif state == 80:
            extendArm(0)
            state = 90

        elif state == 90:
            rotateArm(90)
            state = 20 # Loop back to driving

except KeyboardInterrupt:
    print("\nManual Exit")
finally:
    stopDriving()
    GPIO.cleanup()