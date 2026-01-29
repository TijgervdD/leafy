import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# Test your pins one by one:
GPIO.setup(23, GPIO.OUT) # Motor 1
GPIO.setup(22, GPIO.OUT) # Motor 1
GPIO.setup(24, GPIO.OUT) # EN 1
GPIO.setup(27, GPIO.OUT) # Motor 2
GPIO.setup(18, GPIO.OUT) # Motor 2
GPIO.setup(17, GPIO.OUT) # EN 2
GPIO.setup(5, GPIO.OUT)  # TRIG 1
GPIO.setup(6, GPIO.IN)   # ECHO 1
GPIO.setup(12, GPIO.OUT) # TRIG 2
GPIO.setup(13, GPIO.IN)  # ECHO 2
GPIO.setup(21, GPIO.OUT) # RELAY
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP) # START
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP) # STOP