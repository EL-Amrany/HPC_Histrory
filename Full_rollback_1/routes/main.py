from flask import Blueprint, render_template, request, redirect, url_for, send_file
from flask_login import login_required, current_user
from models.user import User
from app import db
from utils.pdf_generator import generate_certificate_pdf

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Public homepage or welcome page
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Show user progress, HPC modules, next recommended steps, etc.
    return render_template('dashboard.html', user=current_user)

@main_bp.route("/generate")
def generate_module():
    return render_template("generate.html")


@main_bp.route('/generate_certificate')
@login_required
def generate_certificate():
    # Only generate if progress >= 100, or some threshold
    if current_user.progress >= 80.0:
        pdf_path = generate_certificate_pdf(current_user)
        return send_file(pdf_path, as_attachment=True)
    else:
        return "You have not completed enough progress to earn a certificate."
