from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Temporary demo faculty accounts
FACULTY = {
    "faculty@hu.edu": "faculty123",
    "admin@hu.edu": "admin123"
}


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Faculty Security Lab Backend"
    })


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

    # Demo authentication
    if faculty_id in FACULTY and FACULTY[faculty_id] == password:
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "faculty_id": faculty_id
        }), 200

    return jsonify({
        "success": False,
        "message": "Invalid Faculty ID or password."
    }), 401

#Registration Form

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

    print("New Faculty Registration:")
    print("Faculty ID:", faculty_id)
    print("Full Name:", full_name)
    print("Email:", email)
    print("Department:", department)
    print("Password:", password)

    return jsonify({
        "success": True,
        "message": "Registration received successfully.",
        "faculty_id": faculty_id
    }), 201


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )