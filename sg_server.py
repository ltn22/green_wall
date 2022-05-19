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



from pymongo import MongoClient

client = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")


battery_SOC = 0
battery_AC_consumption = 0


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
    global battery_SOC
    global battery_AC_consumption
    battery_SOC = JSONres['records']['bs'][0][1]
    print("The latest battery state of charge is: ", battery_SOC)
    batteryop_url = "https://vrmapi.victronenergy.com/v2/installations/176105/stats?type=custom&attributeCodes[]=o1"
    response = requests.get(batteryop_url, headers=headers)
    JSONres = response.json()
    battery_AC_consumption = round(JSONres['records']['o1'][0][1],2)
    print("The latest battery AC consumption is: ", battery_AC_consumption)

    async def needs_blockwise_assembly(self, request):
        return False

# logging setup
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)


class shed_status(resource.Resource):

    async def render_post(self, request): 
        global battery_SOC
        global battery_AC_consumption
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
            shed_status['BSOC'] = battery_SOC
            shed_status['AC_consumption'] = battery_AC_consumption
                
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
    
    root.add_resource(['shed_status'], shed_status())


    #Uncomment next line to use Default CoAP port
    #asyncio.Task(aiocoap.Context.create_server_context(root))
    #Comment next line to use Default CoAP port 
    asyncio.Task(aiocoap.Context.create_server_context(root,bind=(ip_addr, port)))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()