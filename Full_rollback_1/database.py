# database.py
from app import create_app, db

app = create_app()

with app.app_context():
    # Drop existing tables
    db.drop_all()
    # Create fresh tables
    db.create_all()
    print("Database reset complete.")
