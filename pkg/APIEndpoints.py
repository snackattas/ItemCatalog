import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug('APIEndpts.py')


from pkg import app
from pkg import contextmanager
from pkg import SessionCreator
Session = SessionCreator()
get_session = Session.get_session
from flask import jsonify
from databaseSetup import Item, Category
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, Blueprint
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databaseSetup import User, Category, Item, Base
from contextlib import contextmanager
# JSON APIs to view Restaurant Information
###Does it matter what I call the thin in the return statement?
# engine = create_engine('sqlite:///itemCatalog.db')
# Base.metadata.bind = engine
#
# DBSession = sessionmaker(bind=engine)
# session = DBSession()

# @contextmanager
# def get_session():
#     session = DBSession()
#     try:
#         yield session
#     except:
#         session.rollback()
#         redirect(url_for('pageNotFound', error=404))
#     try:
#         session.commit()
#     except:
#         redirect(url_for('pageNotFound', error=404))

@app.route('/<int:category_id>/item/JSON/')
def categoryItemJSON(category_id):
    with get_session() as session:
        items = session.query(Item).filter_by(
        category_id=category_id).all()
        return jsonify(items=[item.serialize for item in items])


@app.route('/<int:category_id>/item/<int:item_id>/JSON/')
def itemJSON(category_id, item_id):
    with get_session() as session:
        item = session.query(Item).filter_by(id=item_id).one()
        return jsonify(item=item.serialize)


@app.route('/JSON/')
def categoryJSON():
    with get_session() as session:
        categories = session.query(Category).all()
        return jsonify(categories=[category.serialize for category in categories])
