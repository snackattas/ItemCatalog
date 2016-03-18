from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc, union, null, literal_column, ForeignKey
from sqlalchemy.orm import sessionmaker
from databaseSetup import Base, User, Category, Item
import random
import string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests
from contextlib import contextmanager

app = Flask(__name__)
APPLICATION_NAME = "Item Catalog Application"
# Connect to Database and create database session
engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = DBSession()
    try:
        yield session
    except:
        session.rollback()
        raise
    else:
        session.commit()


def createUser(login_session):
    user = getUserID(login_session)
    if user:
        if login_session.get('facebook_id'):
            ### might be dot syntax for adding here
            user.facebook_id = login_session['facebook_id']
            user_id = user.id
        if login_session.get('gplus_id'):
            user.gplus_id = login_session['gplus_id']
            user_id = user.id
        session.add(user)
        session.commit()
        return user_id
    if login_session.get('facebook_id'):
        newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'], facebook_id=login_session['facebook_id'])
    if login_session.get('gplus_id'):
        newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'], gplus_id=login_session['gplus_id'])
    session.add(newUser)
    session.commit()
    return getUserID(login_session).id

def getFacebookUserID(login_session):
    try:
        user = session.query(User).filter_by(email=login_session.get('email'), facebook_id=login_session.get('facebook_id')).one()
        return user.id
    except:
        return None

def getGoogleUserID(login_session):
    try:
        user = session.query(User).filter_by(email=login_session.get('email'), gplus_id=login_session.get('gplus_id')).one()
        return user.id
    except:
        return None

def getUserID(login_session):
    try:
        ### is it a good idea to pass along a query object through functions?
        user = session.query(User).filter_by(email=login_session.get('email')).one()
        return user
    except:
        return None

def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
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
            #del login_session['credentials']
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
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(items=[item.serialize for item in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON/')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


@app.route('/category/JSON/')
def categoryJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])

def latestAdditions():
    categories = session.query(
    Category.id.label('id'),
    Category.name.label('name'),
    null().label('description'),
    Category.user_id.label('user_id'),
    Category.instant_of_creation.label('instant_of_creation'),
    Category.picture.label('picture'),
    null().label('category_id'),
    null().label('category_name'),
    literal_column('"category"').label('type'))

    items = session.query(
    Item.id.label('id'),
    Item.name.label('name'),
    Item.description.label('description'),
    Item.user_id.label('user_id'),
    Item.instant_of_creation.label('instant_of_creation'),
    Item.picture.label('picture'),
    Item.category_id.label('category_id'),
    null().label('category_name'),
    literal_column('"item"').label('type'))

    union = categories.union(items).order_by(desc('instant_of_creation')).limit(10)
    union_dict = [u.__dict__ for u in union]
    for addition in union_dict:
        addition['instant_of_creation'] = addition['instant_of_creation'].strftime("%I:%M:%S %p, %b %w").lstrip('0')
        if addition['type'] == 'item':
            category_of_item = session.query(Category).filter_by(id=addition['category_id']).one()
            addition['category_name'] = category_of_item.name
    return union_dict

# Show all restaurants
@app.route('/category/')
def showCategory():
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    categories = session.query(Category).order_by(asc(Category.name))
    no_categories = False
    try:
        content = categories[0]
    except:
        no_categories = True
    return render_template('category.html', categories=categories, login_session=login_session, no_categories=no_categories, latest_additions=latestAdditions())

# Public face of Restaurant database
@app.route('/')
@app.route('/publicCategory/')
def showPublicCategory():
    categories = session.query(Category).order_by(asc(Category.name))
    no_categories = False
    try:
        content = categories[0]
    except:
        no_categories = True
    return render_template('publicCategory.html', categories=categories, no_categories=no_categories, latest_additions=latestAdditions())

@app.route('/publicCategory/<int:category_id>/publicItem/')
def showPublicItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    creator = getUserInfo(category.user_id)
    return render_template('publicItem.html', items=items, category=category, creator=creator)

@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('newCategory.html', login_session=login_session)

# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    category = session.query(Category).filter_by(id=category_id).one()
    user_id = category.user_id
    ### I have a feeling this will need to be reworked
    if user_id != login_session['user_id']:
        return redirect(url_for('showCategory'))
    editedCategory = session.query(
        Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCategory'))
    else:
        return render_template('editCategory.html', category=editedCategory, login_session=login_session)

# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    category_to_delete = session.query(
        Category).filter_by(id=category_id).one()
    user_id = category_to_delete.user_id
    if user_id != login_session['user_id']:
        return redirect(url_for('showCategory'))
    if request.method == 'POST':
        session.delete(category_to_delete)
        flash('%s Successfully Deleted' % category_to_delete.name)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deleteCategory.html', category=category_to_delete, login_session=login_session)

# Show a category's item
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
def showItem(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicItem', category_id=category_id))
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    creator = getUserInfo(category.user_id)
    return render_template('item.html', items=items, category=category, login_session=login_session, creator=creator, user_id=login_session['user_id'])

# Create a new item
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    category = session.query(Category).filter_by(id=category_id).one()
    user_id = category.user_id
    if user_id != login_session['user_id']:
        return redirect(url_for('showCategory'))
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form[
                           'description'], category_id=category_id)
        session.add(newItem)
        session.commit()
        flash('New Item %s Successfully Created' % (newItem.name))
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('newItem.html', category=category, login_session=login_session)

# Edit a menu item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    edited_item = session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    user_id = edited_item.user_id
    if user_id != login_session['user_id']:
        return redirect(url_for('showCategory'))
    if request.method == 'POST':
        if request.form['name']:
            edited_item.name = request.form['name']
        if request.form['description']:
            edited_item.description = request.form['description']
        session.add(edited_item)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('editItem.html', category_id=category_id, item_id=item_id, item=edited_item, login_session=login_session)

# Delete a menu item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    item_to_delete = session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    user_id = item_to_delete.user_id
    print 'user_id'+str(user_id)
    print login_session['user_id']

    if user_id != login_session['user_id']:
        return redirect(url_for('showCategory'))
    if request.method == 'POST':
        session.delete(item_to_delete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('deleteItem.html', item=item_to_delete, login_session=login_session)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
