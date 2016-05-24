from pkg import app, db, session
from databaseSetup import User, Lizard, Hobby
from databaseSetup import LizardImage, HobbyImage, ChangeLog

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
import os

store = HttpExposedFileSystemStore(
    path=os.path.join(os.path.dirname(__file__), "images"))

app.wsgi_app = store.wsgi_middleware(app.wsgi_app)


# Helper Functions
def requires_login(function):
    """requires_login: a decorator for routes that are designed to be accessible
    only when logged in"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "username" not in login_session:
            # Flash error message if trying to access showHobby or other
            # restricted route
            if function.__name__ != "showLizard":
                flash("You need to be signed in to contribute to the database")
            return redirect(url_for("showPublicLizard"))
        return function(*args, **kwargs)
    return decorated_function


def requires_creator(function):
    """requires_creator: a decorator for routes that are designed to be
    accessible only when logged in as the same user as the creator of the
    lizard being edited/deleted"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "username" not in login_session:
            flash("You need to be signed in to contribute to the database")
            return redirect(url_for("showPublicLizard"))
        lizard = Lizard.query.filter_by(id=kwargs["lizard_id"]).all()
        if not lizard:
            flash("This lizard does not exist or no longer exists")
            return redirect(url_for("showLizard"))
        if lizard[0].user_id != login_session["user_id"]:
            # Flash error message if trying to access addHobby, editHobby or
            # deleteHobby
            if function.__name__ != "showHobby":
                flash("Only the creator of this hobby can edit it")
            return redirect(url_for("showPublicHobby",
                                    lizard_id=kwargs["lizard_id"]))
        return function(*args, **kwargs)
    return decorated_function


def isURLImage(url):
    """isURLImage: Checks if the content-type of the url passed in is an image
    url via a HEAD request, for less overhead

    Args:
        url: url must meet certain qualifications
            - Must have a content-type of image/png, image/jpeg, image/jpg, or
              image/svg+xml
            - Must have content-length of less than 3MB
    Returns:
        url: If url meets qualifications, it will be returned; if url is
             incorrect, null will be returned
        error: If url meets qualifications, null will be returned; if url is
               incorrect, a specific error message will be returned
    Example:
        url = http://www.google.com/logos/doodles/2015/winter-solstice-2015-brazil-5991092264632320-hp2x.jpg"
        (url, error) = IsURLImage(url)
        if error:
            return render_template("error.html", error=error)
        """

    acceptable_image_types = ["image/png", "image/jpeg", "image/jpg",
                              "image/svg+xml"]
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
    """pretty_date: Makes a date difference human-readable

    Args:
        time [default=False]: A python date object
    Returns: The time difference between the time passed in and now, in
             human-readable form"""
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
        return ""

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


def recentActivity():
    """recentActivity: Returns the 10 latest changes (add, delete, update) to
                lizards and hobbies, in descending order"""
    return ChangeLog.query.order_by(db.desc("update_instant")).limit(10).all()


# Public routes, do not require login
@app.route("/")
@app.route("/publicLizard/")
def showPublicLizard():
    """showPublicLizard: Displays lizards, does not require login

    Routes:
        "/"
        "/publicLizard/"""""
    lizards = Lizard.query.order_by(db.asc(Lizard.name)).all()
    total_lizards = len(lizards)
    with store_context(store):
        return render_template("publicLizard.html", lizards=lizards,
                               recent_activity=recentActivity(),
                               pretty_date=pretty_date,
                               total_lizards=total_lizards)


@app.route("/publicLizard/<int:lizard_id>/")
def showPublicHobby(lizard_id):
    """showPublicHobby: Displays hobbies from a particular lizard; does not
                       require login

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    if not lizard:
        flash("This lizard does not exist")
        return redirect(url_for("showPublicLizard"))
    creator = User.query.filter_by(id=lizard.user_id).one()
    hobbies = Hobby.query.\
        filter_by(lizard_id=lizard.id).all()
    with store_context(store):
        return render_template(
            "publicHobby.html", hobbies=hobbies, lizard=lizard,
            creator=creator, login_session=login_session)


# Routes to edit the database, all require login
@app.route("/lizard/")
@requires_login
def showLizard():
    "showLizard: Displays all lizards; requires login"
    lizards = Lizard.query.order_by(db.asc(Lizard.name)).all()
    total_lizards = len(lizards)
    with store_context(store):
        return render_template("lizard.html", lizards=lizards,
                               login_session=login_session,
                               recent_activity=recentActivity(),
                               pretty_date=pretty_date,
                               total_lizards=total_lizards)


@app.route("/lizard/new/", methods=["GET", "POST"])
@requires_login
def newLizard():
    """newLizard: Displays new lizard creation form and posts new lizard
                    to the database; requires login"""
    if request.method == "GET":
        return render_template("newLizard.html", login_session=login_session)
    # First check to see if image URL is valid from HEAD reqauest.
    # If its not return error
    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("newLizard.html",
                               login_session=login_session,
                               error=error)
    # urlopen uses a GET request and does not accept HTTPS urls
    try:
        url_open = urlopen(url)
    except:
        error = "Unable to make a request to this URL: %s" % (url)
        return render_template("newLizard.html",
                               login_session=login_session,
                               error=error)
    # Create Lizard object
    new_lizard = Lizard(
        name=request.form.get("name"),
        user_id=login_session.get("user_id"),
        picture_url=url)

    # Must add picture to lizard object within store_context
    with store_context(store):
        new_lizard.picture.from_file(url_open)  # adding picture here
        session.add(new_lizard)
        session.commit()
        url_open.close()  # make sure to close url connection after commit

    # After commit, retrieve lizard info to add to the ChangeLog
    newest_lizard = Lizard.query.\
        filter_by(user_id=login_session.get("user_id")).\
        order_by(db.desc("creation_instant")).limit(1)[0]

    change_log = ChangeLog(
        user_id=newest_lizard.user_id,
        lizard_name=newest_lizard.name,
        lizard_id=newest_lizard.id,
        update_instant=newest_lizard.creation_instant,
        action="new",
        table="lizard")
    session.add(change_log)
    flash("New Lizard %s Successfully Created" %\
        (newest_lizard.name))
    session.commit()
    return redirect(url_for("showLizard"))


@app.route("/lizard/<int:lizard_id>/edit/", methods=["GET", "POST"])
@requires_creator
def editLizard(lizard_id):
    """editLizard: Displays form to edit a lizard"s name and/or image url
                     and posts that information to the database; requires login

    Arguments are derived from the url"""
    edited_lizard = Lizard.query.filter_by(id=lizard_id).one()
    if request.method == "GET":
        with store_context(store):
            return render_template("editLizard.html",
                                   lizard=edited_lizard,
                                   login_session=login_session)

    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("editLizard.html",
                               login_session=login_session,
                               lizard=edited_lizard,
                               error=error)
    try:
        url_open = urlopen(url)
    except:
        error = "Unable to make a request to this URL: %s" % (url)
        return render_template("editLizard.html",
                               login_session=login_session,
                               lizard=edited_lizard,
                               error=error)

    change_log = ChangeLog(
        user_id=edited_lizard.user_id,
        lizard_name=request.form.get("name"),
        lizard_id=lizard_id,
        update_instant=datetime.datetime.utcnow(),
        action="update",
        table="lizard")

    edited_lizard.name = request.form.get("name")
    edited_lizard.picture_url = url
    # Add all info to session while in store_context
    with store_context(store):
        edited_lizard.picture.from_file(url_open)
        session.add(change_log)
        session.add(edited_lizard)
        flash("Lizard %s Successfully Edited"  % edited_lizard.name)
        session.commit()
        url_open.close()
    return redirect(url_for("showLizard"))


@app.route("/lizard/<int:lizard_id>/delete/", methods=["GET", "POST"])
@requires_creator
def deleteLizard(lizard_id):
    """deleteLizard: Displays form to delete a lizard and posts that
                       information to the database; requires login

    Arguments are derived from the url"""
    lizard_to_delete = Lizard.query.filter_by(id=lizard_id).one()
    if request.method == "GET":
        with store_context(store):
            return render_template(
                "deleteLizard.html", lizard=lizard_to_delete,
                login_session=login_session)

    change_log = ChangeLog(
        user_id=lizard_to_delete.user_id,
        lizard_name=lizard_to_delete.name,
        update_instant=datetime.datetime.utcnow(),
        action="delete",
        table="lizard")

    session.add(change_log)

    Hobby.query.filter_by(lizard_id=lizard_to_delete.id).delete()
    session.delete(lizard_to_delete)
    flash("Lizard %s Successfully Deleted" % lizard_to_delete.name)
    with store_context(store):
        session.commit()
    return redirect(url_for("showLizard"))



@app.route("/lizard/<int:lizard_id>/")
@requires_creator
def showHobby(lizard_id):
    """showHobby: Displays all hobbies of a particular lizard; requires login
                 and that the logged-in user is also the user that created the
                 lizard

    Args:
        lizard_id: : ID of the lizard being edited"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    hobbies = Hobby.query.filter_by(lizard_id=lizard_id).all()
    creator = User.query.filter_by(id=lizard.user_id).one()
    with store_context(store):
        return render_template(
            "hobby.html", hobbies=hobbies, lizard=lizard,
            login_session=login_session, creator=creator,
            user_id=login_session["user_id"])


@app.route("/lizard/<int:lizard_id>/new/", methods=["GET", "POST"])
@requires_creator
def newHobby(lizard_id):
    """newHobby: Displays new hobby creation form and posts new hobby to the
                database; requires login and that the logged-in user is also
                the user that created the lizard

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    if request.method == "GET":
        with store_context(store):
            return render_template("newHobby.html",
                                   lizard=lizard,
                                   login_session=login_session)

    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("newHobby.html",
                               login_session=login_session,
                               lizard=lizard,
                               error=error)
    try:
        url_open = urlopen(url)
    except:
        error = "Unable to make a request to this URL: %s" % (url)
        return render_template("newHobby.html",
                               login_session=login_session,
                               lizard=lizard,
                               error=error)

    new_hobby = Hobby(
        name=request.form.get("name"),
        description=request.form.get("description"),
        lizard_id=lizard_id,
        user_id=lizard.user_id,
        picture_url=url)

    with store_context(store):
        new_hobby.picture.from_file(url_open)
        session.add(new_hobby)
        flash("New Hobby %s Successfully Created" % (new_hobby.name))
        session.commit()
        url_open.close()

    newest_hobby = Hobby.query.\
        filter_by(user_id=lizard.user_id).\
        order_by(db.desc("creation_instant")).limit(1)[0]

    change_log = ChangeLog(
        user_id=lizard.user_id,
        lizard_name=lizard.name,
        lizard_id=lizard_id,
        hobby_name=newest_hobby.name,
        hobby_id=newest_hobby.id,
        update_instant=newest_hobby.creation_instant,
        action="new",
        table="hobby")

    session.add(change_log)
    session.commit()
    return redirect(url_for("showHobby", lizard_id=lizard_id))


@app.route(
    "/lizard/<int:lizard_id>/<int:hobby_id>/edit/",
    methods=["GET", "POST"])
@requires_creator
def editHobby(lizard_id, hobby_id):
    """editHobby: Displays form to edit a particular hobby's name, description,
                 and/or image url and posts that information to the database;
                 requires login and that the logged-in user is also the user
                 that created the lizard

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    edited_hobby = Hobby.query.\
        filter_by(id=hobby_id, lizard_id=lizard_id).one()
    if request.method == "GET":
        with store_context(store):
            return render_template("editHobby.html",
                                   lizard=lizard,
                                   hobby_id=hobby_id,
                                   hobby=edited_hobby,
                                   login_session=login_session)

    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("editHobby.html",
                               login_session=login_session,
                               lizard_id=lizard_id,
                               hobby_id=hobby_id,
                               hobby=edited_hobby,
                               error=error)
    try:
        url_open = urlopen(url)
    except:
        error = "Unable to make a request to this URL: %s" % (url)
        return render_template("editHobby.html",
                               login_session=login_session,
                               lizard_id=lizard_id,
                               hobby_id=hobby_id,
                               hobby=edited_hobby,
                               error=error)

    # The ChangeLog for editing hobbies will have an entry if any change is
    # made to an hobby
    # But the only metadata collected is the new hobby's name, even if the
    # name didn"t change
    change_log = ChangeLog(
        user_id=edited_hobby.user_id,
        lizard_name=lizard.name,
        lizard_id=lizard_id,
        hobby_name=request.form.get("name"),
        hobby_id=hobby_id,
        update_instant=datetime.datetime.utcnow(),
        action="update",
        table="hobby")

    edited_hobby.name = request.form.get("name")
    edited_hobby.description = request.form.get("description")
    edited_hobby.picture_url = url

    with store_context(store):
        edited_hobby.picture.from_file(url_open)
        session.add(change_log)
        flash("Hobby %s Successfully Edited" % (edited_hobby.name))
        session.commit()
        url_open.close()
    return redirect(url_for("showHobby", lizard_id=lizard_id))


@app.route(
    "/lizard/<int:lizard_id>/<int:hobby_id>/delete/",
    methods=["GET", "POST"])
@requires_creator
def deleteHobby(lizard_id, hobby_id):
    """deleteHobby: Displays form to delete an hobby and posts that information
                   to the database; requires login and that the logged-in user
                   is also the user that created the lizard

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    hobby_to_delete = Hobby.query.\
        filter_by(id=hobby_id, lizard_id=lizard_id).one()
    if request.method == "GET":
        with store_context(store):
            return render_template("deleteHobby.html", lizard=lizard,
            hobby=hobby_to_delete, login_session=login_session)

    change_log = ChangeLog(
        user_id=hobby_to_delete.user_id,
        lizard_name=lizard.name,
        lizard_id=lizard_id,
        hobby_name=hobby_to_delete.name,
        update_instant=datetime.datetime.utcnow(),
        action="delete",
        table="hobby")

    session.add(change_log)
    session.delete(hobby_to_delete)
    flash("Hobby %s Successfully Deleted" % (hobby_to_delete.name))
    with store_context(store):
        session.commit()
    return redirect(url_for("showHobby", lizard_id=lizard_id))


@app.route("/error/")
@app.errorhandler(304)
@app.errorhandler(404)
@app.errorhandler(500)
def pageNotFound(error):
    return render_template("pageNotFound.html", error=error), 404
