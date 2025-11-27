#ASCII-schema
 #   5V ---- VCC (motor PCB) ----- L293D Pin16 (Vcc1)
 #   GND ------------------------ L293D GND + Motor GND
 #                       +------- L293D Pin3 -> M+
#Motor PCB: M+ ---+------+
#Motor PCB: M- ---+-------> L293D Pin6 -> M-

#Pi GPIO17 ----- L293D IN1 (Pin2)
#Pi GPIO27 ----- L293D IN2 (Pin7)
#Pi GPIO18 ----- L293D EN (Pin1)   <-- PWM voor snelheid

#Pi GPIO23 <----- H1 sensor
#Pi GPIO24 <----- H2 sensor (optioneel)

import RPi.GPIO as GPIO
import time

# GPIO to L293D
EN  = 18  # PWM enable pin L293D Pin1
IN1 = 17  # L293D Pin2
IN2 = 27  # L293D Pin7

# Hall sensor input
H1 = 23   # Motor sensor pin
# H2 = 24   # Indien quadratuur gewenst

GPIO.setmode(GPIO.BCM)

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(EN, GPIO.OUT)

GPIO.setup(H1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pwm = GPIO.PWM(EN, 1000)  # 1kHz PWM
pwm.start(0)  # begint uit

pulse_count = 0

def hall_callback(channel):
    global pulse_count
    pulse_count += 1

GPIO.add_event_detect(H1, GPIO.RISING, callback=hall_callback)

try:
    while True:
        # richting vooruit
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)

        pwm.ChangeDutyCycle(60)  # snelheid = 0-100%

        time.sleep(1)

        pulses = pulse_count
        pulse_count = 0

        # ---- RPM berekenen ----
        pulses_per_rev = 20  # zelf meten of documentatie
        rpm = (pulses / pulses_per_rev) * 60

        print(f"Pulsen/s: {pulses}   RPM: {rpm:.1f}")

except KeyboardInterrupt:
    pass

pwm.stop()
GPIO.cleanup()
