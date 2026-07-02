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

# Импорт маршрутов
from routes import *

# Регистрация админ-блюпринта
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# Создание БД и админа
with app.app_context():
    try:
        db.create_all()
        print('✅ База данных готова')

        admin = User.query.filter_by(email='tuxigoww@bk.ru').first()
        if admin:
            admin.password = generate_password_hash('Admin1234')
            admin.role = 'admin'
            db.session.commit()
            print(f'✅ Админ обновлён: {admin.email}')
        else:
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