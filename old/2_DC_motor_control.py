import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# =====================
# PIN LAYOUT (jouw exacte schema)
# =====================

# Motor 1
IN1_M1 = 17
IN2_M1 = 27
EN_M1  = 18   # PWM voor motor 1

# Motor 2
IN1_M2 = 22
IN2_M2 = 25
EN_M2  = 13   # PWM voor motor 2

# Setup pins
motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)

# PWM op beide motoren
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)
pwm1.start(0)
pwm2.start(0)

# =====================
# Functies (gelijktijdig)
# =====================

def motors_forward(speed):
    # Motor 1
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)

    # Motor 2
    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)


def motors_backward(speed):
    # Motor 1
    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.HIGH)
    pwm1.ChangeDutyCycle(speed)

    # Motor 2
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.HIGH)
    pwm2.ChangeDutyCycle(speed)


def motors_stop():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.LOW)


# =====================
# USER LOOP
# =====================

try:
    while True:
        richting = input("Direction (f = forward, b = backward, s = stop): ")

        if richting == "f":
            snelheid = int(input("Speed (0–100): "))
            motors_forward(snelheid)
            print(f"BEIDE motoren draaien VOORUIT met {snelheid}%")

        elif richting == "b":
            snelheid = int(input("Speed (0–100): "))
            motors_backward(snelheid)
            print(f"BEIDE motoren draaien ACHTERUIT met {snelheid}%")

        elif richting == "s":
            motors_stop()
            print("BEIDE motoren gestopt")

        else:
            print("Ongeldige keuze (gebruik f / b / s)")

except KeyboardInterrupt:
    pass

motors_stop()
GPIO.cleanup()
print("Programma gestopt.")
