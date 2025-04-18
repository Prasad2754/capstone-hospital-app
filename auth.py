from flask import Blueprint, request, jsonify, session, redirect, url_for
import bcrypt
from db_config import get_connection

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    login_id = data.get("login_id")
    password = data.get("password")

    if not login_id or not password:
        return jsonify({"message": "Missing fields"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT user_id, email, phone, password_hash, role FROM users WHERE email = %s OR phone = %s", (login_id, login_id))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session["user_id"] = user[0]
            session["user_role"] = user[4]

            # ✅ Check if there is a pending doctor booking
            if session.get("pending_doctor_id"):
                pending_id = session.pop("pending_doctor_id")
                return redirect(url_for('quick_book', doctor_id=pending_id))

            return jsonify({"message": "Login successful!", "role": user[4]})
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        print("Login error:", e)
        return jsonify({"message": "Server error"}), 500

@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Missing fields"}), 400

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            conn.close()
            return jsonify({"message": "Email already registered"}), 409

        cur.execute("""
            INSERT INTO users (email, phone, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (email, phone, hashed_pw, "patient"))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"message": "Registration successful!"})

    except Exception as e:
        print("Register error:", e)
        return jsonify({"message": "Server error"}), 500

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth_page'))
