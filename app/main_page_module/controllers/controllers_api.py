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
from app.main_page_module.p_objects.proxy_server_connect import ProxyServer
from app.main_page_module.p_objects.thermostat import Thermo
from app.main_page_module.p_objects.shelly_thermostat import ShellyThermostat
from app.main_page_module.p_objects.shelly_plug import ShellyPlug


from app import app, targets_ram

#import os
import re
import os
import zipfile
import io
import pathlib
from passlib.hash import sha512_crypt
import datetime
from datetime import date, timedelta


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
        app_config = Gears_obj.load_app_config()
        hvac_data_source = app_config.get("hvac_data_source", "systemair")
        
        # Use proxy server if configured, otherwise use systemair
        if hvac_data_source == "proxy":
            proxy_url = app_config.get("proxy_server_ip", "http://proxy-server:5000")
            hvac_obj = ProxyServer(proxy_url)
            source_name = f"proxy server ({proxy_url})"
            app.logger.debug(f"Using proxy server: {proxy_url}")
        else:
            systemair_ip = app_config.get("systemair_hvac_ip", app.config.get('SYSTEMAIR_SERVER', '192.168.0.111'))
            hvac_obj = Sasc(systemair_ip)
            source_name = f"HVAC server ({systemair_ip})"
            app.logger.debug(f"Using Systemair WiFi module: {systemair_ip}")
        
        hvac_data = hvac_obj.hvac_data()
        
        # Check if HVAC data is empty (device unreachable)
        # Empty dict means connection failed - all exceptions were caught and t_data stayed None
        if hvac_data == {}:
            app.logger.warning(f"{source_name} returned empty data - device may be unreachable")
            return jsonify({"error": "HVAC device unreachable", "data": {}}), 503
        
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
        app.logger.error(f"HVAC server error getting data: {e}")      
        return jsonify({"error": str(e)}), 503


# @hvac_api.route('/thermostat_status_get', methods=['GET'])
# @login_required
# def thermostat_status_get():
#     data_ = {}
    
#     try:
#         thermo_obj = Thermo(app.config['THERMOSTAT_SERVER'])
#         thermo_status = thermo_obj.get_status()
                
#         return jsonify(thermo_status), 200
    
#     except Exception as e:
#         app.logger.error(f"Error: {e}")      
#         return "Error", 500


# @hvac_api.route('/thermostat_startstop/<status>', methods=['GET'])
# @login_required
# def thermostat_startstop(status:str):
#     data_ = {}
    
#     if status not in ["1","0"]:
#         status = "0"
#     try:
#         thermo_obj = Thermo(app.config['THERMOSTAT_SERVER'])
#         thermo_status = thermo_obj.set_on_off(status)
#         return jsonify(thermo_status), 200
    
#     except Exception as e:
#         app.logger.error(f"Error: {e}")      
#         return "Error", 500


@hvac_api.route('/shelly_thermostat_status', methods=['GET'])
@login_required
def shelly_thermostat_status():
    try:
        app_config = Gears_obj.load_app_config()
        shelly_src_id = app_config.get("shelly_src_id", "")
        shelly_ip = app_config.get("shelly_thermostat_ip", app.config.get('SHELLY_THERMOSTAT_SERVER', '192.168.0.123'))
        shelly = ShellyThermostat(
            shelly_ip,
            src_id=shelly_src_id
        )
        status = shelly.get_status()
        
        # Check if status is None or if all values are None (device unreachable)
        if status is None:
            app.logger.warning(f"Shelly thermostat ({shelly_ip}) returned None - device may be unreachable")
            return jsonify({"error": "Shelly thermostat unreachable", "current_temp": None, "set_temp": None, "current_humidity": None, "enabled": None}), 503
        
        # Check if all status values are None (device unreachable but get_status returned dict with None values)
        if isinstance(status, dict):
            all_none = (
                status.get("current_temp") is None and 
                status.get("set_temp") is None and 
                status.get("current_humidity") is None and 
                status.get("enabled") is None
            )
            if all_none:
                app.logger.warning(f"Shelly thermostat ({shelly_ip}) returned all None values - device may be unreachable")
                return jsonify({"error": "Shelly thermostat unreachable", **status}), 503
        
        return jsonify(status), 200
    except Exception as e:
        app.logger.error(f"Shelly thermostat error getting status: {e}")
        return jsonify({"error": str(e), "current_temp": None, "set_temp": None, "current_humidity": None, "enabled": None}), 503


@hvac_api.route('/shelly_thermostat_set_temp', methods=['POST'])
@login_required
def shelly_thermostat_set_temp():
    try:
        temperature = float(request.form.get("temperature"))
        app_config = Gears_obj.load_app_config()
        shelly_src_id = app_config.get("shelly_src_id", "")
        shelly_ip = app_config.get("shelly_thermostat_ip", app.config.get('SHELLY_THERMOSTAT_SERVER', '192.168.0.123'))
        shelly = ShellyThermostat(
            shelly_ip,
            src_id=shelly_src_id
        )
        success = shelly.set_temperature(temperature)
        if success:
            return jsonify({"status": "success"}), 200
        else:
            # Device unreachable or request failed
            app.logger.warning(f"Shelly thermostat ({shelly_ip}) set_temperature failed - device may be unreachable")
            return jsonify({"error": "Shelly thermostat unreachable", "status": "error"}), 503
    except Exception as e:
        app.logger.error(f"Shelly thermostat error setting temperature: {e}")
        return jsonify({"error": str(e), "status": "error"}), 503


@hvac_api.route('/shelly_thermostat_enable', methods=['POST'])
@login_required
def shelly_thermostat_enable():
    try:
        enabled = request.form.get("enabled", "false").lower() == "true"
        app_config = Gears_obj.load_app_config()
        shelly_src_id = app_config.get("shelly_src_id", "")
        shelly_ip = app_config.get("shelly_thermostat_ip", app.config.get('SHELLY_THERMOSTAT_SERVER', '192.168.0.123'))
        shelly = ShellyThermostat(
            shelly_ip,
            src_id=shelly_src_id
        )
        success = shelly.set_enabled(enabled)
        if success:
            return jsonify({"status": "success", "enabled": enabled}), 200
        else:
            # Device unreachable or request failed
            app.logger.warning(f"Shelly thermostat ({shelly_ip}) set_enabled failed - device may be unreachable")
            return jsonify({"error": "Shelly thermostat unreachable", "status": "error", "enabled": None}), 503
    except Exception as e:
        app.logger.error(f"Shelly thermostat error enabling/disabling: {e}")
        return jsonify({"error": str(e), "status": "error", "enabled": None}), 503


@hvac_api.route('/shelly_plugs_status', methods=['GET'])
@login_required
def shelly_plugs_status():
    """Return list of all plugs with name, ip, index, and output (on/off). output is null if unreachable."""
    try:
        plugs = Gears_obj.load_shelly_plugs()
        result = []
        for i, plug in enumerate(plugs):
            name = plug.get("name", "")
            ip = plug.get("ip", "")
            output = None
            try:
                client = ShellyPlug(ip)
                output = client.get_status()
            except Exception:
                pass
            result.append({"index": i, "name": name, "ip": ip, "output": output})
        return jsonify({"plugs": result}), 200
    except Exception as e:
        app.logger.error(f"Error getting shelly plugs status: {e}")
        return jsonify({"error": str(e), "plugs": []}), 500


@hvac_api.route('/shelly_plug_set', methods=['POST'])
@login_required
def shelly_plug_set():
    """Set plug on/off. Expects form or JSON: index (int), on (true/false). Returns updated status."""
    try:
        if request.is_json:
            data = request.get_json()
            plug_index = int(data.get("index", -1))
            on = data.get("on", False) in (True, "true", "1")
        else:
            plug_index = int(request.form.get("index", -1))
            on = request.form.get("on", "false").lower() in ("true", "1")
        plugs = Gears_obj.load_shelly_plugs()
        if plug_index < 0 or plug_index >= len(plugs):
            return jsonify({"error": "Invalid plug index"}), 400
        plug = plugs[plug_index]
        client = ShellyPlug(plug["ip"])
        if not client.set_on(on):
            return jsonify({"error": "Plug unreachable", "index": plug_index}), 503
        output = client.get_status()
        return jsonify({
            "index": plug_index,
            "name": plug["name"],
            "ip": plug["ip"],
            "output": output,
            "message": "ok"
        }), 200
    except Exception as e:
        app.logger.error(f"Error setting shelly plug: {e}")
        return jsonify({"error": str(e)}), 500

    
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
        
        
        app_config = Gears_obj.load_app_config()
        hvac_data_source = app_config.get("hvac_data_source", "systemair")
        
        # Use proxy server if configured, otherwise use systemair
        if hvac_data_source == "proxy":
            proxy_url = app_config.get("proxy_server_ip", "http://proxy-server:5000")
            hvac_obj = ProxyServer(proxy_url)
            app.logger.debug(f"Using proxy server for setting: {proxy_url}")
        else:
            systemair_ip = app_config.get("systemair_hvac_ip", app.config.get('SYSTEMAIR_SERVER', '192.168.0.111'))
            hvac_obj = Sasc(systemair_ip)
            app.logger.debug(f"Using Systemair WiFi module for setting: {systemair_ip}")
        
        user_set_temp = user_set_temp * 10
        server_http_code = hvac_obj.set_hvac_temp_vent(user_set_ventilation, user_set_temp)
            
        if int(server_http_code) in [200, 201]:
            return "", 200
        else:
            raise ValueError(f"HVAC server error. Status code: {server_http_code}.")        
            
    
    except Exception as e:
        app.logger.error(f"HVAC server error setting temperature/ventilation: {e}")      
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


@hvac_api.route('/calendar_events', methods=['GET'])
@login_required
def calendar_events_get():
    """Get calendar events for the next 14 days"""
    try:
        today = date.today()
        end_date = today + timedelta(days=14)
        events = Gears_obj.get_calendar_events_for_date_range(today, end_date)
        return jsonify({"events": events}), 200
    except Exception as e:
        app.logger.error(f"Error getting calendar events: {e}")
        return jsonify({"events": [], "error": str(e)}), 500


@hvac_api.route('/calendar_event/<event_id>', methods=['GET'])
@login_required
def calendar_event_get(event_id):
    """Get a single calendar event by ID (for editing)"""
    try:
        # Check recurring events first
        recurring_events = Gears_obj.load_recurring_events()
        for event in recurring_events:
            if event.get("id") == event_id:
                return jsonify({"event": event}), 200
        
        # Check regular events
        for year in range(date.today().year - 1, date.today().year + 2):
            events = Gears_obj.load_calendar_events(year)
            for event in events:
                if event.get("id") == event_id:
                    return jsonify({"event": event}), 200
        
        return jsonify({"error": "Event not found"}), 404
    except Exception as e:
        app.logger.error(f"Error getting calendar event: {e}")
        return jsonify({"error": str(e)}), 500


@hvac_api.route('/calendar_event', methods=['POST'])
@login_required
def calendar_event_create():
    """Create a new calendar event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'date_start', 'date_end', 'color']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate event ID
        event_id = str(datetime.datetime.now().timestamp())
        
        # Create event object
        event = {
            "id": event_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "date_start": data["date_start"],
            "date_end": data["date_end"],
            "time_start": data.get("time_start"),
            "time_end": data.get("time_end"),
            "recurrence_type": data.get("recurrence_type", "none"),
            "recurrence_end_date": data.get("recurrence_end_date"),
            "color": data["color"]
        }
        
        # If recurring, save to recurring.json, otherwise save to year file
        recurrence_type = data.get("recurrence_type", "none")
        if recurrence_type and recurrence_type != "none":
            # Save as recurring event
            recurring_events = Gears_obj.load_recurring_events()
            recurring_events.append(event)
            Gears_obj.save_recurring_events(recurring_events)
        else:
            # Save as regular event
            start_year = datetime.datetime.strptime(data["date_start"], "%Y-%m-%d").year
            events = Gears_obj.load_calendar_events(start_year)
            events.append(event)
            Gears_obj.save_calendar_events(start_year, events)
        
        return jsonify({"event": event, "message": "Event created successfully"}), 201
    except Exception as e:
        app.logger.error(f"Error creating calendar event: {e}")
        return jsonify({"error": str(e)}), 500


@hvac_api.route('/calendar_event/<event_id>', methods=['PUT'])
@login_required
def calendar_event_update(event_id):
    """Update an existing calendar event"""
    try:
        data = request.get_json()
        
        # Check if it's a recurring event first
        recurring_events = Gears_obj.load_recurring_events()
        for i, event in enumerate(recurring_events):
            if event.get("id") == event_id:
                # Update recurring event
                updated_event = event.copy()
                for key in data:
                    updated_event[key] = data[key]
                
                # Check if recurrence type changed
                new_recurrence_type = data.get("recurrence_type", updated_event.get("recurrence_type", "none"))
                if new_recurrence_type == "none":
                    # Convert to regular event - remove from recurring, add to year file
                    recurring_events.pop(i)
                    Gears_obj.save_recurring_events(recurring_events)
                    
                    # Add to regular events
                    start_year = datetime.datetime.strptime(updated_event["date_start"], "%Y-%m-%d").year
                    events = Gears_obj.load_calendar_events(start_year)
                    events.append(updated_event)
                    Gears_obj.save_calendar_events(start_year, events)
                else:
                    # Update in recurring
                    recurring_events[i] = updated_event
                    Gears_obj.save_recurring_events(recurring_events)
                
                return jsonify({"event": updated_event, "message": "Event updated successfully"}), 200
        
        # Not a recurring event, check regular events
        for year in range(date.today().year - 1, date.today().year + 2):  # Check 3 years range
            events = Gears_obj.load_calendar_events(year)
            for i, event in enumerate(events):
                if event.get("id") == event_id:
                    # Check if it's becoming a recurring event
                    new_recurrence_type = data.get("recurrence_type", "none")
                    if new_recurrence_type != "none":
                        # Convert to recurring - remove from year file, add to recurring
                        events.pop(i)
                        Gears_obj.save_calendar_events(year, events)
                        
                        # Add to recurring
                        updated_event = event.copy()
                        for key in data:
                            updated_event[key] = data[key]
                        recurring_events = Gears_obj.load_recurring_events()
                        recurring_events.append(updated_event)
                        Gears_obj.save_recurring_events(recurring_events)
                        return jsonify({"event": updated_event, "message": "Event updated successfully"}), 200
                    
                    # Regular update
                    new_year = year
                    if "date_start" in data:
                        new_year = datetime.datetime.strptime(data["date_start"], "%Y-%m-%d").year
                    
                    updated_event = event.copy()
                    for key in data:
                        updated_event[key] = data[key]
                    
                    # If year changed, move to new year
                    if new_year != year:
                        events.pop(i)
                        Gears_obj.save_calendar_events(year, events)
                        new_events = Gears_obj.load_calendar_events(new_year)
                        new_events.append(updated_event)
                        Gears_obj.save_calendar_events(new_year, new_events)
                        return jsonify({"event": updated_event, "message": "Event updated successfully"}), 200
                    else:
                        events[i] = updated_event
                        Gears_obj.save_calendar_events(year, events)
                        return jsonify({"event": updated_event, "message": "Event updated successfully"}), 200
        
        # Event not found
        return jsonify({"error": "Event not found"}), 404
        
    except Exception as e:
        app.logger.error(f"Error updating calendar event: {e}")
        return jsonify({"error": str(e)}), 500


@hvac_api.route('/calendar_event/<event_id>', methods=['DELETE'])
@login_required
def calendar_event_delete(event_id):
    """Delete a calendar event (including recurring events)"""
    try:
        # Check if it's a recurring event first
        recurring_events = Gears_obj.load_recurring_events()
        for i, event in enumerate(recurring_events):
            if event.get("id") == event_id:
                recurring_events.pop(i)
                Gears_obj.save_recurring_events(recurring_events)
                return jsonify({"message": "Recurring event deleted successfully"}), 200
        
        # Check if it's an instance of a recurring event (has recurring_template_id)
        # If so, delete the template
        for i, event in enumerate(recurring_events):
            if event.get("id") == event_id or event.get("id") == event_id.replace("_instance", ""):
                recurring_events.pop(i)
                Gears_obj.save_recurring_events(recurring_events)
                return jsonify({"message": "Recurring event deleted successfully"}), 200
        
        # Not a recurring event, check regular events
        for year in range(date.today().year - 1, date.today().year + 2):  # Check 3 years range
            events = Gears_obj.load_calendar_events(year)
            for i, event in enumerate(events):
                if event.get("id") == event_id:
                    events.pop(i)
                    Gears_obj.save_calendar_events(year, events)
                    return jsonify({"message": "Event deleted successfully"}), 200
        
        return jsonify({"error": "Event not found"}), 404
        
    except Exception as e:
        app.logger.error(f"Error deleting calendar event: {e}")
        return jsonify({"error": str(e)}), 500