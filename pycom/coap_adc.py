"""
This program runs on Python3 in terminal mode and Lopy4. On LoPy4, it sends
information either on LoRaWAN Networks, Sigfox or Wi-Fi. Selection is done
with the variable SERVER (see below). If a BME280 is connected to the LoPY,
measurement are taken from the sensor, otherwise sensor's behavior is emulated.
On python terminal values are emulated.

Data are sent with CoAP on 4 different URI /temperature, /pressure, /humidity,
/memory. On Sigfox, the SCHC compression of the CoAP header is provided and only
one parameter is sent (it can be changed in the code). On LoRaWAN and Wi-Fi all
the parameters are sent on a full CoAP message. Downlink is limited to error
messages (4.xx and 5.xx) and not taken into account by the program.

"""
#SERVER = "LORAWAN" # change to your server's IP address, or SIGFOX or LORAWAN
#SERVER="SIGFOX"
SERVER = "79.137.84.149" # change to your server's IP address, or SIGFOX or LORAWAN
PORT   = 0x3a11
destination = (SERVER, PORT)

import CoAP
import socket
import time
import sys
import binascii

upython = (sys.implementation.name == "micropython")
print (upython, sys.implementation.name)
if upython:
    import kpn_senml.cbor_encoder as cbor #pycom
    import pycom
    import gc
    import struct
else:
    import cbor2 as cbor  # terminal on computer
    import psutil

#----- CONNECT TO THE APPROPRIATE NETWORK --------



sigfox = False
if SERVER == "LORAWAN":
    from network import LoRa

    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
    #
    mac = lora.mac()
    print ('devEUI: ',  binascii.hexlify(mac))

    # create an OTAA authentication parameters
    app_eui = binascii.unhexlify('0000000000000000'.replace(' ',''))
    app_key = binascii.unhexlify('11223344556677881122334455667788'.replace(' ',''))   # Acklio
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)

    pycom.heartbeat(False) # turn led to white
    pycom.rgbled(0x101010) # white

    # wait until the module has joined the network
    while not lora.has_joined():
        time.sleep(2.5)
        print('Not yet joined...')

    pycom.rgbled(0x000000) # black

    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
    s.setsockopt(socket.SOL_LORA,  socket.SO_CONFIRMED,  False)

    MTU = 200 # Maximun Transmission Unit, for DR 0 should be set to less than 50

elif SERVER == "SIGFOX":
    from network import Sigfox

    # initalise Sigfox for RCZ1 (You may need a different RCZ Region)
    sfx = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
    s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)

    MTU = 12
    print ("SIGFOX", binascii.hexlify(sfx.id()))
    sigfox = True

else: # WIFI with IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    MTU = 200 # maximum packet size, could be higher

# -----------------  SENSORS -----------------------

adc=ADC()

apin16 = adc.channel(pin="P16",attn=ADC.ATTN_11DB)
apin15 = adc.channel(pin="P15",attn=ADC.ATTN_11DB)
apin14 = adc.channel(pin="P14",attn=ADC.ATTN_11DB)
apin13 = adc.channel(pin="P13",attn=ADC.ATTN_11DB)


# ------------- SENDING DATA ------------------------

REPORT_PERIOD = 60 # send a frame every 60 sample (1 hour)

# Offset are used to desynchronize sendings, and the value is != form 0
# at the first round, after the first sending offset is set to 0, but since
# buffers have different filling level, the desynchronization is kept. In the
# default configuration, one message is sent every 15 minutes.



sigfox_MID = 1 # when SCHC is used for Sigfox
def send_coap_message(sock, destination, uri_path, message):
    if destination[0] == "SIGFOX": # do SCHC compression
        global sigfox_MID

        """ SCHC compression for Sigfox, use rule ID 0 stored on 2 bits,
        followed by MID on 4 bits and 2 bits for an index on Uri-path.

        the SCHC header is RRMMMMUU
        """
        uri_idx = ['temperature', 'pressure', 'humidity', 'memory'].index(uri_path)

        schc_residue = 0x00 # ruleID in 2 bits RR
        schc_residue |= (sigfox_MID << 2) | uri_idx # MMMM and UU

        sigfox_MID += 1
        sigfox_MID &= 0x0F # on 4 bits
        if sigfox_MID == 0: sigfox_MID = 1 # never use MID = 0

        msg = struct.pack("!B", schc_residue) # add SCHC header to the message
        msg += cbor.dumps(message)

        print ("length", len(msg), binascii.hexlify(msg))

        s.send(msg)
        return None # don't use downlink

    # for other technologies we wend a regular CoAP message
    coap = CoAP.Message()
    coap.new_header(type=CoAP.NON, code=CoAP.POST)
    coap.add_option (CoAP.Uri_path, uri_path)
    coap.add_option (CoAP.Content_format, CoAP.Content_format_CBOR)
    coap.add_option (CoAP.No_Response, 0b00000010) # block 2.xx notification
    coap.add_payload(cbor.dumps(message))
    coap.dump(hexa=True)
    answer = CoAP.send_ack(s, destination, coap)

    return answer

if destination[0] == "SIGFOX":
    coap_header_size = 1 # SCHC header size
else:
    coap_header_size = 25 #  coap header size approximated

print ("MTU size is", MTU, "Payload size is", MTU-coap_header_size, "samples ", REPORT_PERIOD)

# lets run it forever
while True:

    m = [apin13(), apin14(), apin15(), apin16()]
    print (m)
   
    send_coap_message (s, destination, "humidity", m)

    time.sleep (60) # wait for 1 minute.
