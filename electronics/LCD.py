"""
This Raspberry Pi code was developed by newbiely.com
This Raspberry Pi code is made available for public use without any restriction
For comprehensive instructions and wiring diagrams, please visit:
https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-lcd
"""


import lcddriver
from time import sleep

# I2C address 0x27, 16 column and 2 rows
LCD = lcddriver.lcd()

def display_message(line1, line2, duration):
    LCD.lcd_clear()
    LCD.lcd_display_string(line1, 1)
    LCD.lcd_display_string(line2, 2)
    sleep(duration)

try:
    while True:
        display_message("Newbiely", "newbiely.com", 2)
        display_message("DIYables", "www.diyables.io", 2)

except KeyboardInterrupt:
    pass

finally:
    LCD.lcd_clear()