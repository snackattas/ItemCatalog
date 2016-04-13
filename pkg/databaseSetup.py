from pkg import app, db
from sqlalchemy_imageattach.entity import Image, image_attachment
import datetime


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
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
    picture = image_attachment('CategoryImage')
    picture_url = db.Column(db.String(500))
    creation_instant = db.Column(db.DateTime(timezone=True),
                                 default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name':             self.name,
            'id':               self.id,
            'picture_url':      self.picture_url,
            'creation_instant': self.creation_instant
        }


class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(250))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(Category)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)
    picture = image_attachment('ItemImage')
    picture_url = db.Column(db.String(500))
    creation_instant = db.Column(db.DateTime(timezone=True),
                                 default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name':             self.name,
            'description':      self.description,
            'id':               self.id,
            'picture_url':      self.picture_url,
            'creation_instant': self.creation_instant
        }


# Category table that contains references to image files
class CategoryImage(db.Model, Image):
    __tablename__ = 'categoryimage'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),
                            primary_key=True)
    category = db.relationship(Category)


# Item table that contains references to image files
class ItemImage(db.Model, Image):
    __tablename__ = 'itemimage'
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    item = db.relationship(Item)


# ChangeLog table that contains instants when a category or item is added,
# updated, or deleted
class ChangeLog(db.Model):
    __tablename__ = 'changelog'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)
    category_name = db.Column(db.String(80))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(Category)
    item_name = db.Column(db.String(80))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    item = db.relationship(Item)
    update_instant = db.Column(db.DateTime(timezone=True),
                               default=datetime.datetime.utcnow)
    # Possible actions are "new", "update", or "delete"
    action = db.Column(db.String(6))
    # Possible tables are "category" or "item"
    table = db.Column(db.String(9))

# Command to create all these tables
db.create_all()
