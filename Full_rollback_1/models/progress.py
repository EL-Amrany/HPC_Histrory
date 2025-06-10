# models/progress.py
from extensions import db
from app import db

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    module_name = db.Column(db.String(100))
    completion_percentage = db.Column(db.Float, default=0.0)
    xp = db.Column(db.Integer, default=0)
    badge = db.Column(db.String(100), default="")

    def __repr__(self):
        return f"<Progress user_id={self.user_id}, module={self.module_name}, percent={self.completion_percentage}, XP={self.xp}, badge={self.badge}>"