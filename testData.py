# This module creates 12 lizards, each with 4 hobbies

from pkg import app, db, session
from pkg.databaseSetup import User, Category, Item
from pkg.main import isURLImage

from sqlalchemy_imageattach.context import store_context
from sqlalchemy_imageattach.stores.fs import HttpExposedFileSystemStore
from urllib2 import urlopen

import sys
import json
import os
# First check if user passed in a valid integer
try:
    user_id = int(sys.argv[1])
except:
    raise ValueError

# Next check that the user_id actually exists
try:
    user = User.query.filter_by(id = user_id).one()
except:
    raise ValueError


store = HttpExposedFileSystemStore(
    path=os.path.join(os.path.dirname(__file__), "pkg/images"))

app.wsgi_app = store.wsgi_middleware(app.wsgi_app)

with open("testData.JSON") as data_file:
    lizards = json.load(data_file)
    for lizard in lizards["lizards"]:
        category = Category(
            name=lizard["name"],
            user_id=user_id,
            picture_url=lizard["picture_url"])
        (url, error) = isURLImage(lizard["picture_url"])
        if not error:
            url_open = urlopen(url)
            with store_context(store):
                category.picture.from_file(url_open)
                session.add(category)
                session.commit()
                url_open.close()

            new_category = Category.query.filter_by(
                user_id=user_id, name=lizard["name"]).order_by(db.desc("creation_instant")).limit(1).all()
            new_category_id = new_category[0].id

            for hobby in lizard["hobbies"]:
                a_hobby = Item(
                    name=hobby["name"],
                    description=hobby["description"],
                    picture_url=hobby["picture_url"],
                    category_id=new_category_id,
                    user_id=user_id)
                (url, error) = isURLImage(hobby["picture_url"])
                if not error:
                    url_open = urlopen(url)
                    with store_context(store):
                        a_hobby.picture.from_file(url_open)
                        session.add(a_hobby)
                        session.commit()
                        url_open.close()
