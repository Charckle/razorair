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
        settings = Gears_obj.load_settings()
    except Exception as e:
        app.logger.warn(f"{e}")
        error_msg = "Napaka pri nalaganju nastavitev iz datoteke."
        flash(error_msg, 'error')
        
        return redirect(url_for("main_page_module.base_"))        

    # GET
    if request.method == 'GET':
        form.process(instance_name = settings["instance_name"],
                     admin_email = settings["admin_email"],
                     emails = int(settings["emails"]),
                     send_analitycs_to_admin = int(settings["send_analitycs_to_admin"]),
                     source_check_interval = settings["source_check_interval"],
                     smtp_server = settings["smtp_server"],
                     smtp_port = settings["smtp_port"],
                     smtp_sender_email = settings["smtp_sender_email"],
                     smtp_password = settings["smtp_password"],
                     topic = settings["topic"],
                     message = settings["message"],
                     on_no_memory_send_one = int(settings["on_no_memory_send_one"]),
                     logging_level = settings["logging_level"])
    
    # POST
    if form.validate_on_submit():
        settings_ = {"instance_name": form.instance_name.data,
                      "admin_email": form.admin_email.data,
                      "emails": bool(int(form.emails.data)),
                      "send_analitycs_to_admin": bool(int(form.send_analitycs_to_admin.data)),
                      "source_check_interval": form.source_check_interval.data,
                      "smtp_server": form.smtp_server.data,
                      "smtp_port": form.smtp_port.data,
                      "smtp_sender_email": form.smtp_sender_email.data,
                      "smtp_password": form.smtp_password.data,
                      "topic": form.topic.data,
                      "message": form.message.data,
                      "on_no_memory_send_one": bool(int(form.on_no_memory_send_one.data)),
                      "logging_level": form.logging_level.data}
                
        Gears_obj.save_settings(settings_)
        
        msg_ = "Nastavitve posodobljene."
        flash(msg_, 'success')
        
        return redirect(url_for("main_page_module.settings_edit"))
    
    for field, errors in form.errors.items():
        app.logger.warn(f"Field: {field}")
        for error in errors:
            flash(f'Invalid Data for {field}: {error}', 'error')    
            
    return render_template("main_page_module/admin/settings_edit.html", form=form)



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