from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from products import products
from flask_pymongo import PyMongo
import pymongo
import sys
from pymongo import MongoClient
from ConfigParser import SafeConfigParser
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

#config PyMongo Db
parser = SafeConfigParser( )
parser.read('config.ini')
connection = MongoClient(parser.get('mongo_server', 'mongo_url'))

user_collection = connection.myflaskapp.users
app = Flask(__name__)

#initialize PyMongo
mongo = PyMongo(app)
Products = products( )

@app.route( '/')
def index( ):
    return render_template('home.html')

@app.route( '/about')
def about( ):
    return render_template('about.html')

@app.route( '/contact')
def contact( ):
    return render_template('contact.html')

@app.route('/products')
def products( ):
    return render_template('products.html' , products = Products)

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

        
#route for register form
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


#route for User Log in
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
                app.logger.info('PASSWORD MATCHED')
            else:
                app.logger.info('PASSWORD NOT MATCHED')
        else :
            app.logger.info('NO USER')
    return render_template('login.html')





if __name__ =='__main__':
    app.secret_key = 'secret123'
    app.run(debug= True)
