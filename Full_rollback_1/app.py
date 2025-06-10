from flask import Flask
from flask_login import LoginManager
from config import Config

from extensions import db   # <-- import here instead of from app

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Import models AFTER db.init_app so no loop
    from models.user import User
    from models.progress import Progress
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.chatbot import chatbot_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chatbot_bp)
    
    with app.app_context():
        db.create_all()
    
    return app
