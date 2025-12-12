from RF24 import *
import time

# CE = GPIO25, CSN = CE0 (GPIO8) – zoals gebruikelijk op de Pi
radio = RF24(25, 8)

address = b"00001"   # zelfde adres als op Arduino

# -------------------------------------------------------------
# INITIALISATIE
# -------------------------------------------------------------
radio.begin()
radio.setPALevel(RF24_PA_MIN)
radio.setChannel(76)   # default kanaal, mag je aanpassen (Arduino gebruikt ook default)
radio.openReadingPipe(1, address)
radio.startListening()

print("NRF24 Receiver gestart – wacht op berichten...")

# -------------------------------------------------------------
# LOOP
# -------------------------------------------------------------
while True:
    if radio.available():
        # Lees max 32 bytes (standaard RF24 payload)
        received = radio.read(32)

        # Verwijder null-bytes en decodeer naar string
        message = received.decode('utf-8', errors='ignore').rstrip('\x00')

        print("Ontvangen:", message)

    time.sleep(0.01)
