import RPi.GPIO as GPIO
from gpiozero import PWMOutputDevice
from time import sleep
import pygame
import sys
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper


def clockwise():

	global arr1
	global arr2
	
	# rotating array for stepper control
	arrOUT = arr1[3:] + arr1[:3]
	arr1 = arr2
	arr2 = arrOUT
	
	# send pulse to GPIO pins
	GPIO.output(chan_list, arrOUT)
	sleep(DELAY)
	
	return True
	
def counterclockwise():
	global arr1
	global arr2
	
	arrOUT = arr1[1:] + arr1[:1]
	arr1 = arr2
	arr2 = arrOUT
	
	GPIO.output(chan_list, arrOUT)
	sleep(DELAY)
	
	return True

def double_clockwise():

	kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
	kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
	sleep(DELAY)

	return True

def double_counterclockwise():

	kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
	kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
	sleep(DELAY)

	return True


if __name__ == '__main__':

	pygame.init()

	# delay between steps of the motors
	DELAY = 0.001
	chan_list = [23, 27, 18, 17]
	chan_list.reverse()
	
	# used for turning motors on and off
	ENA = PWMOutputDevice(25)
	ENB = PWMOutputDevice(24)

	pygame.display.set_mode((100, 100))

	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)

	for pin in chan_list:
		print(f'setup pin: {pin}')
		GPIO.setup(pin, GPIO.OUT)

	# pin control for middle motor
	arr1 = [1, 1, 0, 0]
	arr2 = [0, 1, 1, 0]

	# control for left and right motors
	kit = MotorKit()

	try:

		x_axis_forward = False
		x_axis_backward = False
		y_axis_forward = False
		y_axis_backward = False

		while True:
			# pygame for capturing key events
			events = pygame.event.get()
			for event in events:

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_w:
						x_axis_forward = True
					elif event.key == pygame.K_s:
						x_axis_backward = True
					elif event.key == pygame.K_a:
						ENA.value = 1
						ENB.value = 1
						y_axis_forward = True
					elif event.key == pygame.K_d:
						ENA.value = 1
						ENB.value = 1
						y_axis_backward = True

				elif event.type == pygame.KEYUP:
					if event.key == pygame.K_w:
						x_axis_forward = False
					elif event.key == pygame.K_s:
						x_axis_backward = False
					elif event.key == pygame.K_a:
						ENA.value = 0
						ENB.value = 0
						y_axis_forward = False
					elif event.key == pygame.K_d:
						ENA.value = 0
						ENB.value = 0
						y_axis_backward = False

			if x_axis_forward:
				double_clockwise()
			if x_axis_backward:
				double_counterclockwise()

			if y_axis_forward:
				clockwise()
			if y_axis_backward:
				counterclockwise()

	except KeyboardInterrupt:
		print('Program stopped by user')
		GPIO.output(chan_list, (0, 0, 0, 0))
		GPIO.cleanup()
		sys.exit()