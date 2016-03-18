from sqlalchemy import Column, ForeignKey, Integer, String, LargeBinary, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()
import datetime


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable = False)
    email = Column(String(80))
    picture = Column(LargeBinary)
    facebook_id = Column(String(80))
    gplus_id = Column(String(80))

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    picture = Column(LargeBinary)
    instant_of_creation = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'                : self.name,
           'id'                  : self.id,
       }

class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key = True)
    name =Column(String(80), nullable = False)
    description = Column(String(250))
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    picture = Column(LargeBinary)
    instant_of_creation = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'                : self.name,
           'description'         : self.description,
           'id'                  : self.id,
       }


engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.create_all(engine)
