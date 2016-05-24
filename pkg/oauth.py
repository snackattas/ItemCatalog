from pkg import app, session
from databaseSetup import User

from flask import render_template, request
from flask import redirect, url_for, flash, make_response
from flask import session as login_session

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests
import random
import string


# Adds user to User table.
# If a user has a google account, and logs in with a facebook login, the
# facebook login will be added to the google account, and a new account won't be
# created.  Vice versa
def createUser(login_session):
    # First check if the user already has an account
    user_id = getUserID(login_session)
    # If the user already has an account, add (or re-add) the user's google or
    # facebook id, and then quit early so as not to create another user
    if user_id:
        user = User.query.filter_by(id=user_id).one()
        if login_session.get('facebook_id'):
            user.facebook_id = login_session['facebook_id']
        if login_session.get('gplus_id'):
            user.gplus_id = login_session['gplus_id']
        session.add(user)
        session.commit()
        return user_id
    # At this point the user doesn't have an account, so we create a new
    # account for the user
    new_user = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])

    if login_session.get('facebook_id'):
        new_user.facebook_id = login_session['facebook_id']
    if login_session.get('gplus_id'):
        new_user.gplus_id = login_session['gplus_id']

    session.add(new_user)
    session.commit()
    return getUserID(login_session)


def getFacebookUserID(login_session):
    user = User.query.filter_by(
        email=login_session.get('email'),
        facebook_id=login_session.get('facebook_id')).all()
    if not user:
        return None
    return user[0].id


def getGoogleUserID(login_session):
    user = User.query.filter_by(
        email=login_session.get('email'),
        gplus_id=login_session.get('gplus_id')).all()
    if not user:
        return None
    return user[0].id


def getUserID(login_session):
    # Emails are unique so it's used to uniquely identify a user without the id
    if login_session.get('gplus_id'):
        user = User.query.filter_by(
            gplus_id=login_session.get('gplus_id')).all()
    if login_session.get('facebook_id'):
        user = User.query.filter_by(
            facebook_id=login_session.get('facebook_id')).all()
    if not user:
        return None
    return user[0].id


@app.route('/login/')
def showLogin():
    # Create anti-forgery state token
    CSRF_token = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['CSRF_token'] = CSRF_token
    return render_template('login.html', CSRF_token=CSRF_token)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['CSRF_token']:
        response = make_response(json.dumps('Invalid CSRF token.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    login.warning('in fbconnect')
    access_token = request.data
    app_id = json.loads(open('pkg/clientSecrets/fbClientSecrets.json', 'r').
                        read())['web']['app_id']
    app_secret = json.loads(
        open('pkg/clientSecrets/fbClientSecrets.json', 'r').
        read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_'\
        'exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' %\
        (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]
    # First facebook api call
    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]
    # The token must be stored in the login_session in order to properly logout,
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token
    # Get user picture, 2nd facebook API call
    url = 'https://graph.facebook.com/v2.4/me/'\
        'picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getFacebookUserID(login_session)
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Now logged in as %s with user id: %s" % (login_session['username'], login_session['user_id']))
    return output


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate against cross reference site forgery attacks
    if request.args.get('state') != login_session['CSRF_token']:
        response = make_response(json.dumps('Invalid CSRF token.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'pkg/clientSecrets/googleClientSecrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    CLIENT_ID = json.loads(
        open('pkg/clientSecrets/googleClientSecrets.json', 'r').
        read())['web']['client_id']
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Using .get here instead of dict key reference because if these things
    # don't exist in the dictionary yet, dict key reference would crash.  Get
    # just returns None in this case
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['picture'] = data['picture']
    # see if user exists, if user doesn't, make a new one
    user_id = getGoogleUserID(login_session)
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += "<h1>Welcome, "
    output += login_session['username']
    output += "!</h1>"
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Now logged in as %s with user id: %s" % (login_session['username'], login_session['user_id']))
    return output  # this should be a login template!


def gdisconnect():
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %\
        login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
    return response


def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' %\
        (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return result


@app.route('/disconnect/')
def disconnect():
    if 'provider' in login_session:
        login_session.clear()
        flash('You are logged out!')
    else:
        flash('You are not logged in to begin with!')
    return redirect(url_for('showPublicLizard'))
