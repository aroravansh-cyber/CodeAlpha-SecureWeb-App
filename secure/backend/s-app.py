from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import secrets
import smtplib
import time
import re
import hmac
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError("FLASK_SECRET_KEY must be set and at least 32 characters long.")

app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=2 * 1024 * 1024
)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5500")
CORS(
    app,
    origins=[FRONTEND_ORIGIN],
    supports_credentials=True
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "faculty.db")
IMAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "images"))
os.makedirs(IMAGE_DIR, exist_ok=True)

ATTENDANCE_WINDOW_HOURS = 3
OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 60
LOGIN_WINDOW_SECONDS = 300
LOGIN_MAX_ATTEMPTS = 5

LOGIN_ATTEMPTS = {}
OTP_SEND_ATTEMPTS = {}

PROGRAMS = {
    "Engineering": {
        "B.Tech CSE": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
        "B.Tech Cybersecurity": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
        "B.Tech AI/ML": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
        "B.Tech ECE": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
        "B.Tech Mechanical": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
        "B.Tech Civil": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    },
    "Computer Applications": {
        "BCA": ["1st Year", "2nd Year", "3rd Year"]
        ,
        "MCA": ["1st Year", "2nd Year"]
    },
    "Management": {
        "BBA": ["1st Year", "2nd Year", "3rd Year"],
        "MBA": ["1st Year", "2nd Year"]
    },
    "Commerce": {
        "B.Com": ["1st Year", "2nd Year", "3rd Year"],
        "M.Com": ["1st Year", "2nd Year"]
    },
    "Law": {
        "LLB": ["1st Year", "2nd Year", "3rd Year"],
        "BA LLB": ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year"]
    },
    "Medical": {
        "MBBS": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    },
    "Nursing": {
        "B.Sc Nursing": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    },
    "Pharmacy": {
        "B.Pharm": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    },
    "Science": {
        "B.Sc": ["1st Year", "2nd Year", "3rd Year"]
    },
    "Agriculture": {
        "B.Sc Agriculture": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    },
    "Education": {
        "B.Ed": ["1st Year", "2nd Year"]
    },
    "Humanities": {
        "BA": ["1st Year", "2nd Year", "3rd Year"]
    },
    "Social Sciences": {
        "BA": ["1st Year", "2nd Year", "3rd Year"]
    },
    "Hotel Management": {
        "BHM": ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    }
}

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def password_is_hashed(value):
    return isinstance(value, str) and (
        value.startswith("scrypt:") or
        value.startswith("pbkdf2:")
    )

def hash_password(password):
    return generate_password_hash(password, method="scrypt")

def valid_password(password):
    return isinstance(password, str) and 12 <= len(password) <= 128

def valid_email(email):
    return bool(re.fullmatch(r"[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,63}", email))

def client_key():
    return request.remote_addr or "unknown"

def rate_limited(store, key, limit, window):
    now = time.time()
    bucket = store.get(key, [])
    bucket = [stamp for stamp in bucket if now - stamp < window]
    if len(bucket) >= limit:
        store[key] = bucket
        return True
    bucket.append(now)
    store[key] = bucket
    return False

def json_error(message, status):
    return jsonify({"success": False, "message": message}), status

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            password TEXT NOT NULL,
            photo TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            photo TEXT,
            program TEXT NOT NULL,
            specialization TEXT,
            year TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            program TEXT NOT NULL,
            specialization TEXT,
            year TEXT NOT NULL,
            room TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            faculty_id TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_at TEXT NOT NULL,
            UNIQUE (lecture_id, student_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_hash TEXT NOT NULL,
            expires_at REAL NOT NULL,
            attempts INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    seed_demo_data()
    migrate_plaintext_passwords()

def seed_demo_data():
    conn = get_db()
    cursor = conn.cursor()

    faculty_data = [
        ("HU-FAC-001", "Demo Faculty", "faculty@hridyauniversity.edu", "B.Tech Cybersecurity", "Assistant Professor", "FacultyDemo!2026"),
        ("HU-FAC-002", "Dr. Ankit Sharma", "ankit@hridyauniversity.edu", "B.Tech CSE", "Associate Professor", "FacultyDemo!2026"),
        ("HU-FAC-003", "Dr. Neha Kapoor", "neha@hridyauniversity.edu", "B.Tech AI/ML", "Assistant Professor", "FacultyDemo!2026"),
        ("HU-FAC-004", "Prof. Rohan Mehta", "rohan@hridyauniversity.edu", "BCA", "Assistant Professor", "FacultyDemo!2026"),
        ("HU-FAC-005", "Dr. Priyanka Joshi", "priyanka@hridyauniversity.edu", "B.Pharm", "Professor", "FacultyDemo!2026"),
        ("HU-FAC-006", "Dr. Kavita Singh", "kavita@hridyauniversity.edu", "B.Sc Nursing", "Associate Professor", "FacultyDemo!2026")
    ]

    for faculty in faculty_data:
        cursor.execute("""
            INSERT OR IGNORE INTO faculty (
                faculty_id, full_name, email, department, designation, password
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            faculty[0],
            faculty[1],
            faculty[2],
            faculty[3],
            faculty[4],
            hash_password(faculty[5])
        ))

    programs = [
        ("B.Tech Cybersecurity", "Cybersecurity"),
        ("B.Tech CSE", "Computer Science"),
        ("B.Tech AI/ML", "Artificial Intelligence"),
        ("BCA", "Computer Applications"),
        ("B.Pharm", "Pharmacy"),
        ("B.Sc Nursing", "Nursing")
    ]

    first_names = [
        "Aarav", "Vivaan", "Aditya", "Arjun", "Rohan",
        "Rahul", "Karan", "Ankit", "Yash", "Harsh",
        "Aryan", "Dev", "Akash", "Mohit", "Vansh",
        "Shivam", "Nikhil", "Ayush", "Abhishek", "Sahil"
    ]

    last_names = [
        "Sharma", "Singh", "Kumar", "Verma", "Gupta",
        "Joshi", "Mehta", "Kapoor", "Malhotra", "Chauhan"
    ]

    student_count = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    if student_count == 0:
        roll_number = 1
        for program, specialization in programs:
            for year in ["1st Year", "2nd Year", "3rd Year", "4th Year"]:
                if program in ["BCA", "B.Pharm", "B.Sc Nursing"] and year == "4th Year":
                    continue

                for _ in range(10):
                    first = first_names[(roll_number - 1) % len(first_names)]
                    last = last_names[(roll_number - 1) % len(last_names)]
                    name = f"{first} {last}"
                    roll_no = (
                        f"HU-{program.replace(' ', '').replace('.', '')[:4].upper()}"
                        f"-{roll_number:03d}"
                    )

                    cursor.execute("""
                        INSERT INTO students (
                            roll_no, name, program, specialization, year, status
                        )
                        VALUES (?, ?, ?, ?, ?, 'pending')
                    """, (roll_no, name, program, specialization, year))
                    roll_number += 1

    timetable_count = cursor.execute("SELECT COUNT(*) FROM timetable").fetchone()[0]

    if timetable_count == 0:
        today = datetime.now().date()
        demo_lectures = [
            (
                "HU-FAC-001", "Network Security", "B.Tech Cybersecurity",
                "Cybersecurity", "2nd Year", "Lab 301",
                datetime.combine(today, datetime.min.time()).replace(hour=9).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(hour=10).isoformat(timespec="seconds")
            ),
            (
                "HU-FAC-001", "Ethical Hacking", "B.Tech Cybersecurity",
                "Cybersecurity", "2nd Year", "Lab 302",
                datetime.combine(today, datetime.min.time()).replace(hour=11).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(hour=12).isoformat(timespec="seconds")
            ),
            (
                "HU-FAC-001", "Digital Forensics", "B.Tech Cybersecurity",
                "Cybersecurity", "2nd Year", "Room 205",
                datetime.combine(today, datetime.min.time()).replace(hour=14).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(hour=15).isoformat(timespec="seconds")
            ),
            (
                "HU-FAC-001", "Cyber Security Lab", "B.Tech Cybersecurity",
                "Cybersecurity", "2nd Year", "Cyber Lab",
                datetime.combine(today, datetime.min.time()).replace(hour=16).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(hour=17).isoformat(timespec="seconds")
            )
        ]

        for lecture in demo_lectures:
            cursor.execute("""
                INSERT INTO timetable (
                    faculty_id, subject, program, specialization, year,
                    room, start_time, end_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, lecture)

    conn.commit()
    conn.close()

def migrate_plaintext_passwords():
    conn = get_db()
    rows = conn.execute("SELECT id, password FROM faculty").fetchall()

    for row in rows:
        stored = row["password"]
        if not password_is_hashed(stored):
            conn.execute(
                "UPDATE faculty SET password = ? WHERE id = ?",
                (hash_password(stored), row["id"])
            )

    conn.commit()
    conn.close()

def row_to_dict(row):
    return dict(row) if row else None

def current_faculty():
    faculty_id = session.get("faculty_id")
    if not faculty_id:
        return None

    conn = get_db()
    faculty = conn.execute(
        "SELECT * FROM faculty WHERE faculty_id = ?",
        (faculty_id,)
    ).fetchone()
    conn.close()
    return faculty

def login_required():
    return current_faculty()

def parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None

def iso_now():
    return datetime.now().isoformat(timespec="seconds")

def lecture_status(start_time, end_time):
    start = parse_iso_datetime(start_time)
    end = parse_iso_datetime(end_time)

    if not start or not end:
        return "upcoming"

    now = datetime.now()
    if now < start:
        return "upcoming"
    if now <= end:
        return "ongoing"
    return "completed"

def attendance_is_open(start_time):
    start = parse_iso_datetime(start_time)
    if not start:
        return False

    now = datetime.now()
    deadline = start + timedelta(hours=ATTENDANCE_WINDOW_HOURS)
    return start <= now <= deadline

def allowed_image_content(file_bytes, extension):
    if extension == "png":
        return file_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in {"jpg", "jpeg"}:
        return file_bytes.startswith(b"\xff\xd8\xff")
    if extension == "webp":
        return len(file_bytes) >= 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP"
    return False

def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "CodeAlpha SecureWeb backend is running.",
        "database": os.path.basename(DATABASE)
    })

@app.route("/api/csrf", methods=["GET"])
def get_csrf():
    return jsonify({"success": True, "csrf_token": csrf_token()})

@app.before_request
def csrf_protection():
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return

    exempt = {
        "/api/login",
        "/api/register",
        "/api/forgot-password",
        "/api/verify-otp",
        "/api/reset-password"
    }

    if request.path in exempt:
        return

    expected = session.get("csrf_token")
    supplied = request.headers.get("X-CSRF-Token")

    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        return json_error("CSRF validation failed.", 403)

@app.route("/api/login", methods=["POST"])
def login():
    key = f"login:{client_key()}"

    if rate_limited(LOGIN_ATTEMPTS, key, LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_SECONDS):
        return json_error("Too many login attempts. Try again later.", 429)

    data = request.get_json(silent=True) or {}

    login_value = (
        data.get("faculty_id") or
        data.get("email") or
        data.get("username") or
        ""
    ).strip().lower()

    password = data.get("password") or ""

    if not login_value or not password or len(login_value) > 320 or len(password) > 128:
        return json_error("Invalid credentials.", 401)

    conn = get_db()
    faculty = conn.execute("""
        SELECT *
        FROM faculty
        WHERE faculty_id = ? OR email = ?
    """, (login_value, login_value)).fetchone()
    conn.close()

    valid = bool(faculty) and check_password_hash(faculty["password"], password)

    if not valid:
        return json_error("Invalid credentials.", 401)

    LOGIN_ATTEMPTS.pop(key, None)
    session.clear()
    session["faculty_id"] = faculty["faculty_id"]
    session["csrf_token"] = secrets.token_urlsafe(32)

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "faculty": {
            "faculty_id": faculty["faculty_id"],
            "full_name": faculty["full_name"],
            "email": faculty["email"],
            "department": faculty["department"],
            "designation": faculty["designation"],
            "photo_url": f"/images/{secure_filename(faculty['photo'])}" if faculty["photo"] else ""
        }
    })

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/api/me", methods=["GET"])
def me():
    faculty = login_required()
    if not faculty:
        return json_error("Not authenticated.", 401)

    return jsonify({
        "success": True,
        "faculty": {
            "faculty_id": faculty["faculty_id"],
            "full_name": faculty["full_name"],
            "email": faculty["email"],
            "department": faculty["department"],
            "designation": faculty["designation"],
            "photo_url": f"/images/{secure_filename(faculty['photo'])}" if faculty["photo"] else ""
        }
    })

@app.route("/api/register", methods=["POST"])
def register():
    if rate_limited(LOGIN_ATTEMPTS, f"register:{client_key()}", 5, 600):
        return json_error("Too many registration attempts. Try again later.", 429)

    data = request.get_json(silent=True) or {}

    faculty_id = (data.get("faculty_id") or data.get("staff_id") or "").strip()
    full_name = (data.get("full_name") or data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    department = (data.get("department") or data.get("program") or "").strip()
    designation = (data.get("designation") or "Assistant Professor").strip()
    password = data.get("password") or ""

    if not all([faculty_id, full_name, email, department, password]):
        return json_error("All required fields must be filled.", 400)

    if len(faculty_id) > 64 or len(full_name) > 120 or len(department) > 120 or len(designation) > 120:
        return json_error("One or more fields are too long.", 400)

    if not valid_email(email):
        return json_error("Invalid email address.", 400)

    if not valid_password(password):
        return json_error("Password must be between 12 and 128 characters.", 400)

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO faculty (
                faculty_id, full_name, email, department, designation, password
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            faculty_id,
            full_name,
            email,
            department,
            designation,
            hash_password(password)
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return json_error("Faculty ID or email already exists.", 409)

    conn.close()
    return jsonify({"success": True, "message": "Registration successful."})

@app.route("/api/hierarchy", methods=["GET"])
def hierarchy():
    if not login_required():
        return json_error("Not authenticated.", 401)
    return jsonify({"success": True, "programs": PROGRAMS})

@app.route("/api/timetable", methods=["GET"])
def timetable():
    faculty = login_required()
    if not faculty:
        return json_error("Not authenticated.", 401)

    conn = get_db()
    rows = conn.execute("""
        SELECT *
        FROM timetable
        WHERE faculty_id = ?
        ORDER BY start_time ASC
    """, (faculty["faculty_id"],)).fetchall()
    conn.close()

    lectures = []
    for row in rows:
        start_time = row["start_time"]
        end_time = row["end_time"]
        start_dt = parse_iso_datetime(start_time)
        date_value = start_dt.strftime("%Y-%m-%d") if start_dt else ""

        lectures.append({
            "id": f"LEC-{row['id']}",
            "database_id": row["id"],
            "name": row["subject"],
            "subject": row["subject"],
            "start_time": start_time,
            "end_time": end_time,
            "start": start_time,
            "end": end_time,
            "date": date_value,
            "branch": row["program"],
            "program": row["program"],
            "specialization": row["specialization"] or "",
            "year": row["year"],
            "room": row["room"] or "",
            "status": lecture_status(start_time, end_time),
            "faculty_id": faculty["faculty_id"],
            "faculty_name": faculty["full_name"],
            "designation": faculty["designation"],
            "department": faculty["department"]
        })

    return jsonify({"success": True, "timetable": lectures})

@app.route("/api/students", methods=["GET"])
def students():
    faculty = login_required()
    if not faculty:
        return json_error("Not authenticated.", 401)

    conn = get_db()
    rows = conn.execute("""
        SELECT *
        FROM students
        WHERE program = ?
        ORDER BY roll_no ASC
    """, (faculty["department"],)).fetchall()
    conn.close()

    result = []
    for row in rows:
        photo_url = f"/images/{secure_filename(row['photo'])}" if row["photo"] else ""
        result.append({
            "id": row["id"],
            "student_id": row["id"],
            "roll_no": row["roll_no"],
            "roll_number": row["roll_no"],
            "name": row["name"],
            "full_name": row["name"],
            "photo_url": photo_url,
            "program": row["program"],
            "branch": row["program"],
            "specialization": row["specialization"] or "",
            "year": row["year"],
            "study_year": row["year"],
            "status": row["status"] or "pending"
        })

    return jsonify({"success": True, "students": result})

@app.route("/api/attendance/<lecture_id>", methods=["GET"])
def get_attendance(lecture_id):
    faculty = login_required()
    if not faculty:
        return json_error("Not authenticated.", 401)

    raw_lecture_id = str(lecture_id)
    if raw_lecture_id.upper().startswith("LEC-"):
        raw_lecture_id = raw_lecture_id[4:]

    try:
        db_lecture_id = int(raw_lecture_id)
    except ValueError:
        return json_error("Invalid lecture ID.", 400)

    conn = get_db()

    lecture = conn.execute("""
        SELECT *
        FROM timetable
        WHERE id = ? AND faculty_id = ?
    """, (db_lecture_id, faculty["faculty_id"])).fetchone()

    if not lecture:
        conn.close()
        return json_error("Lecture not found.", 404)

    rows = conn.execute("""
        SELECT
            s.*,
            a.status AS attendance_status,
            a.marked_at AS marked_at
        FROM students s
        LEFT JOIN attendance a
            ON a.student_id = s.id
            AND a.lecture_id = ?
        WHERE s.program = ?
          AND s.year = ?
        ORDER BY s.roll_no ASC
    """, (
        db_lecture_id,
        lecture["program"],
        lecture["year"]
    )).fetchall()

    conn.close()

    students_result = []
    for row in rows:
        photo_url = f"/images/{secure_filename(row['photo'])}" if row["photo"] else ""
        students_result.append({
            "id": row["id"],
            "student_id": row["id"],
            "roll_no": row["roll_no"],
            "roll_number": row["roll_no"],
            "name": row["name"],
            "full_name": row["name"],
            "photo_url": photo_url,
            "program": row["program"],
            "branch": row["program"],
            "specialization": row["specialization"] or "",
            "year": row["year"],
            "study_year": row["year"],
            "status": row["attendance_status"] or "pending",
            "marked_at": row["marked_at"]
        })

    present = sum(1 for student in students_result if student["status"] == "present")
    absent = sum(1 for student in students_result if student["status"] == "absent")
    pending = sum(1 for student in students_result if student["status"] == "pending")

    start_dt = parse_iso_datetime(lecture["start_time"])
    deadline = (
        start_dt + timedelta(hours=ATTENDANCE_WINDOW_HOURS)
    ).isoformat(timespec="seconds") if start_dt else None

    lecture_data = {
        "id": f"LEC-{lecture['id']}",
        "database_id": lecture["id"],
        "subject": lecture["subject"],
        "name": lecture["subject"],
        "program": lecture["program"],
        "branch": lecture["program"],
        "specialization": lecture["specialization"] or "",
        "year": lecture["year"],
        "room": lecture["room"] or "",
        "start_time": lecture["start_time"],
        "end_time": lecture["end_time"],
        "start": lecture["start_time"],
        "end": lecture["end_time"],
        "status": lecture_status(lecture["start_time"], lecture["end_time"]),
        "attendance_open": attendance_is_open(lecture["start_time"]),
        "attendance_deadline": deadline
    }

    return jsonify({
        "success": True,
        "lecture": lecture_data,
        "students": students_result,
        "roster": students_result,
        "summary": {
            "total": len(students_result),
            "present": present,
            "absent": absent,
            "pending": pending
        }
    })

@app.route("/api/attendance", methods=["POST"])
def mark_attendance():
    faculty = login_required()
    if not faculty:
        return json_error("Not authenticated.", 401)

    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    lecture_id = data.get("lecture_id")
    status = (data.get("status") or "").lower().strip()

    if student_id is None or lecture_id is None:
        return json_error("Student and lecture are required.", 400)

    if status not in ("present", "absent"):
        return json_error("Status must be present or absent.", 400)

    try:
        raw_lecture_id = str(lecture_id)
        if raw_lecture_id.upper().startswith("LEC-"):
            raw_lecture_id = raw_lecture_id[4:]
        db_lecture_id = int(raw_lecture_id)
        db_student_id = int(student_id)
    except (TypeError, ValueError):
        return json_error("Invalid student or lecture ID.", 400)

    conn = get_db()

    lecture = conn.execute("""
        SELECT *
        FROM timetable
        WHERE id = ? AND faculty_id = ?
    """, (db_lecture_id, faculty["faculty_id"])).fetchone()

    if not lecture:
        conn.close()
        return json_error("Lecture not found.", 404)

    start_dt = parse_iso_datetime(lecture["start_time"])
    if not start_dt:
        conn.close()
        return json_error("Invalid lecture start time.", 500)

    now = datetime.now()
    deadline = start_dt + timedelta(hours=ATTENDANCE_WINDOW_HOURS)

    if now < start_dt:
        conn.close()
        return json_error("Attendance has not opened yet.", 403)

    if now > deadline:
        conn.close()
        return json_error("Attendance window has closed.", 403)

    student = conn.execute("""
        SELECT *
        FROM students
        WHERE id = ? AND program = ? AND year = ?
    """, (
        db_student_id,
        lecture["program"],
        lecture["year"]
    )).fetchone()

    if not student:
        conn.close()
        return json_error("Student does not belong to this lecture.", 403)

    marked_at = iso_now()

    existing = conn.execute("""
        SELECT id
        FROM attendance
        WHERE lecture_id = ? AND student_id = ?
    """, (db_lecture_id, db_student_id)).fetchone()

    if existing:
        conn.execute("""
            UPDATE attendance
            SET status = ?, marked_at = ?, faculty_id = ?
            WHERE id = ?
        """, (
            status,
            marked_at,
            faculty["faculty_id"],
            existing["id"]
        ))
    else:
        conn.execute("""
            INSERT INTO attendance (
                lecture_id, student_id, faculty_id, status, marked_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            db_lecture_id,
            db_student_id,
            faculty["faculty_id"],
            status,
            marked_at
        ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Student marked {status}.",
        "student_id": db_student_id,
        "lecture_id": f"LEC-{db_lecture_id}",
        "status": status,
        "marked_at": marked_at
    })

@app.route("/api/profile/photo", methods=["POST"])
def upload_profile_photo():
    faculty = login_required()
    if not faculty:
        return json_error("Not authenticated.", 401)

    if "photo" not in request.files:
        return json_error("No photo uploaded.", 400)

    file = request.files["photo"]
    if not file.filename:
        return json_error("Invalid file.", 400)

    original_name = secure_filename(file.filename)
    if not original_name:
        return json_error("Invalid filename.", 400)

    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return json_error("Only PNG, JPG, JPEG and WEBP images are allowed.", 400)

    file_bytes = file.read()
    if not file_bytes:
        return json_error("Empty file.", 400)

    if len(file_bytes) > 2 * 1024 * 1024:
        return json_error("Image is too large. Maximum size is 2 MB.", 400)

    if not allowed_image_content(file_bytes, extension):
        return json_error("Uploaded file is not a valid supported image.", 400)

    filename = f"image{faculty['id']}.{extension}"
    save_path = os.path.join(IMAGE_DIR, filename)

    with open(save_path, "wb") as output:
        output.write(file_bytes)

    conn = get_db()
    conn.execute(
        "UPDATE faculty SET photo = ? WHERE faculty_id = ?",
        (filename, faculty["faculty_id"])
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Profile photo updated.",
        "photo_url": f"/images/{filename}"
    })

@app.route("/images/<path:filename>")
def serve_image(filename):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        return json_error("Invalid image path.", 400)

    full_path = os.path.abspath(os.path.join(IMAGE_DIR, safe_name))
    image_root = os.path.abspath(IMAGE_DIR)

    if not full_path.startswith(image_root + os.sep):
        return json_error("Invalid image path.", 400)

    return send_from_directory(IMAGE_DIR, safe_name)

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    key = f"otp:{client_key()}"
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not valid_email(email):
        return json_error("If the email is registered, an OTP has been sent.", 200)

    if rate_limited(OTP_SEND_ATTEMPTS, key, 5, 600):
        return jsonify({
            "success": True,
            "message": "If the email is registered, an OTP has been sent."
        })

    conn = get_db()
    faculty = conn.execute(
        "SELECT * FROM faculty WHERE email = ?",
        (email,)
    ).fetchone()

    if not faculty:
        conn.close()
        return jsonify({
            "success": True,
            "message": "If the email is registered, an OTP has been sent."
        })

    latest = conn.execute("""
        SELECT created_at
        FROM password_otps
        WHERE email = ?
        ORDER BY id DESC
        LIMIT 1
    """, (email,)).fetchone()

    if latest and time.time() - latest["created_at"] < OTP_RESEND_SECONDS:
        conn.close()
        return jsonify({
            "success": True,
            "message": "If the email is registered, an OTP has been sent."
        })

    otp = f"{secrets.randbelow(1_000_000):06d}"
    otp_hash = hmac.new(
        SECRET_KEY.encode(),
        otp.encode(),
        "sha256"
    ).hexdigest()
    expires_at = time.time() + OTP_TTL_SECONDS

    conn.execute("DELETE FROM password_otps WHERE email = ?", (email,))
    conn.execute("""
        INSERT INTO password_otps (
            email, otp_hash, expires_at, attempts, created_at
        )
        VALUES (?, ?, ?, 0, ?)
    """, (email, otp_hash, expires_at, time.time()))
    conn.commit()
    conn.close()

    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")

    if not mail_username or not mail_password:
        return json_error("Password reset email service is not configured.", 503)

    try:
        message = EmailMessage()
        message["Subject"] = "Faculty Secure Portal - Password Reset OTP"
        message["From"] = mail_username
        message["To"] = email
        message.set_content(
            f"""Hello {faculty['full_name']},

Your password reset OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset, you can safely ignore this email.

Faculty Secure Portal
"""
        )

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(message)

    except (OSError, smtplib.SMTPException):
        conn = get_db()
        conn.execute("DELETE FROM password_otps WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return json_error("Unable to send OTP email.", 503)

    return jsonify({
        "success": True,
        "message": "If the email is registered, an OTP has been sent."
    })

def verify_otp_record(conn, email, otp):
    record = conn.execute("""
        SELECT *
        FROM password_otps
        WHERE email = ?
        ORDER BY id DESC
        LIMIT 1
    """, (email,)).fetchone()

    if not record:
        return None, "OTP verification required."

    if record["attempts"] >= OTP_MAX_ATTEMPTS:
        return None, "Maximum OTP attempts exceeded."

    if time.time() > record["expires_at"]:
        conn.execute("DELETE FROM password_otps WHERE id = ?", (record["id"],))
        conn.commit()
        return None, "OTP has expired."

    candidate_hash = hmac.new(
        SECRET_KEY.encode(),
        otp.encode(),
        "sha256"
    ).hexdigest()

    if not hmac.compare_digest(candidate_hash, record["otp_hash"]):
        conn.execute("""
            UPDATE password_otps
            SET attempts = attempts + 1
            WHERE id = ?
        """, (record["id"],))
        conn.commit()
        return None, "Invalid OTP."

    return record, None

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not valid_email(email) or not re.fullmatch(r"\d{6}", otp):
        return json_error("Invalid OTP.", 400)

    conn = get_db()
    record, error = verify_otp_record(conn, email, otp)

    if error:
        conn.close()
        return json_error(error, 400 if "required" in error or "expired" in error or "Invalid" in error else 403)

    conn.close()
    return jsonify({"success": True, "message": "OTP verified successfully."})

@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()
    new_password = data.get("new_password") or data.get("password") or ""

    if not valid_email(email) or not re.fullmatch(r"\d{6}", otp) or not valid_password(new_password):
        return json_error("Email, valid OTP and a password of 12-128 characters are required.", 400)

    conn = get_db()
    record, error = verify_otp_record(conn, email, otp)

    if error:
        conn.close()
        return json_error(error, 400 if "required" in error or "expired" in error or "Invalid" in error else 403)

    faculty = conn.execute(
        "SELECT * FROM faculty WHERE email = ?",
        (email,)
    ).fetchone()

    if not faculty:
        conn.close()
        return json_error("Unable to reset password.", 400)

    conn.execute(
        "UPDATE faculty SET password = ? WHERE email = ?",
        (hash_password(new_password), email)
    )
    conn.execute(
        "DELETE FROM password_otps WHERE email = ?",
        (email,)
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Password reset successfully."})

@app.errorhandler(404)
def not_found(error):
    return json_error("API endpoint not found.", 404)

@app.errorhandler(413)
def request_too_large(error):
    return json_error("Request is too large.", 413)

@app.errorhandler(500)
def server_error(error):
    return json_error("Internal server error.", 500)

init_db()

if __name__ == "__main__":
    print("=" * 60)
    print("CodeAlpha SecureWeb-App Backend")
    print("=" * 60)
    print(f"Database: {DATABASE}")
    print("Server: http://127.0.0.1:5000")
    print(f"Frontend: {FRONTEND_ORIGIN}")
    print("Attendance window: 3 hours")
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
