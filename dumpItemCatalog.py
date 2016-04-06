from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from databaseSetup import User, Category, Item, ChangeLog

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemCatalog.db'
app.config[' SQLALCHEMY_TRACK_MODIFICATIONS'] = 'True'
db = SQLAlchemy(app)
users = User.query.all()
for user in users:
    print "user ID: " + str(user.id)
    print "name: " + user.name
    print "email: " + user.email
    print "picture: " + user.picture
    print "facebook id: %s" % (user.facebook_id)
    print "gplus id: %s" % (user.gplus_id)


print '\n'

categories = Category.query.all()
for category in categories:
    print "ID: " + str(category.id)
    print "name: " + category.name
    print "user ID: " + str(category.user_id)
    print "picture: " + str(category.picture)
    print "IOC: %s" % (category.creation_instant)
print '\n'
items = Item.query.order_by(db.asc(Item.user_id)).all()
for item in items:
    print "ID: " + str(item.id)
    print "name: " + item.name
    print "user ID: " + str(item.user_id)
    print "category_id: " + str(item.category_id)
    print "IOC: " + str(item.creation_instant)
