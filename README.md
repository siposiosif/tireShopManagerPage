🛠️ Vulcanizare Sofronea - Management System
A professional, lightweight web application built with Python (Flask) designed for automotive tire service centers. This system streamlines the booking process for customers and provides a secure management portal for business owners to handle appointments.

🌟 Key Features
Customer Booking Engine: A responsive landing page and reservation form where clients can book 30-minute service slots.

Dynamic Scheduling: Real-time availability checks that prevent double-booking by filtering taken slots from a CSV database.

Secure Admin Panel: A protected management area accessible only via authenticated login (Session-based tokens/cookies).

Manual Entry Support: Allows staff to manually add appointments received via phone calls to keep the schedule synchronized.

Automated Email Notifications: Sends professional HTML confirmation or rejection emails to customers using SMTP.

Calendar & Maps Integration: Confirmed appointments include a direct Google Calendar invitation link and a Google Maps location link.

💻 Tech Stack
Backend: Python 3.x, Flask.

Production Server: Waitress.

Frontend: HTML5, CSS3 (Modern Dark Theme), Vanilla JavaScript.

Data Storage: CSV (Flat-file database).

Security: Flask Sessions, Environment Variables (.env).

🚀 Quick Setup
Clone the repository:

Bash

git clone https://github.com/your-username/vulcanizare-sofronea.git
cd vulcanizare-sofronea
Install dependencies:

Bash

pip install flask python-dotenv waitress
Configure Environment: Create a .env file in the root directory and add:

Fragment de cod

ADMIN_USER=admin
ADMIN_PASS=your_secure_password
SECRET_KEY=your_random_secret_key
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_16_char_app_password
Run with Waitress:

Bash

waitress-serve --port=8000 App:app
