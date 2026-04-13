import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "salon_secret_key")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        print("⚠️ Supabase env vars not set.")
except Exception as e:
    print("Supabase connection error:", e)

stylists = [
    {"name": "Anna Cruz", "specialty": "Haircut & Styling"},
    {"name": "Maria Santos", "specialty": "Makeup Artist"},
    {"name": "Jose Reyes", "specialty": "Shaving & Grooming"},
    {"name": "Liza Gomez", "specialty": "Hair Coloring"},
    {"name": "Carlo Bautista", "specialty": "Hair Treatment"},
    {"name": "Rosa Dela Cruz", "specialty": "Massage Therapist"},
]

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-supabase')
def test_supabase():
    if supabase:
        return "✅ Supabase connected!"
    return "❌ Supabase NOT connected!"

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
        else:
            try:
                result = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
                if result.data:
                    session['user'] = username
                    session['is_admin'] = False
                    return redirect(url_for('index'))
                else:
                    error = 'Invalid username or password.'
            except Exception as e:
                error = 'Login failed. Try again.'
                print("Login error:", e)
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = False
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password != confirm:
            error = 'Passwords do not match.'
        else:
            try:
                existing = supabase.table("users").select("*").eq("username", username).execute()
                if existing.data:
                    error = 'Username already exists.'
                else:
                    supabase.table("users").insert({
                        "username": username,
                        "password": password
                    }).execute()
                    success = True
            except Exception as e:
                error = 'Signup failed. Try again.'
                print("Signup error:", e)
    return render_template('signup.html', error=error, success=success)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    bookings = []
    users = []
    try:
        if supabase:
            bookings = supabase.table("bookings").select("*").execute().data or []
            users = supabase.table("users").select("*").execute().data or []
    except Exception as e:
        print("Fetch error:", e)
    return render_template('admin.html', bookings=bookings, users=users, stylists=stylists)

@app.route('/admin/delete-booking/<int:id>')
def delete_booking(id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    try:
        if supabase:
            supabase.table("bookings").delete().eq("id", id).execute()
    except Exception as e:
        print("Delete error:", e)
    return redirect(url_for('admin'))

@app.route('/admin/delete-user/<username>')
def delete_user(username):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    try:
        if supabase:
            supabase.table("users").delete().eq("username", username).execute()
    except Exception as e:
        print("Delete user error:", e)
    return redirect(url_for('admin'))

@app.route('/admin/add-stylist', methods=['POST'])
def add_stylist():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    name = request.form.get('name')
    specialty = request.form.get('specialty')
    stylists.append({"name": name, "specialty": specialty})
    return redirect(url_for('admin'))

@app.route('/admin/delete-stylist/<int:index>')
def delete_stylist(index):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    if 0 <= index < len(stylists):
        stylists.pop(index)
    return redirect(url_for('admin'))

@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('name')
        service = request.form.get('service')
        stylist = request.form.get('stylist')
        date = request.form.get('date')
        time = request.form.get('time')
        try:
            if supabase:
                supabase.table("bookings").insert({
                    "name": name,
                    "service": service,
                    "stylist": stylist,
                    "date": date,
                    "time": time,
                    "booked_by": session.get('user')
                }).execute()
        except Exception as e:
            print("Insert error:", e)
        return redirect(url_for('bookings_page'))
    return render_template('book.html', stylists=stylists)

@app.route('/bookings')
def bookings_page():
    bookings = []
    try:
        if supabase:
            response = supabase.table("bookings").select("*").eq("booked_by", session.get('user')).execute()
            bookings = response.data or []
    except Exception as e:
        print("Fetch error:", e)
    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    try:
        if supabase:
            supabase.table("bookings").delete().eq("id", booking_id).execute()
    except Exception as e:
        print("Cancel error:", e)
    return redirect(url_for('bookings_page'))

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/stylist')
def stylist():
    return render_template('stylist.html', stylists=stylists)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    message_sent = False
    if request.method == 'POST':
        message_sent = True
    return render_template('contact.html', message_sent=message_sent)

if __name__ == "__main__":
    app.run(debug=True)