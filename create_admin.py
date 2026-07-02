from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        print('Админ уже существует')
    else:
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('Admin1234'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('✅ Админ создан: admin@example.com / Admin1234')