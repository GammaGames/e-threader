import smtplib
import os
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


GMAIL_USERNAME = client_secret=os.getenv("GMAIL_USERNAME")
GMAIL_PASSWORD = client_secret=os.getenv("GMAIL_PASSWORD")


async def send_mail(send_to, subject, text, files=None):
    assert isinstance(send_to, list)
    print("Creating email...", flush=True)

    msg = MIMEMultipart()
    msg["From"] = "ethreader.bot@gmail.com"
    msg["To"] = COMMASPACE.join(send_to)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part["Content-Disposition"] = f"attachment; filename={basename(f)}"
        msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.ehlo()
    server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
    print("Sending email!", flush=True)
    server.sendmail("ethreader.bot@gmail.com", send_to, msg.as_string())
    server.close()
    print("Sent email!", flush=True)
