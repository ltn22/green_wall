from flask import Flask, render_template,url_for, redirect, jsonify, request, session
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired
from flask_pymongo import PyMongo
import os
from pymongo import MongoClient


app= Flask(__name__)


#To connect using a driver via the standard MongoDB URI
mongo = MongoClient("mongodb://gwen:thesard_errant@127.0.0.1")

# app.config["MONGO_DBNAME"] = 'green_wall'
# app.config["MONGO_URI"] = 'mongodb://gwen:thesard_errant@127.0.0.1'
# app.config['SECRET_KEY'] = os.urandom(24)

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
@app.route('/home')
def index():
	device_list = mongo.green_wall.devices.find()
	return render_template("result.html",device_list=device_list)

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
		data = ({'name':name_field, 'unique_id': unique_id_field})
		devices = mongo.green_wall.devices
		devices.insert(data)
		return JSONEncoder().encode(data)
	return render_template("add.html", form = form)

#===================================
#Updating form
#===================================

@app.route('/updateform')
def updateform():
	id = request.args.get('id')
	devices = mongo.green_wall.devices
	result_id = devices.find_one({'_id':ObjectId(id)})
	form = AddForm(name=result_id['name'],unique_id=result_id['unique_id'])
	return render_template("update.html", form=form, id = id)

#===================================
#Updating Document in the collection
#===================================
from bson import json_util
@app.route('/update/<id>', methods=["POST"])
def update(id):
	devices = mongo.green_wall.devices
	form = AddForm()
	if form.validate_on_submit():
		result = devices.update({'_id':ObjectId(id)},{'$set':{'name':form.name.data, 'unique_id': form.unique_id.data}})
	return render_template("update.html",id=id,form=form)

#===================================
#deleting Document in the collection
#===================================

@app.route('/delete/<id>')
def delete(id):
	devices = mongo.green_wall.devices
	delete_record = devices.delete_one({'_id':ObjectId(id)})
	return redirect(url_for('index'))



if __name__=='__main__':
	app.run(host='0.0.0.0')




