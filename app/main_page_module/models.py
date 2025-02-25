from datetime import datetime, date

# Import password / encryption helper tools
#from werkzeug import check_password_hash, generate_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

from datab import DB


class WeatherM:
    @staticmethod
    def create(location_name, location_coordinates):
        db = DB()
        
        sql_command = f"""INSERT INTO group_access (location_name, location_coordinates)
            VALUES (%s, %s);"""
    
        return db.q_exe_new(sql_command, (location_name, location_coordinates))

    # WeatherM
    @staticmethod
    def get_one(weather_id):
        db = DB()
        sql_command = f"""SELECT id, location_name, location_coordinates FROM weather WHERE id = %s;"""
        
        return db.q_r_one(sql_command, (weather_id, ))    

    # WeatherM
    @staticmethod
    def get_all():
        db = DB()
        sql_command = f"""SELECT id, location_name, location_coordinates FROM weather;"""

        return db.q_r_all(sql_command, ())

    # WeatherM
    @staticmethod
    def change(weather_id, location_name, location_coordinate):
        db = DB()
      
        sql_command = f"""UPDATE weather 
        SET location_name = %s, location_coordinate = %s
        WHERE id = %s"""
        
        db.q_exe(sql_command, (location_name, location_coordinate, weather_id,))    


    # WeatherM
    @staticmethod
    def delete(weather_id):
        db = DB()
        sql_command = f"""DELETE FROM weather WHERE id = %s;"""
        
        db.q_exe(sql_command, (weather_id,))
        
        

        


class UserM:
    @staticmethod
    def create(name, username, email, password, status, api_key):
        db = DB()
        
        password_hash = generate_password_hash(password)
        
        created_date = date.today()
        
        sql_command = f"""INSERT INTO users (name, username, email, password, status, api_key, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s);"""
    
        return db.q_exe_new(sql_command, (name, username, email, password_hash, status, api_key, created_date))
    
    # UserM
    @staticmethod
    def check_username(username):
        db = DB()
        sql_command = f"SELECT id, username, password FROM users WHERE (%s = username);"
        
        results = db.q_r_one(sql_command, (username,))  
        
        #is a user is found, returns its ID
        if results is not None:
            return results
        
        return False
    
    # UserM
    @staticmethod
    def id_from_username(username):
        db = DB()
        sql_command = f"SELECT id FROM users WHERE (%s = username);"
        
        return db.q_r_one(sql_command, (username,))  
    
    # UserM
    @staticmethod
    def check_email(email):
        db = DB()
        sql_command = f"SELECT id, email FROM users WHERE (%s = email);"

        return db.q_r_one(sql_command, (email,))
    
    # UserM
    @staticmethod
    def login_check(username_or_email, password):
        db = DB()
        sql_command = f"SELECT id, name, username, email, password FROM users WHERE (%s = username) OR (%s = email);"
        
        results = db.q_r_one(sql_command, (username_or_email, username_or_email))  
        
        #is a user is found, returns its ID
        if results is not None:
            if check_password_hash(results["password"], password):
                
                return results
        
        return False
    
    # UserM
    @staticmethod
    def get_all():
        db = DB()
        sql_command = f"SELECT id, name, username FROM users;"

        return db.q_r_all(sql_command, ())  
    
    # UserM
    @staticmethod
    def get_all_w_status(status):
        db = DB()
        sql_command = f"""SELECT id, name, username 
        FROM users
        WHERE status = %s;"""

        return db.q_r_all(sql_command, (status,))      
    
    # UserM
    @staticmethod
    def get_one(user_id):
        db = DB()
        sql_command = f"""SELECT id, name, username, email, password, status, created_date, api_key 
        FROM users WHERE id = %s;"""
        
        return db.q_r_one(sql_command, (user_id, ))
    
    # UserM
    @staticmethod
    def check_api_access(api_key):
        db = DB()
        sql_command = f"""SELECT id, name, username, email, password, status, created_date, api_key 
        FROM users WHERE api_key = %s AND status = 1;"""
        
        return db.q_r_one(sql_command, (api_key,))      
    
    # UserM
    @staticmethod
    def delete_one(user_id):
        db = DB()
        sql_command = f"DELETE FROM users WHERE id = %s;"
        
        db.q_exe(sql_command, (user_id,))
    
    # UserM
    @staticmethod
    def change_one(user_id, username, name, email, api_key, status):
        db = DB()
      
        sql_command = f"""UPDATE users 
        SET name = %s, username = %s,
        email = %s, api_key = %s,
        status = %s
        WHERE id = %s"""
        
        db.q_exe(sql_command, (name, username, email, api_key, status, user_id,))
        
    # UserM
    @staticmethod
    def change_profile(user_id, name, email, api_key):
        db = DB()
      
        sql_command = f"""UPDATE users 
        SET name = %s, 
        email = %s, api_key = %s
        WHERE id = %s"""
        
        db.q_exe(sql_command, (name, email, api_key, user_id,))        
    
    # UserM
    @staticmethod
    def change_passw(user_id, password):
        db = DB()
        password_hash = generate_password_hash(password)

        sql_command = f"""UPDATE users 
        SET password = %s
        WHERE id = %s"""
        
        db.q_exe(sql_command, (password_hash, user_id,))       
        
        password = None

    # UserM
    @staticmethod
    def save_fido2_creds(user_id, credential_id_bs64, credential_public_key_bs4):
        db = DB()

        sql_command = f"""INSERT INTO user_fido2 (user_id, cred_id_bs64, public_key_bs64)
                      VALUES (%s, %s, %s);"""
        
        return db.q_exe_new(sql_command, (user_id, credential_id_bs64, credential_public_key_bs4))

    # UserM
    @staticmethod
    def get_fido2(cred_id_bs64):
        db = DB()
        sql_command = f"""SELECT user_id, cred_id_bs64, public_key_bs64
        FROM user_fido2 WHERE cred_id_bs64 = %s;"""
        
        return db.q_r_one(sql_command, (cred_id_bs64, ))
    
    # UserM
    @staticmethod
    def get_all_fido2_of_u(user_id):
        db = DB()
        sql_command = f"""SELECT user_id, cred_id_bs64, public_key_bs64 FROM user_fido2
        WHERE user_id = %s"""

        return db.q_r_all(sql_command, (user_id,)) 
    
    # UserM
    @staticmethod
    def delete_one_fido2(cred_id_bs64):
        db = DB()
        sql_command = f"DELETE FROM user_fido2 WHERE cred_id_bs64 = %s;"
        
        db.q_exe(sql_command, (cred_id_bs64,))    
 
        

class AuditLM:
    def add(user_id, change_):
        audit_datetime = datetime.now()
        
        db = DB()
        sql_command = f"""INSERT INTO audit_log (audit_datetime, user_id, change_)
                      VALUES (%s, %s, %s);"""                
            
        return db.q_exe_new(sql_command, (audit_datetime, user_id, change_))
    
    # AuditLM
    def get_all():
        db = DB()
        sql_command = f"""SELECT audit_datetime, user_id, change_ FROM audit_log;"""  

        return db.q_r_all(sql_command, ())
    
    # AuditLM
    def get_all_limit_200():
        db = DB()
        sql_command = f"""
        SELECT audit_datetime, user_id, name, username, change_ FROM audit_log
        LEFT JOIN users ON users.id = audit_log.user_id 
        LIMIT 200;"""  

        return db.q_r_all(sql_command, ())           
    
    # AuditLM
    def delete_all_but_200():
        db = DB()
        sql_command = f"""
        DELETE FROM audit_log
        WHERE audit_datetime NOT IN (
            SELECT audit_datetime
            FROM (
                SELECT audit_datetime
                FROM audit_log
                ORDER BY audit_datetime DESC
                LIMIT 200
            ) AS last_200
            );"""  
        
        db.q_exe(sql_command, ())
