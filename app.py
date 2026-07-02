from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
import os
from dotenv import load_dotenv
from logger import setup_logger

load_dotenv()

logger = setup_logger('app')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///surveys.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    from flask import flash, redirect, url_for
    flash('Пожалуйста, войдите для доступа', 'warning')
    return redirect(url_for('login'))

from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info('✅ База данных инициализирована')
    logger.info(f'🚀 Сервер запущен на http://127.0.0.1:5000')
    app.run(debug=os.getenv('FLASK_ENV') == 'development')