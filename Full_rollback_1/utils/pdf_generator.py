import pdfkit
import os
from datetime import datetime

def generate_certificate_pdf(user):
    # Create a simple HTML for certificate
    certificate_html = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <title>HPC Completion Certificate</title>
    </head>
    <body style="text-align:center; padding:50px;">
        <h1>Certificate of Completion</h1>
        <p>This certifies that <strong>{user.name}</strong> has successfully completed</p>
        <p>the HPC training at a mastery level of <strong>{user.skill_level}</strong></p>
        <p>on {datetime.now().strftime('%Y-%m-%d')} with a progress of {user.progress:.2f}%.</p>
        <p>Congratulations!</p>
    </body>
    </html>
    """

    pdf_path = f"/tmp/{user.name}_certificate.pdf"  # or any path you prefer
    pdfkit.from_string(certificate_html, pdf_path)
    return pdf_path
