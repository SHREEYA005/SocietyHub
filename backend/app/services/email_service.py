"""
Email notifications.

If EMAIL_HOST is not configured, emails are logged instead of sent - this
keeps the app fully runnable in development/evaluation without real SMTP
credentials, while the real send path is fully implemented and used the
moment EMAIL_HOST etc. are set in the environment. Failures to send are
caught and logged; they never break the request that triggered them (e.g. a
status update still succeeds even if the notification email fails).
"""
import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger("societyhub.email")
settings = get_settings()


def _send(to_email: str, subject: str, body: str) -> None:
    if not settings.EMAIL_HOST:
        logger.info("[email:not-configured] To=%s Subject=%s\n%s", to_email, subject, body)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls()
            if settings.EMAIL_USERNAME:
                server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as exc:  # noqa: BLE001 - notification failures must never crash the request
        logger.warning("Failed to send email to %s: %s", to_email, exc)


def send_status_change_email(to_email: str, resident_name: str, reference_code: str,
                              previous_status: str, new_status: str, note: str | None) -> None:
    subject = f"Your maintenance complaint #{reference_code} has been updated"
    body = (
        f"Hi {resident_name},\n\n"
        f"Complaint: #{reference_code}\n"
        f"Previous status: {previous_status}\n"
        f"New status: {new_status}\n"
        f"Admin note: {note or '(no note added)'}\n\n"
        f"Next step: "
        f"{'Our team will follow up shortly.' if new_status != 'RESOLVED' else 'This complaint is now closed. Thank you for your patience.'}\n\n"
        f"- SocietyHub Maintenance Team"
    )
    _send(to_email, subject, body)


def send_important_notice_email(to_email: str, resident_name: str, title: str,
                                 content: str, published_at: str) -> None:
    subject = f"Important notice: {title}"
    body = (
        f"Hi {resident_name},\n\n"
        f"A new important notice has been posted.\n\n"
        f"Title: {title}\n"
        f"Published: {published_at}\n\n"
        f"{content}\n\n"
        f"- SocietyHub"
    )
    _send(to_email, subject, body)
