import os
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
        
        Pylavor.create_folder(os.path.join(location, filename))
        Pylavor.json_write(location, filename, dictio)
        
    @staticmethod
    def load_settings():        
        location = "data"
        filename = "conf.json"

        return Pylavor.json_read(location, filename)
    
    @staticmethod
    def load_events():        
        location = "data"
        filename = "events.json"

        return Pylavor.json_read(location, filename)    