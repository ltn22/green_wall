from network import LoRa
import socket
import time
import pycom
import binascii
import struct
import sys
from machine import ADC

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


lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
#
mac = lora.mac()
print ('devEUI: ',  binascii.hexlify(mac))

# create an OTAA authentication parameters
app_eui = binascii.unhexlify(
     '0000000000000000'.replace(' ',''))

app_key = binascii.unhexlify(
     '11223344556677881122334490345245'.replace(' ',''))  # TTN
     #'11223344556677881122334455667788'.replace(' ',''))   # Acklio
#     '11 00 22 00 33 00 44 00 55 00 66 00 77 00 88 00'.replace(' ',''))   # chirpstack

pycom.heartbeat(False)
pycom.rgbled(0x101010) # white

# join a network using OTAA (Over the Air Activation)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(2.5)
    print('Not yet joined...')

pycom.rgbled(0x000000) # black

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setsockopt(socket.SOL_LORA,  socket.SO_CONFIRMED,  False)

MTU = 200
lorawan_MID = 1 # When SCHC is used for LORAWAN


# -----------------  SENSORS -----------------------

adc=ADC()

apin20 = adc.channel(pin="P20",attn=ADC.ATTN_11DB)
apin19 = adc.channel(pin="P19",attn=ADC.ATTN_11DB)
apin18 = adc.channel(pin="P18",attn=ADC.ATTN_11DB)
apin17 = adc.channel(pin="P17",attn=ADC.ATTN_11DB)
apin16 = adc.channel(pin="P16",attn=ADC.ATTN_11DB)
apin15 = adc.channel(pin="P15",attn=ADC.ATTN_11DB)
apin14 = adc.channel(pin="P14",attn=ADC.ATTN_11DB)
apin13 = adc.channel(pin="P13",attn=ADC.ATTN_11DB)


# ------------- SENDING DATA ------------------------
lorawan_MID = 1
REPORT_PERIOD = 60 # send a frame every 60 sample (1 hour)

# Offset are used to desynchronize sendings, and the value is != form 0
# at the first round, after the first sending offset is set to 0, but since
# buffers have different filling level, the desynchronization is kept. In the
# default configuration, one message is sent every 15 minutes.

message = [apin13(), apin14(), apin15(), apin16(), apin17(), apin18(), apin19(), apin20()]
print("Message Text: ", message)
uri_path = "moisture"

while True:
    pycom.rgbled(0x100000) # red
    s.setblocking(True)
    s.settimeout(10)

    try:
        """ SCHC compression for Sigfox, use rule ID 98 stored fPort,
        followed by MID on 4 bits and 4 bits for an index on Uri-path.
        the SCHC header is TTTT UUUU
        """
        uri_idx = ["moisture", "memory", "battery", None, None, None, None, None,
                    None, None, None, None, None, None, None, None].index(uri_path)

        schc_residue = (lorawan_MID << 4) | uri_idx # MMMM and UU

        lorawan_MID += 1
        lorawan_MID &= 0x0F # on 4 bits
        if lorawan_MID == 0: lorawan_MID = 1 # never use MID = 0

        msg = struct.pack("!B", schc_residue) # add SCHC header to the message
        msg += cbor.dumps(message)

        #msg = cbor.dumps(message)
        print ("length", len(msg), binascii.hexlify(msg))

        rule_ID = 98
        s.bind(rule_ID)
        s.send(msg)
        #s.send(cbor.dumps(m))
    except:
        print ('timeout in sending')

    pycom.rgbled(0x000010) # blue

    try:
        data = s.recv(64)
        print(data)
        pycom.rgbled(0x001000) # green
    except:
        print ('timeout in receive')
        pycom.rgbled(0x000000) # black


    s.setblocking(False)
    time.sleep (29)
