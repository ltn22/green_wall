import network
import time

# setup as a station
wlan = network.WLAN(mode=network.WLAN.STA)

wlan.ifconfig(config=('10.51.0.245', '255.255.255.0', '10.51.0.1', '192.108.119.134'))

#wlan.connect('RSM-B25', auth=(network.WLAN.WEP, 'df72f6ce24'))
#wlan.connect('lala', auth=(network.WLAN.WPA2, '12341234'))
wlan.connect('RSM-B25', auth=(network.WLAN.WPA2, 'df72f6ce24'))

while not wlan.isconnected():
    time.sleep_ms(50)
print(wlan.ifconfig())
