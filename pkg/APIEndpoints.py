from pkg import app, db
from databaseSetup import User, Category, Item, ChangeLog
from flask import request, jsonify
from werkzeug.contrib.atom import AtomFeed
import datetime


# JSON API Endpoints
@app.route('/category/<int:category_id>/item/JSON/')
def categoryItemJSON(category_id):
    items = Item.query.filter_by(category_id=category_id).all()
    return jsonify(items=[item.serialize for item in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON/')
def individualItemJSON(category_id, item_id):
    item = Item.query.filter_by(id=item_id).all()
    if item == []:
        item = Item()  # if no items, populate with null and don't crash
    else:
        item = item[0]
    return jsonify(item=item.serialize)


@app.route('/category/JSON/')
def categoryJSON():
    categories = Category.query.all()
    return jsonify(categories=[category.serialize for category in categories])


# ATOM API Endpoints
@app.route('/category.atom/')
def categoryATOM():
    # Get the last added category's creation date to populate as the
    # last updated date for the ATOM feed
    latest_update = Category.query.order_by(
        db.desc('creation_instant')).limit(1).all()

    updated = None
    if latest_update != []:
        updated = latest_update[0].creation_instant

    feed = AtomFeed(
        'All Categories',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicCategory/",
        updated=updated)

    categories = Category.query.order_by(db.desc('creation_instant')).all()
    for category in categories:
        user = User.query.filter_by(id=category.user_id).one()
        url = "http://localhost:8000/publicCategory/#%s" % (category.id)
        content = "Picture URL: <a href='%s'>%s</a>" % \
            (category.picture_url, category.picture_url)
        feed.add(
            category.name,
            content,
            content_type='html',
            author={'name': user.name},
            url=url,
            id=url,
            updated=category.creation_instant,
            published=category.creation_instant)
    return feed.get_response()


@app.route('/item.atom/')
def itemATOM():
    latest_update = Item.query.order_by(
        db.desc('creation_instant')).limit(1).all()

    updated = None
    if latest_update != []:
        updated = latest_update[0].creation_instant

    feed = AtomFeed(
        'All Items',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicCategory/",
        updated=updated)

    items = Item.query.order_by(db.desc('creation_instant')).all()
    for item in items:
        category = Category.query.filter_by(id=item.category_id).one()
        user = User.query.filter_by(id=item.user_id).one()
        content = """
            Description: %s
            </br>
            Category:
            <a href='http://localhost:8000/publicCategory/#%s'>%s</a>
            </br>
            Picture URL: <a href='%s'>%s</a>""" % \
            (item.description, category.id, category.name,
                item.picture_url, item.picture_url)
        url = "http://localhost:8000/publicCategory/%s/publicItem/#%s" % \
            (category.id, item.id)
        feed.add(
            item.name,
            content,
            content_type='html',
            author={'name': user.name},
            url=url,
            id=url,
            updated=item.creation_instant,
            published=item.creation_instant)
    return feed.get_response()


@app.route('/all.atom/')
def allATOM():
    # Query to perform union on all categories and items
    # Then sort results by creation instant
    results = db.engine.execute("""
        SELECT * FROM
            (SELECT
                id,
                name,
                user_id,
                NULL as description,
                creation_instant,
                picture_url,
                NULL as category_id,
                "category" AS type
            FROM Category
            UNION
            SELECT
                id,
                name,
                user_id,
                description,
                creation_instant,
                picture_url,
                category_id,
                "item" AS type
            FROM Item)
        ORDER BY creation_instant DESC""").fetchall()

    updated = None
    if results != []:
        # Executing the query with raw SQL returns unicode, not python date
        # Need to convert it back to a python date
        updated = datetime.datetime.strptime(
            results[0].creation_instant, '%Y-%m-%d %H:%M:%S.%f')

    feed = AtomFeed(
        'All Categories and Items',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicCategory/",
        updated=updated)

    for result in results:
        user = User.query.filter_by(id=result.user_id).one()
        updated = datetime.datetime.strptime(
            result.creation_instant, '%Y-%m-%d %H:%M:%S.%f')

        if result.type == 'category':
            name = "Category %s" % (result.name)
            url = "http://localhost:8000/publicCategory/#%s" % (result.id)
            content = "Picture URL: <a href='%s'>%s</a>" % \
                (result.picture_url, result.picture_url)

        if result.type == 'item':
            category = Category.query.filter_by(id=result.category_id).one()
            name = "Item %s" % (result.name)
            url = "http://localhost:8000/publicCategory/%s/publicItem/#%s" % \
                (category.id, result.id)
            content = """
                Description: %s
                </br>
                Category:
                <a href='http://localhost:8000/publicCategory/#%s'>%s</a>
                </br>
                Picture URL: <a href='%s'>%s</a>""" % \
                (result.description, result.id, category.name,
                    result.picture_url, result.picture_url)

        feed.add(
            name,
            content,
            content_type='html',
            author={'name': user.name},
            url=url,
            id=url,
            updated=updated,
            published=updated)
    return feed.get_response()


@app.route('/changes.atom/')
def changesATOM():
    changes = ChangeLog.query.order_by(db.desc('update_instant')).all()

    updated = None
    if changes != []:
        updated = changes[0].update_instant

    feed = AtomFeed(
        'Changes to Category Database',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicCategory/",
        updated=updated)

    for change in changes:
        user = User.query.filter_by(id=change.user_id).one()
        content = "Action: %s" % (change.action)

        if change.table == 'category':
            name = "Category %s" % (change.category_name)
            if change.action == 'delete':
                url = None
                unique_url = "http://localhost:8000/publicCategory/"
            if change.action == 'new' or change.action == 'update':
                url = "http://localhost:8000/publicCategory/#%s" % \
                    (change.category_id)
                unique_url = url

        if change.table == 'item':
            name = "Item %s" % (change.item_name)
            if change.action == 'delete':
                url = None
                unique_url = "http://localhost:8000/publicCategory/"
            if change.action == 'new' or change.action == 'update':
                url = "http://localhost:8000/publicCategory/%s/publicItem/#%s" \
                    % (change.category_id, change.item_id)
                unique_url = url

        feed.add(
            name,
            content,
            content_type='html',
            author={'name': user.name},
            url=url,
            id=unique_url,
            updated=change.update_instant,
            published=change.update_instant)
    return feed.get_response()
