from flask import Flask, render_template, request, redirect, url_for, session
import re, sqlite3, qrcode, io, base64, time
from qrcode.image.pil import PilImage
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecret"

# --- Database setup ---
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contact TEXT NOT NULL,
            plate TEXT,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            establishment TEXT NOT NULL,
            slot TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            amount REAL NOT NULL,
            duration TEXT NOT NULL,
            timestamp TEXT,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Validation helpers ---
def valid_email(email): return re.match(r"[^@]+@[^@]+\.[^@]+", email)
def valid_contact(contact): return re.match(r"^\d{10,15}$", contact)
def valid_password(password):
    return (len(password) >= 8 and re.search(r"[A-Z]", password) and re.search(r"\d", password))

# --- Homepage ---
@app.route("/")
def index():
    establishments = {
        "SM Bataan": 50,
        "Vista Mall Bataan": 40,
        "Robinsons Galleria": 30,
        "Capitol Square": 30
    }
    return render_template("establishments.html", establishments=establishments)

# --- Slots page ---
@app.route("/slots/<est>")
def slots(est):
    establishments = {
        "SM Bataan": 50,
        "Vista Mall Bataan": 40,
        "Robinsons Galleria": 30,
        "Capitol Square": 30
    }
    if est not in establishments:
        return f"No data for {est}"
    slot_count = establishments[est]
    rows = []
    for i in range(1, (slot_count // 2) + 1):
        left_label = f"{i}st Left" if i == 1 else f"{i}th Left"
        right_label = f"{i}st Right" if i == 1 else f"{i}th Right"
        rows.append((i, left_label, right_label))
    return render_template("slots.html", establishment=est, rows=rows)

# --- Slot selection with QR ---
@app.route("/select_slot/<est>/<slot>")
def select_slot(est, slot):
    if "user" in session:
        qr_data = f"User: {session['user']} | Establishment: {est} | Slot: {slot}"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(image_factory=PilImage)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return render_template("qr.html", establishment=est, slot=slot, user=session["user"], qr_code=qr_b64)
    else:
        return redirect(url_for("login"))

# --- Payment page ---
@app.route("/payment/<est>/<slot>", methods=["GET", "POST"])
def payment(est, slot):
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        method = request.form["method"]
        amount = 50.0  # fixed price for demo
        duration = "2 hours"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        receipt_id = f"PR-{int(time.time())}"

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO reservations (user, establishment, slot, payment_method, amount, duration, timestamp, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (session["user"], est, slot, method, amount, duration, timestamp, "Pending"))
        conn.commit()
        conn.close()

        # Receipt details vary by method
        if method in ["paypal", "gcash", "maya", "gotyme"]:
            receipt = f"Paid via {method.upper()} | Contact: (from signup)"
        elif method == "card":
            name = request.form["card_name"]
            number = request.form["card_number"]
            cvv = request.form["cvv"]
            exp = request.form["exp"]
            receipt = f"Card Holder: {name} | Card: {number} | CVV: {cvv} | Exp: {exp}"
        else:  # cash
            receipt = "Cash Payment | Please pay at nearest toll booth."

        return render_template("receipt.html",
                               receipt=receipt,
                               receipt_id=receipt_id,
                               user=session["user"],
                               establishment=est,
                               slot=slot,
                               method=method,
                               amount=amount,
                               duration=duration)

    return render_template("payment.html", establishment=est, slot=slot, user=session["user"])

# --- My Reservations page ---
@app.route("/reservations")
def reservations():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, establishment, slot, payment_method, amount, duration, timestamp, status FROM reservations WHERE user=?", (session["user"],))
    rows = c.fetchall()
    conn.close()
    return render_template("reservations.html", reservations=rows, user=session["user"])

# --- Login ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Special admin login
        if email == "admin@parkright.com" and password == "adminonly01":
            session["user"] = "Admin"
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))

        if not valid_email(email):
            error = "Invalid email format"
        else:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("SELECT fullname, password, role FROM users WHERE email=?", (email,))
            row = c.fetchone()
            conn.close()

            if not row or not check_password_hash(row[1], password):
                error = "Invalid credentials"
            else:
                session["user"] = row[0]
                session["role"] = row[2]
                if row[2] == "cashier":
                    return redirect(url_for("cashier_dashboard"))
                else:
                    return render_template("success.html", message=f"Welcome back, {row[0]}!")
    return render_template("login.html", error=error)

# --- Signup ---
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        contact = request.form["contact"]
        plate = request.form["plate"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if not valid_email(email):
            error = "Invalid email format"
        elif not valid_contact(contact):
            error = "Contact number must be 10–15 digits"
        elif not valid_password(password):
            error = "Password must be 8+ chars, include uppercase and number"
        elif password != confirm:
            error = "Passwords do not match"
        else:
            try:
                conn = sqlite3.connect("users.db")
                c = conn.cursor()
                hashed_pw = generate_password_hash(password)
                c.execute("INSERT INTO users (fullname, email, contact, plate, password, role) VALUES (?, ?, ?, ?, ?, ?)",
                          (fullname, email, contact, plate, hashed_pw, "user"))
                conn.commit()
                conn.close()
                session["user"] = fullname
                session["role"] = "user"
                return render_template("success.html", message=f"Account created for {fullname}!")
            except sqlite3.IntegrityError:
                error = "Email already registered"
    return render_template("signup.html", error=error)

# --- Admin Dashboard ---
@app.route("/admin_dashboard")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT fullname, email, role FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM reservations")
    reservations = c.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", users=users, reservations=reservations)

# --- Create Cashier ---
@app.route("/create_cashier", methods=["POST"])
def create_cashier():
    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    email = request.form["email"]
    password = request.form["password"]
    hashed_pw = generate_password_hash(password)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (fullname, email, contact, plate, password, role) VALUES (?, ?, ?, ?, ?, ?)",
              ("Cashier", email, "N/A", "N/A", hashed_pw, "cashier"))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


# --- Cashier Dashboard ---
@app.route("/cashier_dashboard")
def cashier_dashboard():
    if "role" not in session or session["role"] != "cashier":
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, user, establishment, slot, payment_method, amount, duration, timestamp, status FROM reservations")
    reservations = c.fetchall()
    conn.close()

    return render_template("cashier_dashboard.html", reservations=reservations, cashier=session["user"])


# --- Update Reservation (Cashier actions) ---
@app.route("/update_reservation/<int:res_id>", methods=["POST"])
def update_reservation(res_id):
    if "role" not in session or session["role"] != "cashier":
        return redirect(url_for("login"))

    action = request.form["action"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    if action == "confirm":
        c.execute("UPDATE reservations SET status=? WHERE id=?", ("Confirmed", res_id))
    elif action == "cancel":
        c.execute("UPDATE reservations SET status=? WHERE id=?", ("Cancelled", res_id))
    conn.commit()
    conn.close()

    return redirect(url_for("cashier_dashboard"))


# --- Logout ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return render_template("success.html", message="You have been logged out.")


if __name__ == "__main__":
    app.run(debug=True)
