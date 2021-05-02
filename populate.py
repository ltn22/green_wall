from pymongo import MongoClient

def add_elm(col, key_name, elm):
    print (elm)
    key ={}
    key["@type"] = elm["@type"]
    key[key_name] = elm[key_name]
    
    col.replace_one(key, elm, upsert=True)

    return col.find_one(key)["_id"]

client = MongoClient()
db = client ["green_wall"]
desc = db["description"]


res_wall = {
    "@type" : "green_wall",
    "name" : "IMT Lobby",
    "dimension" : [2.00, 1.00]
    }


wall_id = add_elm(desc, "name", res_wall)

print ("wall", wall_id, type(wall_id))

sensor = {
    "@type" : "sensor",
    "brand" : "LoPy4",
    "name"  : "pikachu_16",
    "dev_id" : "1234567812345678"
}

sensor_id = add_elm(desc, "name", sensor)
print ("sensor", sensor_id)

for pos, pin in [([1, 0], 15), ([1, 0.5], 16), ([1, 1], 14), ([1, 1.5], 13),
                 ([1.5, 0], 15), ([1.5, 0.5], 16), ([1.5, 1], 14), ([1.5, 1.5], 13),
                 ([2, 0], 15), ([2, 0.5], 16), ([2, 1], 14), ([2, 1.5], 13)]:
    humidity_location = {
        "@type" : "humidity_loc",
        "position" :pos,
        "wall" : wall_id,
        "collector": sensor_id,
        "hardware": "black arrow",
        "address": {"analog": pin}
    }

    humidity_pos_id = add_elm(desc, "position", humidity_location)
    print ("position", humidity_pos_id)

        
    
