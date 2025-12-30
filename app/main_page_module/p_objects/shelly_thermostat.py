import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import json
import uuid


class ShellyThermostat:
    """
    Shelly Starlight Thermostat ST1820 communication class
    Uses JSON-RPC protocol
    """
    
    def __init__(self, server_ip, src_id=None):
        # Clean up the IP address - remove http:// or https:// prefix and trailing slashes
        server_ip = str(server_ip).strip()
        if server_ip.startswith('http://'):
            server_ip = server_ip[7:]
        elif server_ip.startswith('https://'):
            server_ip = server_ip[8:]
        self.server_ip = server_ip.rstrip('/')
        self.base_url = f"http://{self.server_ip}/rpc"
        self.src_id = src_id  # Will be passed from config
    
    def _make_rpc_request(self, method, params=None, request_id=None):
        """Make a JSON-RPC request to the Shelly device"""
        if request_id is None:
            request_id = 12  # Default from your example
        
        payload = {
            "method": method,
            "id": request_id
        }
        
        # Include src if provided
        if self.src_id:
            payload["src"] = self.src_id
        
        if params:
            payload["params"] = params
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except (ConnectionError, Timeout, RequestException, Exception):
            return None
    
    def get_status(self):
        """Get current temperature, set temperature, humidity, and enabled status"""
        resp_json = {
            "current_temp": None,
            "set_temp": None,
            "current_humidity": None,
            "enabled": None
        }
        
        # Get current temperature from number component (id 201)
        number_status = self._make_rpc_request("number.getstatus", {"id": 201})
        if number_status and "result" in number_status and "error" not in number_status:
            result_data = number_status["result"]
            if isinstance(result_data, dict):
                resp_json["current_temp"] = result_data.get("value", None)
            else:
                resp_json["current_temp"] = result_data
        
        # Get set temperature from number component (id 202)
        number_status = self._make_rpc_request("number.getstatus", {"id": 202})
        if number_status and "result" in number_status and "error" not in number_status:
            result_data = number_status["result"]
            if isinstance(result_data, dict):
                resp_json["set_temp"] = result_data.get("value", None)
            else:
                resp_json["set_temp"] = result_data
        
        # Get current humidity from number component (id 200)
        number_status = self._make_rpc_request("number.getstatus", {"id": 200})
        if number_status and "result" in number_status and "error" not in number_status:
            result_data = number_status["result"]
            if isinstance(result_data, dict):
                resp_json["current_humidity"] = result_data.get("value", None)
            else:
                resp_json["current_humidity"] = result_data
        
        # Get enabled status from boolean component (id 202)
        boolean_status = self._make_rpc_request("boolean.getstatus", {"id": 202})
        if boolean_status and "result" in boolean_status and "error" not in boolean_status:
            result_data = boolean_status["result"]
            if isinstance(result_data, dict):
                resp_json["enabled"] = result_data.get("value", None)
            else:
                resp_json["enabled"] = bool(result_data)
        
        return resp_json
    
    def get_current_temp(self):
        """Get current temperature from the device"""
        status = self.get_status()
        return status.get("current_temp")
    
    def get_set_temp(self):
        """Get set temperature from the device"""
        status = self.get_status()
        return status.get("set_temp")
    
    def set_temperature(self, temperature):
        """
        Set the target temperature
        temperature: float, with 0.5 degree precision
        """
        # Round to 0.5 precision
        temp_value = round(float(temperature) * 2) / 2
        
        params = {
            "value": temp_value,
            "id": 202
        }
        
        # Try lowercase first, then capitalized
        result = self._make_rpc_request("number.set", params)
        if not result:
            result = self._make_rpc_request("Number.Set", params)
        
        if result:
            # Check if there's an error
            if "error" in result:
                return False
            return True
        return False
    
    def set_enabled(self, enabled):
        """
        Enable or disable the thermostat
        enabled: bool, True to enable, False to disable
        """
        params = {
            "value": bool(enabled),
            "id": 202
        }
        
        result = self._make_rpc_request("boolean.set", params)
        if not result:
            result = self._make_rpc_request("Boolean.Set", params)
        
        if result:
            # Check if there's an error
            if "error" in result:
                return False
            return True
        return False

