#Here we will import all the extra functionality desired
from time import *
from adafruit_servokit import ServoKit

state = 0 # global statemachine variable

#Below is an initialising statement stating that we will have access to 16 PWM channels of the HAT and to summon them we will use | kit |
kit = ServoKit(channels=16)

def initialize()
    #Below desides the initial angle that the servo which is attatched to Port 0 will be. In this case we will make it zero degrees.
    kit.servo[0].angle = 0

def positionArmML(pos):
    # control servo to move arm to pos from middle possition to Left
    #Below will rotate the Standard servo to the 180 degree point
    kit.servo[0].angle = -90

def positionArmLR(pos):
    # control servo to move arm to pos from left possition to right
    kit.servo[0].angle = 180

def positionArmRM(pos):
    # control servo to move arm to pos from right possition to middle
    kit.servo[0].angle = -90
#Below will create an infinite loop


while True:
    match state:
        case 0:
            initialize()
            state = 10
        case 10: 
            positionArmML()
            state = 20
        case 20:
            positionArmLR()
            state = 30
        case 30:
            positionArmRM()
            state = 40
        case 40:
            exit()