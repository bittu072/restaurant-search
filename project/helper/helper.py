from flask import render_template
from flask import session as login_session

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from functools import wraps

from db.database_setup import Base, User, RecentSearch, Favorites

# Connect to Database and create database session
engine = create_engine('sqlite:///restaurant_data.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# creates user in the database based on the google's login info
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# gets the user id
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' in login_session:
            return f(*args, **kwargs)
        else:
            return render_template('login_main.html',
                                   error="Please login first!!\
                                    You are not allowed to access the\
                                     page you were trying")
    return decorated_function
