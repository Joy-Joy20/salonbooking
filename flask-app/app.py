from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client
import os

app = Flask(__name__)
app.secret_key = "salon_secret_key"

SUPABASE_URL = "https://hwioziwrdfmcaszzjwuf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3aW96aXdyZGZtY2Fzenpqd3VmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzUwNDYsImV4cCI6MjA5MTMxMTA0Nn0.nzyewOx7vx-QFpULO3-2yp2X8Kqe0VR2mub3x_MoWrQ"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        email = request.form.get("email")
        password = request.form.get("password")
        res = supabase.table("users").select("*").eq("email", email).eq("password", password).execute()
        if res.data:
            session["user"] = res.data[0]
            return redirect(url_for("services"))
        error = "Invalid email or password."
    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        gender = request.form.get("gender")
        email = request.form.get("email")
        address = request.form.get("address")
        birthday = request.form.get("birthday")
        password = request.form.get("password")
        confirm = request.form.get("confirmPassword")

        if password != confirm:
            error = "Passwords do not match."
            return render_template("signup.html", error=error)

        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            error = "Email already exists."
            return render_template("signup.html", error=error)

        supabase.table("users").insert({
            "name": name, "phone": phone, "gender": gender,
            "email": email, "address": address, "birthday": birthday,
            "password": password
        }).execute()

        res = supabase.table("users").select("*").eq("email", email).execute()
        session["user"] = res.data[0]
        return redirect(url_for("services"))

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
        return "", 200
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
    res = supabase.table("bookings").select("*").eq("email", session["user"]["email"]).execute()
    return render_template("my_bookings.html", bookings=res.data)

@app.route("/cancel-booking/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if "user" not in session:
        return redirect(url_for("login"))
    supabase.table("bookings").delete().eq("id", booking_id).execute()
    return redirect(url_for("my_bookings"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
