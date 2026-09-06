import os
from datetime import date, datetime, timedelta
from functools import wraps
from urllib.parse import quote

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from models import Camp, Donor, User, db


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "blood-connect-prototype-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'database.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_TIME_LIMIT"] = None

os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
db.init_app(app)
CSRFProtect(app)

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
STATUSES = ["Available", "Temporarily Unavailable", "Contacted", "Inactive"]


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please sign in to access the admin workspace.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def next_donor_id():
    latest = Donor.query.order_by(Donor.id.desc()).first()
    return f"BD{10001 + (latest.id if latest else 0):05d}"


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def google_maps_url(camp):
    return f"https://www.google.com/maps/search/?api=1&query={camp.latitude},{camp.longitude}"


@app.context_processor
def inject_globals():
    return {"blood_groups": BLOOD_GROUPS, "statuses": STATUSES, "today": date.today()}


@app.route("/")
def index():
    upcoming = Camp.query.filter(Camp.date >= date.today()).order_by(Camp.date, Camp.start_time).limit(3).all()
    return render_template("index.html", upcoming=upcoming)


@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():
    if request.method == "POST":
        required = ["name", "age", "gender", "blood_group", "phone", "email", "city", "address", "availability_status"]
        if any(not request.form.get(field, "").strip() for field in required):
            flash("Please complete every required field.", "danger")
            return render_template("donor_register.html")
        try:
            age = int(request.form["age"])
            if age < 18 or age > 65:
                raise ValueError
            if request.form["blood_group"] not in BLOOD_GROUPS or request.form["availability_status"] not in STATUSES:
                raise ValueError
            donor = Donor(
                donor_id=next_donor_id(), name=request.form["name"].strip(), age=age,
                gender=request.form["gender"], blood_group=request.form["blood_group"],
                phone=request.form["phone"].strip(), email=request.form["email"].strip(),
                city=request.form["city"].strip(), address=request.form["address"].strip(),
                last_donation_date=parse_date(request.form.get("last_donation_date")),
                availability_status=request.form["availability_status"],
            )
            db.session.add(donor)
            db.session.commit()
            return render_template("donor_success.html", donor=donor)
        except (ValueError, TypeError):
            flash("Please check the form values. Donors must be between 18 and 65 years old.", "danger")
    return render_template("donor_register.html")


@app.route("/seeker", methods=["GET", "POST"])
def seeker():
    donor = None
    if request.method == "POST":
        donor_id = request.form.get("donor_id", "").strip().upper()
        if not donor_id.startswith("BD"):
            flash("Enter the Donor ID provided by our organization, for example BD10001.", "warning")
        else:
            donor = Donor.query.filter_by(donor_id=donor_id).first()
            if not donor:
                flash("We could not verify that Donor ID. Please contact the organization.", "danger")
    return render_template("seeker.html", donor=donor)


@app.route("/camps")
def camps():
    all_camps = Camp.query.filter(Camp.date >= date.today()).order_by(Camp.date, Camp.start_time).all()
    return render_template("camps.html", camps=all_camps, maps_url=google_maps_url)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session.clear()
            session["admin_id"] = user.id
            session["admin_username"] = user.username
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def dashboard():
    blood_stats = {group: Donor.query.filter_by(blood_group=group).count() for group in BLOOD_GROUPS}
    donors_query = Donor.query.order_by(Donor.created_at.desc())
    selected_group = request.args.get("blood_group", "")
    donor_search = request.args.get("donor_id", "").strip()
    if selected_group:
        donors_query = donors_query.filter_by(blood_group=selected_group)
    if donor_search:
        donors_query = donors_query.filter(Donor.donor_id.ilike(f"%{donor_search}%"))
    return render_template(
        "admin_dashboard.html", donors=donors_query.all(), camps=Camp.query.order_by(Camp.date).all(),
        total_donors=Donor.query.count(), available_donors=Donor.query.filter_by(availability_status="Available").count(),
        unavailable_donors=Donor.query.filter_by(availability_status="Temporarily Unavailable").count(),
        total_camps=Camp.query.count(), upcoming_camps=Camp.query.filter(Camp.date >= date.today()).count(),
        blood_stats=blood_stats, selected_group=selected_group, donor_search=donor_search,
    )


@app.route("/admin/donor/<int:donor_id>/status", methods=["POST"])
@admin_required
def update_donor_status(donor_id):
    donor = Donor.query.get_or_404(donor_id)
    status = request.form.get("availability_status")
    if status in STATUSES:
        donor.availability_status = status
        db.session.commit()
        flash(f"{donor.donor_id} status updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin/camp/new", methods=["GET", "POST"])
@app.route("/admin/camp/<int:camp_id>/edit", methods=["GET", "POST"])
@admin_required
def camp_form(camp_id=None):
    camp = Camp.query.get_or_404(camp_id) if camp_id else None
    if request.method == "POST":
        try:
            values = {
                "camp_name": request.form["camp_name"].strip(), "organizer_name": request.form["organizer_name"].strip(),
                "date": parse_date(request.form["date"]), "start_time": request.form["start_time"],
                "end_time": request.form["end_time"], "blood_groups_needed": request.form["blood_groups_needed"].strip(),
                "address": request.form["address"].strip(), "city": request.form["city"].strip(),
                "latitude": float(request.form["latitude"]), "longitude": float(request.form["longitude"]),
                "contact_number": request.form["contact_number"].strip(), "description": request.form["description"].strip(),
            }
            if not all(values.values()) or not (-90 <= values["latitude"] <= 90 and -180 <= values["longitude"] <= 180):
                raise ValueError
            if camp:
                for key, value in values.items():
                    setattr(camp, key, value)
                message = "Camp details updated."
            else:
                db.session.add(Camp(**values))
                message = "New camp published."
            db.session.commit()
            flash(message, "success")
            return redirect(url_for("dashboard"))
        except (KeyError, ValueError, TypeError):
            flash("Please check every camp field, including valid coordinates.", "danger")
    return render_template("add_camp.html", camp=camp)


@app.post("/admin/camp/<int:camp_id>/delete")
@admin_required
def delete_camp(camp_id):
    camp = Camp.query.get_or_404(camp_id)
    db.session.delete(camp)
    db.session.commit()
    flash("Camp removed from the public listing.", "success")
    return redirect(url_for("dashboard"))


def seed_database():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password_hash=generate_password_hash("BloodConnect@123")))
        if Camp.query.count() == 0:
            db.session.add_all([
                Camp(camp_name="City Hospital Community Drive", organizer_name="City Hospital", date=date.today() + timedelta(days=7), start_time="09:00", end_time="15:00", blood_groups_needed="O+, O-, A+, B+", address="14 Civic Centre Road", city="New Delhi", latitude=28.6139, longitude=77.2090, contact_number="+91 98765 43210", description="A welcoming weekend drive with free health screening for every donor."),
                Camp(camp_name="Red Cross Youth Camp", organizer_name="Indian Red Cross Society", date=date.today() + timedelta(days=14), start_time="10:00", end_time="16:00", blood_groups_needed="All blood groups", address="Community Hall, Lake View Avenue", city="Bengaluru", latitude=12.9716, longitude=77.5946, contact_number="+91 91234 56789", description="Join local students and volunteers for an energetic community donation day."),
            ])
        if Donor.query.count() == 0:
            db.session.add(Donor(donor_id="BD10001", name="Aarav Mehta", age=28, gender="Male", blood_group="O+", phone="+91 90000 11111", email="aarav@example.com", city="New Delhi", address="Available with organization verification", availability_status="Available"))
        db.session.commit()


with app.app_context():
    seed_database()


if __name__ == "__main__":
    app.run(debug=True)
