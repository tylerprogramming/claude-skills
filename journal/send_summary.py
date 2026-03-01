"""
Send the weekly journal summary via Gmail.

Usage: python3 ~/.claude/skills/journal/send_summary.py

Reads ~/journal/weekly_summary.txt and emails it.

Requires:
  - GMAIL_APP_PASSWORD environment variable (Google App Password, NOT your regular password)
    Generate one at: https://myaccount.google.com/apppasswords
  - Sends from and to: tylerreedytlearning@gmail.com
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

GMAIL_ADDRESS = "tylerreedytlearning@gmail.com"
SUMMARY_FILE = os.path.expanduser("~/journal/weekly_summary.txt")


def main():
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not app_password:
        print("Error: GMAIL_APP_PASSWORD environment variable is not set.")
        print("Generate an App Password at: https://myaccount.google.com/apppasswords")
        sys.exit(1)

    if not os.path.exists(SUMMARY_FILE):
        print(f"Error: No summary file found at {SUMMARY_FILE}")
        print("Run the journal skill with 'email summary' to generate one first.")
        sys.exit(1)

    with open(SUMMARY_FILE, "r") as f:
        summary_text = f.read()

    today = datetime.now().strftime("%B %d, %Y")
    subject = f"Weekly Journal Summary — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS

    msg.attach(MIMEText(summary_text, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, app_password)
            server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f"Weekly summary emailed to {GMAIL_ADDRESS}")
    except smtplib.SMTPAuthenticationError:
        print("Error: Gmail authentication failed.")
        print("Make sure GMAIL_APP_PASSWORD is a valid App Password.")
        sys.exit(1)


if __name__ == "__main__":
    main()
