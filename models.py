from flask.sqlalchemy import SQLAlchemy
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pw_hash = db.Column(db.String(54))
    school = db.Column(db.String(32))
    score = db.Column(db.Integer)
    email = db.Column(db.String(64))
    gamesPlayed = db.Column(db.Integer)

    def __init__(self, school, email, password):
        self.school = school
        self.email = email
        self.set_password(password)

    def __repr__(self):
        '<User %s>' % self.email

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    letters = db.Column(db.String(7))
    u1 = db.Column(db.Integer, db.ForeignKey('user.id'))
    u2 = db.Column(db.Integer, db.ForeignKey('user.id'))
    u1Score = db.Column(db.Integer)
    u2Score = db.Column(db.Integer)

    def __init__(self, letters):
        self.letters = letters

    def __repr__(self):
         '<Game %s>' % self.letters
