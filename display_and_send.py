import socket
import binascii
import cbor2 as cbor

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', 35584)) # 33033 + 2551 as the defined port on pycom device

while True:
    data, addr = s.recvfrom(1500)
    j = cbor.loads(data[1:])
    # just skip the first element becauuse this is SCHC data
    print ("the humidity data: ", j)
    s.sendto("Thanks for sending humidity measurements Pycom !".encode(), addr)