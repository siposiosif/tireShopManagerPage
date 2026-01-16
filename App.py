from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
import os
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

app = Flask(__name__)

# 2. Global Variables
app.secret_key = os.getenv("SECRET_KEY", "fallback-if-not-found")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

CSV_FILE = 'reservations.csv' # Defined globally for all routes
WORKING_HOURS = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]

# 3. Ensure CSV exists with headers
def init_db():
    if not os.path.exists(CSV_FILE):
        fieldnames = ["id", "timestamp", "nume", "email", "telefon", "marca", "model", "serviciu", "data_pref", "ora_pref", "status"]
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        print(f"Created new database file: {CSV_FILE}")

init_db()

# --- HELPER FUNCTIONS ---

def generate_calendar_link(nume, serviciu, data, ora):
    date_str = data.replace("-", "")
    time_str = ora.replace(":", "")
    start_dt = f"{date_str}T{time_str}00"
    
    params = {
        "action": "TEMPLATE",
        "text": f"Programare {serviciu} - Vulcanizare Sofronea",
        "dates": f"{start_dt}/{start_dt}",
        "details": f"Salut {nume}, te asteptam pentru {serviciu} la Vulcanizare Sofronea.",
        "location": "str.27 Nr.2, Sofronea, Romania"
    }
    return "https://www.google.com/calendar/render?" + urllib.parse.urlencode(params)

def send_professional_email(to_email, subject, html_content):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Vulcanizare Sofronea <{EMAIL_USER}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Eroare email: {e}")
        return False

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/rezervation')
def rezervation():
    return render_template('rezervation.html')

@app.route('/get_slots')
def get_slots():
    date = request.args.get('date')
    taken = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['data_pref'] == date and row['status'] != 'Respins':
                    taken.append(row['ora_pref'])
    return jsonify(taken)

@app.route('/submit_reservation', methods=['POST'])
def submit_reservation():
    data = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nume": request.form.get('name'),
        "email": request.form.get('email'),
        "telefon": request.form.get('phone'),
        "marca": request.form.get('car-make'),
        "model": request.form.get('car-model'),
        "serviciu": request.form.get('service'),
        "data_pref": request.form.get('date'),
        "ora_pref": request.form.get('time'),
        "status": "In asteptare"
    }

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        writer.writerow(data)

    return render_template('index.html', msg="Cerere trimisă! Vă rugăm să așteptați confirmarea pe email.")

@app.route('/admin')
def admin():
    reservations = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            reservations = list(reader)
    return render_template('admin.html', reservations=reservations)

@app.route('/update_status/<id>/<action>')
def update_status(id, action):
    rows = []
    if not os.path.exists(CSV_FILE): return redirect('/admin')

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == id:
                if action == 'confirm':
                    row['status'] = 'Confirmat'
                    cal_link = generate_calendar_link(row['nume'], row['serviciu'], row['data_pref'], row['ora_pref'])
                    maps_link = "https://share.google/ZZc5dAjnXWJQoiN5Z"
                    
                    html = f"<h1>Confirmat!</h1><p>Salut {row['nume']}, te asteptam.</p><a href='{cal_link}'>Calendar</a>"
                    send_professional_email(row['email'], "Confirmare Programare", html)
                else:
                    row['status'] = 'Respins'
                    html = f"Salut {row['nume']}, intervalul nu e disponibil."
                    send_professional_email(row['email'], "Anulare Programare", html)
            rows.append(row)

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)