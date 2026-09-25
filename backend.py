from datetime import datetime, date
import os
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

backend = Flask(__name__)

# ---------------------------------------------------------------------------
# DATABASE CONFIG (Supports SQLite fallback + MySQL connection)
# ---------------------------------------------------------------------------
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "dbms")

if DB_USER and DB_PASSWORD:
    backend.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    # Default to local SQLite DB so app works instantly out-of-the-box
    db_path = os.path.join(backend.root_path, "bloodline.db")
    backend.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

backend.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
backend.secret_key = os.environ.get("SECRET_KEY") or uuid.uuid4().hex
backend.config["SESSION_COOKIE_HTTPONLY"] = True
backend.config["SESSION_COOKIE_SAMESITE"] = "Lax"
backend.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
DEMO_ADMIN_PASSWORD = os.environ.get("DEMO_ADMIN_PASSWORD") or uuid.uuid4().hex
DEMO_DONOR_PASSWORD = os.environ.get("DEMO_DONOR_PASSWORD") or uuid.uuid4().hex

db = SQLAlchemy(backend)


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS & DECORATORS
# ---------------------------------------------------------------------------

def generate_custom_id(prefix="ID"):
    """Generates clean auto ID if user leaves ID input empty (e.g., ADM-8F12)"""
    return f"{prefix}-{uuid.uuid4().hex[:5].upper()}"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this section.", "error")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in with Administrator credentials.", "error")
            return redirect(url_for("login", next=request.url))
        if session.get("role") != "admin":
            flash("Access denied. Administrator privileges required.", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


@backend.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        # Check Admin table first, then Donor table
        admin = Admin.query.filter_by(admin_id=user_id).first()
        if admin:
            g.user = {
                "id": admin.admin_id,
                "name": admin.name,
                "username": admin.username,
                "email": admin.email,
                "role": "admin"
            }
        else:
            donor = Donor.query.filter_by(donor_id=user_id).first()
            if donor:
                g.user = {
                    "id": donor.donor_id,
                    "name": donor.name,
                    "username": donor.phone_no,
                    "email": donor.email,
                    "role": "donor"
                }
            else:
                g.user = None


# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

class Admin(db.Model):
    __tablename__ = "admin"

    admin_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    phone_no = db.Column(db.String(10), nullable=False)
    manages = db.Column(db.String(50), nullable=False, default="Blood Bank")
    handles = db.Column(db.String(50), nullable=False, default="Operations")

    donors = db.relationship("Donor", backref="admin", lazy=True, cascade="all, delete-orphan")
    requests = db.relationship("BloodRequest", backref="admin", lazy=True, cascade="all, delete-orphan")


class Donor(db.Model):
    __tablename__ = "donor"

    donor_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    phone_no = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    last_donation_date = db.Column(db.Date, nullable=True)
    availability = db.Column(db.String(15), nullable=False, default="available")
    password = db.Column(db.String(255), nullable=True)

    admin_id = db.Column(db.String(20), db.ForeignKey("admin.admin_id"), nullable=False)

    donations = db.relationship("Donation", backref="donor", lazy=True, cascade="all, delete-orphan")


class BloodRequest(db.Model):
    __tablename__ = "blood_request"

    request_id = db.Column(db.String(20), primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units_required = db.Column(db.Integer, nullable=False)
    hospital_name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    contact_no = db.Column(db.String(10), nullable=False)
    request_date = db.Column(db.Date, nullable=False)
    urgency = db.Column(db.String(15), nullable=False, default="normal")
    status = db.Column(db.String(20), nullable=False, default="pending")

    admin_id = db.Column(db.String(20), db.ForeignKey("admin.admin_id"), nullable=False)

    donations = db.relationship("Donation", backref="blood_request", lazy=True, cascade="all, delete-orphan")


class Donation(db.Model):
    __tablename__ = "donation"

    donation_id = db.Column(db.String(20), primary_key=True)
    blood_group = db.Column(db.String(5), nullable=False)
    donation_date = db.Column(db.Date, nullable=False)
    units = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    donor_id = db.Column(db.String(20), db.ForeignKey("donor.donor_id"), nullable=False)
    request_id = db.Column(db.String(20), db.ForeignKey("blood_request.request_id"), nullable=False)


# ---------------------------------------------------------------------------
# AUTHENTICATION ROUTES (LOGIN / REGISTER / LOGOUT / PROFILE)
# ---------------------------------------------------------------------------

@backend.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Check Admin users
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session.clear()
            session["user_id"] = admin.admin_id
            session["username"] = admin.username
            session["name"] = admin.name
            session["role"] = "admin"
            flash(f"Welcome back, Administrator {admin.name}!", "success")
            next_page = request.args.get("next")
            # Only accept local paths to prevent open-redirect attacks.
            if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
                next_page = url_for("home")
            return redirect(next_page)

        # Check Donor users
        donor = Donor.query.filter_by(phone_no=username).first()
        if donor and donor.password and check_password_hash(donor.password, password):
            session.clear()
            session["user_id"] = donor.donor_id
            session["username"] = donor.phone_no
            session["name"] = donor.name
            session["role"] = "donor"
            flash(f"Welcome back, {donor.name}!", "success")
            return redirect(url_for("home"))

        flash("Invalid username/phone number or password.", "error")

    return render_template("login.html")


@backend.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role", "donor")
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip() or None
        password = request.form.get("password", "").strip()

        if not name or not phone or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("register"))

        if role == "admin":
            username = request.form.get("username", "").strip() or phone
            if Admin.query.filter_by(username=username).first():
                flash(f"Admin username '{username}' already taken.", "error")
                return redirect(url_for("register"))

            admin_id = generate_custom_id("ADM")
            new_admin = Admin(
                admin_id=admin_id,
                name=name,
                username=username,
                email=email,
                password=generate_password_hash(password),
                phone_no=phone,
                manages=request.form.get("manages", "Blood Operations"),
                handles=request.form.get("handles", "Donations & Requests")
            )
            db.session.add(new_admin)
            db.session.commit()

            session.clear()
            session["user_id"] = new_admin.admin_id
            session["username"] = new_admin.username
            session["name"] = new_admin.name
            session["role"] = "admin"

            flash("Admin account created and logged in successfully!", "success")
            return redirect(url_for("home"))
        else:
            admin = Admin.query.first()
            if not admin:
                # Create a default system admin if none exists
                admin = Admin(
                    admin_id="ADM-SYS",
                    name="System Administrator",
                    username="system_admin",
                    password=generate_password_hash(DEMO_ADMIN_PASSWORD),
                    phone_no="0000000000",
                    manages="System",
                    handles="Default"
                )
                db.session.add(admin)
                db.session.commit()

            donor_id = generate_custom_id("DNR")
            new_donor = Donor(
                donor_id=donor_id,
                name=name,
                email=email,
                age=int(request.form.get("age", 25)),
                gender=request.form.get("gender", "other"),
                blood_group=request.form.get("bloodGroup", "O+"),
                phone_no=phone,
                city=request.form.get("city", "").strip(),
                availability=request.form.get("availability", "available"),
                password=generate_password_hash(password),
                admin_id=admin.admin_id
            )
            db.session.add(new_donor)
            db.session.commit()

            session.clear()
            session["user_id"] = new_donor.donor_id
            session["username"] = new_donor.phone_no
            session["name"] = new_donor.name
            session["role"] = "donor"

            flash("Donor profile created and logged in successfully!", "success")
            return redirect(url_for("home"))

    return render_template("register.html")


@backend.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session.get("user_id")
    role = session.get("role")

    if role == "admin":
        user_obj = Admin.query.get_or_404(user_id)
    else:
        user_obj = Donor.query.get_or_404(user_id)

    if request.method == "POST":
        user_obj.name = request.form.get("name", user_obj.name).strip()
        user_obj.phone_no = request.form.get("phone", user_obj.phone_no).strip()
        user_obj.email = request.form.get("email", "").strip() or None

        new_password = request.form.get("password", "").strip()
        if new_password:
            user_obj.password = generate_password_hash(new_password)

        if role == "admin":
            user_obj.manages = request.form.get("manages", user_obj.manages).strip()
            user_obj.handles = request.form.get("handles", user_obj.handles).strip()
        else:
            user_obj.city = request.form.get("city", user_obj.city).strip()
            user_obj.age = int(request.form.get("age", user_obj.age))
            user_obj.gender = request.form.get("gender", user_obj.gender)
            user_obj.blood_group = request.form.get("bloodGroup", user_obj.blood_group)
            user_obj.availability = request.form.get("availability", user_obj.availability)

        db.session.commit()
        session["name"] = user_obj.name
        flash("Your profile details have been updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user_obj, role=role)


@backend.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# HOME / DASHBOARD
# ---------------------------------------------------------------------------

@backend.route("/")
def home():
    stats = {
        "total_admins": Admin.query.count(),
        "total_donors": Donor.query.count(),
        "pending_requests": BloodRequest.query.filter(BloodRequest.status.in_(["pending", "in-progress"])).count(),
        "fulfilled_donations": Donation.query.count(),
    }
    recent_requests = BloodRequest.query.order_by(BloodRequest.request_date.desc()).limit(5).all()
    return render_template("home.html", stats=stats, recent_requests=recent_requests)


# ---------------------------------------------------------------------------
# ADMIN ROUTES
# ---------------------------------------------------------------------------

@backend.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_page():
    if request.method == "POST":
        admin_id = request.form.get("adminId", "").strip() or generate_custom_id("ADM")
        existing = Admin.query.get(admin_id)
        if existing:
            flash(f"Admin ID '{admin_id}' already exists.", "error")
            return redirect(url_for("admin_page"))

        username = request.form["username"].strip()
        if Admin.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already in use.", "error")
            return redirect(url_for("admin_page"))

        new_admin = Admin(
            admin_id=admin_id,
            name=request.form["name"].strip(),
            username=username,
            password=generate_password_hash(request.form["password"]),
            phone_no=request.form["phone"].strip(),
            manages=request.form.get("manages", "Donors"),
            handles=request.form.get("handles", "Approvals"),
        )
        db.session.add(new_admin)
        db.session.commit()
        flash("New Admin account created successfully!", "success")
        return redirect(url_for("admin_list"))

    suggested_id = generate_custom_id("ADM")
    return render_template("admin_form.html", suggested_id=suggested_id)


@backend.route("/admin/list")
@login_required
def admin_list():
    admins = Admin.query.all()
    return render_template("admin_list.html", admins=admins)


@backend.route("/admin/delete/<admin_id>", methods=["POST"])
@admin_required
def delete_admin(admin_id):
    if session.get("user_id") == admin_id:
        flash("You cannot delete your own logged-in admin account.", "error")
        return redirect(url_for("admin_list"))

    admin = Admin.query.get_or_404(admin_id)
    db.session.delete(admin)
    db.session.commit()
    flash(f"Admin {admin_id} deleted successfully.", "success")
    return redirect(url_for("admin_list"))


# ---------------------------------------------------------------------------
# DONOR ROUTES
# ---------------------------------------------------------------------------

@backend.route("/donor", methods=["GET", "POST"])
@login_required
def donor_page():
    if request.method == "POST":
        last_donation = request.form.get("lastDonation") or None
        if last_donation:
            try:
                last_donation = datetime.strptime(last_donation, "%Y-%m-%d").date()
            except ValueError:
                last_donation = None

        admin = Admin.query.first()
        if not admin:
            admin = Admin(
                admin_id="ADM-SYS",
                name="System Administrator",
                username="system_admin",
                password=generate_password_hash(DEMO_ADMIN_PASSWORD),
                phone_no="0000000000",
                manages="System",
                handles="Default"
            )
            db.session.add(admin)
            db.session.commit()

        donor_id = request.form.get("donorId", "").strip() or generate_custom_id("DNR")
        if Donor.query.get(donor_id):
            flash(f"Donor ID '{donor_id}' already exists.", "error")
            return redirect(url_for("donor_page"))

        phone = request.form["phone"].strip()
        new_donor = Donor(
            donor_id=donor_id,
            name=request.form["name"].strip(),
            age=int(request.form["age"]),
            gender=request.form["gender"],
            blood_group=request.form["bloodGroup"],
            phone_no=phone,
            city=request.form["city"].strip(),
            last_donation_date=last_donation,
            availability=request.form["availability"],
            password=generate_password_hash(request.form.get("password") or DEMO_DONOR_PASSWORD),
            admin_id=admin.admin_id,
        )
        db.session.add(new_donor)
        db.session.commit()
        flash("Donor registered successfully!", "success")
        return redirect(url_for("donor_list"))

    suggested_id = generate_custom_id("DNR")
    return render_template("donor_form.html", suggested_id=suggested_id)


@backend.route("/donor/list")
@login_required
def donor_list():
    query = Donor.query

    # Search and Filtering logic
    blood_group = request.args.get("blood_group")
    city = request.args.get("city")
    availability = request.args.get("availability")
    search = request.args.get("search")

    if blood_group:
        query = query.filter(Donor.blood_group == blood_group)
    if city:
        query = query.filter(Donor.city.ilike(f"%{city}%"))
    if availability:
        query = query.filter(Donor.availability == availability)
    if search:
        query = query.filter((Donor.name.ilike(f"%{search}%")) | (Donor.donor_id.ilike(f"%{search}%")))

    donors = query.all()
    return render_template("donor_list.html", donors=donors)


@backend.route("/donor/delete/<donor_id>", methods=["POST"])
@admin_required
def delete_donor(donor_id):
    donor = Donor.query.get_or_404(donor_id)
    db.session.delete(donor)
    db.session.commit()
    flash(f"Donor {donor_id} removed.", "success")
    return redirect(url_for("donor_list"))


# ---------------------------------------------------------------------------
# BLOOD REQUEST ROUTES
# ---------------------------------------------------------------------------

@backend.route("/request", methods=["GET", "POST"])
@login_required
def request_page():
    if request.method == "POST":
        admin = Admin.query.first()
        if not admin:
            admin = Admin(
                admin_id="ADM-SYS",
                name="System Administrator",
                username="system_admin",
                password=generate_password_hash(DEMO_ADMIN_PASSWORD),
                phone_no="0000000000",
                manages="System",
                handles="Default"
            )
            db.session.add(admin)
            db.session.commit()

        request_id = request.form.get("requestId", "").strip() or generate_custom_id("REQ")
        if BloodRequest.query.get(request_id):
            flash(f"Request ID '{request_id}' already exists.", "error")
            return redirect(url_for("request_page"))

        req_date = datetime.strptime(request.form["requestDate"], "%Y-%m-%d").date()

        new_request = BloodRequest(
            request_id=request_id,
            patient_name=request.form["patientName"].strip(),
            blood_group=request.form["bloodGroup"],
            units_required=int(request.form["units"]),
            hospital_name=request.form["hospitalName"].strip(),
            city=request.form["city"].strip(),
            contact_no=request.form["contactNo"].strip(),
            request_date=req_date,
            urgency=request.form["urgency"],
            status=request.form.get("status", "pending"),
            admin_id=admin.admin_id,
        )
        db.session.add(new_request)
        db.session.commit()
        flash("Blood request submitted successfully!", "success")
        return redirect(url_for("request_list"))

    suggested_id = generate_custom_id("REQ")
    today_date = date.today().strftime("%Y-%m-%d")
    return render_template("request_form.html", suggested_id=suggested_id, today_date=today_date)


@backend.route("/request/list")
@login_required
def request_list():
    query = BloodRequest.query

    blood_group = request.args.get("blood_group")
    status = request.args.get("status")
    urgency = request.args.get("urgency")
    search = request.args.get("search")

    if blood_group:
        query = query.filter(BloodRequest.blood_group == blood_group)
    if status:
        query = query.filter(BloodRequest.status == status)
    if urgency:
        query = query.filter(BloodRequest.urgency == urgency)
    if search:
        query = query.filter((BloodRequest.patient_name.ilike(f"%{search}%")) | (BloodRequest.hospital_name.ilike(f"%{search}%")))

    requests_ = query.order_by(BloodRequest.request_date.desc()).all()
    return render_template("request_list.html", requests=requests_)


@backend.route("/request/status/<request_id>/<new_status>", methods=["POST"])
@login_required
def update_request_status(request_id, new_status):
    req = BloodRequest.query.get_or_404(request_id)
    if new_status in ["pending", "in-progress", "fulfilled", "cancelled"]:
        req.status = new_status
        db.session.commit()
        flash(f"Blood Request {request_id} status updated to '{new_status}'.", "success")
    else:
        flash("Invalid status specified.", "error")
    return redirect(url_for("request_list"))


@backend.route("/request/delete/<request_id>", methods=["POST"])
@admin_required
def delete_request(request_id):
    req = BloodRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    flash(f"Blood request {request_id} deleted.", "success")
    return redirect(url_for("request_list"))


# ---------------------------------------------------------------------------
# DONATION ROUTES
# ---------------------------------------------------------------------------

@backend.route("/donation", methods=["GET", "POST"])
@login_required
def donation_page():
    if request.method == "POST":
        donor_id = request.form["donorId"]
        request_id = request.form["requestId"]
        donation_id = request.form.get("donationId", "").strip() or generate_custom_id("DON")

        if Donation.query.get(donation_id):
            flash(f"Donation ID '{donation_id}' already exists.", "error")
            return redirect(url_for("donation_page"))

        if not Donor.query.get(donor_id):
            flash(f"Donor ID '{donor_id}' does not exist.", "error")
            return redirect(url_for("donation_page"))
        if not BloodRequest.query.get(request_id):
            flash(f"Request ID '{request_id}' does not exist.", "error")
            return redirect(url_for("donation_page"))

        don_date = datetime.strptime(request.form["donationDate"], "%Y-%m-%d").date()

        new_donation = Donation(
            donation_id=donation_id,
            blood_group=request.form["bloodGroup"],
            donation_date=don_date,
            units=int(request.form["units"]),
            location=request.form["location"].strip(),
            notes=request.form.get("notes", "").strip(),
            donor_id=donor_id,
            request_id=request_id,
        )
        db.session.add(new_donation)

        # Automatically update donor last donation date & mark linked request as fulfilled
        donor = Donor.query.get(donor_id)
        donor.last_donation_date = don_date

        blood_request = BloodRequest.query.get(request_id)
        blood_request.status = "fulfilled"

        db.session.commit()
        flash("Donation recorded and linked request marked as fulfilled!", "success")
        return redirect(url_for("donation_list"))

    donors = Donor.query.filter_by(availability="available").all()
    if not donors:
        donors = Donor.query.all()
    requests_ = BloodRequest.query.filter(BloodRequest.status != "fulfilled").all()
    if not requests_:
        requests_ = BloodRequest.query.all()

    suggested_id = generate_custom_id("DON")
    today_date = date.today().strftime("%Y-%m-%d")
    return render_template("donation_form.html", donors=donors, requests=requests_, suggested_id=suggested_id, today_date=today_date)


@backend.route("/donation/list")
@login_required
def donation_list():
    donations = Donation.query.order_by(Donation.donation_date.desc()).all()
    return render_template("donation_list.html", donations=donations)


@backend.route("/donation/delete/<donation_id>", methods=["POST"])
@admin_required
def delete_donation(donation_id):
    don = Donation.query.get_or_404(donation_id)
    db.session.delete(don)
    db.session.commit()
    flash(f"Donation record {donation_id} deleted.", "success")
    return redirect(url_for("donation_list"))


# ---------------------------------------------------------------------------
# INITIAL DEMO DATA SEEDING
# ---------------------------------------------------------------------------

def seed_demo_data():
    if Admin.query.count() == 0:
        demo_admin = Admin(
            admin_id="ADM-1001",
            name="Dr. Palak Sharma",
            username="admin",
            email="palak@bloodline.org",
            password=generate_password_hash(DEMO_ADMIN_PASSWORD),
            phone_no="9876543210",
            manages="Blood Banks",
            handles="System Admin",
        )
        db.session.add(demo_admin)
        db.session.commit()

        demo_donor1 = Donor(
            donor_id="DNR-2001",
            name="Aarav Mehta",
            email="aarav@gmail.com",
            age=26,
            gender="male",
            blood_group="O+",
            phone_no="9812345678",
            city="Pune",
            last_donation_date=date(2026, 5, 12),
            availability="available",
            password=generate_password_hash(DEMO_DONOR_PASSWORD),
            admin_id=demo_admin.admin_id,
        )
        demo_donor2 = Donor(
            donor_id="DNR-2002",
            name="Ananya Roy",
            email="ananya@gmail.com",
            age=24,
            gender="female",
            blood_group="AB-",
            phone_no="9765432109",
            city="Mumbai",
            last_donation_date=date(2026, 2, 10),
            availability="available",
            password=generate_password_hash(DEMO_DONOR_PASSWORD),
            admin_id=demo_admin.admin_id,
        )
        db.session.add_all([demo_donor1, demo_donor2])

        demo_req = BloodRequest(
            request_id="REQ-3001",
            patient_name="Rohan Gupta",
            blood_group="O+",
            units_required=2,
            hospital_name="Sahyadri Specialty Hospital",
            city="Pune",
            contact_no="9543210987",
            request_date=date(2026, 9, 10),
            urgency="critical",
            status="pending",
            admin_id=demo_admin.admin_id,
        )
        db.session.add(demo_req)
        db.session.commit()

        demo_donation = Donation(
            donation_id="DON-4001",
            blood_group="O+",
            donation_date=date(2026, 9, 11),
            units=1,
            location="Sahyadri Blood Bank, Pune",
            notes="Routine blood donation drive.",
            donor_id=demo_donor1.donor_id,
            request_id=demo_req.request_id,
        )
        db.session.add(demo_donation)
        db.session.commit()


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with backend.app_context():
        db.create_all()
        seed_demo_data()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"Bloodline Connect server running on http://{host}:{port}")
    backend.run(host=host, debug=debug, port=port)