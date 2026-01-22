import time
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

kit = MotorKit()

def move_stepper(direction, steps, speed):
    """
    direction: 'forward' or 'backward'
    steps: number of steps to move
    speed: delay in seconds (lower = faster)
    """
    for _ in range(steps):
        if direction == "forward":
            kit.stepper2.onestep(direction=stepper.FORWARD)
        elif direction == "backward":
            kit.stepper2.onestep(direction=stepper.BACKWARD)
        else:
            print("Invalid direction! Use 'forward' or 'backward'")
            break
        
        time.sleep(speed)


if __name__ == "__main__":
    while True:
        direction = input("Enter direction (forward/backward): ").strip().lower()
        steps = int(input("Enter number of steps: "))
        speed = float(input("Enter speed (seconds per step, e.g. 0.01): "))

        move_stepper(direction, steps, speed)
        print("Movement complete!\n")
