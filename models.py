from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# --------------------
# USER
# --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# --------------------
# SURVEY
# --------------------
class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)
    show_results = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='surveys')
    questions = db.relationship('Question', backref='survey', cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='survey', cascade='all, delete-orphan')


# --------------------
# QUESTION
# --------------------
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)

    text = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # single / multiple / text

    order = db.Column(db.Integer, default=0)

    # ⭐ баллы за вопрос
    points = db.Column(db.Integer, default=1)

    # ⭐ правильный вариант (для single choice)
    correct_option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=True)

    options = db.relationship(
    'Option',
    backref='question',
    cascade='all, delete-orphan',
    foreign_keys='Option.question_id'
)
    answers = db.relationship('Answer', backref='question', cascade='all, delete-orphan')


# --------------------
# OPTION
# --------------------
class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    text = db.Column(db.String(200), nullable=False)


# --------------------
# ANSWER
# --------------------
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=True)

    text_answer = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='answers')
    option = db.relationship('Option')