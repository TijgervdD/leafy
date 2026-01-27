import RPi.GPIO as GPIO
import time
from time import *
GPIO.setmode(GPIO.BCM)
#relais pin / Solenoid valve
RELAY_PIN = 16

def solenoidValveOpen():
    # If your relay is 'Active Low', use GPIO.LOW to turn it on
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Valve is Open")

def solenoidValveClosed():
    # Use GPIO.HIGH to turn it off
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("Valve is Closed")

while True:
    solenoidValveOpen()
    time.sleep(3)
    solenoidValveClosed