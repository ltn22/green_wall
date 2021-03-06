#!/usr/bin/env python3

# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

"""This is a usage example of aiocoap that demonstrates how to implement a
simple server. See the "Usage Examples" section in the aiocoap documentation
for some more information."""
import sys
sys.path.insert(1, "aiocoap")


import datetime
import time
import logging
import binascii
import pprint
import asyncio
import socket
import json

import aiocoap.resource as resource
import aiocoap

import cbor2 as cbor
import msc_config_bbt #secret keys 
import beebotte


from pymongo import MongoClient

client = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")


bbt = beebotte.BBT(msc_config_bbt.API_KEY, msc_config_bbt.SECRET_KEY)

def to_bbt(channel, res_name, cbor_msg, factor=1, period=10, epoch=None):
    global bbt
    
    prev_value = 0
    data_list = []
    if epoch:
        back_time = epoch
    else:
        back_time = time.mktime(datetime.datetime.now().timetuple())
    
    back_time -= len(cbor_msg)*period

    for e in cbor_msg:
        
        back_time += period

        data_list.append({"resource": res_name,
                          "data" : e*factor,
                          "ts": back_time*1000} )
        
    pprint.pprint (data_list)
    
    bbt.writeBulk(channel, data_list)

def save_measurements(device, measurements):
    sensor_pin_counter = 13
    current_time = str(datetime.datetime.utcnow())
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
        relative_humidity = round((m * 100 / 4096),2)
        measurement_data = { "sensor_id": sensor['_id'], "type": "humidity", "value": relative_humidity, "recorded_at": current_time}
        client.green_wall.measurements.insert_one(measurement_data)
        sensor_pin_counter += 1
    # store the measurements for raw data collection
    device_data = { "device_id": device['_id'],
                "measures": measurements,
                "recorded_at" :  datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()}
    client.green_wall.devicemeasures.insert_one(device_data)   
    #send data to beebotte
    device_measures = client.green_wall.devicemeasures.find({'device_id':device['_id']},{'measures':1}).limit(10)
    beebotte_data = []
    for dm in device_measures:
        beebotte_data.append(dm['measures'][0])
    print ("Looking for channel name: ", device['name'])
    to_bbt(device['name'], 'humidity', measurements, period=200, factor=0.0244) 


class humidity_wifi(resource.PathCapable):

    async def render(self, request):
        print("HERE in HUMIDITY Wifi")
        print("Request details:", request.opt)
        print ("render", request.opt.uri_path)
        unique_id = request.opt.uri_path[0] 
        print ("The unique id is: ", unique_id)

        current_time = str(datetime.datetime.utcnow())
        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']
        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            data = cbor.loads(request.payload)    
            device_name = data[0]   # temporary device name 
            measurements = data[1:] 
            #if not found, add the device details in the device table in MongoDB 
            device = client.green_wall.devices.find_one({"mac_address": unique_id})
            if device:
                newvalues = { "$set": { "last_updated_at": current_time, "name": device_name } }
                client.green_wall.devices.update_one({"mac_address": unique_id}, newvalues)
            else: 
                device = client.green_wall.devices.find_one({"name": device_name})
                if device:
                    newvalues = { "$set": { "last_updated_at": current_time, "mac_address": unique_id } }
                    client.green_wall.devices.update_one({"name": device_name}, newvalues)   
                else:    
                    device_data = { "mac_address": unique_id, "last_updated_at": current_time, "name": device_name}
                    client.green_wall.devices.insert_one(device_data)
                    device = client.green_wall.devices.find_one({"mac_address": unique_id})
            save_measurements(device, measurements)
        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)

        return aiocoap.Message(code=aiocoap.CHANGED)


    async def needs_blockwise_assembly(self, request):
        return False

class humidity_lora(resource.PathCapable):

    async def render(self, request):
        print("HERE in HUMIDITY LORA")
        print("Request details:", request.opt)
        print ("render", request.opt.uri_path)
        unique_id = request.opt.uri_path[0] 
        print ("The unique id is: ", unique_id)
        current_time = str(datetime.datetime.utcnow())
        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']
        print("Content Type is: ", ct)
        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
            data = cbor.loads(request.payload) 
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            data = cbor.loads(request.payload)    
        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)
        print("The LORAWAN data is:", data)
        device_name = data[0]  
        print("The device name is:", device_name)
        measurements = data[1:] 
        #if not found, add the device details in the device table in MongoDB 
        device = client.green_wall.devices.find_one({"dev_eui": unique_id})
        if device:
            newvalues = { "$set": { "last_updated_at": current_time, "name": device_name } }
            client.green_wall.devices.update_one({"dev_eui": unique_id}, newvalues)
        else: 
            device = client.green_wall.devices.find_one({"name": device_name})
            if device:
                newvalues = { "$set": { "last_updated_at": current_time, "dev_eui": unique_id } }
                client.green_wall.devices.update_one({"name": device_name}, newvalues)   
            else:    
                device_data = { "dev_eui": unique_id, "last_updated_at": current_time, "name": device_name}
                client.green_wall.devices.insert_one(device_data)
                device = client.green_wall.devices.find_one({"dev_eui": unique_id})
            save_measurements(device, measurements)

        return aiocoap.Message(code=aiocoap.CHANGED)


    async def needs_blockwise_assembly(self, request):
        return False        

# logging setup
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)


class watering_info(resource.Resource):

    async def render_post(self, request): 
        print ("render", request.opt.uri_path)
        current_time = str(datetime.datetime.utcnow())
        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']
     
        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            #the device_name sent by actuator controller can be used to calculate average humidity
            request_data = cbor.loads(request.payload)
            device_name = request_data[1]
            #if not found, add the actuator device details in the device table in MongoDB 
            unique_id = request_data[0]
            actuator_device = client.green_wall.devices.find_one({"mac_address": unique_id})
            if actuator_device:
                newvalues = { "$set": { "last_updated_at": current_time } }
                client.green_wall.devices.update_one({"mac_address": unique_id}, newvalues)
            else:    
                actuator_device_data = { "mac_address": unique_id, "last_updated_at": current_time, "name": "NA"}
                client.green_wall.devices.insert_one(actuator_device_data)
 
        ic = 0
        totalh = 0
        #fetch the humidity levels for all the pycom sensors
        humidity_levels = []
        if device_name == "ALL":
            devices = client.green_wall.devices.find()
        else:
            devices = client.green_wall.devices.find({"name":device_name})

        for d in devices:
                humidity_level = {}
                humidity_level['device_name'] = d['name']
                latest_measures = list(client.green_wall.devicemeasures.find({"device_id":d['_id']}).sort([('recorded_at', -1)]).limit(1))[0]
                for ms in latest_measures['measures']:
                    ic += 1
                    totalh += ms
                avg_humidity = totalh / ic    
                humidity_level['avg_humidity'] = avg_humidity
                humidity_levels.append(humidity_level)
                
        print("The Humidity Levels of Pycoms on the wall are: ", humidity_levels ) 
        #Compress this data using CBOR before sending it bback to watering pycom controller
        cbor_data = cbor.dumps(humidity_levels)    
        #send back the humidity levels to watering pycom
        return aiocoap.Message(code=aiocoap.CHANGED, payload = binascii.hexlify(cbor_data))

    async def needs_blockwise_assembly(self, request):
        return False

def main():
    # Resource tree creation
    root = resource.Site()

    """In the following lines, we added a block to use another port that is not 
    the default CoAP port, it will be substituted by the 5684 port temporarely
    as we make the corresponding tests (In order to do not affect Gwen's database 
    format"""
    # Comment following block code to use the default CoAP port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80)) # connect outside to get local IP address
        ip_addr = s.getsockname()[0]

    port = 5684
    print ("++++++++++++++++++++++++++++++++++++++++++++")
    print ("server running on ", ip_addr, "at port", port)
    #Comment up to here

    root.add_resource(['humidity_w'], humidity_wifi())
    root.add_resource(['humidity_l'], humidity_lora())
    root.add_resource(['watering'], watering_info())


    #Uncomment next line to use Default CoAP port
    #asyncio.Task(aiocoap.Context.create_server_context(root))
    #Comment next line to use Default CoAP port 
    asyncio.Task(aiocoap.Context.create_server_context(root,bind=("::", port)))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()