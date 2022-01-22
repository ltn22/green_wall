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
        prev_value += e
        
        back_time += period

        data_list.append({"resource": res_name,
                          "data" : prev_value*factor,
                          "ts": back_time*1000} )
        
    pprint.pprint (data_list)
    
    bbt.writeBulk(channel, data_list)

class humidity_sensor(resource.PathCapable):

    async def render(self, request):
        print ("render", request.opt.uri_path)
        unique_id = request.opt.uri_path[0]
    
        print ("The unique id is: " + unique_id)

        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']

        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            measurements = cbor.loads(request.payload)
            current_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
            #if not found, add the device details in the device table in MongoDB 
            device = client.green_wall.devices.find_one({"unique_id": unique_id})
            if device:
                newvalues = { "$set": { "last_updated_at": current_time } }
                client.green_wall.devices.update_one({"unique_id": unique_id}, newvalues)
            else:    
                device_data = { "unique_id": unique_id, "last_updated_at": current_time, "name": "NA"}
                client.green_wall.devices.insert_one(device_data)
                device = client.green_wall.devices.find_one({"unique_id": unique_id})
            
            current_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
            sensor_counter = 1
            sensor_pin_counter = 13
            # store the measurements with relation to device and sensors
            for m in measurements:
                sensor_name = "S" + str(sensor_counter) + "P"+ str(sensor_pin_counter)
                sensor = client.green_wall.sensors.find_one({"name": sensor_name, "device_id": device['_id']})
                if sensor:
                    newvalues = { "$set": { "last_updated_at": current_time } }
                    client.green_wall.sensors.update_one({"_id": sensor['_id']}, newvalues)    
                else:    
                    sensor_data = { "name":sensor_name, "device_id": device['_id'], "last_updated_at": current_time}
                    client.green_wall.sensors.insert_one(sensor_data)
                    sensor = client.green_wall.sensors.find_one({"name": sensor_name, "device_id": device['_id']})
                #add the measurement for the sensor
                measurement_data = { "sensor_id": sensor['_id'], "type": "humidity", "value": m, "recorded_at": current_time}
                client.green_wall.measurements.insert_one(measurement_data)
                sensor_counter += 1
                sensor_pin_counter += 1
            # store the measurements for raw data collection
            device_data = { "device_id": device['_id'],
                        "measures": measurements,
                        "recorded_at" :  datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()}
            client.green_wall.devicemeasures.insert_one(device_data)    

        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)

        return aiocoap.Message(code=aiocoap.CHANGED)


    async def needs_blockwise_assembly(self, request):
        return False

# logging setup
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)


class watering_info(resource.Resource):

    async def render_post(self, request): 
        print ("render", request.opt.uri_path)

        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']
     
        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            #the device_name sent by actuator controller can be used to calculate average humidity
            device_name = cbor.loads(request.payload)        

        ic = 0
        totalh = 0
        #fetch the humidity levels for all the pycom sensors
        humidity_levels = []
        for d in client.green_wall.devices.find():
            humidity_level = {}
            humidity_level['device_name'] = d['name']
            latest_measures = client.green_wall.devicemeasures.find_one({"device_id":d['_id']},{"sort": {"natural": -1}})
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

    root.add_resource(['humidity'], humidity_sensor())
    root.add_resource(['watering'], watering_info())

    #Uncomment next line to use Default CoAP port
    #asyncio.Task(aiocoap.Context.create_server_context(root))
    #Comment next line to use Default CoAP port 
    asyncio.Task(aiocoap.Context.create_server_context(root,bind=(ip_addr, port)))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()