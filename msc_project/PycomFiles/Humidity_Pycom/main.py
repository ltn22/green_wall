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

#device name
DEVICE_NAME = "LP3"

#Service for Gwen's database
SERVER = "79.137.84.149" # change to your server's IP address, or SIGFOX or LORAWAN
PORT   = 5683
destination = (SERVER, PORT)

#Service for Msc project
PORT2 = 5684
destination2 = (SERVER, PORT2)

# change your secondary network to SIGFOX or LORAWAN
SERVER2 = "LORAWAN"

# assign some IP addresses to the PyCOM devices
ipaddr='10.51.0.245'
#ipaddr='10.51.0.242'

import CoAP
import socket
import time
import sys
import binascii
import network
import pycom
import os
import machine

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

try:
    #----- CONNECT TO THE APPROPRIATE NETWORK(S) --------
    if SERVER2 == "LORAWAN":
        from network import LoRa

        lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
        mac = lora.mac()
        dev_eui = binascii.hexlify(mac)
        print ('devEUI: ',  dev_eui)

        # create an OTAA authentication parameters
        app_eui = binascii.unhexlify('0000000000000000'.replace(' ',''))
        app_key = binascii.unhexlify('11223344556677881122334490345245'.replace(' ',''))   # Acklio
        lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)

        pycom.heartbeat(False) # turn led to white
        pycom.rgbled(0x101010) # white

        connection_counter = 0

        # wait until the module has joined the network
        while not lora.has_joined() and connection_counter <= 30:
            time.sleep(2.5)
            print('Not yet joined...')
            connection_counter+=1

        pycom.rgbled(0x000000) # black

        s_lora = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        s_lora.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
        s_lora.setsockopt(socket.SOL_LORA,  socket.SO_CONFIRMED,  False)

        MTU = 200 # Maximun Transmission Unit, for DR 0 should be set to less than 50

    # WIFI with IP address
    s_wifi = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    wlan = network.WLAN(mode=network.WLAN.STA)
    MTU = 200 # maximum packet size, could be higher
    lorawan_MID = 1

    # -----------------  SENSORS -----------------------
    from machine import ADC
    adc=ADC()

    apin20 = adc.channel(pin="P20",attn=ADC.ATTN_11DB)
    apin19 = adc.channel(pin="P19",attn=ADC.ATTN_11DB)
    apin18 = adc.channel(pin="P18",attn=ADC.ATTN_11DB)
    apin17 = adc.channel(pin="P17",attn=ADC.ATTN_11DB)
    apin16 = adc.channel(pin="P16",attn=ADC.ATTN_11DB)
    apin15 = adc.channel(pin="P15",attn=ADC.ATTN_11DB)
    apin14 = adc.channel(pin="P14",attn=ADC.ATTN_11DB)
    apin13 = adc.channel(pin="P13",attn=ADC.ATTN_11DB)

except OSError as err:
    time.sleep(30)
    print("an error ocurred")
    print("OS error: {0}".format(err))
    machine.reset()

def send_coap_message(sock, destination, uri_path, message, unique_id = None):
    if destination == "LORAWAN": # do SCHC compression
        global lorawan_MID # /!\ change name to lorawan_token
        """ SCHC compression for LoraWAN, use rule ID 98 stored in fPort,
        followed by MID on 4 bits and 4 bits for an index on Uri-path.
        the SCHC header is MMMM UUUU
        """
        # uri_index = ["humidity_l", "temperature_l", "pressure_l", "memory_l", None, None, None, None, None,
        #           None, None, None, None, None, None, None,].index(uri_path)
        # print("uri_index",uri_index)
        print("MID", lorawan_MID)
        print("MID", bin(lorawan_MID))
        #schc_residue = (lorawan_MID << 4) | uri_index # MMMM and UUUU
        schc_residue = (lorawan_MID & 0xFF)
        print("SCHC_RESIDUE", bin(schc_residue))
        print("SCHC_RESIDUE normal", schc_residue)
        lorawan_MID += 1
        lorawan_MID &= 0x0F # on 4 bits
        if lorawan_MID == 0: lorawan_MID = 1 # never use MID = 0
        msg = struct.pack("!B", schc_residue) # add SCHC header to the message
        msg += cbor.dumps(message)
        print ("length", len(msg), binascii.hexlify(msg))
        rule_ID = 98
        sock.bind(rule_ID)
        sock.send(msg)
        return None # don't use downlink
    else:
        # for other technologies we wend a regular CoAP message
        coap = CoAP.Message()
        coap.new_header(type=CoAP.NON, code=CoAP.POST)
        coap.add_option(CoAP.Uri_path, uri_path)
        if unique_id:
            coap.add_option(CoAP.Uri_path, unique_id)
        # /proxy/mac_address
        coap.add_option (CoAP.Content_format, CoAP.Content_format_CBOR)
        coap.add_option (CoAP.No_Response, 0b00000010) # block 2.xx notification
        coap.add_payload(cbor.dumps(message))
        coap.dump(hexa=True)
        answer = CoAP.send_ack(sock, destination, coap)
        return answer

def add_measures(current_measures, historic_measures):
    for i in range(len(historic_measures)):
        historic_measures[i] = historic_measures[i] + current_measures[i]
    return historic_measures

def divide_measures(historic_measures, divisor):
    for i in range(len(historic_measures)):
        historic_measures[i] = int(historic_measures[i] / divisor)
    return historic_measures


lora_counter = 1
lora_divisor = 10
historic_measures = [0] * 8

while True:
    try:
        pycom.heartbeat(True) # turn led to heartbeat
        if(lora_counter % lora_divisor == 0):
            if not lora.has_joined():
                print("Trying to connect to LoRAWAN")
                lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)
                time.sleep(30)
            else:
                print("In LORA section")
                print("historic_measures: ", historic_measures)
                measures = divide_measures(historic_measures, lora_divisor - 1)
                print("Avg measures:", measures)
                measures.insert(0, DEVICE_NAME)
                print("Final LoRAWAN measures:", measures)
                send_coap_message (s_lora, "LORAWAN", "humidity_l", measures, dev_eui)
                historic_measures = [0] * 8
                print("Successful LoraWAN request sent.")
                time.sleep(30)
        else:
            if wlan.isconnected():
                print("Here is WiFi connected section")
                #send the mac address of the device as an indentifier
                mac_address = binascii.hexlify(wlan.mac()[0]).decode('utf-8')
                print("The mac address is: " + mac_address)
                print("The device IP adress is: " + ipaddr)
                current_measures = [apin13(), apin14(), apin15(), apin16(), apin17(), apin18(), apin19(), apin20()]
                print(current_measures)
                historic_measures = add_measures(current_measures, historic_measures)
                print("Current historic_measures: ", historic_measures)
                send_coap_message (s_wifi, destination, "moisture", current_measures)
                current_measures.insert(0, DEVICE_NAME)
                send_coap_message (s_wifi, destination2, "humidity_w", current_measures, mac_address)
                print("SUCCESS WiFi")
                time.sleep(200) # wait for 3 minutes 20 seconds
            else:
                print("Here is WiFi not connected section")
                pycom.heartbeat(False) # tu¸rn led to white
                print ("WiFi disconnected")
                wlan.ifconfig(config=(ipaddr, '255.255.255.0', '10.51.0.1', '192.108.119.134'))
                #wlan.connect('iPhone', auth=(network.WLAN.WPA2, 'vivianachima'))
                wlan.connect('RSM-B25', auth=(network.WLAN.WEP, 'df72f6ce24'))
                time.sleep(1)
                pycom.rgbled(0x7f0000) # red
                time.sleep(1)
                pycom.rgbled(0x000000) # turn off led
        lora_counter+=1

    except OSError as err:
        time.sleep(30)
        print("an error ocurred")
        print("OS error: {0}".format(err))
        machine.reset()
