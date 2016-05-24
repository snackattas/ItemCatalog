# This module creates 12 lizards, each with 4 hobbies

from pkg import app, db, session
from pkg.databaseSetup import User, Lizard, Hobby
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
    raise ValueError("User must pass in a valid integer")

# Next check that the user_id actually exists
try:
    user = User.query.filter_by(id = user_id).one()
except:
    raise ValueError("User must pass in a valid user id")


store = HttpExposedFileSystemStore(
    path=os.path.join(os.path.dirname(__file__), "pkg/images"))

app.wsgi_app = store.wsgi_middleware(app.wsgi_app)

with open("testData.JSON") as data_file:
    lizards = json.load(data_file)
    for next_lizard in lizards["lizards"]:
        lizard = Lizard(
            name=next_lizard["name"],
            user_id=user_id,
            picture_url=next_lizard["picture_url"])
        (url, error) = isURLImage(next_lizard["picture_url"])
        if not error:
            url_open = urlopen(url)
            with store_context(store):
                lizard.picture.from_file(url_open)
                session.add(lizard)
                session.commit()
                url_open.close()

            new_lizard = Lizard.query.filter_by(
                user_id=user_id, name=next_lizard["name"]).order_by(db.desc("creation_instant")).limit(1).all()
            new_lizard_id = new_lizard[0].id

            for next_hobby in next_lizard["hobbies"]:
                new_hobby = Hobby(
                    name=next_hobby["name"],
                    description=next_hobby["description"],
                    picture_url=next_hobby["picture_url"],
                    lizard_id=new_lizard_id,
                    user_id=user_id)
                (url, error) = isURLImage(next_hobby["picture_url"])
                if not error:
                    url_open = urlopen(url)
                    with store_context(store):
                        new_hobby.picture.from_file(url_open)
                        session.add(new_hobby)
                        session.commit()
                        url_open.close()
