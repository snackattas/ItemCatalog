from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc, union, null, literal_column, ForeignKey
from sqlalchemy.orm import sessionmaker
from databaseSetup import Base, User, Category, Item, CategoryImage, ItemImage
import random
import string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests
from contextlib import contextmanager
from flask_moment import Moment
import sqlalchemy.exc
from sqlalchemy_imageattach.entity import Image, image_attachment
from urllib2 import urlopen


app = Flask(__name__)
moment = Moment(app)
APPLICATION_NAME = "Item Catalog Application"
# Connect to Database and create database session
engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

from sqlalchemy_imageattach.stores.fs import HttpExposedFileSystemStore
store = HttpExposedFileSystemStore(
    path='/vagrant/images',
    prefix='/static/images/'
)
app.wsgi_app = store.wsgi_middleware(app.wsgi_app)


from sqlalchemy_imageattach.context import store_context
def set_picture(pic, user_id):
    try:
        user = session.query(User).get(int(user_id))
        with store_context(store):
            #user.picture.from_file(request.files['picture'])
            print pic
            user.picture = pic
            session.add(user)
    except Exception:
        session.rollback()
        raise
    session.commit()

import wand.image as image
def test_add(user_id):
    with store_context(store):
        category = session.query(Category).get(int(user_id))
        img = '/vagrant/static/dog.jpg'
        #img = 'http://g-ecx.images-amazon.com/images/G/01/img15/pet-products/small-tiles/23695_pets_vertical_store_dogs_small_tile_8._CB312176604_.jpg'

        with open(img, 'rb') as f:
            print f
            print dir(f)
            print type(f)
            category.picture.from_file(f)
            session.add(category)
            session.commit()

def addz(user_id):
    with store_context(store):
        category = session.query(Category).get(int(user_id))
        img = 'C:/Users/Zach/Desktop.jpg'
        #img = 'http://g-ecx.images-amazon.com/images/G/01/img15/pet-products/small-tiles/23695_pets_vertical_store_dogs_small_tile_8._CB312176604_.jpg'

        with open(img, 'rb') as f:
            print f
            print dir(f)
            category.picture.from_file(f)

            session.add(category)
            session.commit()

def recover():
    Categories = session.query(Category).all()
    for category in Categories:
        print "user ID: " + str(category.id)
        print "name: " + category.name
        print dir(category.picture)
        print category.picture
    imagey = session.query(CategoryImage).all()
    print len(imagey)
    for im in imagey:
        print dir(im)
        print im.size
        print im.object_id
        print im.object_type
        print im.original
        print im.created_at
        print im.metadata
def addUser():
    with store_context(store):
        picture_url='http://g-ecx.images-amazon.com/images/G/01/img15/pet-products/small-tiles/23695_pets_vertical_store_dogs_small_tile_8._CB312176604_.jpg'
        User1 = User(name='Zach Attas Google',
                     email='zach.attas@gmail.com',
                     gplus_id='116711155115807702320')
        session.add(User1)
        session.commit()

def set_picture_url(user_id):
    try:
        category = session.query(Category).get(int(user_id))
        picture_url='http://g-ecx.images-amazon.com/images/G/01/img15/pet-products/small-tiles/23695_pets_vertical_store_dogs_small_tile_8._CB312176604_.jpg'
        with store_context(store):
            category.picture.from_file(urlopen(picture_url))
            session.add(category)
            session.commit()
    except:
        raise
def addcat():
    newcat = Category(
    name="newcat",
    user_id = 1)
    session.add(newcat)
    session.commit()
        # id = Column(Integer, primary_key=True)
        # name = Column(String(250), nullable=False)
        # user_id = Column(Integer, ForeignKey('user.id'))
        # user = relationship(User)
        # picture = image_attachment('CategoryImages')
        # #picture_url = Column(LargeBinary)
        # instant_of_creation = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
def addcatpick():
    category = session.query(Category).get(1)
    picture_url='http://g-ecx.images-amazon.com/images/G/01/img15/pet-products/small-tiles/23695_pets_vertical_store_dogs_small_tile_8._CB312176604_.jpg'
    with store_context(store):
        category.picture.from_file(urlopen(picture_url))
        session.add(category)
        session.commit()

UPLOAD_FOLDER = '/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config
