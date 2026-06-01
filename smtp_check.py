"""Test SMTP Infomaniak — lance avec : python test_smtp.py"""
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
import os

load_dotenv(override=True)

host = os.getenv("SMTP_HOST")
port = int(os.getenv("SMTP_PORT", "587"))
username = os.getenv("SMTP_USERNAME")
password = os.getenv("SMTP_PASSWORD")
from_addr = os.getenv("SMTP_FROM")
to_addr = os.getenv("ADMIN_EMAIL")

print(f"Connexion à {host}:{port} avec {username}...")

try:
    msg = MIMEText("Test SMTP A-SCHOOL — si vous recevez ce mail, la config est correcte.")
    msg["Subject"] = "[A-SCHOOL] Test SMTP"
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.login(username, password)
        server.send_message(msg)

    print(f"OK — mail envoyé à {to_addr}")
except Exception as e:
    print(f"ERREUR : {e}")
