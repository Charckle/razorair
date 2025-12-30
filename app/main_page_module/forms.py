# Import Form and RecaptchaField (optional)
from flask_wtf import FlaskForm # , RecaptchaField
from flask_wtf.file import FileField, MultipleFileField, FileAllowed, FileRequired

# Import Form elements such as TextField and BooleanField (optional)
from wtforms import BooleanField, StringField, TextAreaField, SelectField, PasswordField, HiddenField, SubmitField, validators # BooleanField

# Import Form validators
from wtforms.validators import Email, EqualTo, ValidationError

from app.main_page_module.models import UserM

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
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        
        #check if it is a real email
        if(re.search(regex,email.data)):  
             #if it is, check if there is another user with the same email
            user_sql = UserM.check_email(email.data) 
            if user_sql != None:
                if user_sql["id"] != int(self.id.data):
                    raise ValidationError('Please use a different email address.')     
        
        else:  
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
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        
        #check if it is a real email
        if(re.search(regex,email.data)):  
             #if it is, check if there is another user with the same email
            user_sql = UserM.check_email(email.data) 
            if user_sql != None:
                if user_sql["id"] != int(self.id.data):
                    raise ValidationError('Please use a different email address.')     
        
        else:  
            raise ValidationError('Please use a valid email address.')            


class Configuration(FlaskForm):
    current_location_latitude = StringField('Current Location Latitude', [validators.InputRequired()])
    current_location_longitude = StringField('Current Location Longitude', [validators.InputRequired()])
    high_temp_threshold = StringField('High Temperature Threshold (°C)', [validators.InputRequired()])
    low_temp_threshold = StringField('Low Temperature Threshold (°C)', [validators.InputRequired()])
    
    submit = SubmitField('Save Changes')


class CityForm(FlaskForm):
    city_index = HiddenField('city_index')
    city_name = StringField('City Name', [validators.InputRequired(), validators.Length(max=128)])
    city_latitude = StringField('Latitude', [validators.InputRequired()])
    city_longitude = StringField('Longitude', [validators.InputRequired()])
    
    submit = SubmitField('Save City')

 
form_dicts = {"Weather": Weather,
              "HVACProgram": HVACProgram,
              "User": UserF,
              "Login": Login,
              "Configuration": Configuration,
              "City": CityForm
              } 
