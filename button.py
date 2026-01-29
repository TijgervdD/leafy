import RPi.GPIO as GPIO
import time

PIN = 20 # Your start button
GPIO.setmode(GPIO.BCM)

try:
    print("Testing Pin 20...")
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("Success! GPIO Allocated.")
finally:
    GPIO.cleanup()