import logging
from msilib.schema import Directory
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import sys
sys.path.append('../../')
#import config
#from config import Config

db = SQLAlchemy()
file_path = 'website/mcfresh.db'
def create_app():
    directory = '%s'%os.getcwd
    #UPLOAD_FOLDER = directory+'\static\images'
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mcfresh.db'
    #app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config["SESSION_TYPE"] = "filesystem"
    db.init_app(app)

    from .views import views
    from .fresh import fresh

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(fresh, url_prefix='/')

    from .models import User, Note
    print(logging.info)
    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'fresh.main'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not os.path.exists(file_path):
        db.create_all(app=app)
        print('Created Database!')
