# Blood Connect

A Flask + SQLite prototype for managing private blood donors, verified blood seeker lookups, and community donation camps.

## Run locally

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Initialize the database and seed safe demo records. The app does this automatically on first run.

4. Start Flask:

   ```powershell
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in Chrome.

## Prototype access

- Admin URL: `http://127.0.0.1:5000/login`
- Username: `admin`
- Password: `BloodConnect@123`
- Demo Donor ID: `BD10001`

Change the seeded password and set a strong `SECRET_KEY` through environment variables before any real deployment.

## Features

- Private donor registration with sequential Donor IDs.
- Server-side Donor ID validation for the seeker flow. Public users cannot browse donor records.
- Password-hashed admin login with CSRF protection on forms.
- Admin-only donor status management and blood group filters.
- Admin camp creation, editing, deletion, dates, contact details, and latitude/longitude.
- Public camp cards with Google Maps links using the stored coordinates.

## Location links

Camp administrators enter a latitude and longitude. Public camp pages generate a mobile-friendly Google Maps URL in the format `https://www.google.com/maps/search/?api=1&query=LATITUDE,LONGITUDE`.

## Deployment notes

For a hosted deployment, use a production WSGI server such as Waitress or Gunicorn, provide `SECRET_KEY` and `DATABASE_URL` environment variables, turn off Flask debug mode, use HTTPS, and move SQLite to PostgreSQL if multiple administrators will be active concurrently. Add rate limiting, audit logging, email verification, and a secrets manager before handling real donor data.
