from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from setup_db import Base, Category, Game, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import os

app = Flask(__name__)
app.secret_key = 'AlphaBetaSuperKey'

CLIENT_ID = json.loads(
    open('/vagrant/GameFan/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Game Fan Club App"

engine = create_engine('postgresql://tester:letmein@localhost/gamefandb')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

WARNING = "<script>function myFunction() {alert('You are not authorized to modify this content. Please login or get permission from administrator.');}</script><body onload='myFunction()'>"

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/')
@app.route('/categories/')
@app.route('/GameFan')
def showCategory():
    categories = session.query(Category).all();
    if 'username' not in login_session:
        return render_template('publicCategory.html', categories=categories)
    return render_template('main.html', categories=categories, user_id=login_session['user_id'], user_level=login_session['level'])

@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if (request.method == 'GET'):
        return render_template('newCategory.html')
    else:
        category = Category(name=request.form['name'], description=request.form['description'], 
            img_url=request.form['img_url'], creator_id=login_session['user_id'])
        session.add(category)
        session.commit()
        flash('New category is added')
        return redirect(url_for('showCategory'))


@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')    
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.creator_id and not isAdmin():
        return WARNING
    if (request.method == 'GET'):
        return render_template('editCategory.html', category=category)
    else:
        category.name = request.form['name'].lower()
        category.description = request.form['description']
        category.img_url = request.form['img_url']
        session.add(category)
        session.commit()
        flash('Cotegory updated successfully')
        return redirect(url_for('showCategory'))


@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')           
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.creator_id and not isAdmin():
        return WARNING
    if (request.method == 'GET'):
        return render_template('deleteCategory.html', category=category)
    else:
        session.delete(category)
        session.commit()
        flash('Category deleted successfully')
        return redirect(url_for('showCategory'))


@app.route('/category/<string:category_name>')
def showGame(category_name):
    games = session.query(Game).filter(Game.genre.contains(category_name)).all()
    if 'username' not in login_session:
        return render_template('publicGame.html', games=games, category_name=category_name)
    return render_template('showGame.html', games=games, category_name=category_name, user_id=login_session['user_id'], user_level=login_session['level'])


@app.route('/category/<string:category_name>/<int:game_id>/edit', methods=['GET', 'POST'])
def editGame(game_id, category_name):
    if 'username' not in login_session:
        return redirect('/login')
    game = session.query(Game).filter_by(id=game_id).one()
    if login_session['user_id'] != game.creator_id and not isAdmin():
        return WARNING
    if (request.method == 'GET'):
        return render_template('editGame.html', game=game, category_name=category_name)
    else:
        game.name = request.form['name']
        game.description = request.form['description']
        game.year = request.form['year']
        game.image_url = request.form['img_url']
        game.trailer_url = request.form['trailer_url']
        game.genre = '-'.join(request.form.getlist('genre'))
        game.developer = request.form['developer']
        game.rate = request.form['rate']
        session.add(game)
        session.commit()
        flash('Game info updated succesfully')
        return redirect(url_for('showGame', category_name=category_name))


@app.route('/category/<string:category_name>/newGame', methods=['GET', 'POST'])
def newGame(category_name):
    if 'username' not in login_session:
        return redirect('/login')    
    if (request.method == 'GET'):
        categories = session.query(Category).all()
        return render_template('newGame.html', category_name=category_name, categories=categories)
    else:
        game = Game(name=request.form['name'], description=request.form['description'],year=request.form['year'],
            image_url=request.form['img_url'], trailer_url=request.form['trailer_url'], genre='-'.join(request.form.getlist('genre')),
            developer=request.form['developer'], rate=request.form['rate'], creator_id=login_session['user_id'])
        session.add(game)
        session.commit()
        flash('New Game added succesfully')
        return redirect(url_for('showGame', category_name=category_name))        

@app.route('/category/<string:category_name>/<int:game_id>/deleteGame', methods=['GET', 'POST'])
def deleteGame(game_id, category_name):
    if 'username' not in login_session:
        return redirect('/login')   
    game = session.query(Game).filter_by(id=game_id).one()
    if login_session['user_id'] != game.creator_id and not isAdmin():
        return WARNING    
    if (request.method == 'GET'):
        return render_template('deleteGame.html', game=game, category_name=category_name)
    else:
        session.delete(game)
        session.commit()
        flash('Game successfully deleted')
        return redirect(url_for('showGame', category_name=category_name))


@app.route('/GameFan/game.json', methods=['GET'])
def GameJSON():
    games = session.query(Game).all()
    return jsonify(GameItem=[game.serialize for game in games])


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
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

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(email=login_session['email'])
    if not user_id:
        user_id = createUser(login_session=login_session)

    login_session['user_id'] = user_id
    user = getUserInfo(user_id);
    login_session['level'] = user.level

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] != '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['level']
        flash('Successfully logged out')
        return redirect(url_for('showCategory'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/setLevel', methods=['GET', 'POST'])
def setUserLevel():
    if 'username' not in login_session:
        return redirect('/login')
    if (not isAdmin()):
        return WARNING    
    if (request.method == 'GET'):
        return render_template('setUserLevel.html')
    else:
        user = getUserInfoFromEmail(request.form['email'])
        if not user:
            flash('Level assignment failed, User does not exist')
        else:
            user.level = request.form['level']
            session.add(user)
            session.commit()
            flash('User Level successfully updated')
        return redirect(url_for('showCategory'))

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfoFromEmail(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None

def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None        

def isAdmin():
    level = login_session['level']
    return (level >= 5)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    #app.debug = True
    app.run('0.0.0.0', port) 
