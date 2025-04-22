import sys
from os import environ 


class Config(object):
    # environmental variables are set in .env, for development purpoises
    DEBUG = False
    TESTING = False
    SECRET_KEY = environ.get('RAIR_SECRET_KEY', "B\xb2?.\xdf\x9f\xa7m\xf8\x8a%,\xf7\xc4\xfa\x91")
    
    JWT_SECRET_KEY = environ.get('RAIR_JWT_SECRET_KEY', "sdf34tasdft34")
    
    APP_NAME = environ.get('RAIR_APP_NAME', "Stribog Manager")
    
    ADMIN_USERNAME = environ.get('RAIR_ADMIN_USERNAME', "admin")
    # SHA512
    # banana
    ADMIN_PASS_HASH = environ.get('RAIR_ADMIN_PASS_HASH', "$6$rounds=656000$fwae7LSkwByBpb.3$aHJHT/14VpH3lWIMK9TllW10WK3qi5D5fHvF9JzH6f588ly/GX/j9ojs7mDt/RHgLTAfmEZezob87x/SlKElT/")
    
    SESSION_COOKIE_SECURE = True
    
    APP_LOGGING = environ.get('RAIR_APP_LOGGING', "INFO")    
    SYSTEMAIR_SERVER = environ.get('SYSTEMAIR_SERVER', "127.0.0.1")    
    THERMOSTAT_SERVER = environ.get('THERMOSTAT_SERVER', "127.0.0.1")    
    
    
    

    # Application threads. A common general assumption is
    # using 2 per available processor cores - to handle
    # incoming requests using one and performing background
    # operations using the other.
    THREADS_PER_PAGE = 2
    
    # Enable protection agains *Cross-site Request Forgery (CSRF)*
    # CSRF_ENABLED = environ.get('CSRF_ENABLED', False)
    

    
class ProductionConfig(Config):
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    TESTING = True

    SESSION_COOKIE_SECURE = False