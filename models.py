from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.String(12), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(30), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(240), nullable=False)
    last_donation_date = db.Column(db.Date, nullable=True)
    availability_status = db.Column(db.String(40), nullable=False, default="Available")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Camp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camp_name = db.Column(db.String(140), nullable=False)
    organizer_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    blood_groups_needed = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(240), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    contact_number = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="admin")
