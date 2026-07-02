from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app as app  # <-- ЭТО ВАЖНО
from models import db, User, Survey, Question, Option, Answer
from forms import RegistrationForm, LoginForm, SurveyForm
from logger import setup_logger
import json
logger = setup_logger('routes')

@app.route('/')
def index():
    try:
        surveys = Survey.query.filter_by(is_active=True).all()
        return render_template('index.html', surveys=surveys)
    except Exception as e:
        logger.error(f'Ошибка в index: {str(e)}')
        flash('Произошла ошибка загрузки опросов', 'danger')
        return render_template('index.html', surveys=[])

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data)
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f'Новый пользователь: {user.email}')
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form)
    except Exception as e:
        logger.error(f'Ошибка в register: {str(e)}')
        flash('Ошибка регистрации', 'danger')
        return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                logger.info(f'Вход: {user.email}')
                flash('Добро пожаловать!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Неверный email или пароль', 'danger')
        
        return render_template('login.html', form=form)
    except Exception as e:
        logger.error(f'Ошибка в login: {str(e)}')
        flash('Ошибка входа', 'danger')
        return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f'Ошибка в logout: {str(e)}')
        flash('Ошибка выхода', 'danger')
        return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_survey():
    try:
        form = SurveyForm()
        if form.validate_on_submit():
            survey = Survey(
                creator_id=current_user.id,
                title=form.title.data,
                description=form.description.data,
                is_active=True,
                show_results=True
            )
            db.session.add(survey)
            db.session.flush()
            
            question_index = 0
            while True:
                question_text = request.form.get(f'question_text_{question_index}')
                if not question_text:
                    break
                    
                question_type = request.form.get(f'question_type_{question_index}', 'single')
                question = Question(
                    survey_id=survey.id,
                    text=question_text,
                    type=question_type,
                    order=question_index
                )
                db.session.add(question)
                db.session.flush()
                
                if question_type != 'text':
                    option_index = 0
                    while True:
                        option_text = request.form.get(f'option_text_{question_index}_{option_index}')
                        if not option_text:
                            break
                        option = Option(
                            question_id=question.id,
                            text=option_text
                        )
                        db.session.add(option)
                        option_index += 1
                
                question_index += 1
            
            db.session.commit()
            logger.info(f'Создан опрос: {survey.title} (ID: {survey.id})')
            flash('Опрос создан!', 'success')
            return redirect(url_for('index'))
        
        return render_template('new_survey.html', form=form)
    except Exception as e:
        logger.error(f'Ошибка в create_survey: {str(e)}')
        flash('Ошибка создания опроса', 'danger')
        return render_template('new_survey.html', form=form)

@app.route('/my_surveys')
@login_required
def my_surveys():
    try:
        surveys = Survey.query.filter_by(creator_id=current_user.id).all()
        return render_template('my_surveys.html', surveys=surveys)
    except Exception as e:
        logger.error(f'Ошибка в my_surveys: {str(e)}')
        flash('Ошибка загрузки опросов', 'danger')
        return render_template('my_surveys.html', surveys=[])

@app.route('/survey/<int:survey_id>')
def take_survey(survey_id):
    try:
        survey = Survey.query.get_or_404(survey_id)
        if not survey.is_active:
            flash('Опрос закрыт', 'warning')
            return redirect(url_for('index'))
        return render_template('take_survey.html', survey=survey)
    except Exception as e:
        logger.error(f'Ошибка в take_survey: {str(e)}')
        flash('Опрос не найден', 'danger')
        return redirect(url_for('index'))

@app.route('/survey/<int:survey_id>/vote', methods=['POST'])
def vote(survey_id):
    try:
        survey = Survey.query.get_or_404(survey_id)
        
        if current_user.is_authenticated:
            existing = Answer.query.filter_by(
                survey_id=survey_id,
                user_id=current_user.id
            ).first()
            if existing:
                flash('Вы уже проходили этот опрос', 'warning')
                return redirect(url_for('results', survey_id=survey_id))
        
        for question in survey.questions:
            data = request.form.getlist(f'question_{question.id}')
            if not data:
                continue
                
            if question.type == 'text':
                answer = Answer(
                    survey_id=survey_id,
                    question_id=question.id,
                    text_answer=data[0],
                    user_id=current_user.id if current_user.is_authenticated else None
                )
                db.session.add(answer)
            else:
                for value in data:
                    option = Option.query.get(int(value))
                    if option and option.question_id == question.id:
                        answer = Answer(
                            survey_id=survey_id,
                            question_id=question.id,
                            option_id=option.id,
                            user_id=current_user.id if current_user.is_authenticated else None
                        )
                        db.session.add(answer)
        
        db.session.commit()
        logger.info(f'Проголосовали в опросе {survey_id}')
        flash('Спасибо!', 'success')
        return redirect(url_for('results', survey_id=survey_id))
    except Exception as e:
        logger.error(f'Ошибка в vote: {str(e)}')
        flash('Ошибка отправки ответов', 'danger')
        return redirect(url_for('take_survey', survey_id=survey_id))

@app.route('/survey/<int:survey_id>/results')
def results(survey_id):
    try:
        survey = Survey.query.get_or_404(survey_id)
        total_answers = Answer.query.filter_by(survey_id=survey_id).count()
        
        chart_data = {}
        for question in survey.questions:
            if question.type != 'text':
                chart_data[str(question.id)] = {
                    'labels': [option.text for option in question.options],
                    'data': [len(option.answers) for option in question.options]
                }
        
        return render_template(
            'results.html',
            survey=survey,
            total_answers=total_answers,
            chart_data=json.dumps(chart_data)
        )
    except Exception as e:
        logger.error(f'Ошибка в results: {str(e)}')
        flash('Ошибка загрузки результатов', 'danger')
        return redirect(url_for('index'))

@app.route('/survey/<int:survey_id>/export')
def export_results(survey_id):
    try:
        import csv
        from io import StringIO
        
        survey = Survey.query.get_or_404(survey_id)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Вопрос', 'Ответ'])
        
        for question in survey.questions:
            for answer in question.answers:
                if answer.option_id:
                    option = Option.query.get(answer.option_id)
                    writer.writerow([question.text, option.text if option else ''])
                elif answer.text_answer:
                    writer.writerow([question.text, answer.text_answer])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={survey.title}_results.csv'}
        )
    except Exception as e:
        logger.error(f'Ошибка в export_results: {str(e)}')
        flash('Ошибка экспорта', 'danger')
        return redirect(url_for('results', survey_id=survey_id))

@app.route('/survey/<int:survey_id>/toggle')
@login_required
def toggle_survey(survey_id):
    try:
        survey = Survey.query.get_or_404(survey_id)
        if survey.creator_id != current_user.id:
            flash('Нет прав', 'danger')
            return redirect(url_for('my_surveys'))
        
        survey.is_active = not survey.is_active
        db.session.commit()
        status = 'открыт' if survey.is_active else 'закрыт'
        flash(f'Опрос {status}', 'success')
        return redirect(url_for('my_surveys'))
    except Exception as e:
        logger.error(f'Ошибка в toggle_survey: {str(e)}')
        flash('Ошибка', 'danger')
        return redirect(url_for('my_surveys'))

@app.route('/survey/<int:survey_id>/delete')
@login_required
def delete_survey(survey_id):
    try:
        survey = Survey.query.get_or_404(survey_id)
        if survey.creator_id != current_user.id:
            flash('Нет прав', 'danger')
            return redirect(url_for('my_surveys'))
        
        db.session.delete(survey)
        db.session.commit()
        flash('Опрос удалён', 'success')
        return redirect(url_for('my_surveys'))
    except Exception as e:
        logger.error(f'Ошибка в delete_survey: {str(e)}')
        flash('Ошибка удаления', 'danger')
        return redirect(url_for('my_surveys'))

# ===== АДМИН-МАРШРУТЫ =====
from admin_routes import admin_bp
app.register_blueprint(admin_bp)