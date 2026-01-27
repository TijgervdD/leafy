import sys
import time
from pyrf24 import RF24, RF24_PA_MIN

# Setup voor Pi 5: CE op GPIO 25, CSN op SPI0 (CE0 / GPIO 8)
radio = RF24(25, 0)
#pipes = [[0xE0, 0xE0, 0xF1, 0xF1, 0xE0], [0xF1, 0xF1, 0xF0, 0xF0, 0xE0]]


# Adres MOET exact "0001" zijn zoals in je Arduino code (5 bytes totaal) 
address = b"4570x00" 

humidi = 0

def setup():
    # Try to initialize
    if not radio.begin():
        print("FOUT: nRF24L01 niet gevonden!")
        sys.exit()
    
    # radio.setChannel(0x76)
    # radio.setDataRate(RF24_250KBPS)
    # Lower the data rate to make it more resistant to noise
    # radio.setPALevel(RF24_PA_MIN)
    
    # We openen pipe 1 om te luisteren naar het adres van de zender
    radio.openReadingPipe(1, address)

    radio.setPALevel(RF24_PA_MIN)
    
    # Optioneel: zorg dat de datasnelheid gelijk is (standaard 1Mbps)
    # radio.setDataRate(RF24_1MBPS)

    radio.startListening()
    
    print("--- Pi 5 Ontvanger Status ---")
    radio.printDetails()
    print("-----------------------------")
    print(f"Luisteren op adres: {address}")

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
                    humidi = ord(text)
                    print(humidi)
            except Exception as e:
                print(f"Data ontvangen (geen tekst): {payload}")
        
        time.sleep(0.01)

if __name__ == "__main__":
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        print("\nOntvanger gestopt.")
