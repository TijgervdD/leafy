import smbus2
import time
import math
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# =======================
# MOTOR PIN SETUP
# =======================

IN1_M1 = 17
IN2_M1 = 27
EN_M1  = 18

IN1_M2 = 22
IN2_M2 = 25
EN_M2  = 13

motor_pins = [IN1_M1, IN2_M1, EN_M1, IN1_M2, IN2_M2, EN_M2]
for p in motor_pins:
    GPIO.setup(p, GPIO.OUT)

pwm1 = GPIO.PWM(EN_M1, 1000)
pwm2 = GPIO.PWM(EN_M2, 1000)
pwm1.start(0)
pwm2.start(0)

# =======================
# MPU6050 SETUP
# =======================

bus = smbus2.SMBus(1)
MPU_ADDR = 0x68

# WAKE THE MPU6050
bus.write_byte_data(MPU_ADDR, 0x6B, 0)

def read_word(reg):
    high = bus.read_byte_data(MPU_ADDR, reg)
    low = bus.read_byte_data(MPU_ADDR, reg+1)
    val = (high << 8) + low
    if val >= 0x8000:
        val -= 65536
    return val

def read_mpu():
    accel_x = read_word(0x3B)
    accel_y = read_word(0x3D)
    accel_z = read_word(0x3F)
    gyro_x  = read_word(0x43)
    gyro_y  = read_word(0x45)
    gyro_z  = read_word(0x47)

    Ax = accel_x / 16384.0
    Ay = accel_y / 16384.0
    Az = accel_z / 16384.0
    Gz = gyro_z / 131.0      # deg/sec

    return Ax, Ay, Az, Gz

# =======================
# MOTOR CONTROL
# =======================

def motors_forward(speed_left, speed_right):
    GPIO.output(IN1_M1, GPIO.HIGH)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.HIGH)
    GPIO.output(IN2_M2, GPIO.LOW)

    pwm1.ChangeDutyCycle(speed_left)
    pwm2.ChangeDutyCycle(speed_right)

def motors_stop():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

    GPIO.output(IN1_M1, GPIO.LOW)
    GPIO.output(IN2_M1, GPIO.LOW)
    GPIO.output(IN1_M2, GPIO.LOW)
    GPIO.output(IN2_M2, GPIO.LOW)

# =======================
# FORWARD MOTION WITH GYRO STABILITY & DISTANCE
# =======================

def move_forward_distance(distance_cm, base_speed=60):
    """
    Drive forward using:
    - gyro for heading correction
    - accelerometer integration for distance estimation
    """

    print(f"\nDriving {distance_cm} cm with gyro correction...")

    # ---- INITIAL ORIENTATION ----
    _, _, _, initial_gyro = read_mpu()
    target_heading = 0

    distance = 0
    velocity = 0
    last_time = time.time()

    # ---- CONTROL LOOP ----
    while distance < distance_cm:
        Ax, Ay, Az, Gz = read_mpu()

        now = time.time()
        dt = now - last_time
        last_time = now

        # Integrate gyro to track heading drift
        target_heading += Gz * dt

        # Corrective steering
        correction = target_heading * 0.8

        left_speed = base_speed - correction
        right_speed = base_speed + correction

        # Clamp speed
        left_speed = max(0, min(100, left_speed))
        right_speed = max(0, min(100, right_speed))

        motors_forward(left_speed, right_speed)

        # ---- Distance Estimation ----
        # Use forward acceleration Ay after removing gravity on slopes
        forward_accel = Ay

        velocity += forward_accel * 9.81 * dt      # m/s
        distance += velocity * dt * 100            # m → cm

        print(f"Distance: {distance:.1f} cm | Heading drift: {target_heading:.2f}°")

    motors_stop()
    print("Reached target distance.\n")

# =======================
# MAIN LOOP
# =======================

try:
    while True:
        print("Options:")
        print("d = drive distance (cm)")
        print("q = quit")

        cmd = input("> ")

        if cmd == "d":
            dist = float(input("Distance in cm: "))
            speed = int(input("Speed (0–100): "))
            move_forward_distance(dist, speed)

        elif cmd == "q":
            break

except KeyboardInterrupt:
    pass

motors_stop()
GPIO.cleanup()
print("Program exited cleanly.")
