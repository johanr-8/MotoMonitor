"""Email + SMS notification services.

Email: Sends via SMTP when SMTP_USER is configured, otherwise logs to console.
SMS: Stubbed (logs to console). Structure ready for Twilio integration.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS


def send_email(to_email, subject, body):
    """Send an email notification via SMTP. Falls back to console log."""
    if not SMTP_USER:
        print(f"[EMAIL STUB] To: {to_email} | Subject: {subject} | Body: {body}")
        return True

    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"[EMAIL SENT] To: {to_email} | Subject: {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}")
        return False


def send_sms(phone_number, message):
    """Send an SMS notification. Stubbed — prints to console.

    To integrate Twilio:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=message, from_='+1XXXXXXXXXX', to=phone_number)
    """
    if not phone_number:
        return True
    print(f"[SMS STUB] To: {phone_number} | Message: {message}")
    return True


def send_reminder_alert(user, vehicle, reminder, days_left):
    """Send alert for an upcoming reminder via email and SMS."""
    rtype = reminder["type"].replace("_", " ").title()
    vehicle_name = vehicle.get("nickname") or f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip()
    reg = vehicle.get("registration_number", "")

    if days_left < 0:
        urgency = f"OVERDUE by {abs(days_left)} days"
    elif days_left == 0:
        urgency = "DUE TODAY"
    else:
        urgency = f"due in {days_left} days"

    subject = f"MotoMonitor: {rtype} — {urgency}"
    body = (
        f"Hi {user['name']},\n\n"
        f"Your {rtype} for {vehicle_name} (Reg: {reg}) "
        f"is {urgency}.\n"
        f"Due date: {reminder['due_date']}\n\n"
        f"Please take action to avoid penalties.\n\n"
        f"Regards,\nMotoMonitor"
    )

    email_ok = send_email(user["email"], subject, body)

    sms_msg = f"MotoMonitor: {rtype} for {vehicle_name} ({reg}) is {urgency}. Due: {reminder['due_date']}"
    phone = user["phone"] if "phone" in user.keys() else ""
    sms_ok = send_sms(phone or "", sms_msg)

    family_email = user["family_email"] if "family_email" in user.keys() else ""
    if family_email:
        send_email(family_email, f"[CC] {subject}", body)

    return email_ok and sms_ok


def send_weekly_digest(user, upcoming_reminders):
    """Send a weekly digest email listing all reminders due in the next 30 days."""
    if not upcoming_reminders:
        return True

    lines = [f"Hi {user['name']},", "", "Here's your weekly maintenance digest:", ""]
    for r in upcoming_reminders:
        rtype = r["type"].replace("_", " ").title()
        lines.append(f"  - {rtype} due on {r['due_date']} for {r.get('vehicle_name', 'your vehicle')}")

    lines.extend([
        "",
        "Stay on top of your vehicle maintenance!",
        "",
        "Regards,",
        "MotoMonitor",
    ])

    body = "\n".join(lines)
    subject = f"MotoMonitor: Weekly Digest — {len(upcoming_reminders)} upcoming reminder(s)"

    email_ok = send_email(user["email"], subject, body)

    family_email = user.get("family_email", "")
    if family_email:
        send_email(family_email, f"[CC] {subject}", body)

    return email_ok
