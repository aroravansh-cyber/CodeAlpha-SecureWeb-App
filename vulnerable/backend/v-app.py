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


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )