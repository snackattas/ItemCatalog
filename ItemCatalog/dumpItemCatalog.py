from flask import Flask
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from databaseSetup import Base, User, Category, Item

app = Flask(__name__)
APPLICATION_NAME = "Item Catalog Application"
# Connect to Database and create database session
engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

users = session.query(User).all()
for user in users:
    print "user ID: " + str(user.id)
    print "name: " + user.name
    print "email: " + user.email
    print "picture: " + user.picture
    print "facebook id: %s" % (user.facebook_id)
    print "gplus id: %s" % (user.gplus_id)


print '\n'

categories = session.query(Category).all()
for category in categories:
    print "ID: " + str(category.id)
    print "name: " + category.name
    print "user ID: " + str(category.user_id)
    print "picture: " + str(category.picture)
    print "IOC: %s" % (category.instant_of_creation)
print '\n'
items = session.query(Item).order_by(asc(Item.user_id)).all()
for item in items:
    print "ID: " + str(item.id)
    print "name: " + item.name
    print "user ID: " + str(item.user_id)
    print "category_id: " + str(item.category_id)
    print "IOC: " + str(item.instant_of_creation)
