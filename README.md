<div align="center">

<img src="assets/CodeAlpha-logo.png" width="220" alt="CodeAlpha Logo"/>

<br><br>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=38&pause=1000&color=06B6D4&center=true&vCenter=true&width=700&lines=CodeAlpha+Secure+Coding+Review" alt="Secure Coding Review"/>

<br>


</div>

<br>

---

<br>

## About the Project

A **Faculty Secure Portal** built twice: first full of real-world security mistakes, then rebuilt after a proper security audit. Placing both versions side by side shows exactly how an attack works and how the fix stops it.

<br>

<p align="center">
  <img src="assets/flow.svg" width="800" alt="Vulnerable App to Security Audit to Security Fixes to Secure App"/>
</p>

<br>

> [!WARNING]
> The vulnerable version is intentionally insecure. Run it only on your own machine for testing. Never deploy it.

<br>

---

<br>

## Vulnerable vs Secure

| Security Area | Vulnerable Version | Secure Version |
|:---|:---|:---|
| **Passwords** | Stored as plaintext | Hashed |
| **SQL Queries** | Injection risk | Parameterized queries |
| **CSRF** | No protection | Token validation |
| **OTP** | Stored as plaintext | Hashed |
| **File Upload** | Weak validation | Type, size and content checks |
| **Sessions** | Default settings | Secure cookies |
| **Rate Limiting** | Missing | Login and OTP throttling |
| **Security Headers** | Limited | Enabled |
| **Debug Mode** | Enabled | Disabled |
| **Secrets** | Weak fallback | Environment variables |

<br>

---

<br>

## See the Difference

### SQL Injection Example

<details>
<summary><b>Click to expand</b></summary>

<br>

```python
# Vulnerable: user input goes straight into the query
query = f"SELECT * FROM users WHERE username = '{username}'"

# Secure: parameterized query
db.execute("SELECT * FROM users WHERE username = ?", (username,))
```

Entering `' OR '1'='1` in the login form logs you in on the vulnerable version. The secure version rejects it.

</details>

<br>

---

<br>

## Tech Stack

| Layer | Technology |
|:---|:---|
| **Frontend** | HTML, CSS, JavaScript |
| **Backend** | Python, Flask |
| **Database** | SQLite |
| **Environment** | Local security lab |

<br>

---

<br>

## Project Structure

```
CodeAlpha-SecureWeb-App/
├── assets/
│   ├── CodeAlpha-logo.png
│   └── flow.svg
├── vulnerable/
│   ├── frontend/
│   └── backend/
│       └── v-app.py
└── secure/
    ├── frontend/
    └── backend/
        └── s-app.py
```

<br>

---

<br>

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/CodeAlpha-SecureWeb-App.git
cd CodeAlpha-SecureWeb-App
```

### 2. Install dependencies

```bash
pip install flask
```

### 3. Run the vulnerable version (local testing only)

```bash
python vulnerable/backend/v-app.py
```

### 4. Run the secure version

```bash
export SECRET_KEY="your-long-random-secret"
python secure/backend/s-app.py
```

<br>

---

<br>

## Disclaimer

This project is for **educational and authorized security testing only**. The author is not responsible for misuse.
