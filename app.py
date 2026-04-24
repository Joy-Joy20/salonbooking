import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from supabase import create_client
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "salon_secret_key")

SERVICE_CATALOG = [
    {
        "category": "Hair Services",
        "icon": "✂️",
        "items": [
            {"name": "Haircut", "price": "₱150", "description": "Professional haircut and styling for all hair types.", "image": "/static/images/haircut.jpg", "placeholder": "Haircut"},
            {"name": "Hair Color", "price": "₱500", "description": "Vibrant hair coloring with premium color products.", "image": "/static/images/hair-color.jpg", "placeholder": "Hair+Color"},
            {"name": "Rebonding", "price": "₱1,200", "description": "Smooth and straighten your hair with long-lasting rebonding treatment.", "image": "/static/images/rebonding.jpg", "placeholder": "Rebonding"},
            {"name": "Keratin Treatment", "price": "₱1,500", "description": "Restore shine and eliminate frizz with keratin treatment.", "image": "/static/images/keratin.jpg", "placeholder": "Keratin+Treatment"},
            {"name": "Hot Oil", "price": "₱200", "description": "Deep conditioning hot oil treatment for healthy, shiny hair.", "image": "/static/images/hot-oil.jpg", "placeholder": "Hot+Oil"},
        ]
    },
    {
        "category": "Nail Services",
        "icon": "💅",
        "items": [
            {"name": "Manicure", "price": "₱80", "description": "Classic manicure with nail shaping, cuticle care, and polish.", "image": "/static/images/manicure.jpg", "placeholder": "Manicure"},
            {"name": "Pedicure", "price": "₱100", "description": "Relaxing pedicure with foot soak, nail care, and polish.", "image": "/static/images/pedicure.jpg", "placeholder": "Pedicure"},
            {"name": "Nail Art", "price": "₱250", "description": "Creative nail art designs customized to your style.", "image": "/static/images/nail-art.jpg", "placeholder": "Nail+Art"},
            {"name": "Gel Polish", "price": "₱350", "description": "Long-lasting gel polish that stays chip-free for weeks.", "image": "/static/images/gel-polish.jpg", "placeholder": "Gel+Polish"},
            {"name": "Nail Extension", "price": "₱600", "description": "Beautiful nail extensions for your desired length and shape.", "image": "/static/images/nail-extension.jpg", "placeholder": "Nail+Extension"},
        ]
    },
    {
        "category": "Spa & Wellness",
        "icon": "🌿",
        "items": [
            {"name": "Swedish Massage", "price": "₱500", "description": "Full body relaxation massage using gentle Swedish techniques.", "image": "/static/images/swedish.jpg", "placeholder": "Swedish+Massage"},
            {"name": "Deep Tissue", "price": "₱600", "description": "Targets deep muscle tension and chronic pain relief.", "image": "/static/images/deep-tissue.jpg", "placeholder": "Deep+Tissue"},
            {"name": "Foot Massage", "price": "₱300", "description": "Soothing foot massage to relieve tiredness and stress.", "image": "/static/images/foot-massage.jpg", "placeholder": "Foot+Massage"},
            {"name": "Facial", "price": "₱400", "description": "Deep cleansing facial for glowing, healthy skin.", "image": "/static/images/facial.jpg", "placeholder": "Facial"},
            {"name": "Body Scrub", "price": "₱550", "description": "Exfoliating body scrub for smooth, refreshed skin.", "image": "/static/images/body-scrub.jpg", "placeholder": "Body+Scrub"},
        ]
    }
]

MAIL_USER = os.environ.get('MAIL_USERNAME', '')
if not MAIL_USER:
    print("=== WARNING: MAIL_USERNAME not found in env, checking .env file ===")
    try:
        from dotenv import dotenv_values
        env_vals = dotenv_values(os.path.join(os.path.dirname(__file__), '.env'))
        MAIL_USER = env_vals.get('MAIL_USERNAME', '')
        os.environ['MAIL_PASSWORD'] = env_vals.get('MAIL_PASSWORD', '')
        print(f"=== Loaded from .env directly: MAIL_USER={MAIL_USER or 'STILL NOT SET'} ===")
    except Exception as env_err:
        print(f"=== .env load error: {env_err} ===")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = MAIL_USER
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = ('Salon Booking', MAIL_USER)

print(f"=== MAIL CONFIG: MAIL_USER={MAIL_USER or 'NOT SET'} ===")

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

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
    return render_template('index.html', stylists=_get_stylists(), services=SERVICE_CATALOG, current_user=_get_current_user())

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
                session['user_id'] = user.get('id')
                session['user_email'] = user.get('email', '')
                session['user_phone'] = user.get('phone', '')
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
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username:
            error = 'Username is required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif '@' not in email or '.' not in email.split('@')[-1]:
            error = 'Please enter a valid email address.'
        else:
            try:
                existing_user = supabase.table("users").select("id").eq("username", username).execute()
                if existing_user.data:
                    error = 'Username already exists.'
                else:
                    existing_email = supabase.table("users").select("id").eq("email", email).execute()
                    if existing_email.data:
                        error = 'Email already registered.'
                    else:
                        supabase.table("users").insert({
                            "username": username,
                            "email": email,
                            "password": password,
                            "role": "user"
                        }).execute()
                        success = True
                        # Welcome email — non-blocking
                        try:
                            msg = Message(subject='Welcome to Salon Booking! 🎀', sender=('Salon Booking', MAIL_USER), recipients=[email])
                            msg.html = f'<p>Hi <strong>{username}</strong>! Your account has been created. <a href="/book">Book Now</a></p>'
                            mail.send(msg)
                        except Exception:
                            pass
            except Exception as e:
                print("Signup error:", e)
                error = f'Signup failed: {str(e)}'
    return render_template('signup.html', error=error, success=success)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── USER ROUTES ──────────────────────────────────────────
@app.route('/book')
@login_required
def book():
    return redirect(url_for('index'))

@app.route('/book/appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    stylists = _get_stylists()
    selected_service = request.args.get('service', '')
    if request.method == 'POST':
        name = request.form.get('name')
        service = request.form.get('service')
        stylist = request.form.get('stylist')
        date = request.form.get('date')
        time = request.form.get('time') or None
        payment_method = request.form.get('payment_method', 'Cash')
        gcash_ref = request.form.get('gcash_ref') or None
        service_type = request.form.get('service_type', 'Salon Visit')
        address = request.form.get('address') or None
        gcash_screenshot = None

        if service_type == 'Home Service' and not address:
            flash('Address is required for Home Service bookings.', 'error')
            return redirect(url_for('book_appointment', service=service))

        # Upload screenshot to Supabase Storage
        screenshot_file = request.files.get('gcash_screenshot')
        if screenshot_file and screenshot_file.filename:
            try:
                file_bytes = screenshot_file.read()
                file_name = f"gcash_{session.get('user')}_{screenshot_file.filename}"
                supabase.storage.from_('gcash-screenshots').upload(
                    file_name, file_bytes,
                    {'content-type': screenshot_file.content_type, 'upsert': 'true'}
                )
                gcash_screenshot = supabase.storage.from_('gcash-screenshots').get_public_url(file_name)
            except Exception as upload_err:
                print("Screenshot upload error:", upload_err)

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
                "gcash_screenshot": gcash_screenshot,
                "service_type": service_type,
                "address": address,
                "booked_by": session.get('user')
            }).execute()
            print("Insert result:", result)
            flash('Booking submitted successfully!', 'success')
        except Exception as e:
            print("Insert error details:", str(e))
            flash(f'Booking failed: {str(e)}', 'error')
        return redirect(url_for('bookings_page'))
    return render_template('book_appointment.html', stylists=stylists, selected_service=selected_service)

@app.route('/bookings/create', methods=['POST'])
@login_required
def create_booking():
    current_user = _get_current_user()
    service = request.form.get('service')
    stylist = request.form.get('stylist')
    date = request.form.get('date')
    time = request.form.get('time') or None
    payment_method = request.form.get('payment_method', 'Cash')
    service_type = request.form.get('service_type', 'Salon Visit')
    address = request.form.get('address') or None
    redirect_target = request.form.get('redirect_to') or url_for('index')

    if not current_user:
        flash('Please log in before booking.', 'error')
        return redirect(url_for('login'))

    if service_type == 'Home Service' and not address:
        flash('Address is required for Home Service bookings.', 'error')
        return redirect(redirect_target)

    booking_payload = {
        "user_id": current_user.get('id'),
        "name": current_user.get('name'),
        "service": service,
        "stylist": stylist,
        "date": date,
        "time": time,
        "status": "Pending",
        "payment_method": payment_method,
        "service_type": service_type,
        "address": address,
        "booked_by": session.get('user')
    }

    try:
        supabase.table("bookings").insert(booking_payload).execute()
        flash('Booking submitted successfully!', 'success')
    except Exception as e:
        print("Create booking error:", e)
        fallback_payload = dict(booking_payload)
        fallback_payload.pop("user_id", None)
        try:
            supabase.table("bookings").insert(fallback_payload).execute()
            flash('Booking submitted successfully!', 'success')
        except Exception as inner_err:
            print("Create booking fallback error:", inner_err)
            flash('Booking failed. Please try again.', 'error')

    return redirect(redirect_target)

@app.route('/bookings')
@login_required
def bookings_page():
    bookings = []
    try:
        if session.get('user_id'):
            response = supabase.table("bookings").select("*").eq("user_id", session.get('user_id')).execute()
            bookings = response.data or []
            if not bookings:
                response = supabase.table("bookings").select("*").eq("booked_by", session.get('user')).execute()
        else:
            response = supabase.table("bookings").select("*").eq("booked_by", session.get('user')).execute()
        bookings = response.data or []
    except Exception as e:
        print("Fetch error:", e)
    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        query = supabase.table("bookings").update({"status": "Cancelled"}).eq("id", booking_id)
        if session.get('user_id'):
            query = query.eq("user_id", session.get('user_id'))
        else:
            query = query.eq("booked_by", session.get('user'))
        query.execute()
    except Exception as e:
        print("Cancel error:", e)
    return redirect(url_for('bookings_page'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    current_user = _get_current_user()
    if not current_user:
        flash('Unable to load your profile right now.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()

        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('profile.html', current_user=current_user)

        payload = {"username": name, "email": email, "phone": phone}

        try:
            supabase.table("users").update(payload).eq("id", current_user.get('id')).execute()
        except Exception as e:
            print("Profile update with phone failed:", e)
            fallback_payload = {"username": name, "email": email}
            try:
                supabase.table("users").update(fallback_payload).eq("id", current_user.get('id')).execute()
            except Exception as inner_err:
                print("Profile update fallback failed:", inner_err)
                flash('Failed to update profile.', 'error')
                return render_template('profile.html', current_user=current_user)

        if name != session.get('user'):
            try:
                supabase.table("bookings").update({"booked_by": name, "name": name}).eq("booked_by", session.get('user')).execute()
            except Exception as booking_update_err:
                print("Booking name sync error:", booking_update_err)

        session['user'] = name
        session['user_email'] = email
        session['user_phone'] = phone
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', current_user=current_user)

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

def _get_current_user():
    if not session.get('user'):
        return None

    current_user = {
        "id": session.get('user_id'),
        "name": session.get('user', ''),
        "email": session.get('user_email', ''),
        "phone": session.get('user_phone', '')
    }

    if not supabase:
        return current_user

    try:
        if current_user["id"]:
            res = supabase.table("users").select("*").eq("id", current_user["id"]).execute()
        else:
            res = supabase.table("users").select("*").eq("username", session.get('user')).execute()

        if res.data:
            user = res.data[0]
            session['user_id'] = user.get('id')
            session['user'] = user.get('username', session.get('user'))
            session['user_email'] = user.get('email', '')
            session['user_phone'] = user.get('phone', '')
            current_user = {
                "id": user.get('id'),
                "name": user.get('username', ''),
                "email": user.get('email', ''),
                "phone": user.get('phone', '')
            }
    except Exception as e:
        print("Current user fetch error:", e)

    return current_user

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

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not MAIL_USER:
            flash('Email service is not configured. Contact the admin.', 'error')
            return redirect(url_for('forgot_password'))

        try:
            result = supabase.table('users').select('id').eq('email', email).execute()
            if not result.data:
                flash('No account found with that email.', 'error')
                return redirect(url_for('forgot_password'))

            token = s.dumps(email, salt='password-reset')
            reset_link = url_for('reset_password', token=token, _external=True)

            msg = Message(
                subject='🔐 Salon Booking — Password Reset',
                sender=('Salon Booking', MAIL_USER),
                recipients=[email]
            )
            msg.html = f'''
            <div style="font-family:Poppins,sans-serif;max-width:480px;margin:0 auto;padding:2rem;background:#fff;border-radius:16px;border:1px solid #fce4f0;">
              <h2 style="color:#e91e8c;text-align:center;">🎀 Salon Booking</h2>
              <p style="color:#333;font-size:14px;">We received a request to reset your password.</p>
              <p style="color:#333;font-size:14px;">Click the button below. This link expires in <strong>1 hour</strong>.</p>
              <div style="text-align:center;margin:1.5rem 0;">
                <a href="{reset_link}" style="background:linear-gradient(135deg,#e91e8c,#ff6eb4);color:#fff;padding:12px 32px;border-radius:999px;text-decoration:none;font-weight:700;font-size:14px;">Reset Password 🔑</a>
              </div>
              <p style="color:#888;font-size:12px;">If you didn't request this, ignore this email.</p>
              <hr style="border:none;border-top:1px solid #fce4f0;margin:1rem 0;">
              <p style="color:#aaa;font-size:11px;text-align:center;">© 2025 Salon Booking</p>
            </div>'''

            print(f"=== Sending reset email to: {email} ===")
            mail.send(msg)
            print("=== Email sent successfully ===")
            flash('Password reset link sent! Check your inbox. 📧', 'success')

        except Exception as e:
            print("=== MAIL ERROR ===")
            print(str(e))
            print("==================")
            flash(f'Failed to send email: {str(e)}', 'error')

        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)
    except Exception:
        flash('Reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html', token=token)
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        try:
            supabase.table('users').update({'password': password}).eq('email', email).execute()
            flash('Password reset successful! You can now log in. ✅', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print('Reset error:', e)
            flash('Failed to reset password. Try again.', 'error')
    return render_template('reset_password.html', token=token)

if __name__ == "__main__":
    app.run(debug=True)
