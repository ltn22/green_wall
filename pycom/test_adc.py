from machine import ADC
import time


adc=ADC()

apin16 = adc.channel(pin="P16",attn=ADC.ATTN_11DB)
apin15 = adc.channel(pin="P15",attn=ADC.ATTN_11DB)
apin14 = adc.channel(pin="P14",attn=ADC.ATTN_11DB)
apin13 = adc.channel(pin="P13",attn=ADC.ATTN_11DB)

while True:
  print(apin13(), apin14(), apin15(), apin16())
  time.sleep(5)
