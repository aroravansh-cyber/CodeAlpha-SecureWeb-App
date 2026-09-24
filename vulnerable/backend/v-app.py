from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

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
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

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
            "full_name": faculty["full_name"]
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
    password = data.get("password")

    if not faculty_id or not full_name or not email or not department or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400

    try:
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO faculty
            (faculty_id, full_name, email, department, password)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                faculty_id,
                full_name,
                email,
                department,
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

# Start server
if __name__ == "__main__":
    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )