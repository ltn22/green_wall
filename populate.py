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
    "Dimension" : [2.00, 1.00]
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

humidity_location = {
    "@type" : "humidity_loc",
    "position" :[1, 0.5],
    "wall" : wall_id,
    "collector": sensor_id,
    "hardware": "black arrow",
    "address": {"analog": 16}
    }

humidity_pos_id = add_elm(desc, "position", humidity_location)
print ("position", humidity_pos_id)

        
    
