import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# =====================================================
# PIN LAYOUT
# =====================================================

# Motor 1
IN1_M1 = 17
IN2_M1 = 27
EN_M1  = 18   # PWM voor motor 1

# Motor 2
IN1_M2 = 22
IN2_M2 = 25
EN_M2  = 13   # PWM voor motor 2

# HC-SR04 pins
TRIG = 20
ECHO = 21

# Motor pin setup
motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)

# Ultrasone sensor pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# PWM setup
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)
pwm1.start(0)
pwm2.start(0)

# =====================================================
# MOTOR FUNCTIES
# =====================================================

def motors_forward(speed):
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)

    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)

def motors_stop():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.LOW)

# =====================================================
# AFSTAND FUNCTIE HC-SR04
# =====================================================

def meet_afstand():
    # Trigger puls
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Wachten op echo start
    start_time = time.time()
    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    # Wachten op echo einde
    stop_time = time.time()
    while GPIO.input(ECHO) == 1:
        stop_time = time.time()

    # Tijdsverschil
    time_elapsed = stop_time - start_time

    # Geluidssnelheid: 34300 cm/s
    distance = (time_elapsed * 34300) / 2

    return distance

# =====================================================
# MAIN LOOP
# =====================================================

try:
    print("Robot start automatisch vooruit te rijden.")
    motors_forward(60)  # 60% snelheid

    while True:
        afstand = meet_afstand()
        print(f"Afstand: {afstand:.1f} cm")

        if afstand < 10:
            print("!!! OBSTAKEL GEDTECTEERD binnen 5cm — STOP !!!")
            motors_stop()
            break

        time.sleep(0.1)

except KeyboardInterrupt:
    pass

motors_stop()
GPIO.cleanup()
print("Programma gestopt.")
