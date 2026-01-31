# set the pipe address. this address shoeld be entered on the receiver alo
pipes = [[0xE0, 0xE0, 0xF1, 0xF1, 0xE0], [0xF1, 0xF1, 0xF0, 0xF0, 0xE0]]

radio = NRF24(GPIO, spidev.SpiDev())         #use the gpio pins

def setup():
    GPIO.setmode(GPIO.BCM)                      # set the gpio mode
    radio.begin(0, 15)                                      #start the radio and set the ce,csn pin ce= GPIO08, csn= GPIO25
    radio.setPayloadSize(32)                         #set the payload size as 32 bytes
    radio.setChannel(0x76)                            # set the channel as 76 hex
    radio.setDataRate(NRF24.BR_1MBPS)              #set radio data rate
    radio.setPALevel(NRF24.PA_LOW)                   #set PA level

    radio.setAutoAck(True)                                     # set acknowledgement as true 
    radio.enableDynamicPayloads()
    radio.enableAckPayload()

def main(args):
    setup()
    radio.openWritingPipe(pipes[0])                  # open the defined pipe for writing
    radio.printDetails()                                        #print basic detals of radio

    receptMessage = list("")

    sendMessage = list("Ola, estou na escuta!")                      #the message to be sent

    while len(sendMessage) < 32:
        sendMessage.append(0)

    while True :
        start = time.time()                                                             #start the time for checking delivery time
        radio.write(sendMessage)                                              # just write the message to radio
        print("Sent the message: {}".format(sendMessage))         #print a message after succesfull send
        radio.startListening() #Start listening the radio

        while not radio.available(0): 
            time.sleep(1/100)
            if time.time() - start > 2:
                print("Timed out.")                                   #print errror message if radio disconnected or not functioning anymore
                break

        if radio.available(0):
            print("Recebendo...\n")
            radio.read(receptMessage)                                 #just write the message to radio
            print(receptMessage)
        else:
           print("Nada para receber!\n")

        radio.stopListening()                      #close radio
        time.sleep(3)                       #give delay of 3 seconds

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
