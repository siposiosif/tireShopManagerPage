# Vulcanizare Sofronea – Online Reservation System

A simple **Flask-based web application** for managing service reservations for an auto vulcanization business. Customers can request appointments online, while admins can confirm or reject reservations and automatically notify customers by email.

---

## 🚀 Features

- Online reservation form (date & time selection)
- Dynamic availability checking (prevents double booking)
- Admin dashboard for managing reservations
- Email notifications for confirmation or rejection
- Google Calendar event link generation
- CSV-based storage (no database required)
- Environment variable support for sensitive data

---

## 🛠️ Tech Stack

- **Python 3**
- **Flask**
- **HTML / Jinja2 templates**
- **CSV** for data storage
- **SMTP (Gmail)** for email notifications
- **python-dotenv** for environment variables

---

## 📁 Project Structure

```
.
├── App.py                 # Main Flask application
├── reservations.csv       # Reservation storage (auto-generated)
├── templates/
│   ├── index.html
│   ├── rezervation.html
│   └── admin.html
├── static/                # CSS / JS / assets (if any)
├── .env                   # Environment variables (not committed)
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install flask python-dotenv
```

### 4. Configure environment variables
Create a `.env` file in the project root:

```env
SECRET_KEY=your_secret_key
EMAIL_USER=your_gmail_address@gmail.com
EMAIL_PASS=your_gmail_app_password
```

> ⚠️ **Important:** Use a Gmail *App Password*, not your regular Gmail password.

---

## ▶️ Running the Application

```bash
python App.py
```

The app will be available at:
```
http://127.0.0.1:5000
```

---

## 🌐 Routes Overview

| Route | Description |
|------|------------|
| `/` | Home page |
| `/rezervation` | Reservation form |
| `/get_slots` | Fetch unavailable time slots (AJAX) |
| `/submit_reservation` | Submit reservation (POST) |
| `/admin` | Admin dashboard |
| `/update_status/<id>/<action>` | Confirm or reject reservation |

---

## 📧 Email Notifications

- **Confirmed reservations** receive:
  - Confirmation email
  - Google Calendar event link

- **Rejected reservations** receive:
  - Cancellation email

Emails are sent automatically via Gmail SMTP.

---

## 🧾 Data Storage

All reservations are stored in:
```
reservations.csv
```

Fields:
- id
- timestamp
- nume
- email
- telefon
- marca
- model
- serviciu
- data_pref
- ora_pref
- status

---

## 🔒 Security Notes

- Do **not** commit your `.env` file
- Restrict `/admin` route or protect it with authentication for production use
- This app is intended for **small businesses / local use**

---

## 📌 Future Improvements

- Authentication for admin panel
- Database integration (SQLite / PostgreSQL)
- SMS notifications
- Multi-language support
- Deployment with Docker

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

Developed for **Vulcanizare Sofronea** 🚗

Feel free to fork, improve, and adapt this project.

