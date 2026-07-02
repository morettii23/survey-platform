from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Survey, Answer
from sqlalchemy import desc
from functools import wraps
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# -------------------------
# ДЕКОРАТОР АДМИНА
# -------------------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Сначала войдите в систему", "danger")
            return redirect(url_for('main.login'))

        if current_user.role != 'admin':
            flash("Нет доступа (нужен админ)", "danger")
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)

    return wrapper


# -------------------------
# DASHBOARD
# -------------------------
@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():

    total_users = User.query.count()
    total_surveys = Survey.query.count()
    total_answers = Answer.query.count()
    active_surveys = Survey.query.filter_by(is_active=True).count()

    recent_surveys = Survey.query.order_by(
        desc(Survey.created_at)
    ).limit(5).all()

    # статистика по дням (без func.date — чтобы не ломалось на SQLite/Render)
    date_stats = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)

        next_day = day_start + timedelta(days=1)

        count = Survey.query.filter(
            Survey.created_at >= day_start,
            Survey.created_at < next_day
        ).count()

        date_stats.append({
            "date": day_start.strftime("%d.%m"),
            "count": count
        })

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_surveys=total_surveys,
        total_answers=total_answers,
        active_surveys=active_surveys,
        recent_surveys=recent_surveys,
        date_stats=date_stats
    )


# -------------------------
# USERS
# -------------------------
@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = User.query

    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search))
        )

    users = query.order_by(User.created_at.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    return render_template(
        "admin/users.html",
        users=users,
        search=search
    )


# -------------------------
# TOGGLE USER
# -------------------------
@admin_bp.route('/user/<int:user_id>/toggle')
@login_required
@admin_required
def admin_toggle_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Нельзя заблокировать самого себя", "danger")
        return redirect(url_for('admin.admin_users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = "активирован" if user.is_active else "заблокирован"
    flash(f"Пользователь {user.username} {status}", "success")

    return redirect(url_for('admin.admin_users'))


# -------------------------
# DELETE USER
# -------------------------
@admin_bp.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def admin_delete_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Нельзя удалить самого себя", "danger")
        return redirect(url_for('admin.admin_users'))

    if user.role == "admin":
        flash("Нельзя удалить администратора", "danger")
        return redirect(url_for('admin.admin_users'))

    db.session.delete(user)
    db.session.commit()

    flash("Пользователь удалён", "success")

    return redirect(url_for('admin.admin_users'))


# -------------------------
# SURVEYS
# -------------------------
@admin_bp.route('/surveys')
@login_required
@admin_required
def admin_surveys():

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Survey.query

    if search:
        query = query.filter(Survey.title.contains(search))

    surveys = query.order_by(
        Survey.created_at.desc()
    ).paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    return render_template(
        "admin/surveys.html",
        surveys=surveys,
        search=search
    )


# -------------------------
# DELETE SURVEY
# -------------------------
@admin_bp.route('/survey/<int:survey_id>/delete')
@login_required
@admin_required
def admin_delete_survey(survey_id):

    survey = Survey.query.get_or_404(survey_id)

    db.session.delete(survey)
    db.session.commit()

    flash("Опрос удалён", "success")

    return redirect(url_for('admin.admin_surveys'))