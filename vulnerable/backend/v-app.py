from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from email.message import EmailMessage
import sqlite3
import os
import secrets
import smtplib
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "faculty.db"
)

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

OTP_EXPIRY_SECONDS = 300
MAX_OTP_ATTEMPTS = 5

otp_storage = {}


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


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


def send_otp_email(receiver_email, otp):

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise RuntimeError("Email configuration is missing.")

    message = EmailMessage()

    message["Subject"] = "Hridya University | Faculty Password Reset OTP"
    message["From"] = MAIL_USERNAME
    message["To"] = receiver_email

    message.set_content(
        f"""HRIDYA UNIVERSITY
Faculty Security Lab
================================

PASSWORD RESET REQUEST

Hello Faculty,

We received a request to reset the password
associated with your faculty account.

Your verification code is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset,
you can safely ignore this email.

For your security, do not share this OTP
with anyone.

Regards,
Hridya University
Faculty Security Lab
"""
    )

    message.add_alternative(
        f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f4;
                     font-family:Arial,sans-serif;color:#222;">
            <div style="max-width:600px;margin:40px auto;background:#ffffff;
                        border:1px solid #ddd;border-radius:10px;
                        overflow:hidden;">

                <div style="background:#171717;color:#ffffff;
                            padding:24px 30px;">
                    <div style="font-size:13px;letter-spacing:2px;
                                color:#bbbbbb;">
                        HRIDYA UNIVERSITY
                    </div>

                    <div style="font-size:22px;font-weight:bold;
                                margin-top:8px;">
                        Faculty Security Lab
                    </div>
                </div>

                <div style="padding:30px;">

                    <h2 style="margin-top:0;">
                        Password Reset Request
                    </h2>

                    <p>
                        Hello Faculty,
                    </p>

                    <p>
                        We received a request to reset the password
                        associated with your faculty account.
                    </p>

                    <p>
                        Your verification code is:
                    </p>

                    <div style="margin:25px 0;padding:18px;
                                background:#f3f3f3;border-radius:8px;
                                text-align:center;font-size:32px;
                                font-weight:bold;letter-spacing:8px;">
                        {otp}
                    </div>

                    <p>
                        <strong>This OTP is valid for 5 minutes.</strong>
                    </p>

                    <p style="color:#666;">
                        If you did not request a password reset,
                        you can safely ignore this email.
                    </p>

                    <p style="color:#666;">
                        For your security, do not share this OTP
                        with anyone.
                    </p>

                    <hr style="border:none;border-top:1px solid #eee;
                               margin:30px 0;">

                    <p style="font-size:13px;color:#888;">
                        Hridya University<br>
                        Faculty Security Lab
                    </p>

                </div>
            </div>
        </body>
        </html>
        """,
        subtype="html"
    )

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(message)


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Faculty Security Lab Backend"
    })


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

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


@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json() or {}

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

    email = email.strip().lower()

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


@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json() or {}

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
        SELECT id, email, full_name
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

    otp = str(secrets.randbelow(900000) + 100000)

    otp_storage[email] = {
        "otp": otp,
        "verified": False,
        "created_at": time.time(),
        "attempts": 0
    }

    try:
        send_otp_email(email, otp)

    except Exception as error:
        otp_storage.pop(email, None)

        print("OTP email failed:", error)

        return jsonify({
            "success": False,
            "message": "Unable to send OTP email."
        }), 500

    return jsonify({
        "success": True,
        "message": "OTP has been sent to your registered email."
    }), 200


@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():

    data = request.get_json() or {}

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

    if time.time() - stored_data["created_at"] > OTP_EXPIRY_SECONDS:
        del otp_storage[email]

        return jsonify({
            "success": False,
            "message": "OTP has expired. Please request a new OTP."
        }), 401

    if stored_data["attempts"] >= MAX_OTP_ATTEMPTS:
        del otp_storage[email]

        return jsonify({
            "success": False,
            "message": "Too many incorrect attempts. Please request a new OTP."
        }), 429

    if not secrets.compare_digest(stored_data["otp"], otp):
        stored_data["attempts"] += 1

        remaining = MAX_OTP_ATTEMPTS - stored_data["attempts"]

        return jsonify({
            "success": False,
            "message": f"Invalid OTP. {remaining} attempt(s) remaining."
        }), 401

    stored_data["verified"] = True

    return jsonify({
        "success": True,
        "message": "OTP verified successfully."
    }), 200


@app.route("/api/reset-password", methods=["POST"])
def reset_password():

    data = request.get_json() or {}

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

    stored_data = otp_storage[email]

    if time.time() - stored_data["created_at"] > OTP_EXPIRY_SECONDS:
        del otp_storage[email]

        return jsonify({
            "success": False,
            "message": "OTP verification has expired. Please request a new OTP."
        }), 403

    if not stored_data["verified"]:
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


if __name__ == "__main__":

    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )