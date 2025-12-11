from gpiozero import OutputDevice
from time import sleep 
from multiprocessing import process 
import time 
import keyboard 

#pin definition 

IN1 = OutputDevice(14) 
IN2 = OutputDevice(15) 
IN3 = OutputDevice(18) 
IN4 = OutputDevice(23) 

step_seq= [ 
    [1,0,0,0], #first step: activates the first wire 
    [1,1,0,0], #second step: activates the first and second wire 
    [0,1,0,0], 
    [0,1,1,0], 
    [0,0,1,0], 
    [0,0,1,1], 
    [0,0,0,1], 
    [1,0,0,1] 
    ] 

def set_step(w1, w2, w3, w4): 
    IN1.value = w1 
    IN2.value = w2 
    IN3.value = w3 
    IN4.value = w4 

def step_motor(step, direction, delay): 
    for _ in range (steps): 
        for step in (step_seq if direction > 0 else reversed(step_seq)): 
            set_step(*step) 
            sleep(delay) 

try:
    while True:
        steps = int(input("Enter number of steps (e.g., 512 for one full revolution): "))
        direction = int(input("Enter direction ( 1 for forward, -1 for backward): "))
        delay = float(input("how faastt (0.01 is normal): "))
        step_motor(steps, direction, delay)
except KeyboardInterrupt:
    print("program stopped by user")

#steps = 512 #512 is 1 full rotation 
#direction = 1 # 1 is forward, -1 is backward #step_motor(steps, direction)