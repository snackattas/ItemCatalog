from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itemCatalog.db'
app.config[' SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable = False)
    email = db.Column(db.String(80))
    picture = db.Column(db.LargeBinary)
    facebook_id = db.Column(db.String(80))
    gplus_id = db.Column(db.String(80))

class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)
    picture = db.Column(db.LargeBinary)
    instant_of_creation = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'                : self.name,
           'id'                  : self.id,
       }

class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key = True)
    name =db.Column(db.String(80), nullable = False)
    description = db.Column(db.String(250))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(Category)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)
    picture = db.Column(db.LargeBinary)
    instant_of_creation = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'                : self.name,
           'description'         : self.description,
           'id'                  : self.id,
       }

db.create_all()
