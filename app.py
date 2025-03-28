from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_cors import CORS
from flask_session import Session
from auth import auth
from db_config import get_connection
import boto3

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

CORS(app)
app.register_blueprint(auth)

# Email notification function using AWS SES
def send_email_notification(to_email, doctor_name, date, time_slot, hospital_address):
    ses = boto3.client('ses', region_name='us-east-1')
    ses.send_email(
        Source="gollabhavaniprasad@gmail.com",
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": "Thank you for booking your appointment!"},
            "Body": {
                "Text": {
                    "Data": f"""
Hello,

Thank you for booking your appointment!

✅ Doctor: Dr. {doctor_name}
📅 Date: {date}
🕒 Time: {time_slot}
🏥 Hospital: {hospital_address}

Please arrive 10 minutes early and bring your ID.

Regards,  
Capstone Regional Hospital
                    """
                }
            }
        }
    )

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/auth")
def auth_page():
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))

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

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT role, COALESCE(email, phone) FROM users WHERE user_id = %s", (session["user_id"],))
        role, admin_name = cur.fetchone()

        if role != "admin":
            return "Access Denied", 403

        cur.execute("SELECT email, phone, role, registered_on FROM users")
        users = cur.fetchall()
        user_list = [{"email": u[0], "phone": u[1], "role": u[2], "registered_on": u[3]} for u in users]

        cur.execute("""
            SELECT a.patient_name, d.name, a.date, a.time_slot, d.hospital_address
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
        """)
        appointments = cur.fetchall()
        appt_list = [{
            "patient_name": a[0],
            "doctor_name": a[1],
            "date": a[2],
            "time_slot": a[3],
            "hospital_address": a[4]
        } for a in appointments]

        cur.close()
        conn.close()

        return render_template("admin_dashboard.html", admin_name=admin_name, users=user_list, appointments=appt_list)

    except Exception as e:
        print("Admin dashboard error:", e)
        return "Error loading admin dashboard", 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/get_doctors", methods=["POST"])
def get_doctors():
    data = request.get_json()
    region = data.get("region")
    problem = data.get("problem")

    problem_specialty_map = {
        "heart": "Cardiologist",
        "bone": "Orthopedic",
        "skin": "Dermatologist",
        "brain": "Neurologist",
        "kids": "Pediatrician",
        "mental": "Psychiatrist",
        "general": "General Physician",
        "ear": "ENT"
    }

    specialty = problem_specialty_map.get(problem.lower(), problem)

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT doctor_id, name FROM doctors
            WHERE region = %s AND LOWER(specialty) LIKE %s
        """, (region, f"%{specialty.lower()}%"))
        doctors = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify([{"id": d[0], "name": d[1]} for d in doctors])
    except Exception as e:
        print("Doctor fetch error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    data = request.get_json()
    doctor_id = data.get("doctor_id")
    time_slot = data.get("time_slot")
    date = data.get("date")
    patient_name = data.get("patient_name")

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO appointments (doctor_id, patient_name, date, time_slot)
            VALUES (%s, %s, %s, %s)
        """, (doctor_id, patient_name, date, time_slot))
        conn.commit()

        cur.execute("""
            SELECT d.name, d.hospital_address FROM doctors d WHERE d.doctor_id = %s
        """, (doctor_id,))
        doctor_info = cur.fetchone()

        cur.execute("SELECT email FROM users WHERE COALESCE(email, phone) = %s", (patient_name,))
        user_email = cur.fetchone()[0] if cur.rowcount > 0 else None

        cur.close()
        conn.close()

        if user_email:
            send_email_notification(user_email, doctor_info[0], date, time_slot, doctor_info[1])

        return jsonify({"message": "Appointment booked successfully!"})

    except Exception as e:
        print("Booking error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
