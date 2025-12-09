import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# =====================
# PIN LAYOUT (your exact wiring)
# =====================

# Motor 1 pins
IN1_M1 = 17
IN2_M1 = 27
EN_M1  = 18   # PWM enable

# Motor 2 pins
IN1_M2 = 22
IN2_M2 = 25
EN_M2  = 13   # PWM enable

# Setup all pins
motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)

# PWM channels
pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)
pwm1.start(0)
pwm2.start(0)

# =====================
# Motor control functions
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
# Distance movement (cm)
# =====================

# DEFAULT SPEED CALIBRATION (CHANGE AFTER TESTING!)
# Example: robot moves 20 cm per second at 100% PWM
CM_PER_SEC_AT_100 = 20  

def move_distance_cm(distance_cm, speed):
    """
    Moves both motors forward for a given distance in cm.
    The distance is approximated using a fixed cm/sec speed.
    """
    if speed <= 0:
        print("Speed must be above 0%")
        return

    # Estimate travel speed based on PWM %
    speed_factor = speed / 100.0
    cm_per_sec = CM_PER_SEC_AT_100 * speed_factor

    # Compute required movement time
    move_time = distance_cm / cm_per_sec

    print(f"Moving forward {distance_cm} cm at {speed}% speed...")
    print(f"Estimated time: {move_time:.2f} seconds")

    motors_forward(speed)
    time.sleep(move_time)
    motors_stop()
    print("Movement complete.\n")

# =====================
# MAIN USER LOOP
# =====================

try:
    while True:
        print("\nOptions:")
        print("f = forward")
        print("b = backward")
        print("s = stop")
        print("d = move distance (cm)")
        print("q = quit")

        choice = input("Choose an option: ")

        if choice == "f":
            speed = int(input("Speed (0–100): "))
            motors_forward(speed)
            print(f"Both motors moving FORWARD at {speed}%")

        elif choice == "b":
            speed = int(input("Speed (0–100): "))
            motors_backward(speed)
            print(f"Both motors moving BACKWARD at {speed}%")

        elif choice == "s":
            motors_stop()
            print("Motors stopped")

        elif choice == "d":
            distance = float(input("Distance in cm: "))
            speed = int(input("Speed (0–100): "))
            move_distance_cm(distance, speed)

        elif choice == "q":
            break

        else:
            print("Invalid choice. Use f / b / s / d / q")

except KeyboardInterrupt:
    pass

motors_stop()
GPIO.cleanup()
print("Program exited safely.")
