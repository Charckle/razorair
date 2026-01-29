import requests
from requests.exceptions import ConnectionError, Timeout, RequestException


class ShellyPlug:
    """
    Shelly 3rd generation plug (Switch) control via RPC.
    Get status: GET http://<ip>/rpc/Switch.GetStatus?id=0
    Set on/off: GET http://<ip>/rpc/Switch.Set?id=0&on=true|false
    """

    def __init__(self, ip):
        ip = str(ip).strip()
        if ip.startswith("http://"):
            ip = ip[7:]
        elif ip.startswith("https://"):
            ip = ip[8:]
        self.ip = ip.rstrip("/")
        self.base_url = f"http://{self.ip}/rpc"

    def get_status(self):
        """
        Get relay output status.
        Returns:
            bool: True if on, False if off
            None: if request failed or device unreachable
        """
        try:
            r = requests.get(
                f"{self.base_url}/Switch.GetStatus",
                params={"id": 0},
                timeout=3,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("output", None)
        except (ConnectionError, Timeout, RequestException, ValueError, KeyError):
            return None

    def set_on(self, on):
        """
        Set relay on or off.
        Args:
            on: bool, True for on, False for off
        Returns:
            bool: True if request succeeded, False otherwise
        """
        try:
            r = requests.get(
                f"{self.base_url}/Switch.Set",
                params={"id": 0, "on": "true" if on else "false"},
                timeout=3,
            )
            r.raise_for_status()
            return True
        except (ConnectionError, Timeout, RequestException):
            return False
