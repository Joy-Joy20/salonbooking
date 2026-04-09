from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'salon_secret_key'

bookings = []
users = {}
stylists = [
    {"name": "Anna Cruz", "specialty": "Haircut & Styling"},
    {"name": "Maria Santos", "specialty": "Makeup Artist"},
    {"name": "Jose Reyes", "specialty": "Shaving & Grooming"},
    {"name": "Liza Gomez", "specialty": "Hair Coloring"},
    {"name": "Carlo Bautista", "specialty": "Hair Treatment"},
    {"name": "Rosa Dela Cruz", "specialty": "Massage Therapist"},
]
ADMIN_USER = 'admin'
ADMIN_PASS = 'admin123'


# 🏠 Home
@app.route('/')
def index():
    return render_template('index.html')


# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USER and password == ADMIN_PASS:
            session['user'] = username
            session['is_admin'] = True
            return redirect(url_for('admin'))

        elif username in users and users[username] == password:
            session['user'] = username
            session['is_admin'] = False
            return redirect(url_for('index'))

        error = 'Invalid username or password.'

    return render_template('login.html', error=error)


# 📝 Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = False

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if username in users:
            error = 'Username already exists.'
        elif password != confirm:
            error = 'Passwords do not match.'
        else:
            users[username] = password
            success = True

    return render_template('signup.html', error=error, success=success)


# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# 👑 Admin Dashboard
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('admin.html', bookings=bookings, users=users, stylists=stylists)


# ❌ Delete Booking (Supabase)
@app.route('/admin/delete-booking/<int:index>')
def delete_booking(index):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    if 0 <= index < len(bookings):
        bookings.pop(index)
    return redirect(url_for('admin'))


# ❌ Delete User (local)
@app.route('/admin/delete-user/<username>')
def delete_user(username):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    users.pop(username, None)
    return redirect(url_for('admin'))


# ➕ Add Stylist
@app.route('/admin/add-stylist', methods=['POST'])
def add_stylist():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    name = request.form.get('name')
    specialty = request.form.get('specialty')

    stylists.append({"name": name, "specialty": specialty})
    return redirect(url_for('admin'))


# ❌ Delete Stylist
@app.route('/admin/delete-stylist/<int:index>')
def delete_stylist(index):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    if 0 <= index < len(stylists):
        stylists.pop(index)

    return redirect(url_for('admin'))


# 📅 Book Appointment
@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('name')
        service = request.form.get('service')
        stylist = request.form.get('stylist')
        date = request.form.get('date')
        bookings.append({"name": name, "service": service, "stylist": stylist, "date": date})
        return redirect(url_for('bookings_page'))
    return render_template('book.html', stylists=stylists)


# 📋 View Bookings
@app.route('/bookings')
def bookings_page():
    return render_template('bookings.html', bookings=bookings)


# 💇 Stylists Page
@app.route('/stylist')
def stylist():
    return render_template('stylist.html', stylists=stylists)


# ℹ️ About
@app.route('/about')
def about():
    return render_template('about.html')


# 📞 Contact
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    message_sent = False

    if request.method == 'POST':
        message_sent = True

    return render_template('contact.html', message_sent=message_sent)


if __name__ == "__main__":
    app.run(debug=True)