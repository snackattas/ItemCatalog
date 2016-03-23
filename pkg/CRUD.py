import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug('CRUD.py')

from pkg import app
from pkg import contextmanager
from pkg import SessionCreator
Session = SessionCreator()
get_session = Session.get_session

from sqlalchemy import asc, desc, union, null, literal_column
from flask_moment import Moment
from databaseSetup import User, Category, Item, Base
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, Blueprint
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
moment = Moment(app)

# engine = create_engine('sqlite:///itemCatalog.db')
# Base.metadata.bind = engine
#
# DBSession = sessionmaker(bind=engine)
# session = DBSession()
# @contextmanager
# def get_session():
#     session = DBSession()
#     try:
#         yield session
#     except:
#         session.rollback()
#         redirect(url_for('pageNotFound', error=404))
#     try:
#         session.commit()
#     except:
#         redirect(url_for('pageNotFound', error=404))


def latestAdditions():
    with get_session() as session:
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

        #tz info
        for addition in union_dict:
            # utc_time = addition['instant_of_creation']
            # utc_time = utc_time.replace(tzinfo=tz.tzutc())
            # print utc_time.tzname()
            # local_time = utc_time.astimezone(tz.tzlocal())
            # print local_time.tzname()
            # addition['instant_of_creation'] = local_time.strftime("%I:%M:%S %p, %b %d").lstrip('0')

            #"%I:%M:%S %p, %b %d"
            if addition['type'] == 'item':
                category_of_item = session.query(Category).filter_by(id=addition['category_id']).one()
                addition['category_name'] = category_of_item.name
        return union_dict

# Show all restaurants
@app.route('/')
@app.route('/category')
def showCategory():
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    with get_session() as session:
        categories = session.query(Category).order_by(asc(Category.name))
        no_categories = False
        try:
            content = categories[0]
        except:
            no_categories = True
        return render_template('category.html', categories=categories, login_session=login_session, no_categories=no_categories, latest_additions=latestAdditions())

# Public face of Restaurant database
@app.route('/publicCategory/')
def showPublicCategory():
    with get_session() as session:
        categories = session.query(Category).order_by(asc(Category.name))
        no_categories = False
        try:
            content = categories[0]
        except:
            no_categories = True
        return render_template('publicCategory.html', categories=categories, no_categories=no_categories, latest_additions=latestAdditions())

@app.route('/publicCategory/<int:category_id>/publicItem/')
def showPublicItem(category_id):
    with get_session() as session:
        category = session.query(Category).filter_by(id=category_id).one()
        items = session.query(Item).filter_by(
            category_id=category.id).all()
        logging.debug(items[0].user_id)
        creator = session.query(User).filter_by(id=category.user_id).one()
        return render_template('publicItem.html', items=items, category=category, creator=creator)

@app.route('/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    if request.method == 'POST':
        with get_session() as session:
            newCategory = Category(name=request.form['name'], user_id=login_session['user_id'])
            session.add(newCategory)
        return redirect(url_for('showCategory'))
    else:
        return render_template('newCategory.html', login_session=login_session)

# Edit a category
@app.route('/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    with get_session() as session:
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
@app.route('/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    with get_session() as session:
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
@app.route('/<int:category_id>/')
@app.route('/<int:category_id>/item/')
def showItem(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicItem', category_id=category_id))
    with get_session() as session:
        category = session.query(Category).filter_by(id=category_id).one()
        items = session.query(Item).filter_by(category_id=category_id).all()
        creator = session.query(User).filter_by(id=category.user_id).one()
        return render_template('item.html', items=items, category=category, login_session=login_session, creator=creator, user_id=login_session['user_id'])

# Create a new item
@app.route('/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    with get_session() as session:
        category = session.query(Category).filter_by(id=category_id).one()
        user_id = category.user_id
        if user_id != login_session['user_id']:
            return redirect(url_for('showCategory'))
        if request.method == 'POST':
            newItem = Item(name=request.form['name'], description=request.form[
                               'description'], category_id=category_id, user_id=user_id)
            session.add(newItem)
            session.commit()
            flash('New Item %s Successfully Created' % (newItem.name))
            return redirect(url_for('showItem', category_id=category_id))
        else:
            return render_template('newItem.html', category=category, login_session=login_session)

# Edit a menu item
@app.route('/<int:category_id>/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    with get_session() as session:
        edited_item = session.query(Item).filter_by(id=item_id, category_id=category_id).one()
        user_id = edited_item.user_id
        logging.debug(user_id)
        logging.debug(login_session['user_id'])
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
@app.route('/<int:category_id>/item/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showPublicCategory'))
    with get_session() as session:
        item_to_delete = session.query(Item).filter_by(id=item_id, category_id=category_id).one()
        user_id = item_to_delete.user_id
        if user_id != login_session['user_id']:
            return redirect(url_for('showCategory'))
        if request.method == 'POST':
            session.delete(item_to_delete)
            session.commit()
            flash('Item %s Successfully Deleted' % (item_to_delete.name))
            return redirect(url_for('showItem', category_id=category_id))
        else:
            return render_template('deleteItem.html', item=item_to_delete, login_session=login_session)

@app.route('/error/')
@app.errorhandler(304)
@app.errorhandler(404)
@app.errorhandler(500)
def pageNotFound(error=None):
    return make_response(render_template('pageNotFound.html', error=error), 404)
