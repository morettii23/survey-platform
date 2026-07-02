from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models import db, User
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///surveys.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === ВАЖНО: СОЗДАЁМ АДМИНА ===
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(email='tuxigoww@bk.ru').first()
    if not admin:
        admin = User(
            username='admin',
            email='tuxigoww@bk.ru',
            password=generate_password_hash('Admin1234'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('✅ Админ создан')
    else:
        admin.role = 'admin'
        admin.password = generate_password_hash('Admin1234')
        db.session.commit()
        print('✅ Админ обновлён')

from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)