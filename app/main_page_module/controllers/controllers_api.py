import json

# Import flask dependencies
from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for, jsonify, send_file, Response, abort

# Import module forms
from app.main_page_module.forms import form_dicts
#from app.main_page_module.p_objects.note_o import N_obj


from wrappers import login_required
from app.pylavor import Pylavor
from app.main_page_module.other import Randoms
from app.main_page_module.gears import Gears_obj
from app.main_page_module.p_objects.open_meteo_o import Open_W_obj
from app.main_page_module.p_objects.systemair_server_connect import Sasc


from app import app, targets_ram

#import os
import re
import os
import zipfile
import io
import pathlib
from passlib.hash import sha512_crypt
import datetime


# Define the blueprint: 'auth', set its url prefix: app.url/auth
hvac_api = Blueprint('hvac_api', __name__, url_prefix='/api/')


@app.context_processor
def inject_to_every_page():
    
    return dict(Randoms=Randoms, datetime=datetime, Pylavor=Pylavor)


@hvac_api.route('/hvac_data_get', methods=['GET'])
@login_required
def hvac_data_get():
    data_ = {}
    
    try:
        hvac_obj = Sasc(app.config['SYSTEMAIR_SERVER'])
        hvac_data = hvac_obj.hvac_data()
        
        req_temperature = 24
        req_ventilation = 3
        stat_recuperator = True
        stat_heater = False
        stat_central_heater = True
        
        hvac = {}
        
        hvac["req_temperature"] = req_temperature
        hvac["req_ventilation"] = req_ventilation
        hvac["stat_recuperator"] = stat_recuperator
        hvac["stat_heater"] = stat_heater
        hvac["stat_central_heater"] = stat_central_heater

        hvac = {**hvac, **hvac_data}
                
        return jsonify(hvac), 200
    
    except Exception as e:
        app.logger.error(f"Error: {e}")      
        return "Error", 500
    
@hvac_api.route('/hvac_data_get', methods=['POST'])
@login_required
def hvac_data_set_vet_r_tmp():
    user_set_temp = request.form["user_set_temp"]
    user_set_ventilation = request.form["user_set_ventilation"]

    try:
        user_set_temp = int(user_set_temp)
        user_set_ventilation = int(user_set_ventilation)
        
        if not user_set_temp >= 12 and not user_set_temp <= 30:
            raise ValueError(f"Invalid number: {user_set_temp}. Temp must be between 12 and 30.")
        
        if user_set_ventilation not in [0, 2, 3, 4]:
            raise ValueError(f"Invalid number: {user_set_ventilation}. Must be 2, 3 or 4.")        
        
                
        hvac_obj = Sasc("192.168.0.111")
        user_set_temp = user_set_temp * 10
        server_http_code = hvac_obj.set_hvac_temp_vent(user_set_ventilation, user_set_temp)
            
        if int(server_http_code) in [200, 201]:
            return "", 200
        else:
            raise ValueError(f"Server error. stauts code: {server_http_code}.")        
            
    
    except Exception as e:
        app.logger.error(f"Error: {e}")      
        return "Error", 500


@hvac_api.route('/weather_home', methods=['GET'])
@login_required
def weather_home():
    data_ = {}
    
    try:
        lat = 45.533421368837615
        long = 13.727852449587754
        weather_obj = Open_W_obj(lat, long, 2) 
        
        
        current = {}
        current = weather_obj.current
        
        current["outside_t"] = current["temp"]
        current["inhouse_t"] = 24
        current["icon"] = current["icon"]
        
        
        hourly = weather_obj.hourly
        
        
        data_["current"] = current
        data_["hourly"] = weather_obj.hourly_object()
        data_["daily"] = weather_obj.daily_object()
        
        return jsonify(data_), 200
    except Exception as e:
        app.logger.error(f"Error: {e}")      
        return "Error", 500
    
    


@hvac_api.route('/weather/<lat>/<long>', methods=['GET'])
@login_required
def weather(lat,long):
    # http://127.0.0.1:5000/api/weather/45.533421368837615/13.727852449587754
    #weather_obj = Open_W_obj(45.533421368837615, 13.727852449587754) 
    weather_obj = Open_W_obj(lat, long) 
    
    data_ = {}
    current = weather_obj.current
    
    data_["outside_t"] = current["temp"]
    data_["inhouse_t"] = 24
    data_["icon"] = current["icon"]
    
    return jsonify(data_)