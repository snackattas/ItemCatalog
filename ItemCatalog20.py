from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from flask import session as login_session
#from sqlalchemy import create_engine, asc, desc, union, null, literal_column, ForeignKey
#from sqlalchemy.orm import sessionmaker
from databaseSetup import User, Category, Item, CategoryImage, ItemImage, ChangeLog
from databaseSetup import app, db

import random
import string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests
from flask_moment import Moment
#import sqlalchemy.exc

from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy_imageattach.context import store_context
from sqlalchemy_imageattach.stores.fs import HttpExposedFileSystemStore

import urllib2
from urllib2 import urlopen

from functools import wraps

import datetime

moment = Moment(app)
session = db.session
store = HttpExposedFileSystemStore(
    path='/vagrant/images/',
    prefix='/static/images/'
)
# store = HttpExposedFileSystemStore(
#     path='categoryimage',
#     prefix='/images/'
# )

app.wsgi_app = store.wsgi_middleware(app.wsgi_app)

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper Functions
def requires_login(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            if function.__name__ != 'showCategory':
                flash('You need to be signed in to contribute to the database')
            return redirect(url_for('showPublicCategory'))
        return function(*args, **kwargs)
    return decorated_function

def requires_creator(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            flash('You need to be signed in to contribute to the database')
            return redirect(url_for('showPublicItem', category_id=kwargs['category_id']))
        category = Category.query.filter_by(id=kwargs['category_id']).one()
        if category.user_id != login_session['user_id']:
            if function.__name__ != 'showItem':
                flash('Only the creator of this item can edit it')
            return redirect(url_for('showPublicItem', category_id=kwargs['category_id']))
        return function(*args, **kwargs)
    return decorated_function

import httplib, urlparse
def isURLImage(url):
    acceptable_image_types = ['image/png' , 'image/jpeg', 'image/jpg', 'image/svg+xml']
    scheme, host, path, params, query, fragment = urlparse.urlparse(url)
    if scheme != "http":
        error = "Only supports HTTP requests"
        return ("",error)
    if not path:
        path = "/"
    if params:
        path = path + ";" + params
    if query:
        path = path + "?" + query

    # make a http HEAD request
    h = httplib.HTTP(host)
    h.putrequest("HEAD", path)
    h.putheader("Host", host)
    h.endheaders()

    status, reason, headers = h.getreply()
    # Convert byte size to megabytes
    image_type = headers.get("content-type")
    if image_type not in acceptable_image_types:
        error = "Please enter an image URL"
        h.close()
        return ("", error)
    size = float(headers.get("content-length")) / 1000000.0
    if size > 3.0:
        error = "Only supports images that are less than 3 MB"
        h.close()
        return ("", error)
    h.close()
    return (url, "")

def createUser(login_session):
    user_id = getUserID(login_session)
    if user_id:
        user = User.query.filter_by(id=user_id).one()
        if login_session.get('facebook_id'):
            user.facebook_id = login_session['facebook_id']
        if login_session.get('gplus_id'):
            user.gplus_id = login_session['gplus_id']
        session.add(user)
        session.commit()
        return user_id

    if login_session.get('facebook_id'):
        new_user = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'], facebook_id=login_session['facebook_id'])
    if login_session.get('gplus_id'):
        new_user = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'], gplus_id=login_session['gplus_id'])
    session.add(new_user)
    session.commit()
    return getUserID(login_session)

def getFacebookUserID(login_session):
    try:
        user = User.query.filter_by(email=login_session.get('email'), facebook_id=login_session.get('facebook_id')).one()
        return user.id
    except:
        return None

def getGoogleUserID(login_session):
    try:
        user = User.query.filter_by(email=login_session.get('email'), gplus_id=login_session.get('gplus_id')).one()
        return user.id
    except:
        return None

def getUserID(login_session):
    try:
        ### is it a good idea to pass along a query object through functions?
        user = User.query.filter_by(email=login_session.get('email')).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    try:
        user = User.query.filter_by(id=user_id).one()
        user_info = user
        return user_info
    except:
        return None

@app.route('/login/')
def showLogin():
    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    app_id = json.loads(open('clientSecrets/fbClientSecrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('clientSecrets/fbClientSecrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
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
    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token
    # Get user picture, 2nd facebook API call
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate against cross reference site forgery attacks
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('clientSecrets/googleClientSecrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %  access_token)
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
    CLIENT_ID = json.loads(open('clientSecrets/googleClientSecrets.json', 'r').read())['web']['client_id']
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Using .get here instead of dict key reference because if these things don't exist in the dictionary yet, dict key reference would crash.  Get just returns None in this case
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
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
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    ("you are now logged in as %s" % login_session['username'])
    return output # this should be a login template!

def gdisconnect():
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
    	response = make_response(json.dumps('Successfully disconnected.'), 200)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    else:
    	response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    	response.headers['Content-Type'] = 'application/json'
    	return response

def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/disconnect/')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['user_id']
        del login_session['email']
        del login_session['provider']
        del login_session['picture']
        flash('You have successfully been logged out.')
        return redirect(url_for('showPublicCategory'))
    else:
        flash('You are not logged in to begin with!')
        redirect(url_for('showPublicCategory'))


# JSON APIs to view Restaurant Information
###Does it matter what I call the thin in the return statement?
@app.route('/category/<int:category_id>/item/JSON/')
def categoryItemJSON(category_id):
    items = Item.query.filter_by(
    category_id=category_id).all()
    return jsonify(items=[item.serialize for item in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON/')
def itemJSON(category_id, item_id):
    item = Item.query.filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


@app.route('/category/JSON/')
def categoryJSON():
    categories = Category.query.all()
    return jsonify(categories=[category.serialize for category in categories])

def latestAdditions():
    return ['a','b']

# Show all restaurants

# Piblic face of the Restaurants Databse
@app.route('/')
@app.route('/publicCategory/')
def showPublicCategory():
    categories = Category.query.order_by(db.asc(Category.name))
    no_categories = False
    try:
        content = categories[0]
    except:
        no_categories = True
    return render_template('publicCategory.html', categories=categories, no_categories=no_categories)
    # return render_template('publicCategory.html', categories=categories, no_categories=no_categories, latest_additions=latestAdditions())


@app.route('/publicCategory/<int:category_id>/')
@app.route('/publicCategory/<int:category_id>/publicItem/')
def showPublicItem(category_id):
    category = Category.query.filter_by(id=category_id).one()
    items = Item.query.filter_by(
        category_id=category.id).all()
    creator = User.query.filter_by(id=category.user_id).one()
    return render_template('publicItem.html', items=items, category=category, creator=creator)


@app.route('/category/')
@requires_login
def showCategory():
    categories = Category.query.order_by(db.asc(Category.name))
    no_categories = False
    try:
        content = categories[0]
    except:
        no_categories = True
    with store_context(store):
        return render_template('category.html', categories=categories, login_session=login_session, no_categories=no_categories)
    # return render_template('category.html', categories=categories, login_session=login_session, no_categories=no_categories, latest_additions=latestAdditions())


@app.route('/category/new/', methods=['GET', 'POST'])
@requires_login
def newCategory():
    if request.method == 'POST':
        # First check to see if image URL is valid
        url = request.form['url']
        (url, error) = isURLImage(url)
        if error:
            return render_template('newCategory.html', login_session=login_session, error=error)
        change_log = ChangeLog(
            user_id=login_session['user_id'],
            new_category_name = request.form['name'],
            update_instant = datetime.datetime.utcnow(),
            action="new",
            table="category")
        session.add(change_log)
        newCategory = Category(name=request.form['name'], user_id=login_session['user_id'])
        try:
            url_open = urlopen(url)
        except:
            error = "This website is blocked from making requests to that URL"
            return render_template('newCategory.html', login_session=login_session, error=error)
        with store_context(store):
            newCategory.picture.from_file(url_open)
            session.add(newCategory)
            session.commit()
            url_open.close()
        return redirect(url_for('showCategory'))
    else:
        return render_template('newCategory.html', login_session=login_session)


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@requires_creator
def editCategory(category_id):
    edited_category = Category.query.filter_by(id=category_id).one()
    if request.method == 'POST':
        change_log = ChangeLog(
            user_id=edited_category.user_id,
            old_category_name = edited_category.name,
            new_category_name = request.form['name'],
            update_instant = datetime.datetime.utcnow(),
            action="update",
            table="category")
        edited_category.name = request.form['name']
        session.add(change_log)
        session.add(edited_category)
        flash('Category Successfully Edited %s' % edited_category.name)
        with store_context(store):
            session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('editCategory.html', category=edited_category, login_session=login_session)

# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
@requires_creator
def deleteCategory(category_id):
    category_to_delete = Category.query.filter_by(id=category_id).one()
    if request.method == 'POST':
        change_log = ChangeLog(
            user_id=category_to_delete.user_id,
            old_category_name = category_to_delete.name,
            update_instant = datetime.datetime.utcnow(),
            action="delete",
            table="category")
        session.add(change_log)
        session.delete(category_to_delete)
        flash('%s Successfully Deleted' % category_to_delete.name)
        with store_context(store):
            session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('deleteCategory.html', category=category_to_delete, login_session=login_session)

# Show a category's item
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
@requires_creator
def showItem(category_id):
    category = Category.query.filter_by(id=category_id).one()
    items = Item.query.filter_by(category_id=category_id).all()
    creator = User.query.filter_by(id=category.user_id).one()
    return render_template('item.html', items=items, category=category, login_session=login_session, creator=creator, user_id=login_session['user_id'])

# Create a new item
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
@requires_creator
def newItem(category_id):
    category = Category.query.filter_by(id=category_id).one()
    if request.method == 'POST':
        change_log = ChangeLog(
            user_id=category.user_id,
            new_item_name = request.form['name'],
            update_instant = datetime.datetime.utcnow(),
            action="new",
            table="item")
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,
            user_id=category.user_id)
        session.add(newItem)
        session.add(change_log)
        session.commit()
        flash('New Item %s Successfully Created' % (newItem.name))
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('newItem.html', category=category, login_session=login_session)

# Edit a menu item
@app.route(
    '/category/<int:category_id>/item/<int:item_id>/edit/',
    methods=['GET', 'POST'])
@requires_creator
def editItem(category_id, item_id):
    edited_item = Item.query.filter_by(id=item_id, category_id=category_id).one()
    if request.method == 'POST':
        # The ChangeLog for editing items will have an entry for any change made to an item, but the entry only captures name changes.  Too much effort to load in if it's a description change or an image change
        change_log = ChangeLog(
            user_id=edited_item.user_id,
            old_item_name=edited_item.name,
            new_item_name = request.form['name'],
            update_instant = datetime.datetime.utcnow(),
            action="update",
            table="item")

        edited_item.name = request.form['name']
        edited_item.description = request.form['description']
        session.add(change_log)
        flash('Item %s Successfully Edited' % (edited_item.name))
        session.commit()
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('editItem.html', category_id=category_id, item_id=item_id, item=edited_item, login_session=login_session)

# Delete a menu item
@app.route(
    '/category/<int:category_id>/item/<int:item_id>/delete/',
    methods=['GET', 'POST'])
@requires_creator
def deleteItem(category_id, item_id):
    item_to_delete = Item.query.filter_by(id=item_id, category_id=category_id).one()
    if request.method == 'POST':
        change_log = ChangeLog(
            user_id=item_to_delete.user_id,
            old_item_name = item_to_delete.name,
            update_instant = datetime.datetime.utcnow(),
            action="delete",
            table="item")
        session.add(change_log)
        session.delete(item_to_delete)
        flash('Item %s Successfully Deleted' % (item_to_delete.name))
        with store_context(store):
            session.commit()
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('deleteItem.html', item=item_to_delete, login_session=login_session)

@app.route('/error/')
@app.errorhandler(304)
@app.errorhandler(404)
@app.errorhandler(500)
def pageNotFound(error):
    print 'here'+str(error)
    return render_template('pageNotFound.html', error=error), 404


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)