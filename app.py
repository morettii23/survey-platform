from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
import os
import sys
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key-12345')
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

from routes import *

with app.app_context():
    try:
        db.create_all()
        print('✅ База данных готова')

        from werkzeug.security import generate_password_hash
        user = User.query.filter_by(email='tuxigoww@bk.ru').first()
        if user:
            # Если пользователь есть — обновляем пароль и делаем админом
            user.password = generate_password_hash('Admin1234')
            user.role = 'admin'
            db.session.commit()
            print(f'✅ Пользователь {user.email} обновлён: пароль Admin1234, роль admin')
        else:
            # Если нет — создаём
            admin = User(
                username='admin',
                email='tuxigoww@bk.ru',
                password=generate_password_hash('Admin1234'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('✅ Админ создан: tuxigoww@bk.ru / Admin1234')

    except Exception as e:
        print(f'⚠️ Ошибка при инициализации БД: {e}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)