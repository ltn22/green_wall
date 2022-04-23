import network
import time
import pycom
import os
import machine


try:
    # setup as a station
    ipaddr='10.51.0.245'
    #ipaddr='10.51.0.242'
    wlan = network.WLAN(mode=network.WLAN.STA)
    #Starts a Yellow Flag to show it started booting
    pycom.heartbeat(False)
    pycom.rgbled(0x7f7f00)
    print("Scanning for known wifi nets")
    wlan.ifconfig(config=(ipaddr, '255.255.255.0', '10.51.0.1', '192.108.119.134'))
    #wlan.connect('iPhone', auth=(network.WLAN.WPA2, 'vivianachima'))
    wlan.connect('RSM-B25', auth=(network.WLAN.WEP, 'df72f6ce24'))
    time.sleep_ms (500)


    while not wlan.isconnected():
        print ("WiFi not connected")
        wlan.ifconfig(config=(ipaddr, '255.255.255.0', '10.51.0.1', '192.108.119.134'))
        wlan.connect('iPhone', auth=(network.WLAN.WPA2, 'vivianachima'))
        #wlan.connect('RSM-B25', auth=(network.WLAN.WEP, 'df72f6ce24'))
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

except OSError as err:
    time.sleep(30)
    print("an error ocurred")
    print("OS error: {0}".format(err))
    machine.reset()
