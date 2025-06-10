from app import db
from flask_login import UserMixin
import json
from extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    skill_level = db.Column(db.String(50), default='beginner')  # beginner, intermediate, advanced
    progress = db.Column(db.Float, default=0.0)  # 0-100
    response_history = db.Column(db.Text, default='[]')  # store as JSON string

    def set_response_history(self, history_list):
        self.response_history = json.dumps(history_list)

    def get_response_history(self):
        try:
            return json.loads(self.response_history)
        except:
            return []
        
from app import db
from datetime import datetime

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    bot_message = db.Column(db.Text)
    user_message = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)

    user = db.relationship('User', backref='chats')

