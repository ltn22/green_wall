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
import requests
import aiocoap.resource as resource
import aiocoap
import cbor2 as cbor
import msc_config_bbt #secret keys 
import beebotte


from pymongo import MongoClient

client = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")


bbt = beebotte.BBT(msc_config_bbt.API_KEY, msc_config_bbt.SECRET_KEY)

def to_bbt(channel, res_name, data, factor=1, period=10, epoch=None):
    global bbt
    data_list = []
    for d in data:
        data_list.append({"resource": res_name,
                          "data" : d[1],
                          "ts": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d[0]))} )        
    pprint.pprint (data_list)  
    bbt.writeBulk(channel, data_list)

def get_VRM_data():
    #import urequests
    login_url = 'https://vrmapi.victronenergy.com/v2/auth/login'
    #batterysummary_url = "https://vrmapi.victronenergy.com/v2/installations/176105/widgets/Graph?attributeCodes[]=bs"
    batterysoc_url = "https://vrmapi.victronenergy.com/v2/installations/176105/stats?type=custom&attributeCodes[]=bs"
    login_string = '{"username":"charles.perno@imt-atlantique.net","password":"123456789"}'

    #use the name and password you log in to VRM with
    response = requests.post(login_url , login_string)
    token = json.loads(response.text)["token"]   
    headers = {'X-Authorization': "Bearer " + token }
    response = requests.get(batterysoc_url, headers=headers)
    JSONres = response.json()
    print("The latest battery state of charge is: ",JSONres['records']['bs'][0][1])
    batteryop_url = "https://vrmapi.victronenergy.com/v2/installations/176105/stats?type=custom&attributeCodes[]=OP1"
    response = requests.get(batterysoc_url, headers=headers)
    JSONres = response.json()
    print("The latest battery state of charge is: ",JSONres)
    # device_measures = client.green_wall.devicemeasures.find({'device_id':device['_id']},{'measures':1}).limit(10)
    # beebotte_data = []
    # for dm in device_measures:
    #     beebotte_data.append(dm['measures'][0])
    # print ("Looking for channel name: ", device['name'])
    #to_bbt('smart_grid', 'Batter_SOC', JSONres['records']['data']['144'], period=200, factor=0.0244) 

class humidity_sensor(resource.PathCapable):

    async def render(self, request):
        print ("render", request.opt.uri_path)
        if len(request.opt.uri_path) > 1 :
            device_name = request.opt.uri_path[0]
            unique_id = request.opt.uri_path[1]
        else:
            unique_id = request.opt.uri_path[0] 
            device_name = "capteurs"   
    
        print ("The unique id is: " + unique_id)
        current_time = str(datetime.datetime.utcnow())
        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']

        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            measurements = cbor.loads(request.payload)       
            #if not found, add the device details in the device table in MongoDB 
            device = client.green_wall.devices.find_one({"mac_address": unique_id})
            if device:
                newvalues = { "$set": { "last_updated_at": current_time } }
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

        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)

        return aiocoap.Message(code=aiocoap.CHANGED)


    async def needs_blockwise_assembly(self, request):
        return False

# logging setup
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)


class shed_status(resource.Resource):

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
            parameter_name = request_data[0]
        
        ic = 0
        totalh = 0
        #fetch the humidity levels for all the pycom sensors
        shed_status = {}
        if parameter_name == "BSOC":
            shed_status['BSOC'] = 90.50
                
        print("The shed parameters are: ", shed_status ) 
        #Compress this data using CBOR before sending it bback to watering pycom controller
        cbor_data = cbor.dumps(shed_status)    
        #send back the humidity levels to watering pycom
        return aiocoap.Message(code=aiocoap.CHANGED, payload = binascii.hexlify(cbor_data))

    async def needs_blockwise_assembly(self, request):
        return False

def main():
    # Resource tree creation
    root = resource.Site()

    get_VRM_data()
    """In the following lines, we added a block to use another port that is not 
    the default CoAP port, it will be substituted by the 5684 port temporarely
    as we make the corresponding tests (In order to do not affect Gwen's database 
    format"""
    # Comment following block code to use the default CoAP port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80)) # connect outside to get local IP address
        ip_addr = s.getsockname()[0]

    port = 5685
    print ("++++++++++++++++++++++++++++++++++++++++++++")
    print ("server running on ", ip_addr, "at port", port)
    #Comment up to here

    root.add_resource(['humidity'], humidity_sensor())
    root.add_resource(['shed_status'], shed_status())


    #Uncomment next line to use Default CoAP port
    #asyncio.Task(aiocoap.Context.create_server_context(root))
    #Comment next line to use Default CoAP port 
    asyncio.Task(aiocoap.Context.create_server_context(root,bind=(ip_addr, port)))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()