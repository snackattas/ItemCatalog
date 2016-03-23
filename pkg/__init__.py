import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug('init.py')


from flask import Flask, render_template, request, redirect, url_for, flash, make_response, Blueprint
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
app = Flask(__name__)
from pkg.databaseSetup import User, Category, Item



# APPLICATION_NAME = "Item Catalog Application"
# engine = create_engine('sqlite:///itemCatalog.db')
# Base = declarative_base()
# Base.metadata.bind = engine
# DBSession = sessionmaker(bind=engine)

# category = Blueprint('ItemCatalog', __name__, url_prefix='/category')


class SessionCreator:
    APPLICATION_NAME = "Item Catalog Application"
    engine = create_engine('sqlite:///itemCatalog.db')
    Base = declarative_base()
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    @contextmanager
    def get_session(self, DBSession=DBSession):
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


import pkg.CRUD
import pkg.APIEndpoints
import pkg.oauth
# app.register_blueprint(category)
#
# __all__ = ['app', 'render_template', 'request', 'redirect', 'url_for', 'flash', 'make_response', 'login_session', 'get_session', 'category']
