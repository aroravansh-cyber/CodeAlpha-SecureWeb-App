from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from email.message import EmailMessage
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
    "codealpha-secureweb-development-secret"
)

CORS(
    app,
    origins=["http://127.0.0.1:5500"],
    supports_credentials=True
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "faculty.db")

IMAGE_DIR = os.path.join(
    BASE_DIR,
    "..",
    "images"
)

os.makedirs(IMAGE_DIR, exist_ok=True)

ATTENDANCE_WINDOW_HOURS = 3

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
        "BCA": ["1st Year", "2nd Year", "3rd Year"],
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


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
            otp TEXT NOT NULL,
            expires_at REAL NOT NULL,
            attempts INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    seed_demo_data()


def seed_demo_data():
    conn = get_db()
    cursor = conn.cursor()

    faculty_data = [
        (
            "HU-FAC-001",
            "Demo Faculty",
            "faculty@hridyauniversity.edu",
            "B.Tech Cybersecurity",
            "Assistant Professor",
            "faculty123"
        ),
        (
            "HU-FAC-002",
            "Dr. Ankit Sharma",
            "ankit@hridyauniversity.edu",
            "B.Tech CSE",
            "Associate Professor",
            "faculty123"
        ),
        (
            "HU-FAC-003",
            "Dr. Neha Kapoor",
            "neha@hridyauniversity.edu",
            "B.Tech AI/ML",
            "Assistant Professor",
            "faculty123"
        ),
        (
            "HU-FAC-004",
            "Prof. Rohan Mehta",
            "rohan@hridyauniversity.edu",
            "BCA",
            "Assistant Professor",
            "faculty123"
        ),
        (
            "HU-FAC-005",
            "Dr. Priyanka Joshi",
            "priyanka@hridyauniversity.edu",
            "B.Pharm",
            "Professor",
            "faculty123"
        ),
        (
            "HU-FAC-006",
            "Dr. Kavita Singh",
            "kavita@hridyauniversity.edu",
            "B.Sc Nursing",
            "Associate Professor",
            "faculty123"
        )
    ]

    for faculty in faculty_data:
        cursor.execute("""
            INSERT OR IGNORE INTO faculty (
                faculty_id,
                full_name,
                email,
                department,
                designation,
                password
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, faculty)

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

    student_count = cursor.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    if student_count == 0:
        roll_number = 1

        for program, specialization in programs:
            for year in ["1st Year", "2nd Year", "3rd Year", "4th Year"]:
                if program in ["BCA", "B.Pharm", "B.Sc Nursing"]:
                    if year == "4th Year" and program == "BCA":
                        continue

                for i in range(10):
                    first = first_names[
                        (roll_number - 1) % len(first_names)
                    ]

                    last = last_names[
                        (roll_number - 1) % len(last_names)
                    ]

                    name = f"{first} {last}"

                    roll_no = (
                        f"HU-{program.replace(' ', '').replace('.', '')[:4].upper()}"
                        f"-{roll_number:03d}"
                    )

                    cursor.execute("""
                        INSERT INTO students (
                            roll_no,
                            name,
                            program,
                            specialization,
                            year,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?, 'pending')
                    """, (
                        roll_no,
                        name,
                        program,
                        specialization,
                        year
                    ))

                    roll_number += 1

    timetable_count = cursor.execute(
        "SELECT COUNT(*) FROM timetable"
    ).fetchone()[0]

    if timetable_count == 0:
        today = datetime.now().date()

        demo_lectures = [
            (
                "HU-FAC-001",
                "Network Security",
                "B.Tech Cybersecurity",
                "Cybersecurity",
                "2nd Year",
                "Lab 301",
                datetime.combine(today, datetime.min.time()).replace(
                    hour=9
                ).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(
                    hour=10
                ).isoformat(timespec="seconds")
            ),
            (
                "HU-FAC-001",
                "Ethical Hacking",
                "B.Tech Cybersecurity",
                "Cybersecurity",
                "2nd Year",
                "Lab 302",
                datetime.combine(today, datetime.min.time()).replace(
                    hour=11
                ).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(
                    hour=12
                ).isoformat(timespec="seconds")
            ),
            (
                "HU-FAC-001",
                "Digital Forensics",
                "B.Tech Cybersecurity",
                "Cybersecurity",
                "2nd Year",
                "Room 205",
                datetime.combine(today, datetime.min.time()).replace(
                    hour=14
                ).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(
                    hour=15
                ).isoformat(timespec="seconds")
            ),
            (
                "HU-FAC-001",
                "Cyber Security Lab",
                "B.Tech Cybersecurity",
                "Cybersecurity",
                "2nd Year",
                "Cyber Lab",
                datetime.combine(today, datetime.min.time()).replace(
                    hour=16
                ).isoformat(timespec="seconds"),
                datetime.combine(today, datetime.min.time()).replace(
                    hour=17
                ).isoformat(timespec="seconds")
            )
        ]

        for lecture in demo_lectures:
            cursor.execute("""
                INSERT INTO timetable (
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
            """, lecture)

    conn.commit()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None

    return dict(row)


def current_faculty():
    faculty_id = session.get("faculty_id")

    if not faculty_id:
        return None

    conn = get_db()

    faculty = conn.execute("""
        SELECT *
        FROM faculty
        WHERE faculty_id = ?
    """, (faculty_id,)).fetchone()

    conn.close()

    return faculty


def login_required():
    return current_faculty()


def parse_iso_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "")
        )
    except Exception:
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

    deadline = (
        start +
        timedelta(hours=ATTENDANCE_WINDOW_HOURS)
    )

    return start <= now <= deadline


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "CodeAlpha SecureWeb backend is running.",
        "database": os.path.basename(DATABASE)
    })


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    login_value = (
        data.get("faculty_id") or
        data.get("email") or
        data.get("username") or
        ""
    ).strip()

    password = data.get("password") or ""

    if not login_value or not password:
        return jsonify({
            "success": False,
            "message": "Faculty ID/email and password are required."
        }), 400

    conn = get_db()

    faculty = conn.execute("""
        SELECT *
        FROM faculty
        WHERE (
            faculty_id = ?
            OR email = ?
        )
        AND password = ?
    """, (
        login_value,
        login_value,
        password
    )).fetchone()

    conn.close()

    if not faculty:
        return jsonify({
            "success": False,
            "message": "Invalid credentials."
        }), 401

    session.clear()
    session["faculty_id"] = faculty["faculty_id"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "faculty": {
            "faculty_id": faculty["faculty_id"],
            "full_name": faculty["full_name"],
            "email": faculty["email"],
            "department": faculty["department"],
            "designation": faculty["designation"],
            "photo_url": (
                f"/images/{faculty['photo']}"
                if faculty["photo"]
                else ""
            )
        }
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


@app.route("/api/me", methods=["GET"])
def me():
    faculty = login_required()

    if not faculty:
        return jsonify({
            "success": False,
            "message": "Not authenticated."
        }), 401

    return jsonify({
        "success": True,
        "faculty": {
            "faculty_id": faculty["faculty_id"],
            "full_name": faculty["full_name"],
            "email": faculty["email"],
            "department": faculty["department"],
            "designation": faculty["designation"],
            "photo_url": (
                f"/images/{faculty['photo']}"
                if faculty["photo"]
                else ""
            )
        }
    })


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    faculty_id = (
        data.get("faculty_id") or
        data.get("staff_id") or
        ""
    ).strip()

    full_name = (
        data.get("full_name") or
        data.get("name") or
        ""
    ).strip()

    email = (
        data.get("email") or
        ""
    ).strip().lower()

    department = (
        data.get("department") or
        data.get("program") or
        ""
    ).strip()

    designation = (
        data.get("designation") or
        "Assistant Professor"
    ).strip()

    password = data.get("password") or ""

    if not all([
        faculty_id,
        full_name,
        email,
        department,
        password
    ]):
        return jsonify({
            "success": False,
            "message": "All required fields must be filled."
        }), 400

    conn = get_db()

    try:
        conn.execute("""
            INSERT INTO faculty (
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

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Faculty ID or email already exists."
        }), 409

    conn.close()

    return jsonify({
        "success": True,
        "message": "Registration successful."
    })


@app.route("/api/hierarchy", methods=["GET"])
def hierarchy():
    faculty = login_required()

    if not faculty:
        return jsonify({
            "success": False,
            "message": "Not authenticated."
        }), 401

    return jsonify({
        "success": True,
        "programs": PROGRAMS
    })


@app.route("/api/timetable", methods=["GET"])
def timetable():
    faculty = login_required()

    if not faculty:
        return jsonify({
            "success": False,
            "message": "Not authenticated."
        }), 401

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM timetable
        WHERE faculty_id = ?
        ORDER BY start_time ASC
    """, (
        faculty["faculty_id"],
    )).fetchall()

    conn.close()

    lectures = []

    for row in rows:
        start_time = row["start_time"]
        end_time = row["end_time"]

        start_dt = parse_iso_datetime(start_time)

        date_value = (
            start_dt.strftime("%Y-%m-%d")
            if start_dt
            else ""
        )

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
            "status": lecture_status(
                start_time,
                end_time
            ),
            "faculty_id": faculty["faculty_id"],
            "faculty_name": faculty["full_name"],
            "designation": faculty["designation"],
            "department": faculty["department"]
        })

    return jsonify({
        "success": True,
        "timetable": lectures
    })


@app.route("/api/students", methods=["GET"])
def students():
    faculty = login_required()

    if not faculty:
        return jsonify({
            "success": False,
            "message": "Not authenticated."
        }), 401

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM students
        WHERE program = ?
        ORDER BY roll_no ASC
    """, (
        faculty["department"],
    )).fetchall()

    conn.close()

    result = []

    for row in rows:
        photo_url = ""

        if row["photo"]:
            photo_url = f"/images/{row['photo']}"

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

    return jsonify({
        "success": True,
        "students": result
    })


@app.route("/api/attendance/<lecture_id>", methods=["GET"])
def get_attendance(lecture_id):
    faculty = login_required()

    if not faculty:
        return jsonify({
            "success": False,
            "message": "Not authenticated."
        }), 401

    raw_lecture_id = str(lecture_id)

    if raw_lecture_id.upper().startswith("LEC-"):
        raw_lecture_id = raw_lecture_id[4:]

    try:
        db_lecture_id = int(raw_lecture_id)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid lecture ID."
        }), 400

    conn = get_db()

    lecture = conn.execute("""
        SELECT *
        FROM timetable
        WHERE id = ?
          AND faculty_id = ?
    """, (
        db_lecture_id,
        faculty["faculty_id"]
    )).fetchone()

    if not lecture:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Lecture not found."
        }), 404

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
        photo_url = ""

        if row["photo"]:
            photo_url = f"/images/{row['photo']}"

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

    present = sum(
        1
        for student in students_result
        if student["status"] == "present"
    )

    absent = sum(
        1
        for student in students_result
        if student["status"] == "absent"
    )

    pending = sum(
        1
        for student in students_result
        if student["status"] == "pending"
    )

    start_dt = parse_iso_datetime(
        lecture["start_time"]
    )

    deadline = None

    if start_dt:
        deadline = (
            start_dt +
            timedelta(hours=ATTENDANCE_WINDOW_HOURS)
        ).isoformat(timespec="seconds")

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
        "status": lecture_status(
            lecture["start_time"],
            lecture["end_time"]
        ),
        "attendance_open": attendance_is_open(
            lecture["start_time"]
        ),
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
        return jsonify({
            "success": False,
            "message": "Not authenticated."
        }), 401

    data = request.get_json(silent=True) or {}

    student_id = data.get("student_id")
    lecture_id = data.get("lecture_id")

    status = (
        data.get("status") or
        ""
    ).lower().strip()

    if not student_id or not lecture_id:
        return jsonify({
            "success": False,
            "message": "Student and lecture are required."
        }), 400

    if status not in ("present", "absent"):
        return jsonify({
            "success": False,
            "message": "Status must be present or absent."
        }), 400

    raw_lecture_id = str(lecture_id)

    if raw_lecture_id.upper().startswith("LEC-"):
        raw_lecture_id = raw_lecture_id[4:]

    try:
        db_lecture_id = int(raw_lecture_id)
        db_student_id = int(student_id)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid student or lecture ID."
        }), 400

    conn = get_db()

    lecture = conn.execute("""
        SELECT *
        FROM timetable
        WHERE id = ?
          AND faculty_id = ?
    """, (
        db_lecture_id,
        faculty["faculty_id"]
    )).fetchone()

    if not lecture:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Lecture not found."
        }), 404

    start_dt = parse_iso_datetime(
        lecture["start_time"]
    )

    if not start_dt:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid lecture start time."
        }), 500

    now = datetime.now()

    deadline = (
        start_dt +
        timedelta(hours=ATTENDANCE_WINDOW_HOURS)
    )

    if now < start_dt:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Attendance has not opened yet."
        }), 403

    if now > deadline:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Attendance window has closed."
        }), 403

    student = conn.execute("""
        SELECT *
        FROM students
        WHERE id = ?
          AND program = ?
          AND year = ?
    """, (
        db_student_id,
        lecture["program"],
        lecture["year"]
    )).fetchone()

    if not student:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Student does not belong to this lecture."
        }), 403

    marked_at = iso_now()

    existing = conn.execute("""
        SELECT id
        FROM attendance
        WHERE lecture_id = ?
          AND student_id = ?
    """, (
        db_lecture_id,
        db_student_id
    )).fetchone()

    if existing:
        conn.execute("""
            UPDATE attendance
            SET
                status = ?,
                marked_at = ?,
                faculty_id = ?
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
                lecture_id,
                student_id,
                faculty_id,
                status,
                marked_at
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
        return jsonify({
            "success": False,
            "message": "Not authenticated."
        }), 401

    if "photo" not in request.files:
        return jsonify({
            "success": False,
            "message": "No photo uploaded."
        }), 400

    file = request.files["photo"]

    if not file.filename:
        return jsonify({
            "success": False,
            "message": "Invalid file."
        }), 400

    allowed_extensions = {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }

    original_name = file.filename

    extension = (
        original_name.rsplit(".", 1)[-1].lower()
        if "." in original_name
        else ""
    )

    if extension not in allowed_extensions:
        return jsonify({
            "success": False,
            "message": "Only PNG, JPG, JPEG and WEBP images are allowed."
        }), 400

    filename = f"image{faculty['id']}.{extension}"

    save_path = os.path.join(
        IMAGE_DIR,
        filename
    )

    file.save(save_path)

    conn = get_db()

    conn.execute("""
        UPDATE faculty
        SET photo = ?
        WHERE faculty_id = ?
    """, (
        filename,
        faculty["faculty_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Profile photo updated.",
        "photo_url": f"/images/{filename}"
    })


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(
        IMAGE_DIR,
        filename
    )


@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}

    email = (
        data.get("email") or
        ""
    ).strip().lower()

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    conn = get_db()

    faculty = conn.execute("""
        SELECT *
        FROM faculty
        WHERE email = ?
    """, (
        email,
    )).fetchone()

    if not faculty:
        conn.close()

        return jsonify({
            "success": True,
            "message": "If the email is registered, an OTP has been sent."
        })

    otp = str(
        secrets.randbelow(900000) + 100000
    )

    expires_at = time.time() + 300

    conn.execute("""
        DELETE FROM password_otps
        WHERE email = ?
    """, (
        email,
    ))

    conn.execute("""
        INSERT INTO password_otps (
            email,
            otp,
            expires_at,
            attempts
        )
        VALUES (?, ?, ?, 0)
    """, (
        email,
        otp,
        expires_at
    ))

    conn.commit()
    conn.close()

    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")

    if not mail_username or not mail_password:
        print(
            "MAIL_USERNAME / MAIL_PASSWORD not configured."
        )

        print(
            f"DEVELOPMENT OTP for {email}: {otp}"
        )

        return jsonify({
            "success": True,
            "message": "OTP generated. Configure email credentials to send it."
        })

    try:
        message = EmailMessage()

        message["Subject"] = (
            "Faculty Secure Portal - Password Reset OTP"
        )

        message["From"] = mail_username
        message["To"] = email

        message.set_content(
            f"""
Hello {faculty['full_name']},

Your password reset OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset,
you can safely ignore this email.

Faculty Secure Portal
"""
        )

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:
            server.starttls()

            server.login(
                mail_username,
                mail_password
            )

            server.send_message(message)

    except Exception as error:
        print("SMTP ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Unable to send OTP email."
        }), 500

    return jsonify({
        "success": True,
        "message": "OTP sent successfully."
    })


@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or {}

    email = (
        data.get("email") or
        ""
    ).strip().lower()

    otp = (
        data.get("otp") or
        ""
    ).strip()

    if not email or not otp:
        return jsonify({
            "success": False,
            "message": "Email and OTP are required."
        }), 400

    conn = get_db()

    record = conn.execute("""
        SELECT *
        FROM password_otps
        WHERE email = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        email,
    )).fetchone()

    if not record:
        conn.close()

        return jsonify({
            "success": False,
            "message": "OTP not found."
        }), 400

    if record["attempts"] >= 5:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Maximum OTP attempts exceeded."
        }), 403

    if time.time() > record["expires_at"]:
        conn.execute("""
            DELETE FROM password_otps
            WHERE id = ?
        """, (
            record["id"],
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "success": False,
            "message": "OTP has expired."
        }), 400

    if otp != record["otp"]:
        conn.execute("""
            UPDATE password_otps
            SET attempts = attempts + 1
            WHERE id = ?
        """, (
            record["id"],
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid OTP."
        }), 400

    conn.close()

    return jsonify({
        "success": True,
        "message": "OTP verified successfully."
    })


@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}

    email = (
        data.get("email") or
        ""
    ).strip().lower()

    otp = (
        data.get("otp") or
        ""
    ).strip()

    new_password = (
        data.get("new_password") or
        data.get("password") or
        ""
    )

    if not email or not otp or not new_password:
        return jsonify({
            "success": False,
            "message": "Email, OTP and new password are required."
        }), 400

    conn = get_db()

    record = conn.execute("""
        SELECT *
        FROM password_otps
        WHERE email = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        email,
    )).fetchone()

    if not record:
        conn.close()

        return jsonify({
            "success": False,
            "message": "OTP verification required."
        }), 400

    if record["attempts"] >= 5:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Maximum OTP attempts exceeded."
        }), 403

    if time.time() > record["expires_at"]:
        conn.close()

        return jsonify({
            "success": False,
            "message": "OTP has expired."
        }), 400

    if otp != record["otp"]:
        conn.execute("""
            UPDATE password_otps
            SET attempts = attempts + 1
            WHERE id = ?
        """, (
            record["id"],
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid OTP."
        }), 400

    faculty = conn.execute("""
        SELECT *
        FROM faculty
        WHERE email = ?
    """, (
        email,
    )).fetchone()

    if not faculty:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Faculty account not found."
        }), 404

    conn.execute("""
        UPDATE faculty
        SET password = ?
        WHERE email = ?
    """, (
        new_password,
        email
    ))

    conn.execute("""
        DELETE FROM password_otps
        WHERE email = ?
    """, (
        email,
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Password reset successfully."
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "API endpoint not found."
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "message": "Internal server error."
    }), 500


init_db()


if __name__ == "__main__":
    print("=" * 60)
    print("CodeAlpha SecureWeb-App Backend")
    print("=" * 60)
    print(f"Database: {DATABASE}")
    print("Server: http://127.0.0.1:5000")
    print("Frontend: http://127.0.0.1:5500")
    print("Attendance window: 3 hours")
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )