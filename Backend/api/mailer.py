import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import config

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """
    Envoie un email via SMTP si configuré.
    En développement sans SMTP configuré, l'email est affiché dans le terminal
    (permet de récupérer l'OTP sans serveur de mail).
    """
    if not config.SMTP_HOST or not config.SMTP_USER:
        print(f"\n[MAIL][DEV] À {to} - Sujet: {subject}", flush=True)
        print(f"[MAIL][DEV] {text_body or html_body}", flush=True)
        print("[MAIL][DEV] SMTP non configuré : récupérez l'OTP ici ou configurez SMTP_HOST/SMTP_USER dans le .env\n", flush=True)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config.SMTP_FROM or config.SMTP_USER
        msg["To"] = to
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to], msg.as_string())
        return True
    except Exception as e:
        logger.error("[MAIL] Échec de l'envoi à %s : %s", to, e)
        return False
