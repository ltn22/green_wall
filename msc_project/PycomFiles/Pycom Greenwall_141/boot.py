import network
import time
import pycom
import os
import machine

# setup as a station
wlan = network.WLAN(mode=network.WLAN.STA)

#Starts a Yellow Flag to show it started booting
pycom.rgbled(0x7f7f00)
print("Scanning for known wifi nets")
wlan.ifconfig(config=('10.51.0.241', '255.255.255.0', '10.51.0.1', '192.108.119.134'))
#wlan.connect('lala', auth=(network.WLAN.WPA2, '12341234'))
wlan.connect('RSM-B25', auth=(network.WLAN.WEP, 'df72f6ce24'))
time.sleep_ms (500)


while not wlan.isconnected():
    print ("WiFi not connected")
    wlan.ifconfig(config=('10.51.0.241', '255.255.255.0', '10.51.0.1', '192.108.119.134'))
    #wlan.connect('lala', auth=(network.WLAN.WPA2, '12341234'))
    wlan.connect('RSM-B25', auth=(network.WLAN.WEP, 'df72f6ce24'))
    time.sleep(1)
    pycom.rgbled(0x7f0000) # red
    time.sleep(1)
    pycom.rgbled(0x000000) # turn off led
    #Shows a red light if not connected



#Once it connects, show a green light
print("")
print("***********************************************************************")
print("")
print("Pycom connected to WiFIi")
print(wlan.ifconfig())
pycom.rgbled(0x007f00) # green
print("")
print("***********************************************************************")
time.sleep(6)
pycom.rgbled(0x000000) # go ledd off
