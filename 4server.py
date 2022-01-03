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

import aiocoap.resource as resource
import aiocoap

import cbor2 as cbor
import config_bbt #secret keys 
import beebotte

from pymongo import MongoClient

client = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")

sensor=client.green_wall.description2.find_one ({"@type":"sensor", "name": "pikachu_16"})
print (sensor)
sensor_desc = sensor["_id"]



bbt = beebotte.BBT(config_bbt.API_KEY, config_bbt.SECRET_KEY)

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

        mongo_doc = {
            "@type" : "measure",
            "value" : prev_value*factor,
            "date"  : back_time*1000,
            "sensor": sensor_desc
            }
        client.green_wall.measures2.insert_one(mongo_doc)
        
    pprint.pprint (data_list)
    
    bbt.writeBulk(channel, data_list)

class generic_sensor(resource.PathCapable):

    async def render(self, request):
        print ("render", request.opt.uri_path)
        devEUI = request.opt.uri_path[0]
        measurement = request.opt.uri_path[1]
        print ("KKKKKKKKKKK -----")
        print (devEUI, measurement)

        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']

        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            to_bbt(devEUI, measurement, cbor.loads(request.payload), period=60, factor=0.01)
        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)
        return aiocoap.Message(code=aiocoap.CHANGED)


    async def needs_blockwise_assembly(self, request):
        return False
        
class temperature(resource.Resource):
    async def render_post(self, request):

        print ("request temp", request, request.opt.content_format)
        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']

        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            to_bbt("home_office", "temperature", cbor.loads(request.payload), period=60, factor=0.01)
        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)
        return aiocoap.Message(code=aiocoap.CHANGED)

class ampere(resource.Resource):
    async def render_post(self, request):

        print ("request amp", request, request.opt.content_format)
        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']

        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            print ("cbor:", cbor.loads(request.payload))
            to_bbt("home_office", "ampere", cbor.loads(request.payload), period=60, factor=0.001)
        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)
        return aiocoap.Message(code=aiocoap.CHANGED)


class moisture(resource.Resource):
    async def render_post(self, request):

        qp = request.opt.uri_query()
        print ("KKKKKK :" + qp)
        print ("request mem", request, request.opt.content_format)
        ct = request.opt.content_format or \
                aiocoap.numbers.media_types_rev['text/plain']

        if ct == aiocoap.numbers.media_types_rev['text/plain']:
            print ("text:", request.payload)
        elif ct == aiocoap.numbers.media_types_rev['application/cbor']:
            j = cbor.loads(request.payload)

            mng_dat = {"measure": j,
                        "date" :  datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()}
            client.green_wall.raw2.insert_one(mng_dat)
            #to_bbt("home_office", "moisture", cbor.loads(request.payload), period=60, factor=1)

        else:
            print ("Unknown format")
            return aiocoap.Message(code=aiocoap.UNSUPPORTED_MEDIA_TYPE)
        return aiocoap.Message(code=aiocoap.CHANGED)

# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

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

    root.add_resource(['temp'], temperature())
    root.add_resource(['amp'], ampere())
    root.add_resource(['mo'], moisture())
    root.add_resource(['proxy'], generic_sensor())
    
    #Uncomment next line to use Default CoAP port
    #asyncio.Task(aiocoap.Context.create_server_context(root))
    #Comment next line to use Default CoAP port 
    asyncio.Task(aiocoap.Context.create_server_context(root,bind=(ip_addr, port)))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
