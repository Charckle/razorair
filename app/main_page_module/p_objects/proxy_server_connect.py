import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import json


class ProxyServer:
    # Proxy server connection for HVAC data
    # The proxy server provides pre-formatted data, so no conversion needed
    
    server_url = None
    
    def __init__(self, server_url):
        """
        Initialize proxy server connection.
        
        Args:
            server_url: Base URL of the proxy server (e.g., "http://proxy-server:5000")
        """
        # Ensure server_url doesn't have trailing slash
        self.server_url = server_url.rstrip('/')
    
    def hvac_data(self):
        """
        Get HVAC data from proxy server.
        
        Returns:
            dict: HVAC data dictionary with keys:
                - extract_fan_rpm
                - heat_exchanger_percentage
                - heater_percentage
                - intake_temp
                - moisture_perc
                - outside_temp
                - outtake_temp
                - overheat_temp
                - supply_fan_rpm
                - user_set_temp
                - user_set_ventilation
        """
        temp_dict = {}
        
        try:
            url = f"{self.server_url}/status"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data_json = response.json()
            
            # Extract data from the response
            # The proxy server returns data in format:
            # {"connection_info": {...}, "data": {...}, "status": "connected"}
            if "data" in data_json:
                data = data_json["data"]
                
                # Map the proxy server data to the expected format
                temp_dict["extract_fan_rpm"] = data.get("extract_fan_rpm", 0)
                temp_dict["heat_exchanger_percentage"] = data.get("heat_exchanger_percentage", 0)
                temp_dict["heater_percentage"] = data.get("heater_percentage", 0)
                temp_dict["intake_temp"] = data.get("intake_temp", 0.0)
                temp_dict["moisture_perc"] = data.get("moisture_perc", 0)
                temp_dict["outside_temp"] = data.get("outside_temp", 0.0)
                temp_dict["outtake_temp"] = data.get("outtake_temp", 0.0)
                temp_dict["overheat_temp"] = data.get("overheat_temp", 0.0)
                temp_dict["supply_fan_rpm"] = data.get("supply_fan_rpm", 0)
                temp_dict["user_set_temp"] = data.get("user_set_temp", 0.0)
                temp_dict["user_set_ventilation"] = data.get("user_set_ventilation", 0)
                
                # Also map heat_echanger_percentage (note the typo in original code)
                temp_dict["heat_echanger_percentage"] = data.get("heat_exchanger_percentage", 0)
        
        except ConnectionError:
            print(f"Failed to connect to proxy server ({self.server_url}). Please check your connection or the server's availability.")
        
        except Timeout:
            print(f"The proxy server ({self.server_url}) request timed out. The server might be too slow or unresponsive.")
        
        except RequestException as e:
            print(f"An error occurred connecting to proxy server ({self.server_url}): {e}")
        
        return temp_dict
    
    def set_hvac_temp_vent(self, vent_s, r_temp):
        """
        Set HVAC temperature and ventilation via proxy server.
        
        Args:
            vent_s: Ventilation setting (0, 2, 3, or 4)
            r_temp: Temperature in tenths of degrees (e.g., 280 for 28.0°C)
        
        Returns:
            int: HTTP status code (200/201 for success, 404/408/500 for errors)
        """
        try:
            # Convert temperature from tenths to degrees
            temp_degrees = r_temp / 10.0
            
            # Set temperature
            temp_url = f"{self.server_url}/set_temperature"
            temp_payload = {"temperature": temp_degrees}
            temp_response = requests.post(temp_url, json=temp_payload, timeout=5)
            temp_response.raise_for_status()
            
            # Set ventilation
            vent_url = f"{self.server_url}/set_ventilation"
            vent_payload = {"ventilation": vent_s}
            vent_response = requests.post(vent_url, json=vent_payload, timeout=5)
            vent_response.raise_for_status()
            
            # Return success if both requests succeeded
            return temp_response.status_code if temp_response.status_code == vent_response.status_code else 500
        
        except ConnectionError:
            print(f"Failed to connect to proxy server ({self.server_url}). Please check your connection or the server's availability.")
            return 404
        
        except Timeout:
            print(f"The proxy server ({self.server_url}) request timed out. The server might be too slow or unresponsive.")
            return 408
        
        except RequestException as e:
            print(f"An error occurred connecting to proxy server ({self.server_url}): {e}")
            return 500
