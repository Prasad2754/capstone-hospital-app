from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_cors import CORS
from flask_session import Session
from auth import auth
from db_config import get_connection
import random
from datetime import date

# Create Flask app (IMPORTANT: must be named 'app')
app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

CORS(app)
app.register_blueprint(auth)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/auth")
def auth_page():
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth_page"))

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COALESCE(email, phone) FROM users WHERE user_id = %s", (session["user_id"],))
        user_identity = cur.fetchone()[0]

        cur.execute("""
            SELECT d.name, a.date, a.time_slot, d.hospital_address
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.patient_name = %s
        """, (user_identity,))
        appointments = cur.fetchall()

        cur.execute("SELECT DISTINCT region FROM doctors")
        regions = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        appt_data = [{
            "doctor_name": row[0],
            "date": row[1],
            "time_slot": row[2],
            "hospital_address": row[3]
        } for row in appointments]

        return render_template("dashboard.html", patient_name=user_identity, appointments=appt_data, regions=regions)

    except Exception as e:
        print("Dashboard error:", e)
        return "Error loading dashboard", 500

@app.route("/doctors")
def doctors_page():
    return render_template("doctors.html")

@app.route("/get_doctors_list")
def get_doctors_list():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT doctor_id, name, specialty, hospital_address FROM doctors")
        doctors = cur.fetchall()

        doctor_list = []
        for doc in doctors:
            doctor_list.append({
                "doctor_id": doc[0],
                "name": doc[1],
                "specialty": doc[2],
                "hospital_address": doc[3],
                "morning": True,
                "afternoon": False,
                "evening": True,
                "wait_time": random.choice([15, 30, 45])
            })

        cur.close()
        conn.close()

        return jsonify(doctor_list)

    except Exception as e:
        print("Doctors list fetch error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/quick_book/<int:doctor_id>")
def quick_book(doctor_id):
    if "user_id" not in session:
        session["pending_doctor_id"] = doctor_id  # Save pending booking
        return redirect(url_for('auth_page'))

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COALESCE(email, phone) FROM users WHERE user_id = %s", (session["user_id"],))
        patient_name = cur.fetchone()[0]

        today = date.today().strftime("%Y-%m-%d")
        time_slot = "morning"

        cur.execute("""
            INSERT INTO appointments (doctor_id, patient_name, date, time_slot)
            VALUES (%s, %s, %s, %s)
        """, (doctor_id, patient_name, today, time_slot))
        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for('dashboard'))

    except Exception as e:
        print("Quick book error:", e)
        return "Error booking appointment", 500

# IMPORTANT: Do NOT run app.run(debug=True) here on Render
# Render will automatically use gunicorn
