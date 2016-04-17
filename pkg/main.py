from pkg import app, db, session
from databaseSetup import User, Category, Item
from databaseSetup import CategoryImage, ItemImage, ChangeLog

from flask import render_template, request, redirect, url_for, flash
from flask import session as login_session

from sqlalchemy_imageattach.context import store_context
from sqlalchemy_imageattach.stores.fs import HttpExposedFileSystemStore

import httplib
import urlparse
import requests
from urllib2 import urlopen

from functools import wraps
import datetime

store = HttpExposedFileSystemStore(
    path='/vagrant/pkg/images/',
    prefix='/static/pkg/images/'
)

app.wsgi_app = store.wsgi_middleware(app.wsgi_app)


# Helper Functions
# Decorator for routes only accessable when logged in
def requires_login(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            # Flash error message if trying to access showItem or other
            # restricted route
            if function.__name__ != 'showCategory':
                flash('You need to be signed in to contribute to the database')
            return redirect(url_for('showPublicCategory'))
        return function(*args, **kwargs)
    return decorated_function


# Decorator for routes only accessable when logged in as the creator of a
# particular category
# Intended for the routes pertaining to items
# Uses the category_id kwarg
def requires_creator(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            flash('You need to be signed in to contribute to the database')
            return redirect(url_for('showPublicItem',
                            category_id=kwargs['category_id']))
        category = Category.query.filter_by(id=kwargs['category_id']).all()
        if category == []:
            flash('This category no longer exists')
            return redirect(url_for('showCategory'))
        if category[0].user_id != login_session['user_id']:
            # Flash error message if trying to access addItem, editItem or
            # deleteItem
            if function.__name__ != 'showItem':
                flash('Only the creator of this item can edit it')
            return redirect(url_for('showPublicItem',
                                    category_id=kwargs['category_id']))
        return function(*args, **kwargs)
    return decorated_function


# Checks if url's content-type is image via HEAD request, for less overhead
def isURLImage(url):
    acceptable_image_types = ['image/png', 'image/jpeg', 'image/jpg',
                              'image/svg+xml']
    scheme, host, path, params, query, fragment = urlparse.urlparse(url)
    if scheme != "http":
        error = "Only supports HTTP requests: %s" % (url)
        return ("", error)
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
        error = "Only image URLs accepted: %s" % (url)
        h.close()
        return ("", error)
    size = headers.get("content-length")
    if not size:
        error = "Can't determine size of image from HTTP request: %s" % (url)
        h.close()
        return ("", error)
    size = float(size) / 1000000.0
    if size > 3.0:
        error = "Only supports images that are less than 3 MB: %s" % (url)
        h.close()
        return ("", error)
    h.close()
    return (url, "")

# Function to make date difference human readable, for the Recent Activity
# Copied from here:
# http://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python
def pretty_date(time=False):
    now = datetime.datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime.datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"


# Queries the ChangeLog database, returns 10 latest changes
def changes():
    changes = ChangeLog.query.\
        order_by(db.desc('update_instant')).limit(10).all()
    return changes


# Public routes, do not require login
@app.route('/')
@app.route('/publicCategory/')
def showPublicCategory():
    categories = Category.query.order_by(db.asc(Category.name)).all()
    total_categories = len(categories) - 1
    with store_context(store):
        return render_template('publicCategory.html', categories=categories,
                               changes=changes(), pretty_date=pretty_date,
                               total_categories=total_categories,
                               enumerate=enumerate)


@app.route('/publicCategory/<int:category_id>/')
@app.route('/publicCategory/<int:category_id>/publicItem/')
def showPublicItem(category_id):
    category = Category.query.filter_by(id=category_id).all()
    if category == []:
        flash('This category does not exist')
        return render_template('publicItem.html', items=[], category=[],
                               creator=[], login_session=login_session)
    creator = User.query.filter_by(id=category[0].user_id).one()
    items = Item.query.\
        filter_by(category_id=category[0].id).all()
    with store_context(store):
        return render_template(
            'publicItem.html', items=items, category=category[0],
            creator=creator, login_session=login_session)


# Routes to edit the database, all require login
@app.route('/category/')
@requires_login
def showCategory():
    categories = Category.query.order_by(db.asc(Category.name)).all()
    total_categories = len(categories) - 1
    with store_context(store):
        return render_template('category.html', categories=categories,
                               login_session=login_session, changes=changes(),
                               pretty_date=pretty_date,
                               total_categories=total_categories,
                               enumerate=enumerate)


@app.route('/category/new/', methods=['GET', 'POST'])
@requires_login
def newCategory():
    if request.method == 'POST':
        # First check to see if image URL is valid from HEAD reqauest.
        # If its not return error
        url = request.form['url']
        (url, error) = isURLImage(url)
        if error:
            return render_template('newCategory.html',
                                   login_session=login_session,
                                   error=error)
        # Try to open the URL (urlopen uses a GET request)
        try:
            url_open = urlopen(url)
        except:
            error = "Unable to make a request to this URL: %s" % (url)
            return render_template('newCategory.html',
                                   login_session=login_session,
                                   error=error)
        # Create Category object
        new_category = Category(
            name=request.form['name'],
            user_id=login_session['user_id'],
            picture_url=url)

        # Must add picture to category object within store_context
        with store_context(store):
            new_category.picture.from_file(url_open)  # adding picture here
            session.add(new_category)
            flash('New Category %s Successfully Created' % (new_category.name))
            session.commit()
            url_open.close()  # make sure to close url connection after commit

        # After commit, retrieve category info to add to the ChangeLog
        newest_category = Category.query.\
            filter_by(user_id=login_session['user_id']).\
            order_by(db.desc('creation_instant')).limit(1)

        change_log = ChangeLog(
            user_id=newest_category[0].user_id,
            category_name=newest_category[0].name,
            category_id=newest_category[0].id,
            update_instant=newest_category[0].creation_instant,
            action="new",
            table="category")
        session.add(change_log)
        session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('newCategory.html', login_session=login_session)


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@requires_creator
def editCategory(category_id):
    edited_category = Category.query.filter_by(id=category_id).one()
    if request.method == 'POST':
        url = request.form['url']
        (url, error) = isURLImage(url)
        if error:
            return render_template('editCategory.html',
                                   login_session=login_session,
                                   category=edited_category,
                                   error=error)
        try:
            url_open = urlopen(url)
        except:
            error = "Unable to make a request to this URL: %s" % (url)
            return render_template('editCategory.html',
                                   login_session=login_session,
                                   category=edited_category,
                                   error=error)

        change_log = ChangeLog(
            user_id=edited_category.user_id,
            category_name=request.form['name'],
            category_id=category_id,
            update_instant=datetime.datetime.utcnow(),
            action="update",
            table="category")

        edited_category.name = request.form['name']
        edited_category.picture_url = url
        # Add all info to session while in store_context
        with store_context(store):
            edited_category.picture.from_file(url_open)
            session.add(change_log)
            session.add(edited_category)
            flash('Category Successfully Edited %s' % edited_category.name)
            session.commit()
            url_open.close()
        return redirect(url_for('showCategory'))
    else:
        return render_template('editCategory.html',
                               category=edited_category,
                               login_session=login_session)


@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
@requires_creator
def deleteCategory(category_id):
    category_to_delete = Category.query.filter_by(id=category_id).one()
    if request.method == 'POST':
        change_log = ChangeLog(
            user_id=category_to_delete.user_id,
            category_name=category_to_delete.name,
            update_instant=datetime.datetime.utcnow(),
            action="delete",
            table="category")

        session.add(change_log)
        # Delete last, so information is still present to add to ChangeLog
        session.delete(category_to_delete)
        flash('%s Successfully Deleted' % category_to_delete.name)
        with store_context(store):
            session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template(
            'deleteCategory.html', category=category_to_delete,
            login_session=login_session)


@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
@requires_creator
def showItem(category_id):
    category = Category.query.filter_by(id=category_id).one()
    items = Item.query.filter_by(category_id=category_id).all()
    creator = User.query.filter_by(id=category.user_id).one()
    with store_context(store):
        return render_template(
            'item.html', items=items, category=category,
            login_session=login_session, creator=creator,
            user_id=login_session['user_id'])


@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
@requires_creator
def newItem(category_id):
    category = Category.query.filter_by(id=category_id).one()
    if request.method == 'POST':
        url = request.form['url']
        (url, error) = isURLImage(url)
        if error:
            return render_template('newItem.html',
                                   login_session=login_session,
                                   category=category,
                                   error=error)
        try:
            url_open = urlopen(url)
        except:
            error = "Unable to make a request to this URL: %s" % (url)
            return render_template('newItem.html',
                                   login_session=login_session,
                                   category=category,
                                   error=error)

        new_item = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,
            user_id=category.user_id,
            picture_url=url)

        with store_context(store):
            new_item.picture.from_file(url_open)
            session.add(new_item)
            flash('New Item %s Successfully Created' % (new_item.name))
            session.commit()
            url_open.close()

        newest_item = Item.query.\
            filter_by(user_id=category.user_id).\
            order_by(db.desc('creation_instant')).limit(1)

        change_log = ChangeLog(
            user_id=category.user_id,
            category_name=category.name,
            category_id=category_id,
            item_name=newest_item[0].name,
            item_id=newest_item[0].id,
            update_instant=newest_item[0].creation_instant,
            action="new",
            table="item")

        session.add(change_log)
        session.commit()
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('newItem.html',
                               category=category,
                               login_session=login_session)


@app.route(
    '/category/<int:category_id>/item/<int:item_id>/edit/',
    methods=['GET', 'POST'])
@requires_creator
def editItem(category_id, item_id):
    category = Category.query.filter_by(id=category_id).one()
    edited_item = Item.query.\
        filter_by(id=item_id, category_id=category_id).one()
    if request.method == 'POST':
        # The ChangeLog for editing items will have an entry if any change is
        # made to an item
        # But the only metadata collected is the new item's name, even if the
        # name didn't change
        url = request.form['url']
        (url, error) = isURLImage(url)
        if error:
            return render_template('editItem.html',
                                   login_session=login_session,
                                   category_id=category_id,
                                   item_id=item_id,
                                   item=edited_item,
                                   error=error)
        try:
            url_open = urlopen(url)
        except:
            error = "Unable to make a request to this URL: %s" % (url)
            return render_template('editItem.html',
                                   login_session=login_session,
                                   category_id=category_id,
                                   item_id=item_id,
                                   item=edited_item,
                                   error=error)

        change_log = ChangeLog(
            user_id=edited_item.user_id,
            category_name=category.name,
            category_id=category_id,
            item_name=request.form['name'],
            item_id=item_id,
            update_instant=datetime.datetime.utcnow(),
            action="update",
            table="item")

        edited_item.name = request.form['name']
        edited_item.description = request.form['description']
        edited_item.picture_url = url

        with store_context(store):
            edited_item.picture.from_file(url_open)
            session.add(change_log)
            flash('Item %s Successfully Edited' % (edited_item.name))
            session.commit()
            url_open.close()
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('editItem.html',
                               category_id=category_id,
                               item_id=item_id,
                               item=edited_item,
                               login_session=login_session)


@app.route(
    '/category/<int:category_id>/item/<int:item_id>/delete/',
    methods=['GET', 'POST'])
@requires_creator
def deleteItem(category_id, item_id):
    category = Category.query.filter_by(id=category_id).one()
    item_to_delete = Item.query.\
        filter_by(id=item_id, category_id=category_id).one()
    if request.method == 'POST':
        change_log = ChangeLog(
            user_id=item_to_delete.user_id,
            category_name=category.name,
            category_id=category_id,
            item_name=item_to_delete.name,
            update_instant=datetime.datetime.utcnow(),
            action="delete",
            table="item")

        session.add(change_log)
        session.delete(item_to_delete)
        flash('Item %s Successfully Deleted' % (item_to_delete.name))
        with store_context(store):
            session.commit()
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('deleteItem.html', item=item_to_delete,
                               login_session=login_session)


@app.route('/error/')
@app.errorhandler(304)
@app.errorhandler(404)
@app.errorhandler(500)
def pageNotFound(error):
    return render_template('pageNotFound.html', error=error), 404
