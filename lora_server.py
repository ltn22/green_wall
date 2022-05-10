import socket
import binascii
import cbor2 as cbor
from pymongo import MongoClient
import time
import datetime

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', 35584)) # 33033 + 2551 as the defined port on pycom device

client = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")


while True:
    data, addr = s.recvfrom(1500)
    # just skip the first element becauuse this is SCHC data
    j = cbor.loads(data[1:])
    
    device_name = j[0]
    dev_eui = j[1]
    measurements = j[2:]
    print ("the humidity data: ", measurements )
    current_time = str(datetime.datetime.utcnow())
    #if not found, add the device details in the device table in MongoDB 
    device = client.green_wall.devices.find_one({"dev_eui": dev_eui})
    if device:
        newvalues = { "$set": { "last_updated_at": current_time, "name": device_name } }
        client.green_wall.devices.update_one({"dev_eui": dev_eui}, newvalues)
    else:    
        device = client.green_wall.devices.find_one({"name": device_name})
        if device:
            newvalues = { "$set": { "last_updated_at": current_time, "dev_eui": dev_eui } }
            client.green_wall.devices.update_one({"name": device_name}, newvalues)
        else:    
            device_data = { "dev_eui": dev_eui, "last_updated_at": current_time, "name": device_name}
            client.green_wall.devices.insert_one(device_data)
            device = client.green_wall.devices.find_one({"dev_eui": dev_eui})
    
    sensor_pin_counter = 13
    # store the measurements with relation to device and sensors
    for m in measurements:
        sensor_name = device['name'] + "P"+ str(sensor_pin_counter)
        sensor = client.green_wall.sensors.find_one({"name": sensor_name, "device_id": device['_id']})
        if sensor:
            newvalues = { "$set": { "last_updated_at": current_time} }
            client.green_wall.sensors.update_one({"_id": sensor['_id']}, newvalues)    
        else:    
            sensor_data = { "name":sensor_name, "type":"humidity", "device_id": device['_id'],"pos_X":-1, "pos_Y":-1, "last_updated_at": current_time}
            client.green_wall.sensors.insert_one(sensor_data)
            sensor = client.green_wall.sensors.find_one({"name": sensor_name, "device_id": device['_id']})
        #add the measurement for the sensor
        relative_humidity = (m * 100 / 4096)
        measurement_data = { "sensor_id": sensor['_id'], "type": "humidity", "value": relative_humidity, "recorded_at": current_time}
        client.green_wall.measurements.insert_one(measurement_data)
        sensor_pin_counter += 1
    # store the measurements for raw data collection
    device_data = { "device_id": device['_id'],
                "measures": measurements,
                "recorded_at" :  datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()}
    client.green_wall.devicemeasures.insert_one(device_data)   

    s.sendto("Thanks for sending humidity measurements Pycom !".encode(), addr)