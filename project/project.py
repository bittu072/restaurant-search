from flask import Flask, render_template, request, redirect
from flask import session as login_session
from flask import jsonify, url_for, flash
from flask import make_response

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker

from functools import wraps

import json
import urllib2
import os
import random
import string
import httplib2
import requests

from database_setup import Base, User, RecentSearch
import yelpapi


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


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
            flash("Please login first!!")
            flash("You are not allowed to access the page you were trying")
            return redirect(url_for('showLogin'))
    return decorated_function



@app.route('/')
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login_main.html', STATE=state)


# googe login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current \
                                            user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
        150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# google logout
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

    	response = make_response(json.dumps('Failed to revoke token \
                                         for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/demo')
def showdemo():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('demo.html', STATE=state)


@app.route('/yelprestsearch', methods=['GET', 'POST'])
def yelpRestaurantSearch():
    if request.method == 'GET':
        return render_template('search.html')
    # else part would be for the POST
    else:
        error_there = False
        error=""
        queryInstance = yelpapi.SearchQuery()
        searchItem = request.form['searchitem']
        if not searchItem:
            error_there = True
            error = error + "Please, mention seach item!! "
        location = request.form['location']
        lati = request.form['lat']
        longi = request.form['longi']

        if not location:
            if not (longi and lati):
                error_there = True
                error = error + "Please, mention location or allow the location!!"
            else:
                location_json_string = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + lati + "," + longi + "&key=AIzaSyAVPz6x8WGP1jhFxAqoeU-tE43ZPZl6n4o"
                location_json = urllib2.urlopen(location_json_string)
                loc_obj = json.load(location_json);
                location = loc_obj["results"][1]["formatted_address"]

        if error_there:
            return render_template('search.html', error=error)
        else:
            results = queryInstance.main(location, searchItem)
            if 'username' not in login_session:
                return render_template('searchresults.html', results=results,
                                       location=location)
            else:
                # adding recent search to the table/database
                newSearch = RecentSearch(search=searchItem, location=location,
                                         user_id=login_session['user_id'])
                session.add(newSearch)
                session.commit()

                # ______________having error________need to update this
                if(request.form['favorite']):
                    favorite_info = request.form['favorite_info']
                    newFav = Favorites(rest_name=favorite_info["name"],
                                          rating=favorite_info["rating"],
                                          link=favorite_info["url"],
                                          number=favorite_info["phone"])
                    print "_________________"
                    print favorite_info["name"]+ favorite_info["rating"]
                    +favorite_info["url"]+favorite_info["phone"]
                    print "_________________"
                    session.add(newFav)
                    session.commit()
                return render_template('searchresults.html', results=results,
                        location=location, username=login_session['username'])


@app.route('/userhome')
@login_required
def userHome():
    if 'username' in login_session:
        return render_template('userhome.html', username=login_session['username'], uid=login_session['user_id'])



@app.route('/userhome/<int:user_id>/recents')
@login_required
def userRecents(user_id):
    username = getUserInfo(user_id)
    recents = session.query(RecentSearch).filter_by(user_id=user_id).all()
    return render_template('recents.html', recents=recents)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    # always turn off debugging
    # when the application moves to production environment.
    app.debug = True
    # defines which port to use
    port = int(os.environ.get("PORT", 5000))
    # defines to consider host as localhost
    app.run(host='0.0.0.0', port=port)
