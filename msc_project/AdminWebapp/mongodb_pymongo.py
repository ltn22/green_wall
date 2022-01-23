from flask import Flask, render_template,url_for, redirect, jsonify, request, session
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired
from flask_pymongo import PyMongo
import os
from pymongo import MongoClient
import datetime
from datetime import timedelta
from dateutil import parser


app= Flask(__name__)


#To connect using a driver via the standard MongoDB URI
mongo = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")

# app.config["MONGO_DBNAME"] = 'green_wall'
# app.config["MONGO_URI"] = 'mongodb://gwen:thesard_errant@127.0.0.1'
app.config['SECRET_KEY'] = os.urandom(24)

#mongo = PyMongo(app)

#=============================================================
#From class from WTForms to handle adding and Updating database
#=============================================================
class AddForm(FlaskForm):
	name = StringField('name', validators = [InputRequired()])
	unique_id = StringField('unique_id', validators = [InputRequired()])

#===============================
#List all the users at home page
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

@app.route('/sensors/<device_id>')
def sensors(device_id):
	sensor_list = list(mongo.green_wall.sensors.find({"device_id":ObjectId(device_id)}))
	for s in sensor_list:
		sensor_last_updated_at = datetime.datetime.strptime(s['last_updated_at'], '%Y-%m-%d %H:%M:%S.%f')
		if sensor_last_updated_at < datetime.datetime.utcnow() - timedelta(seconds=300):
			s['status'] = 'Inactive'
		else:
			s['status'] = 'Active'
	return render_template("sensors_result.html",sensor_list=sensor_list)

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
#Create Document in the collection
#===================================

@app.route('/add', methods=["GET","POST"])
def add():
	form = AddForm()
	if form.validate_on_submit():
		name_field = form.name.data
		unique_id_field = form.unique_id.data
		data = ({'name':name_field, 'unique_id': unique_id_field, 'last_updated_at': str(datetime.datetime.utcnow())})
		devices = mongo.green_wall.devices
		devices.insert_one(data)
		return JSONEncoder().encode(data)
	return render_template("add_device.html", form = form)

#===================================
#Updating form
#===================================

@app.route('/updateform')
def updateform():
	id = request.args.get('id')
	devices = mongo.green_wall.devices
	result_id = devices.find_one({'_id':ObjectId(id)})
	form = AddForm(name=result_id['name'],unique_id=result_id['unique_id'])
	return render_template("update_device.html", form=form, id = id)

#===================================
#Updating Document in the collection
#===================================
from bson import json_util
@app.route('/update/<id>', methods=["POST"])
def update(id):
	devices = mongo.green_wall.devices
	form = AddForm()
	if form.validate_on_submit():
		result = devices.update_one({'_id':ObjectId(id)},{'$set':{'name':form.name.data, 'unique_id': form.unique_id.data}})
	return redirect(url_for('devices'))

#===================================
#deleting Document in the collection
#===================================

@app.route('/delete/<id>')
def delete(id):
	devices = mongo.green_wall.devices
	#delete all the sensors associated with this device
	mongo.green_wall.sensors.delete({"device_id":ObjectId(id)})
	#now delete the device itself
	delete_record = devices.delete_one({'_id':ObjectId(id)})
	return redirect(url_for('devices'))



if __name__=='__main__':
	app.run(host='0.0.0.0')




