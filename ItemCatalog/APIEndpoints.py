from ItemCatalog import *
from flask import jsonify

# JSON APIs to view Restaurant Information
###Does it matter what I call the thin in the return statement?
@app.route('/category/<int:category_id>/item/JSON/')
def categoryItemJSON(category_id):
    with get_session() as session:
        items = session.query(Item).filter_by(
        category_id=category_id).all()
        return jsonify(items=[item.serialize for item in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON/')
def itemJSON(category_id, item_id):
    with get_session() as session:
        item = session.query(Item).filter_by(id=item_id).one()
        return jsonify(item=item.serialize)


@app.route('/category/JSON/')
def categoryJSON():
    with get_session() as session:
        categories = session.query(Category).all()
        return jsonify(categories=[category.serialize for category in categories])
