import spidev
import RPi.GPIO as GPIO  # If RPi.GPIO not available, use lgpio
from nrf24 import NRF24
import time

GPIO.setmode(GPIO.BCM)

radio = NRF24(GPIO, spidev.SpiDev())
radio.begin(0, 22)  # SPI bus 0, CE pin GPIO22
radio.setPayloadSize(8)
radio.setChannel(0x60)
radio.setDataRate(NRF24.BR_1MBPS)
radio.setPALevel(NRF24.PA_LOW)
radio.openReadingPipe(1, b"1Node")
radio.startListening()

print("NRF24 ready to receive")

while True:
    if radio.available():
        data = radio.read(8)
        print("Received:", data)
    time.sleep(0.1)
