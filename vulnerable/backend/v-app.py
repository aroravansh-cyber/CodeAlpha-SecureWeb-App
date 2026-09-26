from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import random

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "faculty.db"
)

# Database connection
def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Create database table
def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# Temporary OTP storage
otp_storage = {}


# Home route
@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Faculty Security Lab Backend"
    })


# Login route
@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    faculty_id = data.get("faculty_id")
    password = data.get("password")

    if not faculty_id or not password:
        return jsonify({
            "success": False,
            "message": "Faculty ID and password are required."
        }), 400

    connection = get_db_connection()

    faculty = connection.execute(
        """
        SELECT * FROM faculty
        WHERE (faculty_id = ? OR email = ?)
        AND password = ?
        """,
        (faculty_id, faculty_id, password)
    ).fetchone()

    connection.close()

    if faculty:
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "faculty_id": faculty["faculty_id"],
            "full_name": faculty["full_name"],
            "department": faculty["department"],
            "designation": faculty["designation"]
        }), 200

    return jsonify({
        "success": False,
        "message": "Invalid Faculty ID or password."
    }), 401


# Registration route
@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    faculty_id = data.get("faculty_id")
    full_name = data.get("full_name")
    email = data.get("email")
    department = data.get("department")
    designation = data.get("designation")
    password = data.get("password")

    if (
        not faculty_id
        or not full_name
        or not email
        or not department
        or not designation
        or not password
    ):
        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400

    try:
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO faculty (
                faculty_id,
                full_name,
                email,
                department,
                designation,
                password
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                faculty_id,
                full_name,
                email,
                department,
                designation,
                password
            )
        )

        connection.commit()
        connection.close()

        print("New Faculty Registration:")
        print("Faculty ID:", faculty_id)
        print("Full Name:", full_name)
        print("Email:", email)
        print("Department:", department)
        print("Designation:", designation)
        print("Password:", password)

        return jsonify({
            "success": True,
            "message": "Registration saved successfully.",
            "faculty_id": faculty_id
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Faculty ID or email already exists."
        }), 409


# Forgot password - generate OTP
@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json()

    email = data.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    email = email.strip().lower()

    connection = get_db_connection()

    faculty = connection.execute(
        """
        SELECT id, email
        FROM faculty
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    connection.close()

    if not faculty:
        return jsonify({
            "success": False,
            "message": "No faculty account was found with this email."
        }), 404

    otp = str(random.randint(100000, 999999))

    otp_storage[email] = {
        "otp": otp,
        "verified": False
    }

    print("\nPASSWORD RESET OTP")
    print("Email:", email)
    print("OTP:", otp)
    print()

    return jsonify({
        "success": True,
        "message": "OTP generated successfully."
    }), 200


# Verify OTP
@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():

    data = request.get_json()

    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({
            "success": False,
            "message": "Email and OTP are required."
        }), 400

    email = email.strip().lower()
    otp = str(otp).strip()

    if email not in otp_storage:
        return jsonify({
            "success": False,
            "message": "No OTP request was found."
        }), 400

    stored_data = otp_storage[email]

    if stored_data["otp"] != otp:
        return jsonify({
            "success": False,
            "message": "Invalid OTP."
        }), 401

    otp_storage[email]["verified"] = True

    return jsonify({
        "success": True,
        "message": "OTP verified successfully."
    }), 200


# Reset password
@app.route("/api/reset-password", methods=["POST"])
def reset_password():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    email = email.strip().lower()

    if email not in otp_storage:
        return jsonify({
            "success": False,
            "message": "OTP verification is required."
        }), 403

    if not otp_storage[email]["verified"]:
        return jsonify({
            "success": False,
            "message": "Please verify the OTP first."
        }), 403

    connection = get_db_connection()

    faculty = connection.execute(
        """
        SELECT id
        FROM faculty
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    if not faculty:
        connection.close()

        return jsonify({
            "success": False,
            "message": "Faculty account not found."
        }), 404

    connection.execute(
        """
        UPDATE faculty
        SET password = ?
        WHERE email = ?
        """,
        (password, email)
    )

    connection.commit()
    connection.close()

    del otp_storage[email]

    return jsonify({
        "success": True,
        "message": "Password reset successfully."
    }), 200


# Start server
if __name__ == "__main__":

    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )