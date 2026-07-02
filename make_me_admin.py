from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(email='tuxigoww@bk.ru').first()
    if user:
        user.role = 'admin'
        db.session.commit()
        print(f'✅ Пользователь {user.email} теперь админ')
    else:
        print('❌ Пользователь не найден')
        print('Зарегистрируйся на сайте сначала!')