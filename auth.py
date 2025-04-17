from flask import Blueprint, request, session, redirect, url_for, jsonify
from db_config import get_connection
from generate_hash import hash_password, verify_password

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")

        if not email and not phone:
            return jsonify({"message": "Email or Phone is required!"}), 400

        hashed = hash_password(password)

        conn = get_connection()
        cur = conn.cursor()

        # Insert depending if phone is provided or not
        if phone:
            cur.execute("INSERT INTO users (email, phone, password_hash, role) VALUES (%s, %s, %s, %s)",
                        (email, phone, hashed, "patient"))
        else:
            cur.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
                        (email, hashed, "patient"))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Registration successful!"})

    except Exception as e:
        print("Register error:", e)
        return jsonify({"message": "Server error"}), 500

@auth.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        login_id = data.get("login_id")  # email or phone
        password = data.get("password")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT user_id, email, phone, password_hash, role FROM users WHERE email = %s OR phone = %s",
                    (login_id, login_id))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and verify_password(password, user[3]):
            session["user_id"] = user[0]
            session["role"] = user[4]

            # ✅ If there was a pending doctor appointment to book
            pending_doctor_id = session.pop("pending_doctor_id", None)
            if pending_doctor_id:
                return jsonify({"message": "Login successful!", "redirect": f"/quick_book/{pending_doctor_id}"})

            if user[4].lower() == "admin":
                return jsonify({"message": "Login successful!", "role": "admin"})
            else:
                return jsonify({"message": "Login successful!", "role": "patient"})
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        print("Login error:", e)
        return jsonify({"message": "Server error"}), 500

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth_page"))
