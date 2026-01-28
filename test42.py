# ==============================================================================
# IMPORT SECTION
# ==============================================================================
import time
from time import sleep
import sys
from adafruit_servokit import ServoKit
from pyrf24 import RF24, RF24_PA_MIN
from gpiozero import PWMOutputDevice, DigitalOutputDevice, DistanceSensor, Button, OutputDevice

# ==============================================================================
# GLOBAL VARIABLES
# ==============================================================================
state = 0 
speed = 0.8  # Gpiozero uses 0.0 to 1.0 (80% speed = 0.8)
wateringTime = 0 
humidity = [0, 0, 0] # Initialized as list to prevent index errors

# ==============================================================================
# PIN LAYOUT & HARDWARE SETUP
# ==============================================================================

# Motor 1
IN1_M1 = DigitalOutputDevice(23)
IN2_M1 = DigitalOutputDevice(22)
EN_M1  = PWMOutputDevice(24, frequency=1000)

# Motor 2
IN1_M2 = DigitalOutputDevice(27)
IN2_M2 = DigitalOutputDevice(18)
EN_M2  = PWMOutputDevice(17, frequency=1000)

# Sonar Sensors (gpiozero handles timing internally)
sensor1 = DistanceSensor(echo=6, trigger=5, max_distance=2)
sensor2 = DistanceSensor(echo=13, trigger=12, max_distance=2)

# Relays and Buttons
relay = OutputDevice(21)
# Pull_up=True means the button connects to GND
start_button = Button(20, pull_up=True) 
stop_button = Button(16, pull_up=True)

# I2C Servo HAT
kit = ServoKit(channels=16)

# Radio NRF24L01 (Pi 5: CE=25, CSN=0)
radio = RF24(25, 0)
address = b"0001\x00" 

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def initialize():
    print("System Initializing...")
    stopDriving()
    kit.servo[0].angle = 90
    kit.servo[1].angle = 0
    sleep(1)

def eStop():
    global state
    print("!!! EMERGENCY STOP !!!")
    stopDriving()
    extendArm(0)
    rotateArm(90)
    state = 10

def plantFound():
    global state
    while True:
        # Distance is returned in meters by gpiozero, multiplying by 100 for cm
        dist1 = sensor1.distance * 100
        dist2 = sensor2.distance * 100
        
        print(f"Dist 1: {dist1:.1f} cm | Dist 2: {dist2:.1f} cm")

        if dist1 < 5:
            print("!!! PLANT DETECTED !!!")
            stopDriving()
            break
        
        elif dist2 < 5:
            print("!!! END OF TABLE !!!")
            stopDriving()
            state = 10
            break
        sleep(0.1)

def startDrivingF():
    IN1_M1.on()
    IN2_M1.off()
    EN_M1.value = speed

    IN1_M2.on()
    IN2_M2.off()
    EN_M2.value = speed

def stopDriving():
    EN_M1.value = 0
    EN_M2.value = 0
    IN1_M1.off()
    IN2_M1.off()
    IN1_M2.off()
    IN2_M2.off()

def receiveRemoteControlData():
    if not radio.get_status(): # Check if radio is already started
        radio.begin() 
        radio.setDataRate(RF24_250KBPS)
        radio.openReadingPipe(1, address)
        radio.setPALevel(RF24_PA_MIN)
        radio.startListening()

def wateringTiming(i):
    global wateringTime
    receiveRemoteControlData()
    # Logic based on humidity index
    try:
        val = humidity[i]
        if val > 50: wateringTime = 0
        elif val > 40: wateringTime = 2
        else: wateringTime = 4
    except IndexError:
        wateringTime = 2 # Default safety value

def rotateArm(pos):
    kit.servo[0].angle = pos
    sleep(2)

def extendArm(pos):
    kit.servo[1].angle = pos
    sleep(2)

def wateringPlant():
    print("Valve Opening...")
    relay.on()
    sleep(wateringTime)
    relay.off()
    print("Valve Closed.")

# ==============================================================================
# MAIN STATE MACHINE
# ==============================================================================
try:
    while True:
        if stop_button.is_pressed:
            eStop()

        match state:
            case 0:
                initialize()
                state = 10
            
            case 10: # Standby
                print("Standby - Waiting for Start Button...")
                start_button.wait_for_press()
                print("Button Pressed! Starting...")
                state = 20
            
            case 20: # Drive to plant
                startDrivingF()
                state = 30
            
            case 30: # Check sensors
                plantFound()
                sleep(1)
                state = 40
            
            case 40: # Positioning
                rotateArm(0)
                state = 50
            
            case 50:
                extendArm(80)
                state = 70 # Jump to watering
            
            case 70:
                wateringPlant()
                state = 80
            
            case 80:
                extendArm(0)
                state = 90
            
            case 90:
                rotateArm(90)
                state = 20 # Loop back to find next plant

except KeyboardInterrupt:
    print("\nProgram stopped by user")
    stopDriving()