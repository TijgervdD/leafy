# ============================================================
# FULL ROBOT + CAMERA + WATERING INTEGRATION
# Primary authority: valve_open_time_ml
# ============================================================

# =========================
# IMPORTS
# =========================
from picamera2 import Picamera2
import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
from time import sleep
from adafruit_servokit import ServoKit
from pyrf24 import RF24, RF24_PA_MIN
import os

# =========================
# GLOBAL STATE (UNCHANGED)
# =========================
state = 0
speed = 80
wateringTime = 1
humidity = [0, 0, 0]  # placeholder array

SOIL_HUMIDITY = 75.0  # used in formula

# =========================
# HSV GREEN DETECTION
# =========================
GREEN_LOWER = np.array([46, 53, 53])
GREEN_UPPER = np.array([70, 255, 255])

# =========================
# WATER FORMULAS
# =========================
def predict_water(humidity, greenery):
    return 261.83 - humidity * 3.13314695 + greenery * 2.13997997

def valve_open_time_ml(V_ml):
    a = 0.11455309
    b = 36.75567689
    c = 19.817595 - V_ml

    disc = b**2 - 4*a*c
    if disc < 0:
        return None

    return (-b + np.sqrt(disc)) / (2 * a)

# =========================
# CAMERA FUNCTIONS
# =========================
def capture_frame():
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
    )
    picam2.start()
    sleep(2)
    frame = picam2.capture_array()
    picam2.stop()
    return frame

def analyze_plant(image_rgb):
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)

    green_pixels = np.count_nonzero(green_mask)
    total_pixels = green_mask.size

    return (green_pixels / total_pixels) * 100

# =========================
# GPIO / HARDWARE SETUP
# =========================
GPIO.setmode(GPIO.BCM)

IN1_M1, IN2_M1, EN_M1 = 23, 22, 24
IN1_M2, IN2_M2, EN_M2 = 27, 18, 17

for p in [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]:
    GPIO.setup(p, GPIO.OUT)

pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)

kit = ServoKit(channels=16)
current_extend_angle = 0

RELAY_PIN = 21
START_BUTTON_PIN = 20
STOP_BUTTON_PIN = 16

GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(STOP_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# =========================
# ARM / DRIVE FUNCTIONS
# =========================
def startDrivingF():
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)

    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)

def stopDriving():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.LOW)

def rotateArm(angle):
    kit.servo[0].angle = angle
    sleep(1)

def extendArm(angle):
    kit.servo[1].angle = angle
    sleep(1)

# =========================
# SOLENOID
# =========================
def solenoidValveOpen():
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("🚰 Valve OPEN")

def solenoidValveClosed():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("🚰 Valve CLOSED")

def wateringPlant():
    solenoidValveOpen()
    sleep(wateringTime)
    solenoidValveClosed()

# =========================
# CAMERA-DRIVEN WATERING
# =========================
def wateringTiming():
    global wateringTime

    print("\n📷 Taking picture...")
    image = capture_frame()

    print("🌿 Analyzing greenery...")
    green_ratio = analyze_plant(image)

    # FAILSAFE
    if green_ratio < 1.0:
        print("⚠️ Greenery too low → using failsafe 20%")
        green_ratio = 20.0

    water_ml = predict_water(SOIL_HUMIDITY, green_ratio)
    valve_time = valve_open_time_ml(water_ml)

    if valve_time is None or valve_time < 0:
        valve_time = 0

    wateringTime = valve_time

    print("---- WATER DECISION ----")
    print(f"Green % used : {green_ratio:.2f}")
    print(f"Water (ml)  : {water_ml:.2f}")
    print(f"Valve time : {wateringTime:.2f} s")

# =========================
# MAIN LOOP (STATE MACHINE)
# =========================
while True:

    match state:

        case 0:
            print("Initializing system...")
            pwm1.start(0)
            pwm2.start(0)
            kit.servo[0].angle = 90
            kit.servo[1].angle = 0
            state = 10

        case 10:  # Standby
            print("Waiting for start button...")
            if GPIO.input(START_BUTTON_PIN) == GPIO.LOW:
                state = 20

        case 20:  # Drive to plant
            print("Driving forward...")
            startDrivingF()
            sleep(2)
            stopDriving()
            state = 40

        case 40:  # Rotate arm
            rotateArm(0)
            state = 50

        case 50:  # Extend arm
            extendArm(160)
            state = 60

        case 60:  # TAKE PHOTO + CALCULATE WATER
            wateringTiming()
            state = 70

        case 70:  # WATER
            wateringPlant()
            state = 80

        case 80:  # Retract
            extendArm(0)
            rotateArm(90)
            state = 20
