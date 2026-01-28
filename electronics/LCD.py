import time
import board
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd

# 1. Use the absolute slowest stable I2C speed (10kHz)
i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)

# 2. Initialize
lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2, address=0x27)

# 3. Setup initial state
lcd.backlight = True
lcd.clear()
time.sleep(0.1) # Give it a moment to breathe

def safe_print(line1, line2):
    """
    Overwrites the screen without using lcd.clear() 
    to prevent the reset flicker.
    """
    # Pad strings to 16 characters to 'clear' old text
    l1 = "{:<16}".format(line1[:16])
    l2 = "{:<16}".format(line2[:16])
    
    # Send message as one block
    lcd.message = f"{l1}\n{l2}"

# --- RUN THE TEST ---
print("Running Flicker-Free Test...")

try:
    while True:
        safe_print("SYSTEM: STABLE", "VOLTAGE: GOOD")
        time.sleep(2)
        safe_print("NO CLEAR CMD", "USED HERE")
        time.sleep(2)
except Exception as e:
    print(f"Error: {e}")