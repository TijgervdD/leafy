import RPi.GPIO as GPIO
import time

# =========================
# Pin-instellingen
# =========================
EN  = 18  # PWM enable
IN1 = 17  # richting pin 1
IN2 = 27  # richting pin 2

H1 = 23   # hall sensor input

GPIO.setmode(GPIO.BCM)

# Motor
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

GPIO.setup(EN, GPIO.OUT)
pwm = GPIO.PWM(EN, 1000)  # 1 kHz PWM voor snelheidsregeling
pwm.start(0)              # motor begint uit

# Hall interrupt
pulse_count = 0
def hall_callback(channel):
    global pulse_count
    pulse_count += 1

GPIO.setup(H1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(H1, GPIO.RISING, callback=hall_callback)


# =========================
# Functies om motor te sturen
# =========================

def motor_forward(speed):
    """ speed = 0–100 % """
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def motor_backward(speed):
    """ speed = 0–100 % """
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)

def motor_stop():
    pwm.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)



# =========================
# HIER voer jij zelf richting + snelheid in
# =========================

try:
    while True:
        richting = input("Richting (f = vooruit, b = achteruit, s = stop): ")

        if richting == "f":
            snelheid = int(input("Snelheid (0–100): "))
            motor_forward(snelheid)
            print(f"Motor draait VOORUIT met {snelheid}%")

        elif richting == "b":
            snelheid = int(input("Snelheid (0–100): "))
            motor_backward(snelheid)
            print(f"Motor draait ACHTERUIT met {snelheid}%")

        elif richting == "s":
            motor_stop()
            print("Motor gestopt")

        else:
            print("Ongeldige keuze (gebruik f / b / s)")

        # optioneel RPM uitlezen per seconde:
        time.sleep(1)
        p = pulse_count
        pulse_count = 0
        pulses_per_rev = 20  # aanpassen na meting
        rpm = (p / pulses_per_rev) * 60
        print(f"Puls/s={p} , RPM={rpm:.1f}\n")

except KeyboardInterrupt:
    pass

motor_stop()
GPIO.cleanup()
