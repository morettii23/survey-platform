from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Survey, Question, Option, Answer
from forms import RegistrationForm, LoginForm, SurveyForm
from logger import setup_logger
import json

logger = setup_logger('routes')

main_bp = Blueprint('main', __name__)


# =========================
# INDEX
# =========================
@main_bp.route('/')
def index():
    surveys = Survey.query.filter_by(is_active=True).all()
    return render_template('index.html', surveys=surveys)


# =========================
# REGISTER
# =========================
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()

        flash("Регистрация успешна!", "success")
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


# =========================
# LOGIN
# =========================
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Вход выполнен", "success")
            return redirect(url_for('main.index'))

        flash("Неверные данные", "danger")

    return render_template('login.html', form=form)


# =========================
# LOGOUT
# =========================
@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# =========================
# CREATE SURVEY
# =========================
@main_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_survey():
    form = SurveyForm()

    if form.validate_on_submit():
        survey = Survey(
            creator_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            is_active=True
        )
        db.session.add(survey)
        db.session.flush()

        q_index = 0

        while True:
            q_text = request.form.get(f'question_text_{q_index}')
            if not q_text:
                break

            q_type = request.form.get(f'question_type_{q_index}', 'single')

            question = Question(
                survey_id=survey.id,
                text=q_text,
                type=q_type,
                order=q_index
            )
            db.session.add(question)
            db.session.flush()

            if q_type != 'text':
                o_index = 0
                while True:
                    opt = request.form.get(f'option_text_{q_index}_{o_index}')
                    if not opt:
                        break

                    option = Option(
                        question_id=question.id,
                        text=opt
                    )
                    db.session.add(option)
                    o_index += 1

            q_index += 1

        db.session.commit()

        flash("Опрос создан", "success")
        return redirect(url_for('main.index'))

    return render_template('new_survey.html', form=form)


# =========================
# TAKE SURVEY
# =========================
@main_bp.route('/survey/<int:survey_id>')
def take_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    return render_template('take_survey.html', survey=survey)


# =========================
# VOTE
# =========================
@main_bp.route('/survey/<int:survey_id>/vote', methods=['POST'])
@login_required
def vote(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    for question in survey.questions:
        answers = request.form.getlist(f'question_{question.id}')

        if question.type == 'text':
            db.session.add(Answer(
                survey_id=survey.id,
                question_id=question.id,
                text_answer=answers[0] if answers else "",
                user_id=current_user.id
            ))
        else:
            for opt in answers:
                db.session.add(Answer(
                    survey_id=survey.id,
                    question_id=question.id,
                    option_id=int(opt),
                    user_id=current_user.id
                ))

    db.session.commit()

    flash("Ответы сохранены", "success")
    return redirect(url_for('main.results', survey_id=survey.id))


# =========================
# RESULTS (ВАЖНО — ФИКС ОШИБКИ)
# =========================
@main_bp.route('/survey/<int:survey_id>/results')
def results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    total_answers = Answer.query.filter_by(survey_id=survey_id).count()

    chart_data = {}

    for q in survey.questions:
        if q.type != 'text':
            chart_data[str(q.id)] = {
                "labels": [o.text for o in q.options],
                "data": [len(o.answers) for o in q.options]
            }

    return render_template(
        'results.html',
        survey=survey,
        total_answers=total_answers,
        chart_data=json.dumps(chart_data)
    )


# =========================
# MY SURVEYS
# =========================
@main_bp.route('/my_surveys')
@login_required
def my_surveys():
    surveys = Survey.query.filter_by(creator_id=current_user.id).all()
    return render_template('my_surveys.html', surveys=surveys)


# =========================
# TOGGLE
# =========================
@main_bp.route('/survey/<int:survey_id>/toggle')
@login_required
def toggle_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    if survey.creator_id != current_user.id:
        return redirect(url_for('main.index'))

    survey.is_active = not survey.is_active
    db.session.commit()

    return redirect(url_for('main.my_surveys'))


# =========================
# DELETE
# =========================
@main_bp.route('/survey/<int:survey_id>/delete')
@login_required
def delete_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    if survey.creator_id == current_user.id:
        db.session.delete(survey)
        db.session.commit()

    return redirect(url_for('main.my_surveys'))


# =========================
# EXPORT CSV
# =========================
@main_bp.route('/survey/<int:survey_id>/export')
def export_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Question", "Answer"])

    for q in survey.questions:
        for a in q.answers:
            if a.option_id:
                opt = Option.query.get(a.option_id)
                writer.writerow([q.text, opt.text if opt else ""])
            else:
                writer.writerow([q.text, a.text_answer])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=survey_{survey.id}.csv"}
    )