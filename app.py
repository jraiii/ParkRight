from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import qrcode, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"

# --- Database setup ---
Base = declarative_base()
engine = create_engine("sqlite:///parkright.db")  # ✅ stick with one file
Session = sessionmaker(bind=engine)
db_session = Session()

class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    available = Column(Boolean, default=True)
    tickets = relationship("Ticket", back_populates="slot")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    plate_number = Column(String)
    entry_time = Column(DateTime, default=datetime.now)
    paid = Column(Boolean, default=False)
    slot_id = Column(Integer, ForeignKey("slots.id"))
    slot = relationship("Slot", back_populates="tickets")

Base.metadata.create_all(engine)

# --- Seed default slots once ---
if db_session.query(Slot).count() == 0:
    default_slots = ["A1", "A2", "B1", "B2"]
    for name in default_slots:
        db_session.add(Slot(name=name, available=True))
    db_session.commit()
    print("Default slots seeded:", default_slots)

# --- Helper: generate QR ---
def generate_qr(ticket_id):
    qr_dir = "static/qr_codes"
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = f"{qr_dir}/ticket_{ticket_id}.png"
    if not os.path.exists(qr_path):
        qrcode.make(f"TICKET-{ticket_id}").save(qr_path)
    return qr_path

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/new_ticket", methods=["POST"])
def new_ticket():
    plate = request.form["plate"]
    ticket = Ticket(plate_number=plate)
    db_session.add(ticket)
    db_session.commit()
    session["last_ticket_id"] = ticket.id
    qr_path = generate_qr(ticket.id)
    return render_template("ticket.html", ticket=ticket, qr_file=qr_path)

@app.route("/ticket/<int:ticket_id>")
def ticket(ticket_id):
    ticket = db_session.query(Ticket).get(ticket_id)
    if ticket:
        qr_path = generate_qr(ticket.id)
        return render_template("ticket.html", ticket=ticket, qr_file=qr_path)
    return redirect(url_for("home"))

@app.route("/slots/<int:ticket_id>")
def slots(ticket_id):
    ticket = db_session.query(Ticket).get(ticket_id)
    slots = db_session.query(Slot).all()
    return render_template("slots.html", ticket=ticket, slots=slots)

@app.route("/choose_slot/<int:slot_id>/<int:ticket_id>")
def choose_slot(slot_id, ticket_id):
    slot = db_session.query(Slot).get(slot_id)
    ticket = db_session.query(Ticket).get(ticket_id)
    if slot and ticket and slot.available:
        slot.available = False
        ticket.slot = slot
        db_session.commit()
    return redirect(url_for("slots", ticket_id=ticket_id))

@app.route("/proceed/<int:ticket_id>")
def proceed(ticket_id):
    ticket = db_session.query(Ticket).get(ticket_id)
    if ticket:
        qr_path = generate_qr(ticket.id)
        return render_template("ticket.html", ticket=ticket, qr_file=qr_path)
    return redirect(url_for("home"))

@app.route("/pay/<int:ticket_id>")
def pay(ticket_id):
    ticket = db_session.query(Ticket).get(ticket_id)
    if ticket:
        ticket.paid = True
        db_session.commit()
        qr_path = generate_qr(ticket.id)
        return render_template("payment_success.html", ticket=ticket, qr_file=qr_path)
    return redirect(url_for("home"))

# --- Admin ---
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["password"] == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Invalid password")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    slots = db_session.query(Slot).all()
    tickets = db_session.query(Ticket).all()
    return render_template("dashboard.html", slots=slots, tickets=tickets)

@app.route("/admin/add_slot", methods=["POST"])
def add_slot():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    name = request.form["name"]
    slot = Slot(name=name)
    db_session.add(slot)
    db_session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/release_slot/<int:slot_id>")
def release_slot(slot_id):
    slot = db_session.query(Slot).get(slot_id)
    if slot:
        slot.available = True
        db_session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reset_tickets")
def reset_tickets():
    db_session.query(Ticket).delete()
    db_session.commit()
    return render_template("reset_success.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
