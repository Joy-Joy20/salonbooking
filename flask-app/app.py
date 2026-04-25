import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client
from datetime import timedelta
import hashlib

# LOGGING
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "salon_secret_key_2024")
app.permanent_session_lifetime = timedelta(days=7)

# SUPABASE CONNECTION
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hwioziwrdfmcaszzjwuf.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3aW96aXdyZGZtY2Fzenpqd3VmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzUwNDYsImV4cCI6MjA5MTMxMTA0Nn0.nzyewOx7vx-QFpULO3-2yp2X8Kqe0VR2mub3x_MoWrQ")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_KEY is missing!")
    supabase = None
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase connected successfully.")
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        supabase = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

SERVICES = [
    {"name": "HAIRCUT", "icon": "✂️"},
    {"name": "MAKEUP", "icon": "💄"},
    {"name": "SHAVING", "icon": "🪒"},
    {"name": "HAIR COLORING", "icon": "🎨"},
    {"name": "HAIR TREATMENT", "icon": "🍼"},
    {"name": "MASSAGE", "icon": "💆"},
]

STYLISTS = [
    {"name": "Joy", "role": "Hair Stylist", "photo": "stylist1.jpg"},
    {"name": "Jilly", "role": "Makeup Artist", "photo": "stylist2.jpg"},
    {"name": "Jenny", "role": "Barber", "photo": "stylist3.jpg"},
    {"name": "Charis", "role": "Shaver", "photo": "stylist4.jpg"},
    {"name": "Mae Pearl", "role": "Massage Therapist", "photo": "stylist5.jpg"},
    {"name": "Denziel", "role": "Hair Treatment", "photo": "stylist6.jpg"},
]

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        logger.debug(f"Login attempt for email: {email}")

        if not email or not password:
            error = "Please fill in all fields."
            return render_template("login.html", error=error)

        if supabase is None:
            error = "Database connection error. Please try again later."
            return render_template("login.html", error=error)

        try:
            hashed = hash_password(password)
            res = supabase.table("users").select("*").eq("email", email).eq("password", hashed).execute()
            logger.debug(f"Login query result: {res.data}")

            if res.data:
                session.permanent = True
                session["user"] = res.data[0]
                logger.info(f"User logged in: {email}")
                return redirect(url_for("services"))
            else:
                error = "Invalid email or password."
                logger.warning(f"Failed login for: {email}")
        except Exception as e:
            logger.error(f"Login error: {e}")
            error = f"Login failed: {str(e)}"

    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        birthday = request.form.get("birthday", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirmPassword", "")

        logger.debug(f"Signup attempt for email: {email}")

        if not all([name, phone, gender, email, address, birthday, password, confirm]):
            error = "Please fill in all fields."
            return render_template("signup.html", error=error)

        if password != confirm:
            error = "Passwords do not match."
            return render_template("signup.html", error=error)

        if len(password) < 6:
            error = "Password must be at least 6 characters."
            return render_template("signup.html", error=error)

        if supabase is None:
            error = "Database connection error. Please try again later."
            return render_template("signup.html", error=error)

        try:
            existing = supabase.table("users").select("id").eq("email", email).execute()
            logger.debug(f"Existing user check: {existing.data}")

            if existing.data:
                error = "Email already exists. Please login instead."
                return render_template("signup.html", error=error)

            hashed = hash_password(password)
            supabase.table("users").insert({
                "name": name,
                "phone": phone,
                "gender": gender,
                "email": email,
                "address": address,
                "birthday": birthday,
                "password": hashed
            }).execute()

            logger.info(f"New user created: {email}")

            res = supabase.table("users").select("*").eq("email", email).execute()
            session.permanent = True
            session["user"] = res.data[0]
            return redirect(url_for("services"))

        except Exception as e:
            logger.error(f"Signup error: {e}")
            error = f"Signup failed: {str(e)}"

    return render_template("signup.html", error=error)

@app.route("/services", methods=["GET", "POST"])
def services():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        session["selected_service"] = request.form.get("service")
        return redirect(url_for("stylist"))
    return render_template("services.html", services=SERVICES)

@app.route("/stylist", methods=["GET", "POST"])
def stylist():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        session["selected_stylist"] = request.form.get("stylist")
        return redirect(url_for("booking"))
    return render_template("stylist.html", stylists=STYLISTS)

@app.route("/booking", methods=["GET", "POST"])
def booking():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            supabase.table("bookings").insert({
                "name": session["user"]["name"],
                "phone": session["user"]["phone"],
                "email": session["user"]["email"],
                "service": session["selected_service"],
                "stylist": session["selected_stylist"],
                "date": request.form.get("date"),
                "time": request.form.get("time"),
            }).execute()
            session["booking_date"] = request.form.get("date")
            session["booking_time"] = request.form.get("time")
            logger.info(f"Booking created for {session['user']['email']}")
            return "", 200
        except Exception as e:
            logger.error(f"Booking error: {e}")
            return str(e), 500
    return render_template("booking.html",
        service=session.get("selected_service"),
        stylist=session.get("selected_stylist"),
        user=session["user"]
    )

@app.route("/confirmation")
def confirmation():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("confirmation.html",
        service=session.get("selected_service"),
        stylist=session.get("selected_stylist"),
        date=session.get("booking_date"),
        time=session.get("booking_time"),
        user=session["user"]
    )

@app.route("/my-bookings")
def my_bookings():
    if "user" not in session:
        return redirect(url_for("login"))
    try:
        res = supabase.table("bookings").select("*").eq("email", session["user"]["email"]).execute()
        return render_template("my_bookings.html", bookings=res.data)
    except Exception as e:
        logger.error(f"My bookings error: {e}")
        return render_template("my_bookings.html", bookings=[])

@app.route("/cancel-booking/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if "user" not in session:
        return redirect(url_for("login"))
    try:
        supabase.table("bookings").delete().eq("id", booking_id).execute()
        logger.info(f"Booking {booking_id} cancelled.")
    except Exception as e:
        logger.error(f"Cancel booking error: {e}")
    return redirect(url_for("my_bookings"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
