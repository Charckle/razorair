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
import zipfile
import io
import pathlib
from passlib.hash import sha512_crypt
import datetime


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


@main_page_module.route('/settings_edit/', methods=['POST', 'GET'])
@login_required
def settings_edit():
    form = form_dicts["Configuration"]()
    
    try:
        cities = Gears_obj.load_cities()
        app_config = Gears_obj.load_app_config()
        current_lat = app_config.get("current_location_latitude", "")
        current_long = app_config.get("current_location_longitude", "")
        high_temp = app_config.get("high_temp_threshold", 30.0)
        low_temp = app_config.get("low_temp_threshold", 0.0)
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
                    low_temp_threshold=str(low_temp))
    
    # POST - save changes
    if form.validate_on_submit():
        try:
            app_config["current_location_latitude"] = float(form.current_location_latitude.data)
            app_config["current_location_longitude"] = float(form.current_location_longitude.data)
            app_config["high_temp_threshold"] = float(form.high_temp_threshold.data)
            app_config["low_temp_threshold"] = float(form.low_temp_threshold.data)
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
    
    return render_template("main_page_module/admin/settings_edit.html", 
                         form=form, 
                         cities=cities)


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
            return redirect(url_for("main_page_module.settings_edit"))
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
            return redirect(url_for("main_page_module.settings_edit"))
        
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
                return redirect(url_for("main_page_module.settings_edit"))
            except ValueError:
                flash('Invalid latitude or longitude values.', 'error')
            except Exception as e:
                app.logger.error(f"Error updating city: {e}")
                flash('Error updating city.', 'error')
    except Exception as e:
        app.logger.error(f"Error: {e}")
        flash('Error loading city.', 'error')
        return redirect(url_for("main_page_module.settings_edit"))
    
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
    
    return redirect(url_for("main_page_module.settings_edit"))



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
            
            #set permanent login, if selected
            if form.remember.data == True:
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