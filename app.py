from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from products import products
from flask_pymongo import PyMongo
from pymongo import MongoClient
from ConfigParser import SafeConfigParser
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import sys

#config PyMongo Db
parser = SafeConfigParser( )
parser.read('config.ini')
connection = MongoClient(parser.get('mongo_server', 'mongo_url'))

user_collection = connection.myflaskapp.users
app = Flask(__name__)

#initialize PyMongo
mongo = PyMongo(app)
Products = products( )

#Home Page
@app.route( '/')
def index( ):
    return render_template('home.html')

#About US
@app.route( '/about')
def about( ):
    return render_template('about.html')

#Contact US
@app.route( '/contact')
def contact( ):
    return render_template('contact.html')

# All Products
@app.route('/products')
def products( ):
    return render_template('products.html' , products = Products)

#Single Product Page
@app.route('/product/<string:id>/')
def product( id):
    return render_template('product.html' , id = id)

# Form Class with WTForms
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min = 1, max = 50)])
    username = StringField('Username', [validators.Length(min = 4, max = 50)])
    email = StringField('Email', [validators.Length(min = 6, max = 50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',message = 'Passwords do not match')
        ])
    confirm = PasswordField('Confirm Password')

        
#Register form
@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #post into db
        user_collection.insert_one({'name': name, 'email':email, 'username':username,  'password': password})
        sys.stdout.flush()
        connection.close()
        flash("You have successfully registered !!", 'success')
        return redirect(url_for('register'))

    return render_template('register.html', form = form)


#User Log in
@app.route('/login', methods = ['GET', 'POST'])
def login( ):
    if request.method == 'POST' :
        
        #get login form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Find username from db
        result = user_collection.find_one({'username': username})

        #if username with the specified username in the log in is found
        if result > 0:
            password = result['password']
            #compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #successful login
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                #passwords dont match
                error = 'Invalid Login.'
                return render_template('login.html', error = error)
            #close connection
            connection.close()
        else :
            #username not found in db
            error = 'Username not Registered.'
            return render_template('login.html', error = error)

    return render_template('login.html')


#decorator to check if user is logged in already
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised Access. Please log in first', 'danger')
            return redirect(url_for('login'))
    return wrap


#User Log out
@app.route('/logout')
@is_logged_in
def logout( ):
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


#User Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard( ):
    return render_template('dashboard.html')


if __name__ =='__main__':
    app.secret_key = 'secret123'
    app.run(debug= True)
