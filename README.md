# Lizard Catalog App
This is a Lizard Catalog app created as project 3 of [Udacity's Full Stack Web Developer Nanodegree](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).  I created this app to practice CRUD (create, read, update, delete) database operations and to practice incorporating 3rd-party frameworks and modules into my codebase.  It is currently run on localhost, but it could be deployed to the web in the future.

## What exactly is a Lizard Catalog App?
I believe coding something I care about is far better than coding without drive or purpose.  Project 3 calls for students to create a basic catalog app with two data points connected in a parent/child relationship (like in this [sample website](https://docs.google.com/document/d/1jFjlq_f-hJoAZP8dYuo5H3xY62kGyziQmiv9EPIA7tM/pub?embedded=true)).

Instead of creating an app to organize items within categories (generic and boring), I created an app to organize lizards and their hobbies! Is this practical? No, not really.  But it brings me a smile every time I boot it up :).

## Features
* Supports secure user accounts
* Supports Google and Facebook authentication
* Enables image uploads from image urls for an enhanced UI experience
* Logged-in users can add, edit, and delete their lizards and lizards' hobbies from the database
* Every data point added to the database is viewable, but only the user who added the data can edit or delete it
* A recent activity feed is displayed on the home page, showing the latest updates to the database
* Data can be access via JSON and Atom Endpoints

## Setup
1. Secure shell into the [vagrant VM](https://www.vagrantup.com/docs/getting-started/) installed in this github repository.
2. Navigate to the top-level directory and boot up the app with the command `python lizardCatalog.py`. Press ctrl+c to shut down the app.
3. Open an internet browser and enter the url `localhost:8000`.

## Test Data
If you want to populate the lizard database with data automatically, use the [testData.py](https://github.com/snackattas/LizardApp/blob/master/testData.py)  script.  
Here's how to run the script:

1. First follow the setup steps to get the app up and running.
2. Create a user by logging into the web app.  Record the user id of your user.  It will be shown in the flash message.
3. In the top-level directory, run this command `python testData.py [user id]` subbing in "user id" with your user id.

## Technologies used
### Languages used
Python, Javascript, HTML, CSS
### Python third parties used
* [Flask](http://flask.pocoo.org/docs/0.10/)
* [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.1/)
* [SQLAlchemy-ImageAttach](http://sqlalchemy-imageattach.readthedocs.org/en/stable/index.html)
* [Werkzeug's Atom Syndication module](http://werkzeug.pocoo.org/docs/0.11/contrib/atom/)

## Dependencies
All dependencies are part of the vagrant package and require no updates by the person forking the repo.

## JSON Endpoints
### [localhost:8000/lizard/JSON/](localhost:8000/lizard/JSON/)
    Displays all lizards
### localhost:8000/lizard/\[lizard_id\]/hobby/JSON/
    Displays all hobbies of a particular lizard
### localhost:8000/lizard/\[lizard_id\]/hobby/\[hobby_id\]/JSON/
    Displays only one hobby
## Atom Endpoints
### [localhost:8000/lizard.atom/](localhost:8000/lizard.atom/)
    Displays all lizards
### [localhost:8000/hobby.atom/](localhost:8000/hobby.atom/)
    Displays all hobbies
### [localhost:8000/all.atom/](localhost:8000/all.atom/)
    Displays all lizards and hobbies
###[localhost:8000/changes.atom/](localhost:8000/changes.atom/)
    Displays all content of the recent activity feed

## Screenshots
![Lizard Homepage](/../master/pkg/static/Lizard%20Homepage.JPG?raw=true "Lizard Homepage")
![Lizard's Hobby](/../master/pkg/static/Lizard%20Hobby.JPG?raw=true "Lizard's Hobbies")
