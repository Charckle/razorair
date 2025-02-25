import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import json
from datetime import datetime, date

from flask import url_for


class Open_W_obj:
    # NON-commercial use!
    # under 10.000 calls per day
    # refreshes every 15 min
    
    url = None
    raw_data = {}
    
    current = {}
    daily = {}
    hourly = {}
    
    def __init__(self, lat, long, days=12, daily_data=False):
        if daily_data != False:
            self.current = {}
            self.daily = daily_data
            self.hourly = {}
            
        else:
            # time: centralna evropa
            #current, daily, hourly
            self.url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&current=weather_code,temperature_2m,is_day,precipitation,rain,showers,snowfall,cloud_cover&hourly=weather_code,temperature_2m,precipitation,cloud_cover&daily=sunrise,sunset,weather_code,temperature_2m_max,temperature_2m_min,daylight_duration,sunshine_duration,precipitation_probability_max&timezone=Europe%2FBerlin&forecast_days={days}"
            # daily only
            #self.url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&daily=weather_code,temperature_2m_max,temperature_2m_min,daylight_duration,sunshine_duration,precipitation_probability_max&timezone=Europe%2FBerlin&forecast_days={days}"
            w_data = self.get_data()
            
            if w_data == None:
                self.current = {}
                self.daily = {}
                self.hourly = {}
                
            
            else:
                self.raw_data = w_data.json()
                
                self.populate_current()
                self.populate_daily()                
                
                self.populate_hourly()

    
    def populate_current(self):
        # precipitaitons je v mm
        # cloud cover je v %
        weather_data = self.raw_data

        day = True if weather_data["current"]["is_day"] == 1 else False
        weather_code = weather_data["current"]["weather_code"]
        
        self.current = {"temp": weather_data["current"]["temperature_2m"],
                        "precipitation": weather_data["current"]["precipitation"],
                        "rain": weather_data["current"]["rain"],
                        "showers": weather_data["current"]["showers"],
                        "snowfall": weather_data["current"]["snowfall"],
                        "cloud_cover": weather_data["current"]["cloud_cover"],
                        "is_day": day,
                        "weather_code": weather_code,
                        "icon": Open_W_obj.get_icon(weather_code, day=day)}   
  
    
    def populate_daily(self):
        # sunshine duration in seconds
        # precipitation_probability_max %
        weather_data = self.raw_data

        
        for index, day_ in enumerate(weather_data["daily"]["time"]):
            sunshine_duration = weather_data["daily"]["sunshine_duration"][index]
            if sunshine_duration == None:
                sunshine_duration = 0
            daylight_duration = weather_data["daily"]["daylight_duration"][index]
            cloud_cover = (sunshine_duration / daylight_duration) - 1
            
            day_data = {"temp_max": weather_data["daily"]["temperature_2m_max"][index],
                        "temp_min": weather_data["daily"]["temperature_2m_min"][index],
                        "sunshine_duration": sunshine_duration,
                        "daylight_duration": daylight_duration,
                        "cloud_cover": cloud_cover,
                        "weather_code": weather_data["daily"]["weather_code"][index],
                        "precipitation_probability_max": weather_data["daily"]["precipitation_probability_max"][index],
                        "sunrise": weather_data["daily"]["sunrise"][index],
                        "sunset": weather_data["daily"]["sunset"][index]}
            
            self.daily[day_] = day_data
            

    
    def populate_hourly(self):
        weather_data = self.raw_data
        
        for index, hour_ in enumerate(weather_data["hourly"]["time"]):
            hour_data = {"temp": weather_data["hourly"]["temperature_2m"][index],
                        "precipitation": weather_data["hourly"]["precipitation"][index],
                        "cloud_cover": weather_data["hourly"]["cloud_cover"][index],
                        "weather_code": weather_data["hourly"]["weather_code"][index]}
            
            self.hourly[hour_] = hour_data    


    def get_data(self):
        w_data = None
        
        try:
            response = requests.get(self.url, timeout=5)  # You can adjust the timeout as needed
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            #print(response.text)  # Handle the response here
            w_data = response
        
        except ConnectionError:
            print("Failed to connect to the webpage. Please check your internet connection or the website's availability.")
        
        except Timeout:
            print("The request timed out. The server might be too slow or unresponsive.")
        
        except RequestException as e:
            print(f"An error occurred: {e}")
        
        return w_data
        
        
                
    def get_daily_until(self, date_to_track=None):
        dates_to_return = {}
        
        for date_, values_ in self.daily.items():
            selected_date_obj = datetime.strptime(date_, "%Y-%m-%d").date()
            
            if date_to_track == None:
                dates_to_return[date_] = self.daily[date_]
            else:
                date_to_track_ = datetime.strptime(date_to_track, "%Y-%m-%d").date()                
                
                if date_to_track_ >= selected_date_obj:
                    dates_to_return[date_] = self.daily[date_]
                
        return dates_to_return
            
            
    def get_hourly_from(self, hours_data = 12, hour_from = None):
        hours_to_return = {}

        if hour_from != None:
            hour_from = datetime.strptime(hour_from, "%Y-%m-%dT%H:%M")   
        else:
            hour_from = datetime.now()
            
                    
        for hour_, values_ in self.hourly.items():
            selected_hour_obj = datetime.strptime(hour_, "%Y-%m-%dT%H:%M")
            
            # gets the next hour, since the current date wont be the same as the checked date, due to minutes
            if hour_from < selected_hour_obj and hours_data > 0:
                hours_to_return[hour_] = self.hourly[hour_]
                hours_data -= 1
                        
        
        return hours_to_return

    @staticmethod
    def weather_icons():
        
        #WMO Weather interpretation codes (WW)
        #Code	Description
        #0	Clear sky
        #1, 2, 3	Mainly clear, partly cloudy, and overcast
        #45, 48	Fog and depositing rime fog
        #51, 53, 55	Drizzle: Light, moderate, and dense intensity
        #56, 57	Freezing Drizzle: Light and dense intensity
        #61, 63, 65	Rain: Slight, moderate and heavy intensity
        #66, 67	Freezing Rain: Light and heavy intensity
        #71, 73, 75	Snow fall: Slight, moderate, and heavy intensity
        #77	Snow grains
        #80, 81, 82	Rain showers: Slight, moderate, and violent
        #85, 86	Snow showers slight and heavy
        #95 *	Thunderstorm: Slight or moderate
        #96, 99 *	Thunderstorm with slight and heavy hail        
        
        icons = [[[0,1], ["clear-night", "clear-day"]],
                 [[2], ["partly-cloudy-night", "partly-cloudy-day"]],
                 [[3], ["overcast-night", "overcast-day"]],
                 [[45, 48], ["fog-night", "fog-day"]],
                 [[51, 53, 55], ["drizzle", "drizzle"]],
                 [[56, 57, 66, 67], ["sleet", "sleet"]],
                 [[61, 63, 65, 80, 81, 82], ["rain", "rain"]],
                 [[71, 73, 75, 85, 86], ["snow", "snow"]],
                 [[77], ["hail", "hail"]],
                 [[95, 96, 99], [ "thunderstorms-night-rain", "thunderstorms-day-rain"]]
                 ]
        
        return icons        
    
    
    def get_icon(weather_code, day=True):
        if day:
            day_ = 1
        else:
            day_ = 0
            
        icons = Open_W_obj.weather_icons()
                
        icon_name = "not-available"
        
        for weather_list in icons:
            w_code_list = weather_list[0]
            icons_l = weather_list[1]

            if weather_code in w_code_list:
                icon_name = weather_list[1][day_]
                break
        
        icon_link = url_for('static', filename=f"main_page_module/icons/weather/fill/{icon_name}.svg")
        
        return icon_link
    
    
    def hourly_object(self, hour_to_track=None):
        data_ = self.get_hourly_from(hours_data = 12, hour_from = hour_to_track)
        object_w  = {}

        for day_, data_w in data_.items():
            day = self.check_if_day(day_)
            object_w[day_] = {
                "temp": data_w["temp"],
                "icon": Open_W_obj.get_icon(weather_code=data_w["weather_code"], day=day),
                "day": day
            }
        
        return object_w       
    
    def check_if_day(self, date_time):
        date_w_time = datetime.strptime(date_time, "%Y-%m-%dT%H:%M")
        date_ = datetime.strptime(date_time, "%Y-%m-%dT%H:%M").date()
        
        sunrise_text = self.daily[str(date_)]["sunrise"]
        sunrise = datetime.strptime(sunrise_text, "%Y-%m-%dT%H:%M")        
        sunset_test = self.daily[str(date_)]["sunset"]
        sunset = datetime.strptime(sunset_test, "%Y-%m-%dT%H:%M")        
        
        if date_w_time > sunrise and date_w_time < sunset:
            return True
        else:
            return False
    
    
    def daily_object(self, date_to_track=None, max_hits=None):
        data_ = self.get_daily_until(date_to_track=date_to_track)
        
        object_w  = {}

        for day_, data_w in data_.items():
            day_name = datetime.strptime(day_, "%Y-%m-%d").strftime("%A")[:3]
            
            if datetime.strptime(day_, "%Y-%m-%d").date() == date.today():
                day_name = "Today"
                
            object_w[day_] = {
                "temp_max": data_w["temp_max"],
                "temp_min": data_w["temp_min"],
                "icon": Open_W_obj.get_icon(weather_code=data_w["weather_code"], day=True),
                "day_name": day_name
            }
        
        if max_hits != None:
            first_x = {}
            
            for i, (day_, data_w) in enumerate(object_w.items()):
                if i == 12:  # Stop after 12 items
                        break
                first_x[day_] = data_w    
            return first_x
        else:
            return object_w    