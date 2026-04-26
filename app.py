# -*- coding: utf-8 -*-
import os
import traceback
import hashlib
import uuid
from datetime import datetime
from functools import wraps

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'salon-secret-key')

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin123')

SERVICES = [
    {
        "category": "Hair Services",
        "icon": "\u2702\ufe0f",
        "key": "hair",
        "items": [
            {"name": "Haircut - Children", "description": "Clean cut for kids below 12", "duration": "30 mins", "price": 150},
            {"name": "Haircut - Men", "description": "Classic and modern cuts for men", "duration": "30 mins", "price": 200},
            {"name": "Haircut - Women", "description": "Stylish cuts tailored for women", "duration": "45 mins", "price": 300},
            {"name": "Hair Color - Full", "description": "Full hair coloring service", "duration": "2 hrs", "price": 500},
            {"name": "Highlights / Balayage", "description": "Dimensional color for a natural look", "duration": "3 hrs", "price": 1200},
            {"name": "Rebonding", "description": "Smooth and straight hair treatment", "duration": "4 hrs", "price": 1800},
            {"name": "Keratin Treatment", "description": "Frizz-free silky smooth finish", "duration": "3 hrs", "price": 1500},
            {"name": "Hot Oil Treatment", "description": "Deep nourishing treatment for dry hair", "duration": "45 mins", "price": 250},
            {"name": "Deep Conditioning", "description": "Intense moisture repair for damaged hair", "duration": "1 hr", "price": 400}
        ]
    },
    {
        "category": "Nail Services",
        "icon": "\U0001f485",
        "key": "nails",
        "items": [
            {"name": "Manicure - Classic", "description": "Clean, shape, and polish for hands", "duration": "30 mins", "price": 150},
            {"name": "Pedicure - Classic", "description": "Clean, shape, and polish for feet", "duration": "45 mins", "price": 180},
            {"name": "Gel Polish - Hands", "description": "Long-lasting gel color for hands", "duration": "1 hr", "price": 300},
            {"name": "Gel Polish - Feet", "description": "Long-lasting gel color for feet", "duration": "1 hr", "price": 350},
            {"name": "Nail Art", "description": "Creative designs on any nail shape", "duration": "1.5 hrs", "price": 400},
            {"name": "Nail Extension", "description": "Acrylic or gel nail extensions", "duration": "2 hrs", "price": 600},
            {"name": "Nail Repair", "description": "Fix broken or damaged nails", "duration": "20 mins", "price": 100}
        ]
    },
    {
        "category": "Spa & Wellness",
        "icon": "\U0001f33f",
        "key": "spa",
        "items": [
            {"name": "Swedish Massage", "description": "Relaxing full body massage for stress relief", "duration": "60 mins", "price": 450},
            {"name": "Deep Tissue Massage", "description": "Targets deep muscle tension and pain", "duration": "60 mins", "price": 550},
            {"name": "Foot Massage", "description": "Soothing reflexology for tired feet", "duration": "45 mins", "price": 300},
            {"name": "Full Body Massage", "description": "Complete relaxation from head to toe", "duration": "90 mins", "price": 750},
            {"name": "Make-up - Everyday", "description": "Fresh and natural everyday look", "duration": "1 hr", "price": 500},
            {"name": "Make-up - Special Occasion", "description": "Glam look for events and parties", "duration": "1.5 hrs", "price": 800},
            {"name": "Bridal Make-up", "description": "Full glam for your special day", "duration": "2 hrs", "price": 1500},
            {"name": "Face Shave", "description": "Clean and smooth face shave", "duration": "20 mins", "price": 150},
            {"name": "Beard Trim & Shaping", "description": "Neat and styled beard grooming", "duration": "30 mins", "price": 200}
        ]
    }
]


def get_supabase():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if not url or not key:
        raise Exception('Missing SUPABASE_URL or SUPABASE_KEY')
    return create_client(url, key)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(input_password, hashed_password):
    if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$'):
        try:
            import bcrypt
            return bcrypt.checkpw(input_password.encode(), hashed_password.encode())
        except Exception:
            return False
    return hash_password(input_password) == hashed_password



def get_unread_count():
    try:
        db = get_supabase()
        result = db.table('messages').select('id').eq('status', 'unread').execute()
        return len(result.data or [])
    except Exception:
        return 0

def get_stylists():
    try:
        db = get_supabase()
        res = db.table('stylists').select('*').execute()
        return res.data or []
    except Exception:
        return []


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
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    return render_template('index.html',
        services=SERVICES,
        stylists=get_stylists(),
        logged_in=bool(session.get('user')),
        username=session.get('user', '')
    )


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    message_sent = False
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        print(f"=== CONTACT FORM: name={name} email={email} message={message[:50]} ===")
        try:
            if not name or not message:
                print("=== CONTACT: name or message empty, skipping save ===")
            else:
                db = get_supabase()
                result = db.table('messages').insert({
                    'sender_username': name,
                    'sender_email': email,
                    'subject': 'Contact Form Message',
                    'message': message,
                    'status': 'unread',
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                print(f"=== CONTACT SAVED: {result.data} ===")
            message_sent = True
        except Exception as e:
            print(f"=== CONTACT SAVE ERROR: {str(e)} ===")
            message_sent = True
    return render_template('contact.html', message_sent=message_sent)


@app.route('/services')
def services():
    return render_template('services.html', services=SERVICES, stylists=get_stylists())


@app.route('/stylist')
def stylist():
    return render_template('stylist.html', stylists=get_stylists())


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['user'] = username
            session['role'] = 'admin'
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        try:
            db = get_supabase()
            result = db.table('users').select('*').eq('username', username).execute()
            if result.data:
                user = result.data[0]
                if check_password(password, user.get('password', '')):
                    session['user'] = username
                    session['user_id'] = user.get('id')
                    session['user_email'] = user.get('email', '')
                    session['role'] = user.get('role', 'user')
                    session['is_admin'] = session['role'] == 'admin'
                    if session['is_admin']:
                        return redirect(url_for('admin_dashboard'))
                    return redirect(url_for('index'))
            error = 'Invalid username or password.'
        except Exception as e:
            error = f'Login failed: {str(e)}'
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
        elif not email or '@' not in email:
            error = 'Valid email is required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            try:
                db = get_supabase()
                if db.table('users').select('id').eq('username', username).execute().data:
                    error = 'Username already exists.'
                elif db.table('users').select('id').eq('email', email).execute().data:
                    error = 'Email already registered.'
                else:
                    db.table('users').insert({
                        'username': username,
                        'email': email,
                        'password': hash_password(password),
                        'role': 'user'
                    }).execute()
                    success = True
            except Exception as e:
                error = f'Signup failed: {str(e)}'
    return render_template('signup.html', error=error, success=success)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    current_username = session.get('user', '').strip()
    current_user = None
    try:
        db = get_supabase()
        if session.get('user_id'):
            result = db.table('users').select('*').eq('id', session.get('user_id')).execute()
        else:
            result = db.table('users').select('*').eq('username', current_username).execute()
        current_user = (result.data or [None])[0]
    except Exception as e:
        flash(f'Unable to load profile: {str(e)}', 'error')

    if not current_user:
        flash('Profile not found.', 'error')
        return render_template('profile.html', current_user=None, username=current_username)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        if not name or not email or '@' not in email:
            flash('Name and valid email are required.', 'error')
            return render_template('profile.html', current_user=current_user, username=current_username)
        try:
            db = get_supabase()
            db.table('users').update({'username': name, 'email': email}).eq('username', current_username).execute()
            session['user'] = name
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'Update failed: {str(e)}', 'error')

    return render_template('profile.html', current_user=current_user, username=session.get('user', ''))



@app.route('/dashboard')
@login_required
def user_dashboard():
    user = session.get('user')
    bookings = []
    try:
        db = get_supabase()
        res = db.table('bookings').select('*').eq('username', user).order('created_at', desc=True).execute()
        bookings = res.data or []
        if not bookings:
            res2 = db.table('bookings').select('*').eq('booked_by', user).execute()
            bookings = res2.data or []
    except Exception as e:
        print('Dashboard bookings error:', str(e))

    total = len(bookings)
    pending = len([b for b in bookings if (b.get('status') or '').lower() == 'pending'])
    completed = len([b for b in bookings if (b.get('status') or '').lower() in ['completed', 'confirmed']])
    recent = bookings[:5]
    upcoming = next((b for b in bookings if (b.get('status') or '').lower() == 'pending'), None)

    return render_template('user_dashboard.html',
        username=user,
        user_email=session.get('user_email', ''),
        total_bookings=total,
        pending_bookings=pending,
        completed_bookings=completed,
        recent_bookings=recent,
        upcoming_booking=upcoming
    )

@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True) or request.form
            service = data.get('service_name') or data.get('service', '')
            date = data.get('appointment_date') or data.get('date', '')
            time = data.get('appointment_time') or data.get('time', '')
            stylist = data.get('stylist', 'Any Available')
            notes = data.get('notes', '')
            payment_method = data.get('payment_method', 'Cash')
            service_type = data.get('service_type', 'Salon Visit')
            address = data.get('address', '')
            user = session.get('user')

            if not service or not date or not time:
                flash('Please fill in all required fields.', 'error')
                return redirect(url_for('index'))

            screenshot_url = ''
            gcash_file = request.files.get('gcash_screenshot')
            if gcash_file and gcash_file.filename:
                try:
                    file_bytes = gcash_file.read()
                    file_ext = gcash_file.filename.rsplit('.', 1)[-1].lower() if '.' in gcash_file.filename else 'jpg'
                    unique_filename = f"gcash_{user}_{uuid.uuid4().hex}.{file_ext}"
                    db = get_supabase()
                    db.storage.from_('gcash-payments').upload(
                        path=unique_filename,
                        file=file_bytes,
                        file_options={"content-type": gcash_file.content_type or "image/jpeg"}
                    )
                    screenshot_url = db.storage.from_('gcash-payments').get_public_url(unique_filename)
                except Exception as upload_err:
                    print(f"Screenshot upload error: {str(upload_err)}")

            booking_data = {
                'username': user,
                'booked_by': user,
                'service_name': service,
                'appointment_date': date,
                'appointment_time': time,
                'stylist': stylist,
                'notes': notes,
                'payment_method': payment_method,
                'service_type': service_type,
                'address': address,
                'payment_screenshot': screenshot_url,
                'payment_status': 'under_review' if screenshot_url else 'unpaid',
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
            print(f"=== INSERTING: {booking_data} ===")
            db = get_supabase()
            result = db.table('bookings').insert(booking_data).execute()
            print(f"=== RESULT: {result.data} ===")

            if not result.data:
                raise Exception("Insert returned no data - check Supabase table and RLS")

            if request.is_json:
                return jsonify({'success': True, 'message': 'Booking confirmed!'})
            flash('Booking submitted successfully! \u2705', 'success')
            return redirect(url_for('bookings_page'))

        except Exception as e:
            print(f"Booking error: {str(e)}")
            if request.is_json:
                return jsonify({'success': False, 'message': str(e)}), 500
            flash(f'Booking failed: {str(e)}', 'error')
            return redirect(url_for('index'))

    return redirect(url_for('index'))


@app.route('/bookings')
@login_required
def bookings_page():
    bookings = []
    try:
        db = get_supabase()
        user = session.get('user')
        res = db.table('bookings').select('*').eq('username', user).order('created_at', desc=True).execute()
        bookings = res.data or []
        if not bookings:
            res2 = db.table('bookings').select('*').eq('booked_by', user).execute()
            bookings = res2.data or []
    except Exception as e:
        print('Bookings fetch error:', str(e))
    return render_template('bookings.html', bookings=bookings)


@app.route('/cancel-booking/<booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        db = get_supabase()
        db.table('bookings').update({'status': 'Cancelled'}).eq('id', booking_id).execute()
    except Exception as e:
        print('Cancel error:', str(e))
    return redirect(url_for('bookings_page'))


@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    bookings, users, stylists = [], [], []
    try:
        db = get_supabase()
        bookings = db.table('bookings').select('*').execute().data or []
        users = db.table('users').select('*').execute().data or []
        stylists = get_stylists()
    except Exception as e:
        print('Dashboard error:', str(e))
    pending = [b for b in bookings if b.get('status') == 'pending']
    recent = sorted(bookings, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    return render_template('admin_dashboard.html',
        total_bookings=len(bookings),
        pending_bookings=len(pending),
        total_users=len(users),
        total_stylists=len(stylists),
        recent_bookings=recent,
        services=SERVICES,
        unread_count=get_unread_count()
    )


@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    bookings = []
    try:
        db = get_supabase()
        bookings = db.table('bookings').select('*').execute().data or []
    except Exception as e:
        print('Admin bookings error:', str(e))
    return render_template('admin_bookings.html', bookings=bookings, unread_count=get_unread_count())


@app.route('/admin/bookings/status/<booking_id>', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    try:
        db = get_supabase()
        db.table('bookings').update({'status': request.form.get('status')}).eq('id', booking_id).execute()
    except Exception as e:
        print('Status update error:', str(e))
    return redirect(url_for('admin_bookings'))


@app.route('/admin/bookings/delete/<booking_id>')
@admin_required
def admin_delete_booking(booking_id):
    try:
        db = get_supabase()
        db.table('bookings').delete().eq('id', booking_id).execute()
    except Exception as e:
        print('Delete booking error:', str(e))
    return redirect(url_for('admin_bookings'))


@app.route('/admin/stylists')
@admin_required
def admin_stylists():
    return render_template('admin_stylists.html', stylists=get_stylists(), unread_count=get_unread_count())


@app.route('/admin/stylists/add', methods=['POST'])
@admin_required
def admin_add_stylist():
    try:
        db = get_supabase()
        db.table('stylists').insert({
            'name': request.form.get('name'),
            'specialty': request.form.get('specialty'),
            'photo': request.form.get('photo', '')
        }).execute()
    except Exception as e:
        print('Add stylist error:', str(e))
    return redirect(url_for('admin_stylists'))


@app.route('/admin/stylists/delete/<int:stylist_id>')
@admin_required
def admin_delete_stylist(stylist_id):
    try:
        db = get_supabase()
        db.table('stylists').delete().eq('id', stylist_id).execute()
    except Exception as e:
        print('Delete stylist error:', str(e))
    return redirect(url_for('admin_stylists'))


@app.route('/admin/users')
@admin_required
def admin_users():
    users = []
    try:
        db = get_supabase()
        users = db.table('users').select('*').execute().data or []
    except Exception as e:
        print('Admin users error:', str(e))
    return render_template('admin_users.html', users=users, unread_count=get_unread_count())


@app.route('/admin/users/role/<username>', methods=['POST'])
@admin_required
def admin_update_role(username):
    try:
        db = get_supabase()
        db.table('users').update({'role': request.form.get('role')}).eq('username', username).execute()
    except Exception as e:
        print('Role update error:', str(e))
    return redirect(url_for('admin_users'))


@app.route('/admin/users/delete/<username>')
@admin_required
def admin_delete_user(username):
    try:
        db = get_supabase()
        db.table('users').delete().eq('username', username).execute()
    except Exception as e:
        print('Delete user error:', str(e))
    return redirect(url_for('admin_users'))



@app.route('/admin/services')
@admin_required
def admin_services_page():
    services_db = []
    try:
        db = get_supabase()
        result = db.table('services').select('*').order('category').execute()
        services_db = result.data or []
    except Exception as e:
        print('Services fetch error:', str(e))
    return render_template('admin_services.html',
        services=SERVICES,
        services_db=services_db,
        unread_count=get_unread_count()
    )


@app.route('/admin/messages')
@admin_required
def admin_messages():
    messages = []
    try:
        db = get_supabase()
        result = db.table('messages').select('*').order('created_at', desc=True).execute()
        messages = result.data or []
    except Exception as e:
        print('Messages error:', str(e))
    return render_template('admin_messages.html',
        messages=messages,
        unread_count=get_unread_count()
    )


@app.route('/admin/messages/reply/<message_id>', methods=['POST'])
@admin_required
def admin_reply_message(message_id):
    try:
        reply = request.form.get('reply', '').strip()
        db = get_supabase()
        db.table('messages').update({
            'reply': reply,
            'status': 'replied',
            'replied_at': datetime.utcnow().isoformat()
        }).eq('id', message_id).execute()
        flash('Reply sent!', 'success')
    except Exception as e:
        flash(f'Reply failed: {str(e)}', 'error')
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/delete/<message_id>')
@admin_required
def admin_delete_message(message_id):
    try:
        db = get_supabase()
        db.table('messages').delete().eq('id', message_id).execute()
        flash('Message deleted.', 'success')
    except Exception as e:
        flash(f'Delete failed: {str(e)}', 'error')
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/read/<message_id>')
@admin_required
def admin_mark_read(message_id):
    try:
        db = get_supabase()
        db.table('messages').update({'status': 'read'}).eq('id', message_id).execute()
    except Exception as e:
        print('Mark read error:', str(e))
    return redirect(url_for('admin_messages'))


@app.route('/admin/bookings/edit/<booking_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_booking(booking_id):
    try:
        db = get_supabase()
        if request.method == 'POST':
            db.table('bookings').update({
                'service_name': request.form.get('service_name'),
                'appointment_date': request.form.get('appointment_date'),
                'appointment_time': request.form.get('appointment_time'),
                'stylist': request.form.get('stylist'),
                'notes': request.form.get('notes'),
                'status': request.form.get('status'),
                'payment_status': request.form.get('payment_status')
            }).eq('id', booking_id).execute()
            flash('Booking updated successfully!', 'success')
            return redirect(url_for('admin_bookings'))
        result = db.table('bookings').select('*').eq('id', booking_id).execute()
        booking = result.data[0] if result.data else None
        return render_template('admin_edit_booking.html',
            booking=booking, stylists=get_stylists(),
            services=SERVICES, unread_count=get_unread_count())
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_bookings'))


@app.route('/admin/stylists/edit/<stylist_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_stylist(stylist_id):
    try:
        db = get_supabase()
        if request.method == 'POST':
            update_data = {
                'name': request.form.get('name'),
                'specialty': request.form.get('specialty'),
            }
            photo_url = request.form.get('photo_url', '').strip()
            if photo_url:
                update_data['photo'] = photo_url
            db.table('stylists').update(update_data).eq('id', stylist_id).execute()
            flash('Stylist updated!', 'success')
            return redirect(url_for('admin_stylists'))
        result = db.table('stylists').select('*').eq('id', stylist_id).execute()
        stylist = result.data[0] if result.data else None
        return render_template('admin_edit_stylist.html',
            stylist=stylist, unread_count=get_unread_count())
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_stylists'))


@app.route('/admin/users/edit/<username>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(username):
    try:
        db = get_supabase()
        if request.method == 'POST':
            update_data = {
                'username': request.form.get('username'),
                'email': request.form.get('email'),
                'role': request.form.get('role')
            }
            new_password = request.form.get('new_password', '')
            if new_password:
                update_data['password'] = hash_password(new_password)
            db.table('users').update(update_data).eq('username', username).execute()
            flash('User updated!', 'success')
            return redirect(url_for('admin_users'))
        result = db.table('users').select('*').eq('username', username).execute()
        user = result.data[0] if result.data else None
        return render_template('admin_edit_user.html',
            user=user, unread_count=get_unread_count())
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_users'))


@app.route('/admin/services/add', methods=['POST'])
@admin_required
def admin_add_service():
    try:
        db = get_supabase()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        duration = request.form.get('duration', '').strip()
        description = request.form.get('description', '').strip()
        try:
            price_int = int(float(request.form.get('price', 0)))
        except Exception:
            price_int = 0

        if not name or not category:
            flash('Service name and category are required.', 'error')
            return redirect(url_for('admin_services_page'))

        category_lower = category.lower()
        if 'hair' in category_lower:
            category_key = 'hair'
        elif 'nail' in category_lower:
            category_key = 'nails'
        else:
            category_key = 'spa'

        result = db.table('services').insert({
            'name': name,
            'category': category,
            'category_key': category_key,
            'description': description,
            'duration': duration,
            'price': price_int
        }).execute()
        print(f"Service added: {result.data}")
        flash(f'Service "{name}" added successfully!', 'success')
    except Exception as e:
        print(f"Add service error: {str(e)}")
        flash(f'Failed to add service: {str(e)}', 'error')
    return redirect(url_for('admin_services_page'))


@app.route('/admin/services/delete/<service_id>')
@admin_required
def admin_delete_service(service_id):
    try:
        db = get_supabase()
        db.table('services').delete().eq('id', service_id).execute()
        flash('Service deleted!', 'success')
    except Exception as e:
        flash(f'Delete failed: {str(e)}', 'error')
    return redirect(url_for('admin_services_page'))

@app.route('/debug')
def debug():
    return jsonify({
        "status": "ok",
        "user": session.get('user'),
        "supabase_url_set": bool(os.environ.get('SUPABASE_URL')),
        "supabase_key_set": bool(os.environ.get('SUPABASE_KEY')),
        "secret_key_set": bool(os.environ.get('SECRET_KEY'))
    })


@app.route('/test-booking')
def test_booking():
    try:
        db = get_supabase()
        result = db.table('bookings').insert({
            "username": "test_user",
            "service_name": "Test Service",
            "appointment_date": "2025-05-01",
            "appointment_time": "10:00",
            "stylist": "Any Available",
            "notes": "Test",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return jsonify({"status": "SUCCESS", "data": result.data})
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})


@app.errorhandler(500)
def internal_error(error):
    return f"<h1>500 Error</h1><pre>{traceback.format_exc()}</pre>", 500


@app.errorhandler(404)
def not_found(error):
    return f"<h1>404 Not Found</h1><pre>{str(error)}</pre>", 404


if __name__ == '__main__':
    app.run(debug=True)
