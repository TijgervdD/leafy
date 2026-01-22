import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
button_pin = 21  # Change to your GPIO pin number
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        if GPIO.input(button_pin) == GPIO.LOW:  # Button pressed
            print("Button was pressed!")
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()