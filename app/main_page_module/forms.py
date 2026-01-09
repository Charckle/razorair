# Import Form and RecaptchaField (optional)
from flask_wtf import FlaskForm # , RecaptchaField
from flask_wtf.file import FileField, MultipleFileField, FileAllowed, FileRequired

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import BooleanField, StringField, TextAreaField, SelectField, PasswordField, HiddenField, SubmitField, validators # BooleanField

# Import Form validators
from wtforms.validators import Email, EqualTo, ValidationError

#email verification
import re
import os.path


class Weather(FlaskForm):
    id = HiddenField('id', [validators.InputRequired(message='Dont fiddle around with the code!')])
    
    location_name = StringField('Name of the Location', [validators.InputRequired(message='You need to specify a name'),
                                             validators.Length(max=128)])    

    location_coordinates = StringField('Coordinates', [validators.InputRequired(message='You need to specify coordinates'),
                                             validators.Length(max=128)])    
    
    submit = SubmitField('Submit changes')


class HVACProgram(FlaskForm):
    id = HiddenField('id', [validators.InputRequired(message='Dont fiddle around with the code!')])
    
    location_name = StringField('Name of the Location', [validators.InputRequired(message='You need to specify a name'),
                                             validators.Length(max=128)])    

    location_coordinates = StringField('Coordinates', [validators.InputRequired(message='You need to specify coordinates'),
                                             validators.Length(max=128)])    
    
    submit = SubmitField('Submit changes')


class Login(FlaskForm):
    username_or_email = StringField('Username or Email', [validators.InputRequired(message='Forgot your email address?')])
    password = PasswordField('Password', [validators.InputRequired(message='Must provide a password.')])
    remember = BooleanField()
    
    submit = SubmitField('Login')

class UserF(FlaskForm):

    id = HiddenField('id', [validators.InputRequired(message='Dont fiddle around with the code!')])
    name   = StringField('Identification name', [validators.InputRequired(message='We need a name for the user.')])
    
    username   = StringField('Username', [validators.InputRequired(message='We need a username for your account.')])
    email    = StringField('Email', [validators.InputRequired(message='We need an email for your account.')])
    password  = PasswordField('Password')    
    password_2 = PasswordField('Repeat password', [EqualTo('password', message='Passwords must match')])
    
    status = SelectField(u'User Status?', [
        validators.InputRequired(message='You need to specify the status')], 
                         choices=[('0', 'Disabled'), ('1', 'Enabled')])      
    
    api_key = StringField('Api Key', [validators.InputRequired(message='We need an api key.'),
                                      validators.Length(max=20)])    
    
    submit = SubmitField('Submit changes')
    
    def validate_email(self, email):
        regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        
        #check if it is a valid email format
        if not re.search(regex, email.data):  
            raise ValidationError('Please use a valid email address.')            
    

class UserProfileF(FlaskForm):

    id = HiddenField('id', [validators.InputRequired(message='Dont fiddle around with the code!')])
    name   = StringField('Identification name', [validators.InputRequired(message='We need a name for the user.')])
    username   = StringField('Username')
    
    email    = StringField('Email', [validators.InputRequired(message='We need an email for your account.')])
    password  = PasswordField('Password')    
    password_2 = PasswordField('Repeat password', [EqualTo('password', message='Passwords must match')])
    
    api_key = StringField('Api Key', [validators.InputRequired(message='We need an api key.'),
                                      validators.Length(max=20)])    
    
    submit = SubmitField('Submit changes')
    
    def validate_email(self, email):
        regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        
        #check if it is a valid email format
        if not re.search(regex, email.data):  
            raise ValidationError('Please use a valid email address.')            


class Configuration(FlaskForm):
    current_location_latitude = StringField('Current Location Latitude', [validators.InputRequired()])
    current_location_longitude = StringField('Current Location Longitude', [validators.InputRequired()])
    high_temp_threshold = StringField('High Temperature Threshold (°C)', [validators.InputRequired()])
    low_temp_threshold = StringField('Low Temperature Threshold (°C)', [validators.InputRequired()])
    shelly_src_id = StringField('Shelly Source ID', [validators.InputRequired()])
    shelly_thermostat_ip = StringField('Shelly Thermostat IP', [validators.InputRequired()])
    systemair_hvac_ip = StringField('Systemair HVAC IP', [validators.InputRequired()])
    
    submit = SubmitField('Save Changes')


class CityForm(FlaskForm):
    city_index = HiddenField('city_index')
    city_name = StringField('City Name', [validators.InputRequired(), validators.Length(max=128)])
    city_latitude = StringField('Latitude', [validators.InputRequired()])
    city_longitude = StringField('Longitude', [validators.InputRequired()])
    
    submit = SubmitField('Save City')


class CalendarEventForm(FlaskForm):
    event_id = HiddenField('event_id')
    title = StringField('Title', [validators.InputRequired(), validators.Length(max=128)])
    description = TextAreaField('Description', [validators.Optional(), validators.Length(max=500)])
    date_start = StringField('Start Date', [validators.InputRequired()])
    date_end = StringField('End Date', [validators.InputRequired()])
    time_start = StringField('Start Time', [validators.Optional()])
    time_end = StringField('End Time', [validators.Optional()])
    recurrence_type = SelectField('Recurrence', 
                       choices=[
                           ('none', 'No Recurrence'),
                           ('yearly', 'Yearly (e.g., birthdays)'),
                           ('monthly', 'Monthly'),
                           ('weekly', 'Weekly'),
                           ('daily', 'Daily')
                       ],
                       default='none')
    recurrence_end_date = StringField('Recurrence End Date (optional)', [validators.Optional()])
    color = SelectField('Color', 
                       choices=[
                           ('primary', 'Blue'),
                           ('secondary', 'Gray'),
                           ('success', 'Green'),
                           ('danger', 'Red'),
                           ('warning', 'Yellow'),
                           ('info', 'Cyan'),
                           ('light', 'Light'),
                           ('dark', 'Dark')
                       ],
                       default='primary')
    
    submit = SubmitField('Save Event')

 
form_dicts = {"Weather": Weather,
              "HVACProgram": HVACProgram,
              "User": UserF,
              "Login": Login,
              "Configuration": Configuration,
              "City": CityForm,
              "CalendarEvent": CalendarEventForm
              } 
