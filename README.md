b<div align="center">

<img src="assets/CodeAlpha-logo.png" width="250" alt="CodeAlpha Logo"/>

  <br/>

  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=44&pause=1000&color=06B6D4&center=true&vCenter=true&width=600&lines=Secure+Coding+Review" alt="Secure Coding Review"/>

</div>

🔐 CodeAlpha SecureWeb-App
A web application security project demonstrating the difference between a Vulnerable Version and a Secure Version of a Faculty Secure Portal.
🔴 Vulnerable Version
The vulnerable version intentionally contains common security weaknesses to demonstrate how insecure implementations can create risks.
Examples:

Plaintext password storage
SQL injection risk
Missing CSRF protection
Plaintext OTP storage
Weak file upload validation
Default session settings
No rate limiting
Limited security headers
Debug mode enabled
Weak secret fallbacks

🟢 Secure Version
The secure version applies security controls to address the identified weaknesses.
Examples:

Password hashing
Parameterized SQL queries
CSRF token validation
Hashed OTP storage
File type/size/content validation
Secure session cookies
Login and OTP rate limiting
Security headers
Debug mode disabled
Environment-based secrets

⚖️ Vulnerable vs Secure



Area
🔴 Vulnerable
🟢 Secure




Passwords
Plaintext
Hashed


SQL
Injection risk
Parameterized queries


CSRF
Missing
Token validation


OTP
Plaintext
Hashed


File Upload
Weak validation
Strict validation


Sessions
Default
Secure settings


Rate Limiting
Missing
Login/OTP throttling


Headers
Limited
Security headers


Debug
Enabled
Disabled


Secrets
Weak fallback
Environment-based



🛡️ Security Audit
The application was reviewed for:

Authentication & password security
SQL Injection
CSRF
OTP security
File upload security
Session security
Rate limiting
Security headers
Debug configuration
Secret management

🧰 Tech Stack
Frontend: HTML, CSS, JavaScript
Backend: Python, Flask
Database: SQLite
⚠️ Note
The Vulnerable Version is intended only for controlled local security testing and should not be used with real credentials or production data.
🎯 Objective
To practically demonstrate:
Vulnerability → Security Audit → Fix → Secure Implementation
