state = 0 # global statemachine variable
speed = 40 # global motor speed setting

# Import files
import RPi.GPIO as GPIO
import time
from time import *
from adafruit_servokit import ServoKit
import sys
import time
from pyrf24 import RF24, RF24_PA_MIN
GPIO.setmode(GPIO.BCM)

# ==============================================================================
# PIN layout and initial setup
# Motor 1
IN1_M1 = 17
IN2_M1 = 18
EN_M1  = 23   # PWM voor motor 1

# Motor 2
IN1_M2 = 22
IN2_M2 = 27
EN_M2  = 24   # PWM voor motor 2

# Setup pins
motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)
# PWM op beide motoren
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)

#Initialising statement stating that we will have access to 16 PWM channels of the HAT and to summon them we will use | kit |
kit = ServoKit(channels=16)

# Setup voor Pi 5: CE op GPIO 25, CSN op SPI0 (CE0 / GPIO 8)
radio = RF24(25, 0)

# Adres MOET exact "0001" zijn zoals in je Arduino code (5 bytes totaal)
address = b"0001\x00" 

# HC-SR04 pins (sonar sensor)
TRIG1 = 6
ECHO1 = 5

TRIG2 = 12
ECHO2 =13

# Ultrasone sensor pins
GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)

GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)

# =====================================================================================

def initialize():
    # initialize the system
    #initializing the start speed of the DC motors
    pwm1.start(0)
    pwm2.start(0)

    #Desiding the initial angle that the servo which is attatched to Port 0 will be.
    kit.servo[0].angle = 90
    kit.servo[1].angle = 0

#    distance1 = measuringDistance1()
#    distance2 = measuringDistance2()

def eStop():
    # turn off all moving parts and return to safe state

    # go to standby
    state = 10

#def buttonPressedEstop():
    # start the system when the button is pressed

def endStop():
    # sensor measuring the end of the table
    distance2 = measuringDistance()
    if distance2 < 5:
            print("!!! END OF TABLE DETECTED — STOP !!!")
            stopDriving()      

def measuringDistance1():
        # Distance sensor initialization - sensor measuring that a plant is nearby
    # Trigger puls
    GPIO.output(TRIG1, True)
    time.sleep(0.00001)
    GPIO.output(TRIG1, False)

    # Wachten op echo start
    start_time = time.time()
    while GPIO.input(ECHO1) == 0:
        start_time = time.time()

    # Wachten op echo einde
    stop_time = time.time()
    while GPIO.input(ECHO1) == 1:
        stop_time = time.time()

    # Tijdsverschil
    time_elapsed = stop_time - start_time

    # Geluidssnelheid: 34300 cm/s
    distance1 = (time_elapsed * 34300) / 2

    return distance1


def measuringDistance2():
        # Distance sensor initialization - sensor measuring that a plant is nearby
    # Trigger puls
    GPIO.output(TRIG2, True)
    time.sleep(0.00001)
    GPIO.output(TRIG2, False)

    # Wachten op echo start
    start_time = time.time()
    while GPIO.input(ECHO2) == 0:
        start_time = time.time()

    # Wachten op echo einde
    stop_time = time.time()
    while GPIO.input(ECHO2) == 1:
        stop_time = time.time()

    # Tijdsverschil
    time_elapsed = stop_time - start_time

    # Geluidssnelheid: 34300 cm/s
    distance2 = (time_elapsed * 34300) / 2

    return distance2

def plantFound():
    while True:
        distance1 = measuringDistance1()
        distance2 = measuringDistance2()
        
        print(f"Dist 1: {distance1:.1f} cm | Dist 2: {distance2:.1f} cm")

        # Specific check for Sensor 1
        if distance1 < 5:
            print("!!! PLANT DETECTED — STOPPING !!!")
            stopDriving()
            break
        
        # Specific check for Sensor 2
        elif distance2 < 5:
            print("!!! END OF TABLE DETECTED — STOP !!!")
            stopDriving()
            state = 10
            break

        time.sleep(0.1)

def startDrivingF():
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)

    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
    pwm2.ChangeDutyCycle(speed)

def startDrivingB():
    # Motor 1
    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.HIGH)
    pwm1.ChangeDutyCycle(speed)

    # Motor 2
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.HIGH)
    pwm2.ChangeDutyCycle(speed)

def stopDriving():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.LOW)

def receiveRemoteControlData():
    # handle nrf24l data reception
    radio.begin() # Slower air speed is more stable
    radio.setDataRate(RF24_250KBPS)
    #  radio.setPALevel(RF24_PA_MIN)
    radio.openReadingPipe(1, address)
    radio.setPALevel(RF24_PA_MIN)
    radio.startListening()
    radio.printDetails()

def radioLoop():
    while True:
        if radio.available():
            # We lezen 32 bytes (zoals de Arduino char buffer)
            payload = radio.read(32)
            
            try:
                # Decodeer de bytes en verwijder lege karakters
                text = payload.decode('utf-8').rstrip('\x00')
                if text:
                    print(f"Ontvangen: {text}")
            except Exception as e:
                print(f"Data ontvangen (geen tekst): {payload}")
        
        time.sleep(0.01)

    if __name__ == "__main__":
        setup()
        try:
            loop()
        except KeyboardInterrupt:
            print("\nOntvanger gestopt.")

def radioListen():
        receiveRemoteControlData()
        radioLoop()

def rotateArm(pos):
    # control servo to move arm to pos
    kit.servo[0].angle = pos

def extendArm(pos):
    # control servo to extend the arm
    kit.servo[1].angle = pos

# =========================================================================================
# LOOP
while True:
    #if (buttonPressedEstop()):
    #    eStop()

    match state:
        case 0:
            initialize()
            sleep(3)
            state = 20
        case 10: # Standby, wait for start command
#            if (startButtonPressed):
                state = 10
        # Distance sensor initialization - sensor measuring that a plant is nearby
        case 20: # Start driving until reached a plant
            startDrivingF()
            state = 30
        case 30:
            plantFound()
            sleep(3)
            state = 40
        case 40:
            rotateArm(0)
            sleep(3)
            state = 50
        case 50:
            extendArm(40)
            sleep(3)
            state = 20
        case 60:
            waterThePlant()
            state = 70
        case 80:
            retractArm()
            state = 90
        case 90:
            rotateArm(90)
            state = 20
        case 999:
            exit()
