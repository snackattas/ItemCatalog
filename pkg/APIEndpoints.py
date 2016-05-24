from pkg import app, db
from databaseSetup import User, Lizard, Hobby, ChangeLog
from flask import request, jsonify
from werkzeug.contrib.atom import AtomFeed
import datetime


# JSON API Endpoints
@app.route('/lizard/<int:lizard_id>/hobby/JSON/')
def lizardHobbyJSON(lizard_id):
    hobbies = Hobby.query.filter_by(lizard_id=lizard_id).all()
    return jsonify(hobbies=[hobby.serialize for hobby in hobbies])


@app.route('/lizard/<int:lizard_id>/hobby/<int:hobby_id>/JSON/')
def individualHobbyJSON(lizard_id, hobby_id):
    hobby = Hobby.query.filter_by(id=hobby_id).all()
    if not hobby:
        hobby = Hobby()  # if no hobbies, populate with null and don't crash
    else:
        hobby = hobby[0]
    return jsonify(hobby=hobby.serialize)


@app.route('/lizard/JSON/')
def lizardJSON():
    lizards = Lizard.query.all()
    return jsonify(lizards=[lizard.serialize for lizard in lizards])


# ATOM API Endpoints
@app.route('/lizard.atom/')
def lizardATOM():
    # Get the last added lizard's creation date to populate as the
    # last updated date for the ATOM feed
    latest_update = Lizard.query.order_by(
        db.desc('creation_instant')).limit(1).all()

    updated = None
    if latest_update:
        updated = latest_update[0].creation_instant

    feed = AtomFeed(
        'All Lizards',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicLizard/",
        updated=updated)

    lizards = Lizard.query.order_by(db.desc('creation_instant')).all()
    for lizard in lizards:
        user = User.query.filter_by(id=lizard.user_id).one()
        url = "http://localhost:8000/publicLizard/#%s" % (lizard.id)
        content = "Picture URL: <a href='%s'>%s</a>" % \
            (lizard.picture_url, lizard.picture_url)
        feed.add(
            lizard.name,
            content,
            content_type='html',
            author={'name': user.name},
            url=url,
            id=url,
            updated=lizard.creation_instant,
            published=lizard.creation_instant)
    return feed.get_response()


@app.route('/hobby.atom/')
def hobbyATOM():
    latest_update = Hobby.query.order_by(
        db.desc('creation_instant')).limit(1).all()

    updated = None
    if latest_update:
        updated = latest_update[0].creation_instant

    feed = AtomFeed(
        'All Hobbies',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicLizard/",
        updated=updated)

    hobbies = Hobby.query.order_by(db.desc('creation_instant')).all()
    for hobby in hobbies:
        lizard = Lizard.query.filter_by(id=hobby.lizard_id).one()
        user = User.query.filter_by(id=hobby.user_id).one()
        content = """
            Description: %s
            </br>
            Lizard:
            <a href='http://localhost:8000/publicLizard/#%s'>%s</a>
            </br>
            Picture URL: <a href='%s'>%s</a>""" % \
            (hobby.description, lizard.id, lizard.name,
                hobby.picture_url, hobby.picture_url)
        url = "http://localhost:8000/publicLizard/%s/publicHobby/#%s" % \
            (lizard.id, hobby.id)
        feed.add(
            hobby.name,
            content,
            content_type='html',
            author={'name': user.name},
            url=url,
            id=url,
            updated=hobby.creation_instant,
            published=hobby.creation_instant)
    return feed.get_response()


@app.route('/all.atom/')
def allATOM():
    # Query to perform union on all lizards and hobbies
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
                NULL as lizard_id,
                "lizard" AS type
            FROM Lizard
            UNION
            SELECT
                id,
                name,
                user_id,
                description,
                creation_instant,
                picture_url,
                lizard_id,
                "hobby" AS type
            FROM Hobby)
        ORDER BY creation_instant DESC""").fetchall()

    updated = None
    if results:
        # Executing the query with raw SQL returns unicode, not python date
        # Need to convert it back to a python date
        updated = datetime.datetime.strptime(
            results[0].creation_instant, '%Y-%m-%d %H:%M:%S.%f')

    feed = AtomFeed(
        'All Lizards and Hobbies',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicLizard/",
        updated=updated)

    for result in results:
        user = User.query.filter_by(id=result.user_id).one()
        updated = datetime.datetime.strptime(
            result.creation_instant, '%Y-%m-%d %H:%M:%S.%f')

        if result.type == 'lizard':
            name = "Lizard %s" % (result.name)
            url = "http://localhost:8000/publicLizard/#%s" % (result.id)
            content = "Picture URL: <a href='%s'>%s</a>" % \
                (result.picture_url, result.picture_url)

        if result.type == 'hobby':
            lizard = Lizard.query.filter_by(id=result.lizard_id).one()
            name = "Hobby %s" % (result.name)
            url = "http://localhost:8000/publicLizard/%s/publicHobby/#%s" % \
                (lizard.id, result.id)
            content = """
                Description: %s
                </br>
                Lizard:
                <a href='http://localhost:8000/publicLizard/#%s'>%s</a>
                </br>
                Picture URL: <a href='%s'>%s</a>""" % \
                (result.description, result.id, lizard.name,
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
    if changes:
        updated = changes[0].update_instant

    feed = AtomFeed(
        'Changes to Lizard Database',
        feed_url=request.url,
        url=request.url_root,
        author={'name': 'Zach Attas', 'email': 'zach.attas@gmail.com'},
        id="http://localhost:8000/publicLizard/",
        updated=updated)

    for change in changes:
        user = User.query.filter_by(id=change.user_id).one()
        content = "Action: %s" % (change.action)

        if change.table == 'lizard':
            name = "Lizard %s" % (change.lizard_name)
            if change.action == 'delete':
                url = None
                unique_url = "http://localhost:8000/publicLizard/"
            if change.action == 'new' or change.action == 'update':
                url = "http://localhost:8000/publicLizard/#%s" % \
                    (change.lizard_id)
                unique_url = url

        if change.table == 'hobby':
            name = "Hobby %s" % (change.hobby_name)
            if change.action == 'delete':
                url = None
                unique_url = "http://localhost:8000/publicLizard/"
            if change.action == 'new' or change.action == 'update':
                url = "http://localhost:8000/publicLizard/%s/publicHobby/#%s" \
                    % (change.lizard_id, change.hobby_id)
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
