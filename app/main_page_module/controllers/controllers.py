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


from app import app, targets_ram

#import os
import re
import os
import uuid
import zipfile
import io
import pathlib
from passlib.hash import sha512_crypt
import datetime
from datetime import date


# Define the blueprint: 'auth', set its url prefix: app.url/auth
main_page_module = Blueprint('main_page_module', __name__, url_prefix='/')


@app.context_processor
def inject_to_every_page():
    
    return dict(Randoms=Randoms, datetime=datetime, Pylavor=Pylavor)


@main_page_module.route('/', methods=['GET'])
@login_required
def index():
    
    return render_template("main_page_module/index.html", Open_W_obj=Open_W_obj)


@main_page_module.route('/hvac', methods=['GET'])
@login_required
def hvac():
    
    return render_template("main_page_module/hvac.html", Open_W_obj=Open_W_obj)


@main_page_module.route('/calendar', methods=['GET'])
@login_required
def calendar():
    # Get current year events and filter out past events
    current_year = datetime.date.today().year
    today = datetime.date.today()
    end_of_year = datetime.date(current_year, 12, 31)
    
    # Get regular events for current year
    all_events = Gears_obj.load_calendar_events(current_year)
    
    # Filter out events that have ended (end_date < today)
    events = []
    for event in all_events:
        # Skip recurring events (they're handled separately)
        if event.get("recurrence_type") and event.get("recurrence_type") != "none":
            continue
        event_end = datetime.datetime.strptime(event["date_end"], "%Y-%m-%d").date()
        if event_end >= today:
            events.append(event)
    
    # Get recurring events and generate instances for current year
    recurring_events = Gears_obj.load_recurring_events()
    for recurring_event in recurring_events:
        instances = Gears_obj.generate_recurring_instances(recurring_event, today, end_of_year)
        events.extend(instances)
    
    # Sort events by date_start
    events.sort(key=lambda x: x["date_start"])
    
    # Get all years with events for archive
    all_archive_years = Gears_obj.get_years_with_events()
    archive_years = all_archive_years
    
    # Also pass recurring event templates for the filter view
    recurring_templates = Gears_obj.load_recurring_events()
    
    return render_template("main_page_module/calendar.html", 
                         events=events, 
                         recurring_templates=recurring_templates,
                         current_year=current_year,
                         archive_years=archive_years)


@main_page_module.route('/calendar/event/<event_id>', methods=['GET'])
@login_required
def calendar_event_view(event_id):
    """View a single calendar event (including recurring events)"""
    event = None
    
    # Check if it's a recurring event first
    recurring_events = Gears_obj.load_recurring_events()
    for e in recurring_events:
        if e.get("id") == event_id:
            event = e
            break
    
    # If not found in recurring, check regular events
    if not event:
        for year in range(datetime.date.today().year - 1, datetime.date.today().year + 2):
            events = Gears_obj.load_calendar_events(year)
            for e in events:
                if e.get("id") == event_id:
                    event = e
                    break
            if event:
                break
    
    if not event:
        flash("Event not found.", 'error')
        return redirect(url_for("main_page_module.calendar"))
    
    return render_template("main_page_module/calendar_event_view.html", event=event)


@main_page_module.route('/calendar/archive/<int:year>', methods=['GET'])
@login_required
def calendar_archive(year):
    """View archived events for a specific year"""
    # Get regular events for the year
    events = Gears_obj.load_calendar_events(year)
    
    # Get recurring events and generate instances for the year
    recurring_events = Gears_obj.load_recurring_events()
    year_start = datetime.date(year, 1, 1)
    year_end = datetime.date(year, 12, 31)
    
    for recurring_event in recurring_events:
        instances = Gears_obj.generate_recurring_instances(recurring_event, year_start, year_end)
        events.extend(instances)
    
    # Sort events by date_start
    events.sort(key=lambda x: x["date_start"])
    
    # Get all years with events for archive navigation
    archive_years = Gears_obj.get_years_with_events()
    
    return render_template("main_page_module/calendar_archive.html", 
                         events=events, 
                         year=year,
                         archive_years=archive_years)


@main_page_module.route('/calendar/recurring', methods=['GET'])
@login_required
def calendar_recurring():
    """View and edit core recurring event templates only"""
    recurring_events = Gears_obj.load_recurring_events()
    return render_template("main_page_module/calendar_recurring.html",
                         recurring_events=recurring_events)


@main_page_module.route('/radar', methods=['GET'])
#@login_required
def radar():

    return render_template("main_page_module/radar.html")


# Set the route and accepted methods
@main_page_module.route('/targets_all/', methods=['GET'])
@login_required
def targets_all():
    all_targets = Gears_obj.load_targets()

    return render_template("main_page_module/targets/targets_all.html", all_targets=all_targets)


@main_page_module.route('/targets_new', methods=['GET', 'POST'])
@login_required
def targets_new():   
    form = form_dicts["Target"]()
    
    # Verify the sign in form
    if form.validate_on_submit():
        new_target = {"name": form.name.data,
                      "email": form.email.data,
                      "active": bool(int(form.active.data))}
        
        all_targets = Gears_obj.load_targets()        
        all_targets.append(new_target)
        target_index = len(all_targets) - 1
        
        Gears_obj.save_targets(all_targets)
    
        msg_ = "Nov naslovnik dodan."
        flash(msg_, 'success')
        
        return redirect(url_for("main_page_module.targets_edit", target_index=target_index))
    
    for field, errors in form.errors.items():
        app.logger.error(f"Field: {field}")      
        for error in errors:
            flash(f'Invalid Data for {field}: {error}', 'error')        
    
    
    return render_template("main_page_module/targets/targets_new.html", form=form)


@main_page_module.route('/targets_edit/<int:target_index>', methods=['GET', 'POST'])
@main_page_module.route('/targets_edit/', methods=['POST'])
@login_required
def targets_edit(target_index:int=None):
    form = form_dicts["Target"]()
    
    if target_index == None:
        target_index = int(form.target_index.data)
    else:
        form.target_index.data = target_index
    
    all_targets = Gears_obj.load_targets()

    if not len(all_targets) > target_index:
        msg_ = "Ni naslovnika pod tem indexom."
        flash(msg_, 'error')        
        return redirect(url_for("main_page_module.targets_all"))
    

    # GET
    if request.method == 'GET':
        target = all_targets[target_index]
        
        form.process(target_index = target_index,
                     name = target["name"],
                     email = target["email"],
                     active = int(target["active"]))
    
    # POST
    if form.validate_on_submit():
        new_target = {"name": form.name.data,
                      "email": form.email.data,
                      "active": bool(int(form.active.data))}
        
        all_targets[target_index] = new_target
        
        Gears_obj.save_targets(all_targets)
        
        msg_ = "Naslovnik posodobljen."
        flash(msg_, 'success')
        
        return redirect(url_for("main_page_module.targets_edit", target_index=target_index))
    
    for field, errors in form.errors.items():
        app.logger.warn(f"Field: {field}")      
        for error in errors:
            flash(f'Invalid Data for {field}: {error}', 'error')    
            
    return render_template("main_page_module/targets/targets_edit.html", form=form,
                           target_index=target_index)


@main_page_module.route('/targets_delete/<int:target_index>', methods=['GET'])
@login_required
def targets_delete(target_index:int):   
    try:
        all_targets = Gears_obj.load_targets()
        
        all_targets.pop(target_index)
        
        Gears_obj.save_targets(all_targets)
        
        error_msg = "Naslovnik zbrisan"
        flash(error_msg, 'success')
        
        return redirect(url_for("main_page_module.targets_all"))
    except Exception as e:
        app.logger.warn(f"{e}")
        error_msg = "Ni naslovnika pod tem indexom."
        flash(error_msg, 'error')
        
        return redirect(url_for("main_page_module.targets_all"))        


@main_page_module.route('/weather_cities', methods=['GET'])
@login_required
def weather_cities():
    """Dedicated view for editing weather cities (daily forecast locations)."""
    cities = Gears_obj.load_cities()
    return render_template("main_page_module/admin/weather_cities.html", cities=cities)


@main_page_module.route('/settings_edit/', methods=['POST', 'GET'])
@login_required
def settings_edit():
    form = form_dicts["Configuration"]()
    
    try:
        app_config = Gears_obj.load_app_config()
        current_lat = app_config.get("current_location_latitude", "")
        current_long = app_config.get("current_location_longitude", "")
        high_temp = app_config.get("high_temp_threshold", 30.0)
        low_temp = app_config.get("low_temp_threshold", 0.0)
        shelly_src_id = app_config.get("shelly_src_id", str(uuid.uuid4()))
        shelly_thermostat_ip = app_config.get("shelly_thermostat_ip", "192.168.0.123")
        systemair_hvac_ip = app_config.get("systemair_hvac_ip", "192.168.0.111")
        proxy_server_ip = app_config.get("proxy_server_ip", "http://proxy-server:5000")
        hvac_data_source = app_config.get("hvac_data_source", "systemair")
    except Exception as e:
        app.logger.warn(f"{e}")
        error_msg = "Napaka pri nalaganju nastavitev."
        flash(error_msg, 'error')
        return redirect(url_for("main_page_module.index"))
        
    # GET - populate form
    if request.method == 'GET':
        form.process(current_location_latitude=str(current_lat),
                    current_location_longitude=str(current_long),
                    high_temp_threshold=str(high_temp),
                    low_temp_threshold=str(low_temp),
                    shelly_src_id=shelly_src_id,
                    shelly_thermostat_ip=shelly_thermostat_ip,
                    systemair_hvac_ip=systemair_hvac_ip,
                    proxy_server_ip=proxy_server_ip,
                    hvac_data_source=hvac_data_source)
    
    # POST - save changes
    if form.validate_on_submit():
        try:
            app_config["current_location_latitude"] = float(form.current_location_latitude.data)
            app_config["current_location_longitude"] = float(form.current_location_longitude.data)
            app_config["high_temp_threshold"] = float(form.high_temp_threshold.data)
            app_config["low_temp_threshold"] = float(form.low_temp_threshold.data)
            app_config["shelly_src_id"] = form.shelly_src_id.data
            app_config["shelly_thermostat_ip"] = form.shelly_thermostat_ip.data.strip()
            app_config["systemair_hvac_ip"] = form.systemair_hvac_ip.data.strip()
            app_config["proxy_server_ip"] = form.proxy_server_ip.data.strip() if form.proxy_server_ip.data else "http://proxy-server:5000"
            app_config["hvac_data_source"] = form.hvac_data_source.data
        except ValueError:
            flash('Invalid numeric values.', 'error')
            return redirect(url_for("main_page_module.settings_edit"))
        
        Gears_obj.save_app_config(app_config)
        
        msg_ = "Nastavitve posodobljene."
        flash(msg_, 'success')
        return redirect(url_for("main_page_module.settings_edit"))
    
    for field, errors in form.errors.items():
        app.logger.warn(f"Field: {field}")
        for error in errors:
            flash(f'Invalid Data for {field}: {error}', 'error')    
            
    return render_template("main_page_module/admin/settings_edit.html", form=form)


@main_page_module.route('/settings_city_new', methods=['GET', 'POST'])
@login_required
def settings_city_new():
    form = form_dicts["City"]()
    
    if form.validate_on_submit():
        try:
            new_city = {
                "name": form.city_name.data,
                "latitude": float(form.city_latitude.data),
                "longitude": float(form.city_longitude.data)
            }
            
            cities = Gears_obj.load_cities()
            cities.append(new_city)
            Gears_obj.save_cities(cities)
            
            flash("City added successfully.", 'success')
            return redirect(url_for("main_page_module.weather_cities"))
        except ValueError:
            flash('Invalid latitude or longitude values.', 'error')
        except Exception as e:
            app.logger.error(f"Error adding city: {e}")
            flash('Error adding city.', 'error')
    
    return render_template("main_page_module/admin/settings_city_edit.html", form=form)


@main_page_module.route('/settings_city_edit/<int:city_index>', methods=['GET', 'POST'])
@login_required
def settings_city_edit(city_index):
    form = form_dicts["City"]()
    
    try:
        cities = Gears_obj.load_cities()
        
        if city_index >= len(cities):
            flash("City not found.", 'error')
            return redirect(url_for("main_page_module.weather_cities"))
        
        city = cities[city_index]
        
        if request.method == 'GET':
            form.process(city_index=city_index,
                         city_name=city["name"],
                         city_latitude=str(city["latitude"]),
                         city_longitude=str(city["longitude"]))
        
        if form.validate_on_submit():
            try:
                cities[city_index] = {
                    "name": form.city_name.data,
                    "latitude": float(form.city_latitude.data),
                    "longitude": float(form.city_longitude.data)
                }
                Gears_obj.save_cities(cities)
                
                flash("City updated successfully.", 'success')
                return redirect(url_for("main_page_module.weather_cities"))
            except ValueError:
                flash('Invalid latitude or longitude values.', 'error')
            except Exception as e:
                app.logger.error(f"Error updating city: {e}")
                flash('Error updating city.', 'error')
    except Exception as e:
        app.logger.error(f"Error: {e}")
        flash('Error loading city.', 'error')
        return redirect(url_for("main_page_module.weather_cities"))
    
    return render_template("main_page_module/admin/settings_city_edit.html", form=form, city_index=city_index)


@main_page_module.route('/settings_city_delete/<int:city_index>', methods=['GET'])
@login_required
def settings_city_delete(city_index):
    try:
        cities = Gears_obj.load_cities()
        
        if city_index >= len(cities):
            flash("City not found.", 'error')
        else:
            cities.pop(city_index)
            Gears_obj.save_cities(cities)
            flash("City deleted successfully.", 'success')
    except Exception as e:
        app.logger.error(f"Error deleting city: {e}")
        flash('Error deleting city.', 'error')
    
    return redirect(url_for("main_page_module.weather_cities"))


# Stikala (Shelly plugs) - list, add, edit, delete
@main_page_module.route('/stikala', methods=['GET'])
@login_required
def stikala():
    plugs = Gears_obj.load_shelly_plugs()
    return render_template("main_page_module/stikala/stikala.html", plugs=plugs)


@main_page_module.route('/stikala/new', methods=['GET', 'POST'])
@login_required
def stikala_new():
    form = form_dicts["Plug"]()
    if form.validate_on_submit():
        try:
            plugs = Gears_obj.load_shelly_plugs()
            plugs.append({
                "name": form.plug_name.data.strip(),
                "ip": form.plug_ip.data.strip(),
            })
            Gears_obj.save_shelly_plugs(plugs)
            flash("Stikalo dodano.", 'success')
            return redirect(url_for("main_page_module.stikala"))
        except Exception as e:
            app.logger.error(f"Error adding plug: {e}")
            flash('Napaka pri dodajanju.', 'error')
    return render_template("main_page_module/stikala/stikala_edit.html", form=form)


@main_page_module.route('/stikala/edit/<int:plug_index>', methods=['GET', 'POST'])
@login_required
def stikala_edit(plug_index):
    form = form_dicts["Plug"]()
    try:
        plugs = Gears_obj.load_shelly_plugs()
        if plug_index >= len(plugs):
            flash("Stikalo ni najdeno.", 'error')
            return redirect(url_for("main_page_module.stikala"))
        plug = plugs[plug_index]
        if request.method == 'GET':
            form.process(plug_name=plug["name"], plug_ip=plug["ip"])
        if form.validate_on_submit():
            plugs[plug_index] = {
                "name": form.plug_name.data.strip(),
                "ip": form.plug_ip.data.strip(),
            }
            Gears_obj.save_shelly_plugs(plugs)
            flash("Stikalo posodobljeno.", 'success')
            return redirect(url_for("main_page_module.stikala"))
    except Exception as e:
        app.logger.error(f"Error editing plug: {e}")
        flash('Napaka pri posodabljanju.', 'error')
        return redirect(url_for("main_page_module.stikala"))
    return render_template("main_page_module/stikala/stikala_edit.html", form=form, plug_index=plug_index)


@main_page_module.route('/stikala/delete/<int:plug_index>', methods=['GET'])
@login_required
def stikala_delete(plug_index):
    try:
        plugs = Gears_obj.load_shelly_plugs()
        if plug_index >= len(plugs):
            flash("Stikalo ni najdeno.", 'error')
        else:
            plugs.pop(plug_index)
            Gears_obj.save_shelly_plugs(plugs)
            flash("Stikalo izbrisano.", 'success')
    except Exception as e:
        app.logger.error(f"Error deleting plug: {e}")
        flash('Napaka pri brisanju.', 'error')
    return redirect(url_for("main_page_module.stikala"))


# Set the route and accepted methods
@main_page_module.route('/login/', methods=['GET', 'POST'])
def login():
    if ('user_id' in session):
        return redirect(url_for("main_page_module.index"))
    
    # If sign in form is submitted
    form = form_dicts["Login"]()

    # Verify the sign in form
    if form.validate_on_submit():
        admin_username = app.config['ADMIN_USERNAME']
        admin_password = app.config['ADMIN_PASS_HASH']
        
        # Generate the password hash
        same_pass = sha512_crypt.verify(form.password.data, admin_password)

        if not same_pass or admin_username != form.username_or_email.data:
            error_msg = "Login napačen."
            flash(error_msg, 'error')
            
        else:
            session['user_id'] = 1
            
            # Always set permanent session for persistent login
            session.permanent = True
    
            error_msg = "Dobrodošel!"
            flash(error_msg, 'success')
            
            return redirect(url_for('main_page_module.index'))
    
        

    for field, errors in form.errors.items():
        app.logger.warn(f"Field: {field}")      
        for error in errors:
            flash(f'Invalid Data for {field}: {error}', 'error')

    return render_template("main_page_module/auth/login.html", form=form)
        

@main_page_module.route('/logout/')
def logout():
    #session.pop("user_id", None)
    #session.permanent = False
    session.clear()
    flash('You have been logged out. Have a nice day!', 'success')

    return redirect(url_for("main_page_module.index"))