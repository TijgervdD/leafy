 # If your serial output has these values same then Your nrf24l01 module is in working condition :
 
 # EN_AA          = 0x3f
 # EN_RXADDR      = 0x02
 # RF_CH          = 0x4c
 # RF_SETUP       = 0x03
 # CONFIG         = 0x0f
 
 # This code is under public domain
 
 # Last updated on 21/08/28
 # https://dhirajkushwaha.com/elekkrypt
 
import sys
import time
from pyrf24 import RF24, RF24_PA_MIN

# Setup voor Pi 5: CE op GPIO 25, CSN op SPI0 (CE0 / GPIO 8)
radio = RF24(25, 0)

# Adres MOET exact "0001" zijn zoals in je Arduino code (5 bytes totaal)
address = b"0001\x00" 

#def setup():

def setup():
  radio.begin()
  radio.openReadingPipe(1, address)
  radio.setPALevel(RF24_PA_MIN)
  radio.startListening()
  radio.printDetails()


def loop():
    while True:
        if radio.available():
            # We lezen 32 bytes (zoals de Arduino char buffer)
            payload = radio.read(32)
            
            try:
                # Decodeer de bytes en verwijder lege karakters
                text = payload.decode('utf-8').rstrip('\x00')
                if text:
                    print(f"Ontvangen: {text}")
            except Exception as e:
                print(f"Data ontvangen (geen tekst): {payload}")
        
        time.sleep(0.01)

if __name__ == "__main__":
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        print("\nOntvanger gestopt.")
