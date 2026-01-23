import os
import uuid
import calendar
from datetime import datetime, timedelta, date
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
                "systemair_hvac_ip": "192.168.0.111",
                "proxy_server_ip": "http://proxy-server:5000",
                "hvac_data_source": "systemair"
            }
            Gears_obj.save_app_config(default_config)
            return default_config
    
    @staticmethod
    def get_calendar_file_path(year):
        """Get the file path for a calendar year"""
        location = os.path.join("data", "calendar")
        filename = f"{year}.json"
        return location, filename
    
    @staticmethod
    def save_calendar_events(year, events):
        """Save calendar events for a specific year"""
        location, filename = Gears_obj.get_calendar_file_path(year)
        Pylavor.create_folder(location)
        Pylavor.json_write(location, filename, events)
    
    @staticmethod
    def load_calendar_events(year):
        """Load calendar events for a specific year"""
        location, filename = Gears_obj.get_calendar_file_path(year)
        try:
            json__ = Pylavor.json_read(location, filename)
            return json__
        except FileNotFoundError:
            return []
    
    @staticmethod
    def get_calendar_events_for_date_range(start_date, end_date):
        """Get all calendar events within a date range (inclusive)"""
        all_events = []
        start_year = start_date.year
        end_year = end_date.year
        
        for year in range(start_year, end_year + 1):
            events = Gears_obj.load_calendar_events(year)
            for event in events:
                event_start = datetime.strptime(event["date_start"], "%Y-%m-%d").date()
                event_end = datetime.strptime(event["date_end"], "%Y-%m-%d").date()
                
                # Check if event overlaps with the date range
                if event_start <= end_date and event_end >= start_date:
                    all_events.append(event)
        
        # Sort events by date_start
        all_events.sort(key=lambda x: x["date_start"])
        return all_events
    
    @staticmethod
    def get_years_with_events():
        """Get a list of all years that have calendar events"""
        import os
        years = []
        calendar_dir = os.path.join("data", "calendar")
        
        if not os.path.exists(calendar_dir):
            return years
        
        try:
            for filename in os.listdir(calendar_dir):
                if filename.endswith(".json"):
                    try:
                        year = int(filename.replace(".json", ""))
                        # Check if the year file actually has events
                        events = Gears_obj.load_calendar_events(year)
                        if events and len(events) > 0:
                            years.append(year)
                    except ValueError:
                        # Skip files that don't have a valid year number
                        continue
                    except Exception as e:
                        # Log but continue
                        continue
        except Exception as e:
            # If directory listing fails, return empty list
            return []
        
        return sorted(years, reverse=True)  # Most recent first
    
    @staticmethod
    def save_recurring_events(recurring_events):
        """Save recurring events to a special file"""
        location = os.path.join("data", "calendar")
        filename = "recurring.json"
        Pylavor.create_folder(location)
        Pylavor.json_write(location, filename, recurring_events)
    
    @staticmethod
    def load_recurring_events():
        """Load recurring events from the special file"""
        location = os.path.join("data", "calendar")
        filename = "recurring.json"
        try:
            json__ = Pylavor.json_read(location, filename)
            return json__
        except FileNotFoundError:
            return []
    
    @staticmethod
    def generate_recurring_instances(recurring_event, start_date, end_date):
        """Generate instances of a recurring event within a date range"""
        instances = []
        
        recurrence_type = recurring_event.get("recurrence_type", "none")
        if recurrence_type == "none":
            return instances
        
        # Get original event dates
        original_start = datetime.strptime(recurring_event["date_start"], "%Y-%m-%d").date()
        original_end = datetime.strptime(recurring_event["date_end"], "%Y-%m-%d").date()
        duration_days = (original_end - original_start).days
        
        # Get recurrence end (if specified)
        recurrence_end = None
        if recurring_event.get("recurrence_end_date"):
            recurrence_end = datetime.strptime(recurring_event["recurrence_end_date"], "%Y-%m-%d").date()
        
        # Note: interval is always 1 for now (daily/weekly/monthly/yearly)
        # Can be extended later if needed for "every 2 weeks", etc.
        interval = 1
        
        # Generate instances
        current_date = original_start
        instance_count = 0
        max_instances = 366  # Safety limit (max 1 year of daily events)
        
        while current_date <= end_date and instance_count < max_instances:
            # Check if we've passed the recurrence end date
            if recurrence_end and current_date > recurrence_end:
                break
            
            # Check if this instance overlaps with our date range
            instance_end = current_date + timedelta(days=duration_days)
            if instance_end >= start_date and current_date <= end_date:
                # Create instance
                instance = recurring_event.copy()
                instance["date_start"] = current_date.strftime("%Y-%m-%d")
                instance["date_end"] = instance_end.strftime("%Y-%m-%d")
                instance["is_recurring"] = True
                instance["recurring_template_id"] = recurring_event["id"]
                instances.append(instance)
            
            # Move to next occurrence
            if recurrence_type == "daily":
                current_date += timedelta(days=interval)
            elif recurrence_type == "weekly":
                current_date += timedelta(weeks=interval)
            elif recurrence_type == "monthly":
                # Add months (handle month-end edge cases)
                year = current_date.year
                month = current_date.month
                for _ in range(interval):
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                # Handle day-of-month (e.g., if original is 31st but next month has 30 days)
                day = min(original_start.day, calendar.monthrange(year, month)[1])
                try:
                    current_date = date(year, month, day)
                except ValueError:
                    # If date is invalid (e.g., Feb 30), use last day of month
                    current_date = date(year, month, calendar.monthrange(year, month)[1])
            elif recurrence_type == "yearly":
                # Same month/day, different year
                try:
                    current_date = date(current_date.year + interval, original_start.month, original_start.day)
                except ValueError:
                    # Handle leap year edge case (Feb 29)
                    current_date = date(current_date.year + interval, original_start.month, 28)
            
            instance_count += 1
        
        return instances
    
    @staticmethod
    def get_calendar_events_for_date_range(start_date, end_date):
        """Get all calendar events within a date range (inclusive), including recurring instances"""
        all_events = []
        start_year = start_date.year
        end_year = end_date.year
        
        # Get regular events
        for year in range(start_year, end_year + 1):
            events = Gears_obj.load_calendar_events(year)
            for event in events:
                # Skip if it's marked as recurring (shouldn't happen, but safety check)
                if event.get("recurrence_type") and event.get("recurrence_type") != "none":
                    continue
                event_start = datetime.strptime(event["date_start"], "%Y-%m-%d").date()
                event_end = datetime.strptime(event["date_end"], "%Y-%m-%d").date()
                
                # Check if event overlaps with the date range
                if event_start <= end_date and event_end >= start_date:
                    all_events.append(event)
        
        # Get recurring events and generate instances
        recurring_events = Gears_obj.load_recurring_events()
        for recurring_event in recurring_events:
            instances = Gears_obj.generate_recurring_instances(recurring_event, start_date, end_date)
            all_events.extend(instances)
        
        # Sort events by date_start
        all_events.sort(key=lambda x: x["date_start"])
        return all_events    