from flask import Blueprint, request, session, redirect, url_for, jsonify
from db_config import get_connection
from generate_hash import hash_password, verify_password

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["POST"])
def register():
    try:
        # Getting data from the request (JSON)
        data = request.get_json()
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")
        
        # Validation: If neither email nor phone is provided, return error
        if not email and not phone:
            return jsonify({"message": "Email or Phone is required!"}), 400
        
        # Connect to the database
        conn = get_connection()
        cur = conn.cursor()

        # Check if the email already exists
        if email:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({"message": "Email already registered!"}), 400

        # Check if the phone already exists
        if phone:
            cur.execute("SELECT * FROM users WHERE phone = %s", (phone,))
            if cur.fetchone():
                return jsonify({"message": "Phone number already registered!"}), 400

        # Hash the password before inserting
        hashed = hash_password(password)

        # Insert user into the database
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
        # Getting data from the request (JSON)
        data = request.get_json()
        login_id = data.get("login_id")  # email or phone
        password = data.get("password")

        # Connect to the database
        conn = get_connection()
        cur = conn.cursor()

        # Query to check if user exists (using email or phone)
        cur.execute("SELECT user_id, email, phone, password_hash, role FROM users WHERE email = %s OR phone = %s",
                    (login_id, login_id))
        user = cur.fetchone()

        # Close the database connection
        cur.close()
        conn.close()

        # If the user exists and the password is correct
        if user and verify_password(password, user[3]):
            session["user_id"] = user[0]  # Store user ID in session
            session["role"] = user[4]  # Store user role in session

            # ✅ If there was a pending doctor appointment to book
            pending_doctor_id = session.pop("pending_doctor_id", None)
            if pending_doctor_id:
                # Redirect to the quick booking page
                return jsonify({"message": "Login successful!", "redirect": f"/quick_book/{pending_doctor_id}"})

            # If user is admin, return admin role
            if user[4].lower() == "admin":
                return jsonify({"message": "Login successful!", "role": "admin"})
            else:
                # Otherwise, return patient role
                return jsonify({"message": "Login successful!", "role": "patient"})
        else:
            # If credentials are invalid
            return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        # Handle any exceptions (e.g., DB errors, etc.)
        print("Login error:", e)
        return jsonify({"message": "Server error"}), 500


@auth.route("/logout")
def logout():
    session.clear()  # Clear session data
    return redirect(url_for("auth_page"))  # Redirect to the login page
