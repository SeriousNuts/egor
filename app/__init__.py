from datetime import timedelta

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem' # храним файлы на стороне сервера
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5) # храним файлы в течение 5 часов
Session(app)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = '/login'
from app import views, models, makefile
