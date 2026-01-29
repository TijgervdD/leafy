import RPi.GPIO as GPIO
import time

PIN = 20
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Testing button on BCM 20 (Physical 38). Press it now!")

try:
    while True:
        if GPIO.input(PIN) == GPIO.LOW:
            print("Button Pressed!")
            time.sleep(0.2) # Debounce
        time.sleep(0.01)
except KeyboardInterrupt:
    GPIO.cleanup()