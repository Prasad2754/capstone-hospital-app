from flask import Blueprint, request, jsonify, session
import bcrypt
from db_config import get_connection
import re

auth = Blueprint("auth", __name__)

def is_strong_password(password):
    return (
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(not c.isalnum() for c in password)
    )

@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not (email or phone) or not password:
        return jsonify({"message": "Email or phone and password required"}), 400

    if not is_strong_password(password):
        return jsonify({"message": "Password must be 8+ chars, include 1 uppercase and 1 symbol"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s OR phone = %s", (email, phone))
        if cur.fetchone():
            return jsonify({"message": "User already exists"}), 409

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur.execute(
            "INSERT INTO users (email, phone, password_hash, role) VALUES (%s, %s, %s, %s)",
            (email, phone, hashed_pw, "patient")
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Registration successful!"}), 201

    except Exception as e:
        print("Register error:", e)
        return jsonify({"message": "Server error", "error": str(e)}), 500

@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    login_id = data.get("login_id")
    password = data.get("password")

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, email, phone, password_hash, role FROM users WHERE email = %s OR phone = %s",
            (login_id, login_id)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session["user_id"] = user[0]
            session["role"] = user[4]
            return jsonify({
                "message": "Login successful!",
                "user_id": user[0],
                "role": user[4]
            })
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        print("Login error:", e)
        return jsonify({"message": "Server error", "error": str(e)}), 500

@auth.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200
