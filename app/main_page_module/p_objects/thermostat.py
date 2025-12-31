import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import json
from datetime import datetime, date

from flask import url_for


class Thermo:
    server_ip = None

    
    def __init__(self, server_ip):
        self.server_ip = server_ip
        
    def get_status(self):
        json_status= self.get_curr_temp()
        json_is_on = self.get_is_on()
        json_set_temp = self.get_set_temp()
        
        json_status["is_on"] = json_is_on["is_on"]
        json_status["set_temp"] = json_set_temp["set_temp"]
        
        return json_status
        
        
        
    def get_curr_temp(self):
        resp_json = {"temp_": 000,
                     "centr_on": 999}
        try:
            url = f"http://{self.server_ip}" + "/api/status"
            response = requests.get(url, timeout=5)  # You can adjust the timeout as needed
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            t_data = response
        
        except ConnectionError:
            print("Failed to connect to the server. Please check your internet connection or the server's availability.")
        
        except Timeout:
            print("The request timed out. The server might be too slow or unresponsive.")
        
        except RequestException as e:
            print(f"An error occurred: {e}")       
        
        # če pride do errorja, vrže exception ampak spodaj ne nmore prebrat, ker ne dobi nikoli statusa od serverja, če ni opnline
        if response.status_code in [200, 201]:
            data_ = response.text.split(":")
            resp_json["temp_"] = int(data_[0])
            resp_json["centr_on"] = int(data_[1])
        
        return resp_json
            
        
        
    def get_is_on(self):
        resp_json = {"is_on": 999}
        try:
            url = f"http://{self.server_ip}" + "/api/on"
            response = requests.get(url, timeout=5)  # You can adjust the timeout as needed
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            t_data = response
        
        except ConnectionError:
            print("Failed to connect to the server. Please check your internet connection or the server's availability.")
        
        except Timeout:
            print("The request timed out. The server might be too slow or unresponsive.")
        
        except RequestException as e:
            print(f"An error occurred: {e}")       
            
        if response.status_code in [200, 201]:
            resp_json["is_on"] = int(response.text)
        
        return resp_json
    
    
    def set_on_off(self, on_off=0):        
        try:
            url = f"http://{self.server_ip}" + "/api/on"
            headers = {
                "Content-Type": "text/plain"
            }
            data = str(on_off)
            response = requests.post(url, timeout=5, data=on_off, headers=headers)  # You can adjust the timeout as needed
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        
        except ConnectionError:
            print("Failed to connect to the server. Please check your internet connection or the server's availability.")
        
        except Timeout:
            print("The request timed out. The server might be too slow or unresponsive.")
        
        except RequestException as e:
            print(f"An error occurred: {e}")       
            
        
        return response.text       
    
    
    def get_set_temp(self):
        resp_json = {"set_temp": 9999}
        
        try:
            url = f"http://{self.server_ip}" + "/api/desiredTemp"
            response = requests.get(url, timeout=5)  # You can adjust the timeout as needed
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            t_data = response
        
        except ConnectionError:
            print("Failed to connect to the server. Please check your internet connection or the server's availability.")
        
        except Timeout:
            print("The request timed out. The server might be too slow or unresponsive.")
        
        except RequestException as e:
            print(f"An error occurred: {e}")       
            
        if response.status_code in [200, 201]:
            resp_json["set_temp"] = int(response.text)
        
        return resp_json 
    
    
          