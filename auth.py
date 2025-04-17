from flask import Blueprint, request, jsonify, session, redirect, url_for
from db_config import get_connection
from generate_hash import hash_password, verify_password
from datetime import datetime

auth = Blueprint('auth', __name__)

# Registration Route
@auth.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400

        hashed = hash_password(password)

        # Fix: Make phone = None if empty
        if not phone:
            phone = None

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (email, phone, password_hash, role, registered_on) VALUES (%s, %s, %s, %s, %s)",
            (email, phone, hashed, "patient", datetime.now())
        )
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"message": "Registration successful!"})

    except Exception as e:
        print("Register error:", e)
        return jsonify({"message": "Server error"}), 500

# Login Route
@auth.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        login_id = data.get("login_id")
        password = data.get("password")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT user_id, email, phone, password_hash, role FROM users WHERE email = %s OR phone = %s",
            (login_id, login_id)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and verify_password(password, user[3]):
            session["user_id"] = user[0]
            session["role"] = user[4]

            # If patient had clicked Book Appointment before login
            pending_doctor_id = session.pop("pending_doctor_id", None)
            if pending_doctor_id:
                return jsonify({"message": "Login successful!", "redirect": f"/quick_book/{pending_doctor_id}", "role": user[4]})
            else:
                return jsonify({"message": "Login successful!", "redirect": "/dashboard", "role": user[4]})

        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        print("Login error:", e)
        return jsonify({"message": "Server error"}), 500

# Logout Route
@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.auth_page'))
