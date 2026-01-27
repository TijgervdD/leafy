# ============================================================
# Raspberry Pi Plant Watering Robot
# Fully integrated: motors, servos, sensors, NRF24, camera
# ============================================================

state = 0  # global statemachine variable
speed = 80  # global motor speed setting
wateringTime = 0  # defining start value wateringTime
humidity = 0  # will be updated live from NRF24

# ===================================================================
# IMPORTS
# ===================================================================
import RPi.GPIO as GPIO
import time
from time import *
from adafruit_servokit import ServoKit
import sys
from pyrf24 import RF24, RF24_PA_MIN

# CAMERA IMPORTS
from picamera2 import Picamera2
import cv2
import numpy as np
import matplotlib.pyplot as plt

GPIO.setmode(GPIO.BCM)

# ===================================================================
# PIN LAYOUT
# ===================================================================
# Motor 1
IN1_M1 = 23
IN2_M1 = 22
EN_M1 = 24  # PWM motor 1

# Motor 2
IN1_M2 = 27
IN2_M2 = 18
EN_M2 = 17  # PWM motor 2

motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)

pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)

# ServoKit
kit = ServoKit(channels=16)

# NRF24 Setup
radio = RF24(25, 0)
address = b"0001\x00"  # 5-byte address

# HC-SR04 Pins
TRIG1 = 5
ECHO1 = 6
TRIG2 = 12
ECHO2 = 13
GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)

# Solenoid / Relay and Buttons
RELAY_PIN = 21
START_BUTTON_PIN = 20
STOP_BUTTON_PIN = 16
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(START_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(STOP_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ============================================================
# CAMERA / PLANT ANALYSIS SETTINGS
# ============================================================
GREEN_LOWER = np.array([46, 53, 53])
GREEN_UPPER = np.array([70, 255, 255])

# ============================================================
# INITIALIZATION FUNCTIONS
# ============================================================
def initialize():
    pwm1.start(0)
    pwm2.start(0)
    kit.servo[0].angle = 90
    kit.servo[1].angle = 0

def eStop():
    stopDriving()
    extendArm(0)
    rotateArm(90)
    global state
    state = 10

# ============================================================
# DISTANCE SENSORS
# ============================================================
def measuringDistance1():
    GPIO.output(TRIG1, True)
    time.sleep(0.00001)
    GPIO.output(TRIG1, False)
    start_time = time.time()
    while GPIO.input(ECHO1) == 0:
        start_time = time.time()
    stop_time = time.time()
    while GPIO.input(ECHO1) == 1:
        stop_time = time.time()
    time_elapsed = stop_time - start_time
    distance1 = (time_elapsed * 34300) / 2
    return distance1

def measuringDistance2():
    GPIO.output(TRIG2, True)
    time.sleep(0.00001)
    GPIO.output(TRIG2, False)
    start_time = time.time()
    while GPIO.input(ECHO2) == 0:
        start_time = time.time()
    stop_time = time.time()
    while GPIO.input(ECHO2) == 1:
        stop_time = time.time()
    time_elapsed = stop_time - start_time
    distance2 = (time_elapsed * 34300) / 2
    return distance2

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
        time.sleep(0.1)

# ============================================================
# MOTOR FUNCTIONS
# ============================================================
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

# ============================================================
# OLD NRF24 RECEIVER (commented out)
# ============================================================
# def receiveRemoteControlData():
#     radio.begin()
#     radio.setDataRate(RF24_250KBPS)
#     radio.openReadingPipe(1, address)
#     radio.setPALevel(RF24_PA_MIN)
#     radio.startListening()
#     radio.printDetails()

# ============================================================
# NEW NRF24 RECEIVER
# ============================================================
def read_remote_humidity():
    """
    Updates the global humidity list with data from the NRF24 receiver.
    Works with a single numeric byte (like the working code) or a string.
    """
    global humidity
    radio.begin()
    radio.setDataRate(RF24_250KBPS)
    radio.openReadingPipe(1, address)
    radio.setPALevel(RF24_PA_MIN)
    radio.startListening()

    if radio.available():
        payload = radio.read(32)
        try:
            text = payload.decode("utf-8").rstrip("\x00")
            if text:  # if the hub sends a CSV string
                parts = text.split(",")
                humidity = [float(p) for p in parts]
            else:  # if the hub sends a single byte
                humidity = [payload[0]]
            print(f"Humidity updated: {humidity}")
        except:
            # fallback if decoding fails
            humidity = [payload[0]]
            print(f"Humidity updated (non-text): {humidity}")


# ============================================================
# ARM AND VALVE FUNCTIONS
# ============================================================
def rotateArm(pos):
    sleep(2)
    kit.servo[0].angle = pos
    sleep(2)

def extendArm(pos):
    kit.servo[1].angle = pos
    sleep(2)

def solenoidValveOpen():
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Valve is Open")

def solenoidValveClosed():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("Valve is Closed")

# ============================================================
# CAMERA / PLANT ANALYSIS FUNCTIONS
# ============================================================
def predict_water(current_humidity, greenery):
    """
    Calculates the water amount in ml using live humidity and greenery %
    """
    return 261.83 - current_humidity * 3.13314695 + greenery * 2.13997997

def valve_open_time_ml(V_ml):
    a = 0.11455309
    b = 36.75567689
    c = 19.817595 - V_ml
    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        return None
    t = (-b + np.sqrt(discriminant)) / (2*a)
    return t

def is_valid_pixel(y, x, mask, radius=3, threshold=0.75):
    h, w = mask.shape
    y0 = max(0, y-radius)
    y1 = min(h, y+radius+1)
    x0 = max(0, x-radius)
    x1 = min(w, x+radius+1)
    patch = mask[y0:y1, x0:x1]
    return (np.count_nonzero(patch) / patch.size) >= threshold

def connected_vertically(y, x, mask, direction="up", length=10, min_ratio=0.6):
    h, w = mask.shape
    connected_rows = 0
    if direction=="up":
        for dy in range(1, length+1):
            if y-dy < 0:
                break
            if mask[y-dy, x] > 0:
                connected_rows += 1
    else:
        for dy in range(1, length+1):
            if y+dy >= h:
                break
            if mask[y+dy, x] > 0:
                connected_rows += 1
    return (connected_rows / length) >= min_ratio

def capture_frame():
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"format":"RGB888","size":(640,480)}))
    picam2.start()
    sleep(2)
    frame = picam2.capture_array()
    picam2.stop()
    return frame

def analyze_plant(image_rgb):
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)
    h, w = green_mask.shape
    center_strip = green_mask[:, w//2 - w//20 : w//2 + w//20]
    top_pixel = None
    bottom_pixel = None
    for y in reversed(range(center_strip.shape[0])):
        xs = np.where(center_strip[y]>0)[0]
        for x in xs:
            if is_valid_pixel(y,x,center_strip) and connected_vertically(y,x,center_strip,"up"):
                bottom_pixel = y
                break
        if bottom_pixel is not None:
            break
    for y in range(center_strip.shape[0]):
        xs = np.where(center_strip[y]>0)[0]
        for x in xs:
            if is_valid_pixel(y,x,center_strip) and connected_vertically(y,x,center_strip,"down"):
                top_pixel = y
                break
        if top_pixel is not None:
            break
    plant_height = bottom_pixel - top_pixel if top_pixel is not None and bottom_pixel is not None else None
    restricted_green_mask = green_mask.copy()
    if plant_height is not None:
        restricted_green_mask[:top_pixel,:] = 0
        restricted_green_mask[bottom_pixel+1:,:] = 0
    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]
    green_pixels = np.count_nonzero(restricted_green_mask)
    green_ratio = (green_pixels / total_pixels) * 100
    return green_ratio, restricted_green_mask, top_pixel, bottom_pixel, plant_height

# ============================================================
# WATERING FUNCTION UPDATED (uses live humidity)
# ============================================================
def wateringPlant(plant_index=0):
    """
    Capture plant image, analyze it, and water based on live humidity
    plant_index = which plant in NRF24 humidity list to use
    """
    global humidity
    if isinstance(humidity, list) and len(humidity) > plant_index:
        current_humidity = humidity[plant_index]
    else:
        print("No humidity data received yet, skipping watering.")
        return
    image = capture_frame()
    green_ratio, _, top_pixel, bottom_pixel, plant_height = analyze_plant(image)
    water_ml = predict_water(current_humidity, green_ratio)
    t_open = valve_open_time_ml(water_ml)
    if t_open is None:
        t_open = 0
    print(f"Plant {plant_index+1} | Soil humidity {current_humidity:.1f}% | Watering: {water_ml:.2f}ml | Valve open {t_open:.2f}s")
    solenoidValveOpen()
    sleep(t_open)
    solenoidValveClosed()

# ============================================================
# STATE MACHINE LOOP
# ============================================================
while True:
    if GPIO.input(STOP_BUTTON_PIN) == GPIO.LOW:
        print("Emergency STOP button was pressed!")
        eStop()

    # Read live humidity from remote
    read_remote_humidity()

    match state:
        case 0:
            initialize()
            sleep(1)
            state = 10
        case 10:
            print("Waiting for initialization")
            if GPIO.input(START_BUTTON_PIN) == GPIO.LOW:
                print("Button was pressed!")
                state = 20
        case 20:
            startDrivingF()
            state = 30
        case 30:
            plantFound()
            sleep(3)
            state = 40
        case 40:
            rotateArm(0)
            sleep(3)
            state = 50
        case 50:
            extendArm(80)
            sleep(3)
            state = 70
        case 60:
            # Old wateringTiming replaced
            state = 70
        case 70:
            wateringPlant(plant_index=0)
            state = 51
        case 51:
            extendArm(160)
            sleep(3)
            state = 71
        case 61:
            # Old wateringTiming replaced
            state = 80
        case 71:
            wateringPlant(plant_index=1)
            state = 80
        case 80:
            extendArm(0)
            state = 90
        case 90:
            rotateArm(90)
            state = 20
        case 999:
            exit()
