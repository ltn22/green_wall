from curses import mouseinterval
from distutils.log import debug
from flask import Flask, render_template,url_for, redirect, jsonify, request, session, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import InputRequired
from flask_pymongo import PyMongo
import os
from pymongo import MongoClient
import datetime
from datetime import timedelta
import csv


app= Flask(__name__)


#To connect using a driver via the standard MongoDB URI
mongo = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")

# app.config["MONGO_DBNAME"] = 'green_wall'
# app.config["MONGO_URI"] = 'mongodb://gwen:thesard_errant@127.0.0.1'
app.config['SECRET_KEY'] = os.urandom(24)

#mongo = PyMongo(app)

#=============================================================
#From class from WTForms to handle adding and Updating Devices
#=============================================================
class AddForm(FlaskForm):
    name = StringField('name', validators = [InputRequired()])
    #unique_id = StringField('unique_id', validators = [InputRequired()])


#=============================================================
#From class from WTForms to handle adding and Updating Sensors
#=============================================================
class AddSensorForm(FlaskForm):
    name = StringField('name', validators = [InputRequired()])
    stype = StringField('type', validators = [InputRequired()])
    position_x = IntegerField('pos_X', validators = [InputRequired()])
    position_y = IntegerField('pos_Y', validators = [InputRequired()])

#===============================
#Homepage
#===============================
@app.route('/')
def home():
    return render_template("home.html")

@app.route('/devices')
def devices():
    device_list = list(mongo.green_wall.devices.find())
    for d in device_list:
        device_last_updated_at = datetime.datetime.strptime(d['last_updated_at'], '%Y-%m-%d %H:%M:%S.%f')
        if device_last_updated_at < datetime.datetime.utcnow() - timedelta(seconds=300):
            d['status'] = 'Inactive'
        else:
            d['status'] = 'Active'			
    return render_template("devices_result.html",device_list=device_list)



#===============================
#Helper function to hande Bson
#===============================
import json
from bson import ObjectId
from bson.objectid import ObjectId
import bson 

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


#===================================
#Updating Device : GET
#===================================

@app.route('/updateform')
def updateform():
    id = request.args.get('id')
    devices = mongo.green_wall.devices
    result_id = devices.find_one({'_id':ObjectId(id)})
    form = AddForm(name=result_id['name'])
    return render_template("update_device.html", form=form, id = id)

#===================================
#Updating Device in the collection
#===================================
from bson import json_util
@app.route('/update/<id>', methods=["POST"])
def update(id):
    devices = mongo.green_wall.devices
    form = AddForm()
    if form.validate_on_submit():
        result = devices.update_one({'_id':ObjectId(id)},{'$set':{'name':form.name.data}})
    return redirect(url_for('devices'))

#===================================
#deleting Device in the collection
#===================================

@app.route('/delete/<id>')
def delete(id):
    devices = mongo.green_wall.devices
    #delete all the sensors associated with this device
    mongo.green_wall.sensors.remove({"device_id":ObjectId(id)})
    #now delete the device itself
    delete_record = devices.delete_one({'_id':ObjectId(id)})
    return redirect(url_for('devices'))


        
#===================================
#List all the sensors for a device : GET
#===================================

@app.route('/sensors/<device_id>')
def sensors(device_id):
    sensor_list = list(mongo.green_wall.sensors.find({"device_id":ObjectId(device_id)}))
    device_name = mongo.green_wall.devices.find_one({"_id":ObjectId(device_id)},{'name': 1})
    for s in sensor_list:
        sensor_last_updated_at = datetime.datetime.strptime(s['last_updated_at'], '%Y-%m-%d %H:%M:%S.%f')
        if sensor_last_updated_at < datetime.datetime.utcnow() - timedelta(seconds=300):
            s['status'] = 'Inactive'
        else:
            s['status'] = 'Active'
        last_recorded_value = list(mongo.green_wall.measurements.find({"sensor_id":s['_id']}).sort([('recorded_at', -1)]).limit(1))[0]  
        s['last_value'] = round(last_recorded_value['value'],2)
    return render_template("sensors_result.html",sensor_list=sensor_list, device_name = device_name['name'])


#===================================
#Updating Sensor : GET
#===================================

@app.route('/updatesensorform')
def updatesensorform():
    id = request.args.get('id')
    result_id = mongo.green_wall.sensors.find_one({'_id':ObjectId(id)})
    device_name = mongo.green_wall.devices.find_one({"_id":result_id['device_id']},{'name': 1})
    form = AddSensorForm(name=result_id['name'],stype=result_id['type'],position_x=result_id['pos_X'], position_y=result_id['pos_Y'])
    return render_template("update_sensor.html", form=form, id = id, device_name = device_name['name'])

#===================================
#Updating Sensor in the Database: POST
#===================================
from bson import json_util
@app.route('/updatesensor/<id>', methods=["POST"])
def updatesensor(id):
    sensor = mongo.green_wall.sensors.find_one({'_id':ObjectId(id)})
    form = AddSensorForm()
    if form.validate_on_submit():
        result = mongo.green_wall.sensors.update_one({'_id':ObjectId(id)},{'$set':{'name':form.name.data, 'type': form.stype.data, 'pos_X': form.position_x.data, 'pos_Y': form.position_y.data}})
    return redirect(url_for('sensors',device_id=sensor['device_id']))

#===================================
#deleting Sensor in the collection
#===================================

@app.route('/deletesensor/<id>')
def deletesensor(id):
    device = mongo.green_wall.sensors.find_one({'_id':ObjectId(id)})
    delete_record = mongo.green_wall.sensors.delete_one({'_id':ObjectId(id)})
    return redirect(url_for('sensors',device_id=device['_id']))


#===================================
# Method to show a Heatmap of Wall
#===================================
@app.route('/uploadsensormap', methods=['GET', 'POST'])
def uploadsensormap():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        #extension = os.path.splitext(uploaded_file.filename)[1]
        if uploaded_file.filename != '':
            uploaded_file.save('./static/images/sensor_map.jpg')
        return render_template('upload_sensor_map.html', message="Sensor Map Updated !")
    return render_template('upload_sensor_map.html')

@app.route('/showsensormap')
def showsensormap():
    map_filepath = './static/images/sensor_map.jpg'
    if os.path.exists(map_filepath):
        return render_template('show_sensor_map.html', map_exists = True, sensor_map_image = map_filepath)
    else:
        return render_template('show_sensor_map.html', map_exists = False)   


@app.route('/heatmap')
def heatmap():
    device_list = list(mongo.green_wall.devices.find({"name":{"$in":["LP1","LP2"]}}))
    sensor_list = list(mongo.green_wall.sensors.find({"device_id":{"$in":[ObjectId(device_list[0]['_id']),ObjectId(device_list[1]['_id'])]}}).sort([("pos_Y",-1),("pos_X",1)]))
    for s in sensor_list:
        #sensor_last_updated_at = datetime.datetime.strptime(s['last_updated_at'], '%Y-%m-%d %H:%M:%S.%f')
        last_recorded_value = list(mongo.green_wall.measurements.find({"sensor_id":s['_id']}).sort([('recorded_at', -1)]).limit(1))[0]  
        s['last_value'] = round(last_recorded_value['value'],2)	
        s['humidity_level'] = getHumidityLevel(s['last_value'])	
    return render_template("wall_heatmap.html",sensor_list=sensor_list, sensor_count = len(sensor_list))




#===================================
# Method to generate sensor report
#===================================

@app.route('/reports')
def reports():
    return render_template("reports.html")


@app.route('/sensor_report')
def sensor_report():
    sensor_list = list(mongo.green_wall.sensors.find({}))
    field_names = ['_id','name','type','pos_X','pos_Y','last_updated_at']
    with open('report_files/sensor_data.csv', 'w', newline='') as f_output:
        csv_output = csv.writer(f_output, delimiter=",")
        csv_output.writerow(field_names)
        for data in sensor_list:
            csv_output.writerow([
                data['_id'],
                data['name'],
                data['type'],
                data['pos_X'],
                data['pos_Y'],
                data['last_updated_at']])
    return send_file('report_files/sensor_data.csv', as_attachment=True)      

@app.route('/measurement_report')
def measurement_report():
    measurements = list(mongo.green_wall.measurements.find().sort([('recorded_at', -1)]).limit(5000))
    field_names = ['_id','sensor_id','type','value','recorded_at']
    with open('report_files/measurement_data.csv', 'w', newline='') as f_output:
        csv_output = csv.writer(f_output, delimiter=",")
        csv_output.writerow(field_names)
        for data in measurements:
            csv_output.writerow([
                data['_id'],
                data['sensor_id'],
                data['type'],
                data['value'],
                data['recorded_at']])
    return send_file('report_files/measurement_data.csv', as_attachment=True)  


def getHumidityLevel(humidity):
    humidity_level = ''
    if humidity > 75.0:
        humidity_level = "moist"
    elif humidity > 50.0:
        humidity_level = "normal"
    elif humidity > 25.0:
        humidity_level = "dry"
    else:
        humidity_level = "severe"
    return humidity_level            

if __name__=='__main__':
    app.run(host='0.0.0.0', debug=True)




