from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from email.message import EmailMessage
from email.mime.image import MIMEImage

import sqlite3
import os
import secrets
import smtplib
import time
from datetime import datetime, timedelta


load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-secret-change-this"
)

CORS(app, supports_credentials=True)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "faculty.db"
)

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

OTP_EXPIRY_SECONDS = 300
MAX_OTP_ATTEMPTS = 5

otp_storage = {}


# Database
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
            password TEXT NOT NULL,
            photo TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            photo TEXT,
            program TEXT NOT NULL,
            specialization TEXT,
            year TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            program TEXT NOT NULL,
            specialization TEXT,
            year TEXT NOT NULL,
            room TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            faculty_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
            marked_at TEXT NOT NULL,
            UNIQUE(lecture_id, student_id)
        )
    """)

    connection.commit()
    connection.close()

    seed_demo_data()


# Programs
PROGRAMS = {
    "Engineering & Technology": {
        "B.Tech Computer Science & Engineering": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Cybersecurity": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech AI & ML": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Data Science": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Information Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Electronics & Communication Engineering": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Electrical Engineering": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Mechanical Engineering": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Civil Engineering": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Biotechnology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        }
    },

    "Computer Applications & IT": {
        "BCA": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BCA Cybersecurity": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BCA AI & ML": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "B.Sc Computer Science": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "B.Sc Information Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "MCA": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        }
    },

    "Medical": {
        "MBBS": {
            "specializations": [],
            "years": [
                "1st Year",
                "2nd Year",
                "3rd Year",
                "4th Year",
                "5th Year",
                "Internship"
            ]
        },
        "BDS": {
            "specializations": [],
            "years": [
                "1st Year",
                "2nd Year",
                "3rd Year",
                "4th Year",
                "Internship"
            ]
        },
        "BAMS": {
            "specializations": [],
            "years": [
                "1st Year",
                "2nd Year",
                "3rd Year",
                "4th Year",
                "5th Year"
            ]
        },
        "BHMS": {
            "specializations": [],
            "years": [
                "1st Year",
                "2nd Year",
                "3rd Year",
                "4th Year",
                "5th Year"
            ]
        },
        "BUMS": {
            "specializations": [],
            "years": [
                "1st Year",
                "2nd Year",
                "3rd Year",
                "4th Year",
                "5th Year"
            ]
        }
    },

    "Nursing": {
        "B.Sc Nursing": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "Post Basic B.Sc Nursing": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        },
        "M.Sc Nursing": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        },
        "GNM": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "ANM": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        }
    },

    "Pharmacy": {
        "B.Pharm": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "Pharm.D": {
            "specializations": [],
            "years": [
                "1st Year",
                "2nd Year",
                "3rd Year",
                "4th Year",
                "5th Year",
                "Internship"
            ]
        },
        "D.Pharm": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        },
        "M.Pharm": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        }
    },

    "Allied Health Sciences": {
        "B.Sc Medical Laboratory Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Radiology & Imaging Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Operation Theatre Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Anesthesia Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Optometry": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Cardiac Care Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Dialysis Technology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Respiratory Therapy": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "Bachelor of Physiotherapy": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        }
    },

    "Agriculture & Forestry": {
        "B.Sc Agriculture": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Horticulture": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Sc Forestry": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "B.Tech Agricultural Engineering": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        }
    },

    "Management & Commerce": {
        "BBA": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BBA Finance": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BBA Marketing": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BBA Human Resources": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "B.Com": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "B.Com Hons.": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "M.Com": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        },
        "MBA": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        }
    },

    "Law": {
        "LLB": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA LLB": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year"]
        },
        "BBA LLB": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year"]
        },
        "LLM": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        }
    },

    "Arts & Humanities": {
        "BA": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA English": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA Psychology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA Economics": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA Sociology": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA Political Science": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA History": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        },
        "BA Journalism & Mass Communication": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year"]
        }
    },

    "Education": {
        "B.Ed": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        },
        "M.Ed": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        },
        "D.El.Ed": {
            "specializations": [],
            "years": ["1st Year", "2nd Year"]
        }
    },

    "Hospitality & Tourism": {
        "BHM": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        },
        "BTTM": {
            "specializations": [],
            "years": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        }
    }
}


# Seed demo data
def seed_demo_data():

    connection = get_db_connection()

    faculty = connection.execute(
        "SELECT faculty_id FROM faculty LIMIT 1"
    ).fetchone()

    if not faculty:
        connection.execute("""
            INSERT INTO faculty
            (faculty_id, full_name, email, department, designation, password)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "HU-FAC-001",
            "Demo Faculty",
            "faculty@hridyauniversity.edu",
            "B.Tech Cybersecurity",
            "Assistant Professor",
            "faculty123"
        ))

        connection.commit()

        faculty_id = "HU-FAC-001"

    else:
        faculty_id = faculty["faculty_id"]

    timetable_count = connection.execute(
        "SELECT COUNT(*) AS total FROM timetable WHERE faculty_id = ?",
        (faculty_id,)
    ).fetchone()["total"]

    if timetable_count == 0:

        today = datetime.now().replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0
        )

        lectures = [
            (
                faculty_id,
                "Network Security Fundamentals",
                "B.Tech Cybersecurity",
                None,
                "2nd Year",
                "LH-204",
                today,
                today + timedelta(hours=1)
            ),
            (
                faculty_id,
                "Applied Cryptography",
                "B.Tech Cybersecurity",
                None,
                "3rd Year",
                "LH-107",
                today + timedelta(hours=1, minutes=15),
                today + timedelta(hours=2, minutes=15)
            ),
            (
                faculty_id,
                "Cyber Security Lab",
                "B.Tech Cybersecurity",
                None,
                "2nd Year",
                "Lab-3",
                today + timedelta(hours=2, minutes=30),
                today + timedelta(hours=4)
            )
        ]

        for lecture in lectures:
            connection.execute("""
                INSERT INTO timetable
                (
                    faculty_id,
                    subject,
                    program,
                    specialization,
                    year,
                    room,
                    start_time,
                    end_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lecture[0],
                lecture[1],
                lecture[2],
                lecture[3],
                lecture[4],
                lecture[5],
                lecture[6].isoformat(),
                lecture[7].isoformat()
            ))

    students_count = connection.execute(
        "SELECT COUNT(*) AS total FROM students"
    ).fetchone()["total"]

    if students_count == 0:

        students = [
            ("CSECS2101", "Rahul Verma", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2102", "Sneha Patil", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2103", "Aarav Mehta", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2104", "Ishita Rao", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2105", "Kabir Singh", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2106", "Priya Nair", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2107", "Dev Kulkarni", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2108", "Ananya Iyer", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS2109", "Vivaan Joshi", "B.Tech Cybersecurity", "2nd Year"),
            ("CSECS21010", "Riya Kapoor", "B.Tech Cybersecurity", "2nd Year")
        ]

        for roll_no, name, program, year in students:
            connection.execute("""
                INSERT INTO students
                (roll_no, name, program, year, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                roll_no,
                name,
                program,
                year,
                "pending"
            ))

    connection.commit()
    connection.close()


# Send OTP
def send_otp_email(receiver_email, otp, faculty_name):

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise RuntimeError("Email configuration is missing.")

    message = EmailMessage()

    message["Subject"] = (
        "Hridya University | Faculty Password Reset OTP"
    )

    message["From"] = MAIL_USERNAME
    message["To"] = receiver_email

    message.set_content(
        f"""HRIDYA UNIVERSITY

HU Security Team

PASSWORD RESET REQUEST

Hello {faculty_name},

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

    logo_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../images/logo.png"
        )
    )

    if os.path.exists(logo_path):

        message.add_alternative(
            f"""
            <html>
            <body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:30px;">
            <div style="max-width:600px;margin:auto;background:#fff;padding:30px;border-radius:10px;">
            <div style="text-align:center;background:#171717;color:#fff;padding:20px;">
            <img src="cid:hu_logo" width="70" height="70">
            <h2>Faculty Security Lab</h2>
            </div>

            <h2>Password Reset Request</h2>

            <p>Hello {faculty_name},</p>

            <p>We received a request to reset the password associated with your faculty account.</p>

            <p>Your verification code is:</p>

            <div style="font-size:32px;font-weight:bold;letter-spacing:8px;text-align:center;padding:20px;background:#f3f3f3;">
            {otp}
            </div>

            <p><strong>This OTP is valid for 5 minutes.</strong></p>

            <p>If you did not request a password reset, you can safely ignore this email.</p>

            <p>For your security, do not share this OTP with anyone.</p>

            <p>Hridya University<br>Faculty Security Lab</p>
            </div>
            </body>
            </html>
            """,
            subtype="html"
        )

        with open(logo_path, "rb") as file:
            logo = MIMEImage(file.read())

        logo.add_header(
            "Content-ID",
            "<hu_logo>"
        )

        logo.add_header(
            "Content-Disposition",
            "inline",
            filename="logo.png"
        )

        message.attach(logo)

    with smtplib.SMTP(
        "smtp.gmail.com",
        587,
        timeout=20
    ) as server:

        server.starttls()

        server.login(
            MAIL_USERNAME,
            MAIL_PASSWORD
        )

        server.send_message(message)


# Home
@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "message": "Faculty Security Lab Backend"
    })


# Login
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

    faculty = connection.execute("""
        SELECT *
        FROM faculty
        WHERE (faculty_id = ? OR email = ?)
        AND password = ?
    """, (
        faculty_id,
        faculty_id,
        password
    )).fetchone()

    connection.close()

    if not faculty:

        return jsonify({
            "success": False,
            "message": "Invalid Faculty ID or password."
        }), 401

    session["faculty_id"] = faculty["faculty_id"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "faculty_id": faculty["faculty_id"],
        "full_name": faculty["full_name"],
        "email": faculty["email"],
        "department": faculty["department"],
        "designation": faculty["designation"],
        "photo_url": (
            f"http://127.0.0.1:5000/images/{faculty['photo']}"
            if faculty["photo"]
            else None
        )
    })


# Current faculty
@app.route("/api/me", methods=["GET"])
def get_current_faculty():

    faculty_id = session.get("faculty_id")

    if not faculty_id:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    connection = get_db_connection()

    faculty = connection.execute("""
        SELECT
            faculty_id,
            full_name,
            email,
            department,
            designation,
            photo
        FROM faculty
        WHERE faculty_id = ?
    """, (faculty_id,)).fetchone()

    connection.close()

    if not faculty:

        session.clear()

        return jsonify({
            "success": False,
            "message": "Faculty account not found."
        }), 401

    return jsonify({
        "success": True,
        "faculty_id": faculty["faculty_id"],
        "full_name": faculty["full_name"],
        "email": faculty["email"],
        "department": faculty["department"],
        "designation": faculty["designation"],
        "photo_url": (
            f"http://127.0.0.1:5000/images/{faculty['photo']}"
            if faculty["photo"]
            else None
        )
    })


# Logout
@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


# Register
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

    faculty_id = faculty_id.strip()
    full_name = full_name.strip()
    email = email.strip().lower()
    department = department.strip()
    designation = designation.strip()

    try:

        connection = get_db_connection()

        connection.execute("""
            INSERT INTO faculty
            (
                faculty_id,
                full_name,
                email,
                department,
                designation,
                password
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            faculty_id,
            full_name,
            email,
            department,
            designation,
            password
        ))

        connection.commit()
        connection.close()

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


# Hierarchy
@app.route("/api/hierarchy", methods=["GET"])
def get_hierarchy():

    return jsonify(PROGRAMS)


# Timetable
@app.route("/api/timetable", methods=["GET"])
def get_timetable():

    faculty_id = session.get("faculty_id")

    if not faculty_id:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    connection = get_db_connection()

    lectures = connection.execute("""
        SELECT
            id,
            subject,
            program,
            specialization,
            year,
            room,
            start_time,
            end_time
        FROM timetable
        WHERE faculty_id = ?
        ORDER BY start_time
    """, (faculty_id,)).fetchall()

    connection.close()

    now = datetime.now()

    result = []

    for lecture in lectures:

        try:
            start = datetime.fromisoformat(
                lecture["start_time"]
            )

            end = datetime.fromisoformat(
                lecture["end_time"]
            )

            if now >= end:
                status = "completed"
            elif now >= start:
                status = "ongoing"
            else:
                status = "upcoming"

        except ValueError:
            status = "upcoming"

        branch = lecture["program"]

        if lecture["specialization"]:
            branch += " · " + lecture["specialization"]

        result.append({
            "id": "LEC-" + str(lecture["id"]),
            "database_id": lecture["id"],
            "name": lecture["subject"],
            "start_time": lecture["start_time"],
            "end_time": lecture["end_time"],
            "branch": branch,
            "program": lecture["program"],
            "specialization": lecture["specialization"],
            "year": lecture["year"],
            "room": lecture["room"],
            "status": status
        })

    return jsonify(result)


# Students
@app.route("/api/students", methods=["GET"])
def get_students():

    faculty_id = session.get("faculty_id")

    if not faculty_id:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    connection = get_db_connection()

    faculty = connection.execute("""
        SELECT department
        FROM faculty
        WHERE faculty_id = ?
    """, (faculty_id,)).fetchone()

    if not faculty:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Faculty account not found."
        }), 404

    students = connection.execute("""
        SELECT
            id,
            roll_no,
            name,
            photo,
            program,
            specialization,
            year,
            status
        FROM students
        WHERE program = ?
        ORDER BY roll_no
    """, (
        faculty["department"],
    )).fetchall()

    connection.close()

    result = []

    for student in students:

        result.append({
            "id": str(student["id"]),
            "roll_no": student["roll_no"],
            "name": student["name"],
            "photo_url": (
                f"http://127.0.0.1:5000/images/{student['photo']}"
                if student["photo"]
                else None
            ),
            "faculty": "Academic",
            "branch": student["program"],
            "specialization": student["specialization"],
            "year": student["year"],
            "status": student["status"] or "pending"
        })

    return jsonify(result)


# Attendance
@app.route("/api/attendance", methods=["GET"])
def get_attendance():

    faculty_id = session.get("faculty_id")

    if not faculty_id:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    lecture_id = request.args.get("lecture_id")

    if not lecture_id:

        return jsonify({
            "success": False,
            "message": "Lecture ID is required."
        }), 400

    if lecture_id.startswith("LEC-"):
        lecture_id = lecture_id.replace("LEC-", "", 1)

    connection = get_db_connection()

    lecture = connection.execute("""
        SELECT *
        FROM timetable
        WHERE id = ?
        AND faculty_id = ?
    """, (
        lecture_id,
        faculty_id
    )).fetchone()

    if not lecture:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Lecture not found."
        }), 404

    students = connection.execute("""
        SELECT
            s.id,
            s.roll_no,
            s.name,
            s.photo,
            s.program,
            s.specialization,
            s.year,
            COALESCE(a.status, 'pending') AS attendance_status
        FROM students s
        LEFT JOIN attendance a
            ON a.student_id = s.id
            AND a.lecture_id = ?
        WHERE s.program = ?
        AND s.year = ?
        ORDER BY s.roll_no
    """, (
        lecture_id,
        lecture["program"],
        lecture["year"]
    )).fetchall()

    connection.close()

    result = []

    for student in students:

        result.append({
            "id": str(student["id"]),
            "roll_no": student["roll_no"],
            "name": student["name"],
            "photo_url": (
                f"http://127.0.0.1:5000/images/{student['photo']}"
                if student["photo"]
                else None
            ),
            "program": student["program"],
            "branch": student["program"],
            "specialization": student["specialization"],
            "year": student["year"],
            "status": student["attendance_status"]
        })

    return jsonify(result)


# Mark attendance
@app.route("/api/attendance", methods=["POST"])
def mark_attendance():

    faculty_id = session.get("faculty_id")

    if not faculty_id:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    data = request.get_json() or {}

    student_id = data.get("student_id")
    lecture_id = data.get("lecture_id")

    if not student_id or not lecture_id:

        return jsonify({
            "success": False,
            "message": "Student ID and lecture ID are required."
        }), 400

    if str(lecture_id).startswith("LEC-"):
        lecture_id = str(lecture_id).replace("LEC-", "", 1)

    connection = get_db_connection()

    lecture = connection.execute("""
        SELECT *
        FROM timetable
        WHERE id = ?
        AND faculty_id = ?
    """, (
        lecture_id,
        faculty_id
    )).fetchone()

    if not lecture:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Lecture not found."
        }), 404

    student = connection.execute("""
        SELECT *
        FROM students
        WHERE id = ?
        AND program = ?
        AND year = ?
    """, (
        student_id,
        lecture["program"],
        lecture["year"]
    )).fetchone()

    if not student:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Student does not belong to this lecture."
        }), 403

    try:
        start_time = datetime.fromisoformat(
            lecture["start_time"]
        )
    except ValueError:
        start_time = datetime.now()

    window_end = start_time + timedelta(hours=3)

    now = datetime.now()

    if now < start_time or now > window_end:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Attendance window has closed."
        }), 409

    try:

        connection.execute("""
            INSERT INTO attendance
            (
                lecture_id,
                student_id,
                faculty_id,
                status,
                marked_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            lecture_id,
            student_id,
            faculty_id,
            "present",
            datetime.now().isoformat()
        ))

        connection.execute("""
            UPDATE students
            SET status = 'present'
            WHERE id = ?
        """, (
            student_id,
        ))

        connection.commit()
        connection.close()

        return jsonify({
            "success": True,
            "status": "present",
            "message": "Attendance marked successfully."
        }), 200

    except sqlite3.IntegrityError:

        connection.close()

        return jsonify({
            "success": False,
            "status": "present",
            "message": "Attendance already marked."
        }), 409


# Forgot password
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

    faculty = connection.execute("""
        SELECT id, email, full_name
        FROM faculty
        WHERE email = ?
    """, (email,)).fetchone()

    connection.close()

    if not faculty:

        return jsonify({
            "success": False,
            "message": "No faculty account was found with this email."
        }), 404

    otp = str(
        secrets.randbelow(900000) + 100000
    )

    otp_storage[email] = {
        "otp": otp,
        "verified": False,
        "created_at": time.time(),
        "attempts": 0
    }

    try:

        send_otp_email(
            email,
            otp,
            faculty["full_name"]
        )

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
    })


# Verify OTP
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

    if (
        time.time()
        - stored_data["created_at"]
        > OTP_EXPIRY_SECONDS
    ):

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

    if not secrets.compare_digest(
        stored_data["otp"],
        otp
    ):

        stored_data["attempts"] += 1

        remaining = (
            MAX_OTP_ATTEMPTS
            - stored_data["attempts"]
        )

        return jsonify({
            "success": False,
            "message": f"Invalid OTP. {remaining} attempt(s) remaining."
        }), 401

    stored_data["verified"] = True

    return jsonify({
        "success": True,
        "message": "OTP verified successfully."
    })


# Profile photo
@app.route("/api/profile/photo", methods=["POST"])
def upload_profile_photo():

    faculty_id = session.get("faculty_id")

    if not faculty_id:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    if "photo" not in request.files:

        return jsonify({
            "success": False,
            "message": "No photo selected."
        }), 400

    photo = request.files["photo"]

    if photo.filename == "":

        return jsonify({
            "success": False,
            "message": "No photo selected."
        }), 400

    connection = get_db_connection()

    faculty = connection.execute("""
        SELECT id
        FROM faculty
        WHERE faculty_id = ?
    """, (
        faculty_id,
    )).fetchone()

    if not faculty:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Faculty account not found."
        }), 404

    image_filename = f"image{faculty['id']}.png"

    images_folder = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../images"
        )
    )

    os.makedirs(
        images_folder,
        exist_ok=True
    )

    photo.save(
        os.path.join(
            images_folder,
            image_filename
        )
    )

    connection.execute("""
        UPDATE faculty
        SET photo = ?
        WHERE faculty_id = ?
    """, (
        image_filename,
        faculty_id
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Profile photo uploaded successfully.",
        "photo_url": (
            f"http://127.0.0.1:5000/images/{image_filename}"
        )
    })


# Serve images
@app.route("/images/<filename>")
def serve_image(filename):

    images_folder = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../images"
        )
    )

    return send_from_directory(
        images_folder,
        filename
    )


# Reset password
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

    if (
        time.time()
        - stored_data["created_at"]
        > OTP_EXPIRY_SECONDS
    ):

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

    faculty = connection.execute("""
        SELECT id
        FROM faculty
        WHERE email = ?
    """, (
        email,
    )).fetchone()

    if not faculty:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Faculty account not found."
        }), 404

    connection.execute("""
        UPDATE faculty
        SET password = ?
        WHERE email = ?
    """, (
        password,
        email
    ))

    connection.commit()
    connection.close()

    del otp_storage[email]

    return jsonify({
        "success": True,
        "message": "Password reset successfully."
    })


# Start server
if __name__ == "__main__":

    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )