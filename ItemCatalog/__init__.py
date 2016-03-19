from flask import Flask
app = Flask(__name__)

from ItemCatalog import CRUD, oauth, APIEndpoints
# import ItemCatalog.oauth
# import ItemCatalog.APIEndpoints
from databaseSetup import Base, User, Category, Item

from flask import render_template, request, redirect, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

APPLICATION_NAME = "Item Catalog Application"
engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = DBSession()
    try:
        yield session
    except:
        session.rollback()
        redirect(url_for('pageNotFound', error=404))
    try:
        session.commit()
    except:
        redirect(url_for('pageNotFound', error=404))
__all__ = ['Base', 'User', 'Category', 'Item', 'render_template', 'request', 'redirect', 'url_for', 'flash', 'make_response', 'login_session', 'create_engine', 'sessionmaker', 'contextmanager', 'APPLICATION_NAME', 'engine', 'DBSession', 'get_session', 'oauth', 'CRUD', 'APIEndpoints']
