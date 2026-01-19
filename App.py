from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
import os
import json
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

app = Flask(__name__)

# 2. Global Variables
app.secret_key = os.getenv("SECRET_KEY", "fallback-if-not-found")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

CSV_FILE = 'reservations.csv' # Defined globally for all routes
ARCHIVE_FILE = 'reservations_archive.csv'
SERVICES_FILE = 'services.json'
FIELDNAMES = [
    "id",
    "timestamp",
    "nume",
    "email",
    "telefon",
    "marca",
    "model",
    "serviciu",
    "data_pref",
    "ora_pref",
    "status",
    "status_updated",
    "pret",
]
ARCHIVE_FIELDNAMES = FIELDNAMES + ["archived_at", "archive_reason"]
WORKING_HOURS = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]

# 3. Ensure CSV exists with headers
def init_db():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        print(f"Created new database file: {CSV_FILE}")
    if not os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=ARCHIVE_FIELDNAMES)
            writer.writeheader()
        print(f"Created new archive file: {ARCHIVE_FILE}")

init_db()

def load_services():
    if not os.path.exists(SERVICES_FILE):
        # Create default services file
        default_services = {
            "services": [
                {
                    "id": "tire-change",
                    "name": "Schimb Anvelope Sezonier",
                    "duration": 60,
                    "price": 0,
                    "description": "Schimb complet al anvelopelor pentru sezonul curent"
                },
                {
                    "id": "balancing",
                    "name": "Echilibrare Roți",
                    "duration": 30,
                    "price": 0,
                    "description": "Echilibrare profesională a roților"
                }
            ]
        }
        with open(SERVICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_services, f, indent=2, ensure_ascii=False)
        return default_services["services"]
    
    with open(SERVICES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("services", [])

def save_services(services):
    data = {"services": services}
    with open(SERVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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

def is_local_request():
    return request.remote_addr in {"127.0.0.1", "::1"}

def require_admin_access():
    if not is_local_request():
        return False
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    return bool(admin_token and token == admin_token)

def parse_timestamp(timestamp_str):
    if not timestamp_str:
        return None
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def parse_reservation_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None

def archive_old_reservations(rows):
    now = datetime.now()
    remaining = []
    archived = []

    for row in rows:
        row.setdefault("status_updated", row.get("timestamp", ""))
        status_updated_dt = parse_timestamp(row.get("status_updated")) or parse_timestamp(row.get("timestamp"))
        created_dt = parse_timestamp(row.get("timestamp"))
        scheduled_dt = parse_reservation_datetime(row.get("data_pref"), row.get("ora_pref"))
        archive_reason = None

        if row.get("status") == "Confirmat" and scheduled_dt:
            if now >= scheduled_dt + timedelta(hours=8):
                archive_reason = "confirmat_peste_8_ore"
        elif row.get("status") == "Respins" and status_updated_dt:
            if now >= status_updated_dt + timedelta(hours=24):
                archive_reason = "respins_peste_24_ore"
        elif row.get("status") == "In asteptare":
            if scheduled_dt and now >= scheduled_dt:
                row["status"] = "Respins"
                row["status_updated"] = now.strftime("%Y-%m-%d %H:%M:%S")
                archive_reason = "expirat_ora_programarii"
            elif created_dt and now >= created_dt + timedelta(days=72):
                row["status"] = "Respins"
                row["status_updated"] = now.strftime("%Y-%m-%d %H:%M:%S")
                archive_reason = "expirat_72_zile"

        if archive_reason:
            archived_row = {key: row.get(key, "") for key in ARCHIVE_FIELDNAMES}
            archived_row["archived_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            archived_row["archive_reason"] = archive_reason
            archived.append(archived_row)
        else:
            remaining.append(row)

    return remaining, archived

def load_reservations():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_reservations(rows):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            normalized = {key: row.get(key, "") for key in FIELDNAMES}
            writer.writerow(normalized)

def append_archived(rows):
    if not rows:
        return
    with open(ARCHIVE_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=ARCHIVE_FIELDNAMES)
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in ARCHIVE_FIELDNAMES})

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/services')
def api_services():
    services = load_services()
    return jsonify(services)

@app.route('/rezervation')
def rezervation():
    return render_template('rezervation.html')

@app.route('/get_slots')
def get_slots():
    date = request.args.get('date')
    services_param = request.args.get('services', '')
    duration_param = request.args.get('duration', '30')
    
    try:
        total_duration = int(duration_param)
    except ValueError:
        total_duration = 30
    
    taken = []
    
    # Get current date and time
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['data_pref'] == date and row['status'] != 'Respins':
                    # Calculate duration for this reservation
                    reservation_duration = 0
                    
                    # Check if this reservation has multiple services
                    reservation_services = row['serviciu'].split(',') if row['serviciu'] else []
                    
                    if reservation_services:
                        services = load_services()
                        for service_id in reservation_services:
                            service = next((s for s in services if s['id'] == service_id), None)
                            if service:
                                reservation_duration += service['duration']
                            else:
                                # Fallback for default services
                                if service_id == 'tire-change':
                                    reservation_duration += 60
                                elif service_id == 'balancing':
                                    reservation_duration += 30
                    else:
                        # Legacy single service support
                        services = load_services()
                        service_duration = 30  # default
                        for service in services:
                            if service['id'] == row['serviciu']:
                                service_duration = service['duration']
                                break
                        reservation_duration = service_duration
                    
                    # Block slots based on reservation duration
                    start_time = datetime.strptime(row['ora_pref'], '%H:%M')
                    end_time = start_time + timedelta(minutes=reservation_duration)
                    
                    # Generate all 30-minute slots that this reservation occupies
                    current_time = start_time
                    while current_time < end_time:
                        taken.append(current_time.strftime('%H:%M'))
                        current_time += timedelta(minutes=30)
    
    # Filter out unavailable time slots based on current time
    available_slots = []
    for hour in WORKING_HOURS:
        slot_time = datetime.strptime(hour, '%H:%M').time()
        
        # If the requested date is today, check time restrictions
        if date == today_str:
            # Don't allow reservations before current time or within 20 minutes
            current_time_plus_20 = (now + timedelta(minutes=20)).time()
            if slot_time <= now.time() or slot_time <= current_time_plus_20:
                taken.append(hour)  # Mark as taken/unavailable
                continue
        
        # If the requested date is in the past, mark all slots as unavailable
        elif date < today_str:
            taken.append(hour)
            continue
            
        # For future dates, slot is available unless already taken
        if hour not in taken:
            available_slots.append(hour)
    
    # Return only available slots for future dates, or taken slots for filtering
    if date > today_str:
        return jsonify(available_slots)  # Return available slots
    else:
        return jsonify(taken)  # Return taken slots (including time-restricted ones)

@app.route('/submit_reservation', methods=['POST'])
def submit_reservation():
    # Get form data
    requested_date = request.form.get('date')
    requested_time = request.form.get('time')
    
    # Validate that reservation is not in the past or too soon
    if requested_date and requested_time:
        try:
            reservation_datetime = datetime.strptime(f"{requested_date} {requested_time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            
            # Don't allow reservations in the past
            if reservation_datetime <= now:
                return render_template('index.html', msg="Eroare: Nu puteți face rezervări în trecut!")
            
            # Don't allow reservations within 20 minutes of current time
            if reservation_datetime <= now + timedelta(minutes=20):
                return render_template('index.html', msg="Eroare: Rezervările trebuie să fie cu cel puțin 20 de minute în viitor!")
                
        except ValueError:
            return render_template('index.html', msg="Eroare: Format de dată/oră invalid!")
    
    # Get selected services
    services_string = request.form.get('services', '')
    selected_service_ids = services_string.split(',') if services_string else []
    
    # Calculate total price
    services = load_services()
    total_price = 0
    
    for service_id in selected_service_ids:
        service = next((s for s in services if s['id'] == service_id), None)
        if service:
            total_price += service.get('price', 0)
        else:
            # Fallback for default services
            if service_id == 'tire-change':
                total_price += 150
            elif service_id == 'balancing':
                total_price += 50

    data = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nume": request.form.get('name'),
        "email": request.form.get('email'),
        "telefon": request.form.get('phone'),
        "marca": request.form.get('car-make'),
        "model": request.form.get('car-model'),
        "serviciu": services_string,  # Store as comma-separated string
        "data_pref": request.form.get('date'),
        "ora_pref": request.form.get('time'),
        "status": "In asteptare",
        "status_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pret": total_price,
    }

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(data)

    return render_template('index.html', msg="Cerere trimisă! Vă rugăm să așteptați confirmarea pe email.")

@app.route('/admin')
def admin():
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not (admin_token and token == admin_token):
        return ("Not Found", 404)
    reservations = load_reservations()
    remaining, archived = archive_old_reservations(reservations)
    if archived or len(remaining) != len(reservations):
        save_reservations(remaining)
        append_archived(archived)
    reservations = remaining
    services = load_services()
    
    # Calculate values for JavaScript
    pending_count = sum(1 for res in reservations if res.get('status') == 'In asteptare')
    latest_timestamp = max([res.get('timestamp', '') for res in reservations]) if reservations else ''
    
    return render_template('admin.html', 
                         reservations=reservations, 
                         token=token, 
                         services=services,
                         pending_count=pending_count,
                         latest_timestamp=latest_timestamp)

@app.route('/update_status/<id>/<action>')
def update_status(id, action):
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not (admin_token and token == admin_token):
        return ("Not Found", 404)
    rows = load_reservations()
    if not rows:
        return redirect(url_for('admin', token=request.args.get('token')))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in rows:
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
            row['status_updated'] = now_str

    remaining, archived = archive_old_reservations(rows)
    save_reservations(remaining)
    append_archived(archived)
    return redirect(url_for('admin', token=request.args.get('token')))

@app.route('/add_manual_reservation', methods=['POST'])
def add_manual_reservation():
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not (admin_token and token == admin_token):
        return ("Not Found", 404)
    data = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nume": request.form.get('name'),
        "email": "",
        "telefon": request.form.get('phone'),
        "marca": request.form.get('car-make'),
        "model": request.form.get('car-model'),
        "serviciu": request.form.get('service'),
        "data_pref": request.form.get('date'),
        "ora_pref": request.form.get('time'),
        "status": "Confirmat",
        "status_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    rows = load_reservations()
    rows.append(data)
    save_reservations(rows)
    return redirect(url_for('admin', token=request.args.get('token')))

@app.route('/api/services', methods=['POST'])
def api_add_service():
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not (admin_token and token == admin_token):
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    services = load_services()
    
    # Check if service ID already exists
    if any(s['id'] == data['id'] for s in services):
        return jsonify({"error": "Service ID already exists"}), 400
    
    new_service = {
        "id": data['id'],
        "name": data['name'],
        "duration": int(data['duration']),
        "price": float(data.get('price', 0)),
        "description": data.get('description', '')
    }
    
    services.append(new_service)
    save_services(services)
    
    return jsonify(new_service)

@app.route('/api/services/<service_id>', methods=['DELETE'])
def api_delete_service(service_id):
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not (admin_token and token == admin_token):
        return jsonify({"error": "Unauthorized"}), 403
    
    services = load_services()
    services = [s for s in services if s['id'] != service_id]
    save_services(services)
    
    return jsonify({"success": True})

@app.route('/api/services/<service_id>/price', methods=['PUT'])
def api_update_service_price(service_id):
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not (admin_token and token == admin_token):
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    new_price = data.get('price', 0)
    
    services = load_services()
    for service in services:
        if service['id'] == service_id:
            service['price'] = float(new_price)
            break
    
    save_services(services)
    return jsonify({"success": True})

@app.route('/api/reservations/updates')
def api_reservations_updates():
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not (admin_token and token == admin_token):
        return jsonify({"error": "Unauthorized"}), 403
    
    reservations = load_reservations()
    remaining, archived = archive_old_reservations(reservations)
    if archived or len(remaining) != len(reservations):
        save_reservations(remaining)
        append_archived(archived)
    reservations = remaining
    
    # Get services for name resolution
    services = load_services()
    
    # Count pending reservations
    pending_count = sum(1 for res in reservations if res.get('status') == 'In asteptare')
    
    # Get latest reservation timestamp for comparison
    latest_timestamp = max([res.get('timestamp', '') for res in reservations]) if reservations else ''
    
    return jsonify({
        "pending_count": pending_count,
        "total_count": len(reservations),
        "latest_timestamp": latest_timestamp,
        "reservations": reservations,
        "services": services
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
