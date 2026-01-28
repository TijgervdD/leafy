# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
"""Simple test for I2C RGB character LCD shield kit"""
import time
import board
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
# Modify this if you have a different sized Character LCD
lcd_columns = 16
lcd_rows = 2
# Initialise I2C bus.
i2c = board.I2C() # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C() # For using the built-in STEMMA QT connector on a
microcontroller
# Initialise the LCD class
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
lcd.clear()
# Set LCD color to red
lcd.color = [100, 0, 0]
time.sleep(1)
# Print two line message
lcd.message = "Hello\nCircuitPython"
# Wait 5s
time.sleep(5)
# Set LCD color to blue
lcd.color = [0, 100, 0]
time.sleep(1)
# Set LCD color to green
lcd.color = [0, 0, 100]
time.sleep(1)
# Set LCD color to purple
lcd.color = [50, 0, 50]
time.sleep(1)
lcd.clear()
# Print two line message right to left
lcd.text_direction = lcd.RIGHT_TO_LEFT
lcd.message = "Hello\nCircuitPython"
# Wait 5s
time.sleep(5)
# Return text direction to left to right
lcd.text_direction = lcd.LEFT_TO_RIGHT
# Display cursor
lcd.clear()
lcd.cursor = True