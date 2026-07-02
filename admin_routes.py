from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_required, current_user
from models import db, User, Survey, Answer
from sqlalchemy import func, desc
from functools import wraps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ запрещен. Требуются права администратора.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_surveys = Survey.query.count()
    total_answers = Answer.query.count()
    active_surveys = Survey.query.filter_by(is_active=True).count()
    
    recent_surveys = Survey.query.order_by(desc(Survey.created_at)).limit(5).all()
    
    date_stats = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        count = Survey.query.filter(
            func.date(Survey.created_at) == date.date()
        ).count()
        date_stats.append({
            'date': date.strftime('%d.%m'),
            'count': count
        })
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_surveys=total_surveys,
        total_answers=total_answers,
        active_surveys=active_surveys,
        recent_surveys=recent_surveys,
        date_stats=date_stats
    )

@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/user/<int:user_id>/toggle')
@login_required
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя заблокировать самого себя', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    status = 'активирован' if user.is_active else 'заблокирован'
    flash(f'Пользователь {user.username} {status}', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя удалить самого себя', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    if user.role == 'admin':
        flash('Нельзя удалить администратора', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.username} удален', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/surveys')
@login_required
@admin_required
def admin_surveys():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    query = Survey.query
    
    if search:
        query = query.filter(Survey.title.contains(search))
    
    surveys = query.order_by(desc(Survey.created_at)).paginate(page=page, per_page=per_page)
    return render_template('admin/surveys.html', surveys=surveys, search=search)

@admin_bp.route('/survey/<int:survey_id>/delete')
@login_required
@admin_required
def admin_delete_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    db.session.delete(survey)
    db.session.commit()
    flash(f'Опрос "{survey.title}" удален', 'success')
    return redirect(url_for('admin.admin_surveys'))