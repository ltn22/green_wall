from machine import ADC
import time
import kpn_senml.cbor_encoder as cbor
import socket

s_wifi = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)

adc=ADC()

apin16 = adc.channel(pin="P16",attn=ADC.ATTN_11DB)
apin15 = adc.channel(pin="P15",attn=ADC.ATTN_11DB)
apin14 = adc.channel(pin="P14",attn=ADC.ATTN_11DB)
apin13 = adc.channel(pin="P13",attn=ADC.ATTN_11DB)

while True:
  measure = [apin13(), apin14(), apin15(), apin16()]
  print(measure)
  time.sleep(5)
