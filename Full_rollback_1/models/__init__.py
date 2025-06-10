from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Where to redirect if user not logged in

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.chatbot import chatbot_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chatbot_bp)

    # Create DB tables if not exist
    with app.app_context():
        db.create_all()

    return app
