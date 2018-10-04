from flask import (Flask,
                   render_template,
                   g,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   flash,
                   make_response)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from database_setup import Base, Category, Item, User
from functools import wraps
from flask_httpauth import HTTPBasicAuth
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import requests
import json
import random
import string

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine(
    'sqlite:///itemcatalog.db',
    connect_args={
        'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

auth = HTTPBasicAuth
# Read the client id from client_secrets.json file
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']
APPLICATION_NAME = "Bharatiya Krati"


# Login Page
@app.route('/login')
def start():
    if 'username' not in login_session:
        state = ''.join(
            random.choice(
                string.ascii_uppercase +
                string.digits) for x in xrange(32))
        login_session['state'] = state
        # return "The current session state is %s" % login_session['state']
        return render_template('login.html', STATE=state)
    else:
        return "<h3> You are already logged in .. </br> \
        <a href='/catalog'}>Go back to homepage</a></h3>"

# Function to remove the present user data from the application


@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        del login_session['picture']
        del login_session['provider']

        flash('You are logged out Successfully')
        return redirect(url_for('showCategory'))

    else:
        flash('You are not logged in')
        return redirect(url_for('start'))


# Using Google OPENID Connect for registration/login of the user
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Authorization Code Retreival
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match the given user ID"), 401)
        response.header['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists or if it doesn't make a new one
    print 'User email is' + str(login_session['email'])
    try:
        user = session.query(User).filter_by(
            email=str(login_session['email'])).first()
        user_id = user.id
    except BaseException:
        user_id = None
    if user_id:
        print 'Existing user#' + str(user_id) + 'matches this email'
    else:
        newUser = User(
            name=login_session['username'],
            email=login_session['email'],
            picture=login_session['picture'])
        session.add(newUser)
        session.commit()
        print 'New user_id#' + str(user_id) + 'created'

    user = session.query(User).filter_by(email=login_session['email']).first()
    user_id = user.id

    login_session['user_id'] = user_id
    print 'Login session is  tied to :id#' + str(login_session['user_id'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# For removing the token from Google server
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']    # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to \
        revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# To check whether the user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("Please Login to access this service")
            return redirect('/login')
    return decorated_function


# API Endpoint for displaying all the categories
@app.route('/catalog.json')
def catalogJSON():
    category = session.query(Category).all()
    return jsonify(category=[c.serialize for c in category])


# API Endpoint for displaying all the items in a category
@app.route('/catalog/<int:category_id>/item.json')
def categoryItemJSON(category_id):
    item = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(item=[i.serialize for i in item])


# API Endpoint for displaying all the information regarding a particular item
@app.route('/catalog/<int:category_id>/item/<int:item_id>/info.json')
def ItemJSON(category_id, item_id):
    item = session.query(Item).filter_by(
        id=item_id, category_id=category_id).one_or_none()
    return jsonify(item=item.serialize)


@app.route('/')
@app.route('/catalog/')
def showCategory():
    cat = session.query(Category).all()
    return render_template('catalog.html', cat=cat)


# Create a new Category
@app.route('/catalog/new/', methods=['GET', 'POST'])
@login_required
def newCategory():
    if request.method == 'POST':
        if not (
                request.form['name']):
            flash('Please enter the name of the category')
            return redirect(url_for('newCategory'))
        newcat = Category(
            name=request.form['name'],
            description=request.form['description'],
            picture=request.form['picture'],
            user_id=login_session['user_id'])
        session.add(newcat)
        flash('New Category %s Added' % newcat.name)
        session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('newCategory.html')


# Edit a Category
@app.route('/catalog/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    """Edit a category.

    arguments:
    category_id -- The id of the category to be edited
    """
    cate
    editedCategory = session.query(Category).filter_by(
        id=category_id).one_or_none()
    if editedCategory.user_id != login_session['user_id']:
        return "<script> window.alert('You are not authorized\
        to edit this category.');window.location.href='/';</script>"

    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash(
                'Updated Category Name Successfully to %s' %
                editedCategory.name)
            session.commit()

        if request.form['description']:
            editedCategory.description = request.form['description']
            flash('Updated Category Description')
            session.commit()
        if request.form['picture']:
            editedCategory.picture = request.form['picture']
            flash('Updated Picture Description')
            session.commit()

        return redirect(url_for('showCategory'))
    else:
        return render_template('editCategory.html', c=editedCategory)


# Delete a Category
@app.route('/catalog/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    catdel = session.query(
        Category).filter_by(id=category_id).one_or_none()
    if catdel.user_id != login_session['user_id']:
        return "<script> window.alert('You are not authorized to\
        delete this category. Create your own category to delete.'\
        );window.location.href='/';</script>"
    if request.method == 'POST':
        session.delete(catdel)
        flash('%s Successfully Deleted' % catdel.name)
        session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('deleteCategory.html', cat=catdel)


# Display all the items in a category
@app.route('/catalog/<int:category_id>/items/')
def showItems(category_id):
    cat = session.query(Category).filter_by(id=category_id).one_or_none()
    ite = session.query(Item).filter_by(category_id=category_id).all()
    return render_template('items.html', cat=cat, ite=ite)


# Adding a new item to the Category
@app.route('/catalog/<int:category_id>/new/', methods=['POST', 'GET'])
@login_required
def newItem(category_id):
    cat = session.query(Category).filter_by(id=category_id).one_or_none()
    if login_session['user_id'] != cat.user_id:
        return "<script> window.alert('You are not authorized\
        to add an item to this category since you are not owner\
        of this category.');window.location.href='/';</script>"
    if request.method == 'POST':
        if not (
                request.form['name']):
            flash('Please enter the name of the item')
            return redirect(url_for('newItem', category_id=category_id))
        ni = Item(
            name=request.form['name'],
            description=request.form['description'],
            picture=request.form['picture'],
            category_id=category_id)
        session.add(ni)
        session.commit()
        flash('New form of %s added' % (cat.name))
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('newItem.html', c=cat)


# Edit Item information
@app.route(
    '/catalog/<int:category_id>/items/<int:item_id>/edit',
    methods=[
        'POST',
        'GET'])
@login_required
def editItem(category_id, item_id):
    cat = session.query(Category).filter_by(id=category_id).one_or_none()
    editedItem = session.query(Item).filter_by(id=item_id).one_or_none()
    if login_session['user_id'] != cat.user_id:
        return "<script> window.alert('You are not authorized  \
        to edit this item.');window.location.href='/';</script>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['picture']:
            editedItem.picture = request.form['picture']
        if not (
                request.form['name'] or request.form['description'] or
                request.form['picture']):
            flash('No value changed')
            return redirect(
                url_for(
                    'editItem',
                    category_id=category_id,
                    item_id=item_id))
        session.add(editedItem)
        session.commit()
        flash('Updated Subcategory %s' % editedItem.name)
        return redirect(url_for('showItems', category_id=cat.id))
    else:
        return render_template('editItem.html', c=cat, ei=editedItem)


# Delete Item
@app.route(
    '/catalog/<int:category_id>/items/<int:item_id>/delete',
    methods=[
        'GET',
        'POST'])
@login_required
def deleteItem(category_id, item_id):
    cat = session.query(Category).filter_by(id=category_id).one_or_none()
    deleteItem = session.query(Item).filter_by(id=item_id).one_or_none()
    if login_session['user_id'] != cat.user_id:
        return "<script> window.alert('You are not authorized \
        to delete this item.');window.location.href='/';</script>"
    if request.method == 'POST':
        flash('Deleted %s' % deleteItem.name)
        session.delete(deleteItem)
        session.commit()
        return redirect(url_for('showItems', category_id=cat.id))
    else:
        return render_template('deleteItem.html', c=cat, d=deleteItem)


# Show the item info
@app.route('/catalog/<int:category_id>/items/<int:item_id>')
def itemDescription(category_id, item_id):
    cat = session.query(Category).filter_by(id=category_id).one_or_none()
    ite = session.query(Item).filter_by(
        id=item_id, category_id=category_id).one_or_none()
    return render_template('item.html', cat=cat, ite=ite)


if __name__ == '__main__':
    app.secret_key = 'super_bharat'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
