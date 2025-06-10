import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hpc_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.environ.get('sk-proj-Kl1lflhbwL0QhXOnzJ1UT3BlbkFJoqsfEVjW0uZyLwo2DCVr')
