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
from app.main_page_module.p_objects.thermostat import Thermo


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


@hvac_api.route('/thermostat_status_get', methods=['GET'])
@login_required
def thermostat_status_get():
    data_ = {}
    
    try:
        thermo_obj = Thermo(app.config['THERMOSTAT_SERVER'])
        thermo_status = thermo_obj.get_status()
                
        return jsonify(thermo_status), 200
    
    except Exception as e:
        app.logger.error(f"Error: {e}")      
        return "Error", 500


@hvac_api.route('/thermostat_startstop/<status>', methods=['GET'])
@login_required
def thermostat_startstop(status:str):
    data_ = {}
    
    if status not in ["1","0"]:
        status = "0"
    try:
        thermo_obj = Thermo(app.config['THERMOSTAT_SERVER'])
        thermo_status = thermo_obj.set_on_off(status)
        return jsonify(thermo_status), 200
    
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
        cities = Gears_obj.load_cities()
        app_config = Gears_obj.load_app_config()
        current_lat = app_config.get("current_location_latitude")
        current_long = app_config.get("current_location_longitude")
        
        cities_data = []
        local_weather = None
        hourly_weather = {}
        
        # Get hourly weather and local weather from current location
        warnings = []
        if current_lat is not None and current_long is not None:
            try:
                weather_obj = Open_W_obj(float(current_lat), float(current_long), 12)
                hourly_weather = weather_obj.hourly_object()
                if weather_obj.current:
                    current = weather_obj.current.copy()
                    current["outside_t"] = current.get("temp", 0)
                    current["inhouse_t"] = 24
                    local_weather = current
                
                # Check for temperature warnings in next 24 hours
                high_threshold = app_config.get("high_temp_threshold", 30.0)
                low_threshold = app_config.get("low_temp_threshold", 0.0)
                
                # Get next 24 hours of hourly data
                from datetime import datetime, timedelta
                now = datetime.now()
                next_24h = now + timedelta(hours=24)
                
                high_temp_found = False
                low_temp_found = False
                high_temp_value = None
                low_temp_value = None
                
                # Check all hourly data (weather_obj.hourly contains all hours, not just 12)
                for hour_str, hour_data in weather_obj.hourly.items():
                    try:
                        hour_time = datetime.strptime(hour_str, "%Y-%m-%dT%H:%M")
                        if now < hour_time <= next_24h:
                            temp = hour_data.get("temp", 0)
                            if not high_temp_found and temp > high_threshold:
                                high_temp_found = True
                                high_temp_value = temp
                            if not low_temp_found and temp < low_threshold:
                                low_temp_found = True
                                low_temp_value = temp
                            
                            # Track max/min for better warning messages
                            if high_temp_found and temp > high_temp_value:
                                high_temp_value = temp
                            if low_temp_found and temp < low_temp_value:
                                low_temp_value = temp
                    except Exception:
                        continue
                
                if high_temp_found:
                    warnings.append({
                        "type": "high",
                        "message": f"V naslednjih 24 urah bo temperatura nad {high_threshold}°C (do {high_temp_value:.1f}°C)"
                    })
                
                if low_temp_found:
                    warnings.append({
                        "type": "low",
                        "message": f"V naslednjih 24 urah bo temperatura pod {low_threshold}°C (do {low_temp_value:.1f}°C)"
                    })
                    
            except Exception as e:
                app.logger.warning(f"Error getting current location weather: {e}")
        
        # Get daily weather for all cities
        for city in cities:
            city_name = city.get("name", "Unknown")
            lat = city.get("latitude")
            long = city.get("longitude")
            
            if lat is None or long is None:
                app.logger.warning(f"City {city_name} missing latitude or longitude")
                continue
                
            weather_obj = Open_W_obj(lat, long, 12)
            
            city_weather = {
                "name": city_name,
                "current": {},
                "daily": {}
            }
            
            if weather_obj.current:
                current = weather_obj.current.copy()
                current["outside_t"] = current.get("temp", 0)
                current["inhouse_t"] = 24
                city_weather["current"] = current
            
            city_weather["daily"] = weather_obj.daily_object()
            cities_data.append(city_weather)
        
        data_["cities"] = cities_data
        data_["local"] = local_weather
        data_["hourly"] = hourly_weather
        data_["warnings"] = warnings
        
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