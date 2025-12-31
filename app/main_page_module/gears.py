import os
import uuid
from datetime import datetime, timedelta
from app.pylavor import Pylavor

class Gears_obj:
    @staticmethod
    def save_targets(all_targets):
        location = "data"
        filename = "targets.json"
        
        Pylavor.create_folder(os.path.join(location, filename))        
        Pylavor.json_write(location, filename, all_targets)
        
    @staticmethod
    def load_targets():
        location = "data"
        filename = "targets.json"
        
        json__ = Pylavor.json_read(location, filename)

        return json__
        
    @staticmethod
    def save_settings(dictio):
        location = "data"
        filename = "conf.json"
        
        Pylavor.create_folder(location)
        Pylavor.json_write(location, filename, dictio)
        
    @staticmethod
    def load_settings():        
        location = "data"
        filename = "conf.json"

        try:
            return Pylavor.json_read(location, filename)
        except FileNotFoundError:
            # Return default settings if file doesn't exist
            default_settings = {
                "instance_name": "",
                "admin_email": "",
                "emails": False,
                "send_analitycs_to_admin": False,
                "source_check_interval": "",
                "smtp_server": "",
                "smtp_port": "",
                "smtp_sender_email": "",
                "smtp_password": "",
                "topic": "",
                "message": "",
                "on_no_memory_send_one": False,
                "logging_level": ""
            }
            Gears_obj.save_settings(default_settings)
            return default_settings
    
    @staticmethod
    def load_events():        
        location = "data"
        filename = "events.json"

        return Pylavor.json_read(location, filename)
    
    @staticmethod
    def save_cities(all_cities):
        location = "data"
        filename = "cities.json"
        
        Pylavor.create_folder(location)        
        Pylavor.json_write(location, filename, all_cities)
        
    @staticmethod
    def load_cities():
        location = "data"
        filename = "cities.json"
        
        try:
            json__ = Pylavor.json_read(location, filename)
            return json__
        except FileNotFoundError:
            # Return default city if file doesn't exist
            default_cities = [
                {
                    "name": "Koper",
                    "latitude": 45.533421368837615,
                    "longitude": 13.727852449587754
                }
            ]
            Gears_obj.save_cities(default_cities)
            return default_cities
    
    @staticmethod
    def save_app_config(config_dict):
        location = "data"
        filename = "config.json"
        
        Pylavor.create_folder(location)
        Pylavor.json_write(location, filename, config_dict)
        
    @staticmethod
    def load_app_config():
        location = "data"
        filename = "config.json"
        
        try:
            json__ = Pylavor.json_read(location, filename)
            return json__
        except FileNotFoundError:
            # Return default config if file doesn't exist
            default_config = {
                "current_location_latitude": 45.533421368837615,
                "current_location_longitude": 13.727852449587754,
                "high_temp_threshold": 30.0,
                "low_temp_threshold": 0.0,
                "shelly_src_id": str(uuid.uuid4()),
                "shelly_thermostat_ip": "192.168.0.123",
                "systemair_hvac_ip": "192.168.0.111"
            }
            Gears_obj.save_app_config(default_config)
            return default_config    