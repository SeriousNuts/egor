from flask_login import UserMixin
from sqlalchemy import Table, Column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1200), index=True, unique=True)
    type = db.Column(db.String(64), index=True)  # 2 типа pick, conform
    question_number = db.Column(db.Integer)

    def __repr__(self):
        return 'Question {}'.format(self.text)


class ObjectOfInfluence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Integer, db.ForeignKey(Question.id))
    object_name = db.Column(db.String(1200), index=True, unique=True)

    def __repr__(self):
        return '{}'.format(self.object_name)


class ThreatSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Integer, db.ForeignKey(Question.id))
    object_name = db.Column(db.String(1200), index=True, unique=True)
    category = db.Column(db.String(1200))


class Threat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ubi_name = db.Column(db.String(1200), index=True)
    description = db.Column(db.String(1200), index=True)
    ThreatSource = db.Column(db.String(1200), index=True)
    ObjectOfInfluence = db.Column(db.String(1200), index=True)
    privacy_violation = db.Column(db.Integer)
    integrity_breach = db.Column(db.Integer)
    accessibility_violation = db.Column(db.Integer)
    date_UBI = db.Column(db.String(1200))
    date_edit = db.Column(db.String(1200))
    text = db.Column(db.String(1200))

    def __repr__(self):
        return '{}'.format(str(self.id) + ' ' + self.ubi_name)


class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1200))
    question_id = db.Column(db.Integer, db.ForeignKey(Question.id))

    def __repr__(self):
        return '{}'.format(self.text)


class SessionQuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey(Question.id))
    quesion_number = db.Column(db.Integer)
    session_id = db.Column(db.Integer)
    session_name = db.Column(db.Integer)

    def __repr__(self):
        return 'Session {}'.format(self.question_id)


class OptionConf(db.Model):  # вопросам с выбором соответствий
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1200))
    question_id = db.Column(db.Integer, db.ForeignKey(Question.id))
    confs = db.relationship('OptionConfs', backref='Option_conf',
                            lazy='dynamic')

    def __repr__(self):
        return '{}'.format(self.text)


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer)
    resultJSON = db.Column(db.TEXT)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1200))
    password = db.Column(db.String(1200))
    UUID = db.Column(db.String(1200))

    def set_password(self, password):
        self.password = generate_password_hash(password)
        return self.password

    def check_password(self, password):
        return check_password_hash(self.password, password)


class ComponentObjectOfInfluence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1200))
    ObjectOfInfluenceId = db.Column(db.Integer, db.ForeignKey(ObjectOfInfluence.id))

    def __repr__(self):
        return '{}'.format(self.text)


class TypeOfRisks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(1200))  # номер риска в таблице
    text = db.Column(db.String(1200))  # вид риска


class TypeOfNegativeConseq(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typeId = db.Column(db.String(1200), db.ForeignKey(TypeOfRisks.id))
    text = db.Column(db.String(1200))  # возможное негативное последствие

    def __repr__(self):
        return '{}'.format(self.text)


class OptionConfs(db.Model):  # варианты ответов для вопросов с выбором соответствий
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey(OptionConf.id))
    option_conf_1 = db.Column(db.String(1200))
    option_conf_2 = db.Column(db.String(1200))


class TechTactics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    threat_id = db.Column(db.Integer, db.ForeignKey(Threat.id))
    fstek_tactic = db.Column(db.String(1200))
    fstek_technik = db.Column(db.String(1200))
    mitre_tactic = db.Column(db.String(1200))
    mitre_technik = db.Column(db.String(1200))

    def __repr__(self):
        return '{}'.format(self.text)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1200), unique=True)
    desc = db.Column(db.String(1200))
    owner = db.Column(db.String(1200), db.ForeignKey(User.name))
    date = db.Column(db.TIMESTAMP)
    file = db.Column(db.BLOB)

