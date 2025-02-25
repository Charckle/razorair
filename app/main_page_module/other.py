from unidecode import unidecode
import re
import os
import secrets
import string

from datetime import datetime

from enum import Enum


class UserRole(Enum):
    ADMIN = 1
    READWRITE = 2
    READ = 3
    
class Countries(Enum):
    SLOVENIA = 1
    CROATIA = 2    
    ENGLISH = 3
    AUSTRIA = 4   
    ITALY = 5
    HUNGARY = 6    


class Randoms():
    @staticmethod
    def zerodivision(n, d):
        n = float(n)
        d = float(d)
        
        return n / d if d else 0
    
    # Randoms
    #sanitize the code for saving to a file on the OS
    @staticmethod
    def get_valid_filename(s):
    
        """
        Stolen from Django, me thinks?
        Return the given string converted to a string that can be used for a clean
        filename. Remove leading and trailing spaces; convert other spaces to
        underscores; and remove anything that is not an alphanumeric, dash,
        underscore, or dot.
        >>> get_valid_filename("john's portrait in 2004.jpg")
        'johns_portrait_in_2004.jpg'
        """
    
        s = unidecode(str(s).strip().replace(' ', '_'))
    
        return re.sub(r'(?u)[^-\w.]', '', s)
    
    # Randoms
    def generate_file_id(length=15):
        # Define the character set from which to generate the ID
        characters = string.ascii_letters + string.digits  # You can include other characters if needed
        
        # Generate the random ID
        file_id = ''.join(secrets.choice(characters) for i in range(length))
        
        return file_id    
    
    # Randoms
    @staticmethod
    def icon_name(config):
        env_color = config['ICON_COLOR']
        favicon_name = f"favicon_{env_color}.ico"
        static_path = "app/static"
        file_path = f"{static_path}/{favicon_name}"
        
        if not os.path.exists(file_path):
            favicon_name = f"favicon_RED.ico"
        
        return favicon_name
    
    # Randoms    
    @staticmethod    
    def format_file_size(file_size):
        file_size = file_size / 1024
        if file_size < 1024:
            return f"{file_size:.2f} KB"
        else:
            return f"{file_size / 1024:.2f} MB"    
        
    
    # Randoms    
    @staticmethod    
    def verify_folder(folder_path):
        if not os.path.exists(folder_path):
            # If it doesn't exist, create it
            os.makedirs(folder_path)
    
    # Randoms
    @staticmethod    
    def get_version():    
        with open('VERSION') as f:
            lines = f.readlines()
        
        return lines[0]    
    
    
   


class EventsS():
    # EventsS
    @staticmethod
    def list_tag_colors(id_=None):    
        colors = {0: "primary",
                    1: "secondary",
                    2: "success",
                    3: "danger",
                    4: "warning",
                    5: "info",
                    6: "light",
                    7: "dark"}
        
        if id_ == None:
            return colors
        else:
            return colors[int(id_)]
    
    # EventsS    
    @staticmethod
    def languaged_tags(tag_, translation_language):
        language_table = {1: "name_slo",
                          2: "name_hrv",
                          3: "name_eng",
                          4: "name_aut",
                          5: "name_ita",
                          6: "name_hun"}
                    
        trans_lang = language_table[int(translation_language)]
        tag_["name"] = tag_[trans_lang]

        return tag_
    
    

    # EventsS    
    def get_years_months_between(start_date, end_date):
        # List to store the months with years
        dates_ = {}
        current_year = start_date.year
        current_month = start_date.month
        
        while (current_year, current_month) <= (end_date.year, end_date.month):
            # Append the current year and month in "YYYY-MM" format
            if current_year not in dates_:
                dates_[current_year] = []
                
            dates_[current_year].append(current_month) 
            
            # Increment month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        return dates_
    
    
    # EventsS    
    def add_months(start_date, months):
        # Move to the correct month
        new_month = start_date.month - 1 + months
        new_year = start_date.year + new_month // 12
        new_month = new_month % 12 + 1
        # Return the new date
        return start_date.replace(year=new_year, month=new_month, day=1)
    
    # EventsS
    def get_map_url(coord, iframe=False, zoom=15):
        coord = coord.split(",")
        if len(coord) < 2:
            return ""
        
        lat = float(coord[0].strip())
        long = float(coord[1].strip())
        
        if iframe == True:
            left_lon = long - 0.01
            right_lon = long + 0.01
            bottom_lat = lat - 0.01
            top_lat = lat + 0.01         

            return  f"https://www.openstreetmap.org/export/embed.html?bbox={left_lon},{top_lat},{right_lon},{bottom_lat}&layer=mapnik&marker={lat},{long}"
       # f"https://www.openstreetmap.org/export/embed.html?bbox=2.3422,48.8466,2.3622,48.8666&layer=mapnik&marker={lat},{long}"
        else:
            return f"https://www.openstreetmap.org/?mlat={lat}&mlon={long}#map={zoom}/{lat}/{long}"
    