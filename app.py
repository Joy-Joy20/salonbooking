import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from supabase import create_client
from functools import wraps

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "salon_secret_key")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print("Supabase connection error:", e)

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

# ─── DECORATORS ───────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            if 'user' in session:
                return redirect(url_for('index'))
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── PUBLIC ROUTES ────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    message_sent = False
    if request.method == 'POST':
        message_sent = True
    return render_template('contact.html', message_sent=message_sent)

@app.route('/stylist')
def stylist():
    stylists = _get_stylists()
    return render_template('stylist.html', stylists=stylists)

# ─── AUTH ─────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USER and password == ADMIN_PASS:
            session['user'] = username
            session['role'] = 'admin'
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))

        try:
            result = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
            if result.data:
                user = result.data[0]
                session['user'] = username
                session['role'] = user.get('role', 'user')
                session['is_admin'] = session['role'] == 'admin'
                if session['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
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
                        "password": password,
                        "role": "user"
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

# ─── USER ROUTES ──────────────────────────────────────────
@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    stylists = _get_stylists()
    if request.method == 'POST':
        name = request.form.get('name')
        service = request.form.get('service')
        stylist = request.form.get('stylist')
        date = request.form.get('date')
        time = request.form.get('time') or None
        payment_method = request.form.get('payment_method', 'Cash')
        gcash_ref = request.form.get('gcash_ref') or None

        try:
            result = supabase.table("bookings").insert({
                "name": name,
                "service": service,
                "stylist": stylist,
                "date": date,
                "time": time,
                "status": "Pending",
                "payment_method": payment_method,
                "gcash_ref": gcash_ref,
                "booked_by": session.get('user')
            }).execute()
            print("Insert result:", result)
            flash('Booking submitted successfully!', 'success')
        except Exception as e:
            print("Insert error details:", str(e))
            flash(f'Booking failed: {str(e)}', 'error')
        return redirect(url_for('bookings_page'))
    return render_template('book.html', stylists=stylists)

@app.route('/bookings')
@login_required
def bookings_page():
    bookings = []
    try:
        response = supabase.table("bookings").select("*").eq("booked_by", session.get('user')).execute()
        bookings = response.data or []
    except Exception as e:
        print("Fetch error:", e)
    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        supabase.table("bookings").update({"status": "Cancelled"}).eq("id", booking_id).eq("booked_by", session.get('user')).execute()
    except Exception as e:
        print("Cancel error:", e)
    return redirect(url_for('bookings_page'))

# ─── ADMIN ROUTES ─────────────────────────────────────────
def _get_stylists():
    try:
        res = supabase.table("stylists").select("*").execute()
        return res.data or []
    except:
        return []

def _get_services():
    try:
        res = supabase.table("services").select("*").execute()
        return res.data or []
    except:
        return []

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    bookings, users, stylists, services = [], [], [], []
    try:
        bookings = supabase.table("bookings").select("*").execute().data or []
        users = supabase.table("users").select("*").execute().data or []
        stylists = _get_stylists()
        services = _get_services()
    except Exception as e:
        print("Dashboard fetch error:", e)
    pending = [b for b in bookings if b.get('status') == 'Pending']
    recent = sorted(bookings, key=lambda x: x.get('date',''), reverse=True)[:10]
    return render_template('admin_dashboard.html',
        total_bookings=len(bookings),
        pending_bookings=len(pending),
        total_users=len(users),
        total_stylists=len(stylists),
        recent_bookings=recent
    )

@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    bookings = []
    try:
        bookings = supabase.table("bookings").select("*").execute().data or []
    except Exception as e:
        print("Bookings fetch error:", e)
    return render_template('admin_bookings.html', bookings=bookings)

@app.route('/admin/bookings/status/<int:booking_id>', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    status = request.form.get('status')
    try:
        supabase.table("bookings").update({"status": status}).eq("id", booking_id).execute()
    except Exception as e:
        print("Status update error:", e)
    return redirect(url_for('admin_bookings'))

@app.route('/admin/bookings/delete/<int:booking_id>')
@admin_required
def admin_delete_booking(booking_id):
    try:
        supabase.table("bookings").delete().eq("id", booking_id).execute()
    except Exception as e:
        print("Delete booking error:", e)
    return redirect(url_for('admin_bookings'))

@app.route('/admin/services')
@admin_required
def admin_services():
    services = _get_services()
    return render_template('admin_services.html', services=services)

@app.route('/admin/services/add', methods=['POST'])
@admin_required
def admin_add_service():
    try:
        supabase.table("services").insert({
            "name": request.form.get('name'),
            "category": request.form.get('category'),
            "description": request.form.get('description'),
            "price": request.form.get('price')
        }).execute()
    except Exception as e:
        print("Add service error:", e)
    return redirect(url_for('admin_services'))

@app.route('/admin/services/delete/<int:service_id>')
@admin_required
def admin_delete_service(service_id):
    try:
        supabase.table("services").delete().eq("id", service_id).execute()
    except Exception as e:
        print("Delete service error:", e)
    return redirect(url_for('admin_services'))

@app.route('/admin/stylists')
@admin_required
def admin_stylists():
    stylists = _get_stylists()
    return render_template('admin_stylists.html', stylists=stylists)

@app.route('/admin/stylists/add', methods=['POST'])
@admin_required
def admin_add_stylist():
    try:
        supabase.table("stylists").insert({
            "name": request.form.get('name'),
            "specialty": request.form.get('specialty'),
            "photo": request.form.get('photo', '')
        }).execute()
    except Exception as e:
        print("Add stylist error:", e)
    return redirect(url_for('admin_stylists'))

@app.route('/admin/stylists/delete/<int:stylist_id>')
@admin_required
def admin_delete_stylist(stylist_id):
    try:
        supabase.table("stylists").delete().eq("id", stylist_id).execute()
    except Exception as e:
        print("Delete stylist error:", e)
    return redirect(url_for('admin_stylists'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = []
    try:
        users = supabase.table("users").select("*").execute().data or []
    except Exception as e:
        print("Users fetch error:", e)
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/role/<username>', methods=['POST'])
@admin_required
def admin_update_role(username):
    role = request.form.get('role')
    try:
        supabase.table("users").update({"role": role}).eq("username", username).execute()
    except Exception as e:
        print("Role update error:", e)
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<username>')
@admin_required
def admin_delete_user(username):
    try:
        supabase.table("users").delete().eq("username", username).execute()
    except Exception as e:
        print("Delete user error:", e)
    return redirect(url_for('admin_users'))

if __name__ == "__main__":
    app.run(debug=True)
