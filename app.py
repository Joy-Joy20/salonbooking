from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Temporary in-memory storage (no database)
bookings = []

# Home
@app.route('/')
def index():
    return render_template('index.html')

# Book Appointment
@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        name = request.form.get('name')
        service = request.form.get('service')
        date = request.form.get('date')

        bookings.append({
            "name": name,
            "service": service,
            "date": date
        })

        return redirect(url_for('bookings_page'))

    return render_template('book.html')

# View Bookings
@app.route('/bookings')
def bookings_page():
    return render_template('bookings.html', bookings=bookings)


# IMPORTANT: This is needed for deployment
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)