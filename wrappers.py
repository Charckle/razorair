from functools import wraps
from flask import session, redirect, url_for, request, flash


#login decorator
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if ('user_id' in session):
            return f(*args, **kwargs)

        session.clear()        
        flash("Please login to access the site.", "error")
        
        return redirect(url_for("main_page_module.login"))
    
    return wrapper