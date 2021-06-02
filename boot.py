import network
import time

# setup as a station
wlan = network.WLAN(mode=network.WLAN.STA)
wlan.connect('RSM-B25', auth=(network.WLAN.WEP, 'df72f6ce24'))

while not wlan.isconnected():
    time.sleep_ms(50)
print(wlan.ifconfig())
