from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import os

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 用户与尽调记录的关系
    due_diligences = db.relationship('DueDiligence', backref='author', lazy=True)
    # 用户与批注的关系 - 修改反向引用名称
    comments = db.relationship('DueDiligenceComment', backref='comment_author', lazy=True)


class PrivateFund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    establishment_date = db.Column(db.DateTime)
    management_scale = db.Column(db.Float)
    team_size = db.Column(db.Integer)
    strategy_tags = db.Column(db.String(500))
    region = db.Column(db.String(100))
    keywords = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 私募与尽调记录的关系
    due_diligences = db.relationship('DueDiligence', backref='fund', lazy=True)

    def get_latest_due_diligence_date(self):
        if self.due_diligences:
            return max([dd.date for dd in self.due_diligences])
        return None


class DueDiligence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey('private_fund.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 尽调记录与批注的关系
    comments = db.relationship('DueDiligenceComment', backref='due_diligence', lazy=True, cascade='all, delete-orphan')


class DueDiligenceComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    due_diligence_id = db.Column(db.Integer, db.ForeignKey('due_diligence.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 修改关系定义，避免名称冲突
    author = db.relationship('User', backref='authored_comments')