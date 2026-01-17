state = 0 # global statemachine variable
speed = 20 # global motor speed setting

def initialize():
    # initialize the system

def eStop():
    # turn off all moving parts and return to safe state

    # go to standby
    state = 10

def startDriving():
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    pwm1.ChangeDutyCycle(speed)

    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)
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

def positionArm(pos):
    # control servo to move arm to pos



while True:
    if (buttonPressedEstop()):
        eStop()

    match state:
        case 0:
            initialize()
            state = 10
        case 10: # Standby, wait for start command
            if (startButtonPressed):
                state = 20
        case 20: # Start driving until reached a plant
            startDriving()
            state = 30
        case 30:
            if (plantFound()):
                stopDriving()
                state = 40
            if (endStop()):
                stopDriving()
                state = 10
        case 40:
            extendArm()
            state = 50
        case 50:
            waterThePlant()
            state = 60
        case 60:
            retractArm()
            state = 20

        case 999:
            exit()
