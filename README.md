# Lizard Database
This is a Lizard database web application created as project 3 of [Udacity's Full Stack Web Developer Nanodegree](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).  It is meant to organize one's lizards and their various hobbies.  It is currently run on localhost, but it could be deployed to the web in the future.

## Features
* Supports user accounts so that one user does not tamper with another user's data.
* Supports Google and Facebook authentication.
* Grabs images from image urls and displays them to users for an enhanced UI experience.
* Logged-in users can add, edit, and delete their lizards and lizards' hobbies from the database.
* Every data point added to the database is viewable, but only the user who added the data can edit or delete it.
* A recent activity feed is displayed on the home page, showing the latest updates to the database.
* Data can be access via JSON and Atom Endpoints.

## Setup
1. Secure shell into the [vagrant VM](https://www.vagrantup.com/docs/getting-started/) installed in this github repository.
2. Navigate to the top-level directory and boot up the app with the command `python ItemCatalog.py`. Press ctrl+c to shut down the app.
3. Open an internet browser and enter the url `localhost:8000`.

## Endpoints
### JSON
#### [localhost:8000/category/JSON/](localhost:8000/category/JSON/)
Displays all lizards with this metadata:
* creation_instant
* id
* name
* picture_url
#### localhost:8000/category/<category_id>/item/JSON/
Displays all hobbies of a particular lizard with this metadata
* creation_instant
* description
* id
* name
* picture_url
#### localhost:8000/category/<category_id>/item/<item_id>/JSON/
Displays only one hobby, with same metadata as above
### Atom
#### [localhost:8000/category.atom/](localhost:8000/category.atom/)
Displays all lizards
#### [localhost:8000/item.atom/](localhost:8000/item.atom/)
Displays all hobbies
#### [localhost:8000/all.atom/](localhost:8000/all.atom/)
Displays all lizards and hobbies
####[localhost:8000/changes.atom/](localhost:8000/changes.atom/)
Displays all content of the recent activity feed

## Test Data
If you want to populate the lizard database with data automatically, use the [testData.py](https://github.com/snackattas/ItemCatalog/blob/master/testData.py)  script.  
Here's how to run the script:
1. First follow the setup steps to get the app up and running.
2. Create a user by logging into the web app.  Record the user id of your user.  It will be shown in the flash message.
3. In the top-level directory, run this command `python testData.py <user id>` subbing in "<user id>" with your user id.

## Technologies used
* Languages: Python, Javascript, HTML, CSS
* Python third parties used: [Flask](http://flask.pocoo.org/docs/0.10/), [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.1/), [SQLAlchemy-ImageAttach](http://sqlalchemy-imageattach.readthedocs.org/en/stable/index.html), [Werkzeug's Atom Syndication module](http://werkzeug.pocoo.org/docs/0.11/contrib/atom/)

## Dependencies
All dependencies are part of the vagrant package and require no updates by the person forking the repo.
