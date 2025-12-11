from RF24 import *
import struct

radio = RF24(25, 8)         # CE=GPIO7, CSN=CE0 (GPIO8)
pipes = [b"1Node", b"2Node"]  # Zorg dat deze gelijk zijn aan de Arduino

radio.begin()
radio.setPALevel(RF24_PA_LOW)
radio.setChannel(76)
radio.openReadingPipe(1, pipes[1])
radio.startListening()

print("Listening for humidity data...")

while True:
    if radio.available():
        received_payload = radio.read(32)  # Max 32 bytes
        message = received_payload.decode('utf-8').strip("\x00")
        print("Received:", message)
